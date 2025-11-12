import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import textwrap
import mplcursors

# ---------------- Adjustable Parameters ---------------- #
wrap_width = 6        # max characters per line inside node
max_lines = 3         # max lines shown inside node

# ---------------- Graph Building ---------------- #
def build_graph(data):
    G = nx.DiGraph()
    root = data.get("name", "Chatbot")
    G.add_node(root, layer=0, type="root", full_text=root)

    for gi, group in enumerate(data.get("qa_groups", []), start=1):
        group_node = f"Group: {group['group_name']}"
        G.add_node(group_node, layer=1, type="group", full_text=group_node)
        G.add_edge(root, group_node)

        for q in group.get("questions", []):
            q_node = f"Q: {q}"
            G.add_node(q_node, layer=2, type="question", full_text=q)
            G.add_edge(group_node, q_node)

        for a in group.get("answers", []):
            a_node = f"A: {a}"
            G.add_node(a_node, layer=3, type="answer", full_text=a)
            G.add_edge(group_node, a_node)

        def add_followups(followups, parent, depth):
            for f in followups:
                f_node = f"Follow: {f['question']}"
                G.add_node(f_node, layer=depth, type="followup", full_text=f['question'])
                G.add_edge(parent, f_node)

                a_node = f"A: {f['answer']}"
                G.add_node(a_node, layer=depth+1, type="answer", full_text=f['answer'])
                G.add_edge(f_node, a_node)

                add_followups(f.get("children", []), f_node, depth+1)

        add_followups(group.get("follow_ups", []), group_node, 4)

    return G

# ---------------- Layout ---------------- #
def wrap_and_truncate(text, width=wrap_width, max_lines=max_lines):
    """Wrap text and truncate with ... if too many lines."""
    lines = textwrap.wrap(text, width=width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] += "..."
    return "\n".join(lines)

def wrap_labels(G):
    """Create labels for nodes, truncated with ellipsis if too long."""
    return {n: wrap_and_truncate(G.nodes[n]['full_text']) for n in G.nodes}

def custom_layout_scaled(G):
    """Uniform node size layout with extra spacing for green (question) nodes."""
    layers = {}
    for node, data in G.nodes(data=True):
        layer = data.get("layer", 0)
        layers.setdefault(layer, []).append(node)

    pos = {}
    for layer, nodes in layers.items():
        n_nodes = len(nodes)
        extra_space = 0.05  # extra padding for green nodes
        y_positions = []
        if n_nodes == 1:
            y_positions = [0.5]
        else:
            y_step = 1 / (n_nodes - 1)
            for i, node in enumerate(nodes):
                y = 1 - i * y_step
                if G.nodes[node]['type'] == 'question':
                    y -= extra_space
                y_positions.append(y)
        for node, y in zip(nodes, y_positions):
            pos[node] = (layer, y)
    return pos

# ---------------- Visualization ---------------- #
def visualize_graph(G, canvas_frame):
    fig, ax = plt.subplots(figsize=(18, 10))
    pos = custom_layout_scaled(G)

    color_map = {
        "root": "gold",
        "group": "skyblue",
        "question": "lightgreen",
        "answer": "orange",
        "followup": "violet"
    }
    node_colors = [color_map.get(G.nodes[n].get("type", "group"), "gray") for n in G.nodes]
    node_sizes = [1500 for _ in G.nodes]  # uniform node size
    labels = wrap_labels(G)

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, edgecolors="black", ax=ax)
    nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, alpha=0.6, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_family="sans-serif", ax=ax)

    ax.set_title("Rule-Based Chatbot as Neural Network", fontsize=18)
    ax.axis("off")

    # Hover tooltips for full text
    cursor = mplcursors.cursor(ax.collections, hover=True)
    def show_text(sel):
        node_idx = sel.index
        node = list(G.nodes)[node_idx]
        full_text = G.nodes[node]['full_text']
        sel.annotation.set_text(full_text)
    cursor.connect("add", show_text)

    # Embed in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# ---------------- GUI ---------------- #
class ChatbotVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chatbot Visualizer")
        self.geometry("1200x800")

        # Menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load JSON", command=self.load_json)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # Canvas Frame
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

    def load_json(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filepath:
            return
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            # Clear previous canvas
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            G = build_graph(data)
            visualize_graph(G, self.canvas_frame)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON:\n{e}")

# ---------------- Main ---------------- #
if __name__ == "__main__":
    app = ChatbotVisualizer()
    app.mainloop()
