# Visualizer.py
"""
QA Neural Network Visualizer (Tkinter + Matplotlib + NetworkX)

Neural-network-style layered layout:
- AI root → Groups → Question variants ↔ Answer variants → Follow-up Q/A
- Roots and branches are logical; only Q/A nodes exist visually
- Distinct colors for root vs follow-up questions/answers
- Camera-style zoom & pan
- Initial viewport fits exactly all nodes (no padding)
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ------------------- Config -------------------
MAX_WORDS_PER_LINE = 4
MAX_LETTERS_TOTAL = 60

BASE_LABEL_SIZE = 8.0
BASE_NODE_EDGEWIDTH = 2.0
BASE_LINEWIDTH = 1.5

INITIAL_SCALE = 1.0
SCALE_STEP = 1.15

AI_LEFT_OFFSET = -8
LAYER_X_SPACING = 5.0
VERTICAL_SPACING = 1.5
VERTICAL_MARGIN = 0.05

MIN_SCALE = 0.1
MAX_SCALE = 50.0

# ------------------- UI -------------------
root = tk.Tk()
root.title("QA Neural Network Visualizer")
root.geometry("1400x900")
root.configure(bg="#222222")

toolbar = tk.Frame(root, bg="#222222")
toolbar.pack(side=tk.TOP, fill=tk.X)
load_btn = tk.Button(toolbar, text="Load JSON File", bg="#444444", fg="white",
                     activebackground="#555555", activeforeground="white")
load_btn.pack(side=tk.LEFT, padx=8, pady=6)

# ------------------- Graph / state -------------------
G = nx.DiGraph()
base_pos = {}
base_node_sizes = []
node_list = []
label_artists = {}
node_collection = None
edge_collection = None

scale = INITIAL_SCALE
view_center = (0.0, 0.0)
base_span_x = 1.0
base_span_y = 1.0

is_dragging = False
last_mouse = None

fig = None
ax = None
canvas = None

# ------------------- Helpers -------------------
def format_label(raw: str) -> str:
    if raw is None: raw = ""
    raw = str(raw)
    if len(raw) > MAX_LETTERS_TOTAL: raw = raw[:MAX_LETTERS_TOTAL] + "..."
    words = raw.split()
    lines = [" ".join(words[i:i+MAX_WORDS_PER_LINE]) for i in range(0, len(words), MAX_WORDS_PER_LINE)]
    return "\n".join(lines)

def safe_text_from_node_id(node_id: str) -> str:
    for p in ("Q: ", "A: ", "Group: ", "AI: "):
        if node_id.startswith(p):
            return node_id[len(p):]
    return node_id

# ------------------- Graph building -------------------
def add_followup_nodes(fu_node, parent_answers, level):
    q_text = fu_node.get("question", "").strip()
    a_text = fu_node.get("answer", "").strip()
    current_q_nodes = []
    current_a_nodes = []

    if q_text:
        q_id = f"Q: {q_text}"
        G.add_node(q_id, type="follow_up_question", level=level)
        for pa in parent_answers:
            G.add_edge(pa, q_id)
        current_q_nodes.append(q_id)

    if a_text:
        a_id = f"A: {a_text}"
        G.add_node(a_id, type="follow_up_answer", level=level+1)
        for qn in current_q_nodes or parent_answers:
            G.add_edge(qn, a_id)
        current_a_nodes.append(a_id)

    # Fully connect questions ↔ answers
    for qn in current_q_nodes:
        for an in current_a_nodes:
            G.add_edge(qn, an)
    for an in current_a_nodes:
        for qn in current_q_nodes:
            G.add_edge(an, qn)

    next_parents = current_a_nodes or current_q_nodes or parent_answers
    for child in fu_node.get("children", []):
        add_followup_nodes(child, next_parents, level+2)

def add_group_nodes(group, parent=None, level=0):
    group_id = f"Group: {group.get('group_name','')}"
    G.add_node(group_id, type="group", level=level)
    if parent:
        G.add_edge(parent, group_id)

    questions = group.get("questions", [])
    answers = group.get("answers", [])
    q_nodes = []
    a_nodes = []

    for q in questions:
        q_id = f"Q: {q}"
        G.add_node(q_id, type="root_question", level=level+1)
        G.add_edge(group_id, q_id)
        q_nodes.append(q_id)

    for a in answers:
        a_id = f"A: {a}"
        G.add_node(a_id, type="root_answer", level=level+2)
        a_nodes.append(a_id)

    for q in q_nodes:
        for a in a_nodes:
            G.add_edge(q, a)
    for a in a_nodes:
        for q in q_nodes:
            G.add_edge(a, q)

    for fu in group.get("follow_ups", []):
        add_followup_nodes(fu, a_nodes, level+3)

# ------------------- Layout -------------------
def compute_base_layout():
    _compute_layered_layout()

def _compute_layered_layout():
    global base_pos
    base_pos.clear()
    layers = {}
    for n, attr in G.nodes(data=True):
        lvl = attr.get('level', 0)
        layers.setdefault(lvl, []).append(n)

    for lvl in sorted(layers.keys()):
        nodes = layers[lvl]
        count = len(nodes)
        y_step = 1.0 / (count + 1)
        for i, n in enumerate(nodes):
            y = 0.5 - (i+1)*y_step
            x = AI_LEFT_OFFSET + lvl * LAYER_X_SPACING
            base_pos[n] = (x, y)

# ------------------- Prepare drawing -------------------
def prepare_drawing_state():
    global node_list, base_node_sizes, label_artists, base_span_x, base_span_y, view_center
    node_list = list(G.nodes())
    base_node_sizes = []
    sizes_map = {
        'ai_root':5000, 'group':4000,
        'root_question':3000, 'root_answer':2400,
        'follow_up_question':3000, 'follow_up_answer':2400
    }
    for n in node_list:
        t = G.nodes[n].get('type')
        base_node_sizes.append(sizes_map.get(t,2000))

    xs = [p[0] for p in base_pos.values()] if base_pos else [0]
    ys = [p[1] for p in base_pos.values()] if base_pos else [0]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    # Exact fit, no padding
    base_span_x = max(1.0e-3, (maxx - minx))
    base_span_y = max(1.0e-3, (maxy - miny))
    view_center = ((minx+maxx)/2.0,(miny+maxy)/2.0)
    label_artists.clear()

# ------------------- Draw -------------------
def get_node_color(n):
    t = G.nodes[n].get('type')
    colors = {
        'ai_root':"#FFAA00",
        'group':"#1f77b4",
        'root_question':"#2ca02c",
        'root_answer':"#d62728",
        'follow_up_question':"#17becf",
        'follow_up_answer':"#ff7f0e"
    }
    return colors.get(t,"#888888")

def draw_graph():
    global node_collection, edge_collection, label_artists, fig, ax, canvas
    ax.clear()
    fig.patch.set_facecolor("#222222")
    ax.set_facecolor("#222222")
    ax.set_axis_off()

    half_x = (base_span_x / 2.0) / scale
    half_y = (base_span_y / 2.0) / scale
    cx, cy = view_center
    ax.set_xlim(cx-half_x, cx+half_x)
    ax.set_ylim(cy-half_y, cy+half_y)

    pos = base_pos.copy()
    node_sizes_now = [s*(scale**2) for s in base_node_sizes]

    node_collection = nx.draw_networkx_nodes(G, pos=pos, nodelist=node_list,
                                             node_color=[get_node_color(n) for n in node_list],
                                             node_size=node_sizes_now,
                                             edgecolors='black',
                                             linewidths=BASE_NODE_EDGEWIDTH*scale,
                                             ax=ax)
    edge_collection = nx.draw_networkx_edges(G, pos=pos, ax=ax,
                                             edge_color='white', width=BASE_LINEWIDTH*scale, arrows=False)
    label_artists.clear()
    fontsize_now = max(1.0, BASE_LABEL_SIZE*scale)
    for n in node_list:
        x, y = pos[n]
        txt = format_label(safe_text_from_node_id(n))
        ta = ax.text(x, y, txt, ha='center', va='center', fontsize=fontsize_now, color='white', fontweight='bold')
        label_artists[n] = ta
    canvas.draw_idle()

# ------------------- Interaction -------------------
def on_scroll(event):
    global scale, view_center
    zoom_in = getattr(event, 'step',0) > 0
    new_scale = min(MAX_SCALE, scale*SCALE_STEP) if zoom_in else max(MIN_SCALE, scale/SCALE_STEP)
    mx, my = getattr(event,'xdata',None), getattr(event,'ydata',None)
    if mx is None or my is None: mx,my=view_center
    old_scale = scale
    scale = new_scale
    if old_scale != 0:
        view_center = (mx+(view_center[0]-mx)*(old_scale/scale),
                       my+(view_center[1]-my)*(old_scale/scale))
    draw_graph()

def on_press(event):
    global is_dragging,last_mouse
    if getattr(event,'button',None)==1:
        is_dragging=True
        last_mouse=(event.x,event.y)

def on_release(event):
    global is_dragging
    is_dragging=False

def on_motion(event):
    global last_mouse,view_center
    if not is_dragging or last_mouse is None or event.x is None or event.y is None: return
    dx, dy = event.x-last_mouse[0], event.y-last_mouse[1]
    last_mouse=(event.x,event.y)
    w,h = max(1,canvas.get_tk_widget().winfo_width()), max(1,canvas.get_tk_widget().winfo_height())
    dx_data = dx*((base_span_x/scale)/w)
    dy_data = dy*((base_span_y/scale)/h)   # fixed: positive dy moves graph up
    view_center = (view_center[0]-dx_data, view_center[1]-dy_data)
    draw_graph()

# ------------------- Load JSON -------------------
def on_load_click():
    global fig,ax,canvas,scale,view_center,base_pos
    path=filedialog.askopenfilename(title="Open QA JSON",filetypes=[("JSON files","*.json")])
    if not path: return
    try:
        with open(path,"r",encoding="utf-8") as fh:
            data=json.load(fh)
    except Exception as e:
        messagebox.showerror("Failed to open JSON",str(e))
        return

    G.clear()
    ai_name = f"AI: {data.get('name','Unknown')}"
    G.add_node(ai_name, type='ai_root', level=0)

    for group in data.get("qa_groups",[]):
        add_group_nodes(group,parent=ai_name,level=1)

    compute_base_layout()
    prepare_drawing_state()

    try:
        if fig is not None: plt.close(fig)
    except: pass
    fig=plt.figure(figsize=(14,9))
    ax=fig.add_subplot(111)
    canvas=FigureCanvasTkAgg(fig,master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH,expand=True)

    canvas.mpl_connect("scroll_event",on_scroll)
    canvas.mpl_connect("button_press_event",on_press)
    canvas.mpl_connect("button_release_event",on_release)
    canvas.mpl_connect("motion_notify_event",on_motion)

    scale=INITIAL_SCALE
    draw_graph()

load_btn.config(command=on_load_click)
root.mainloop()
