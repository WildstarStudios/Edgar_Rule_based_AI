import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from ai_engine import AdvancedChatbot

class ModelManager:
    def __init__(self, parent, on_model_change=None):
        self.parent = parent
        self.on_model_change = on_model_change
        self.models_folder = "models"
        self.current_model = None
        self.available_models = []
        
        # Create models folder if it doesn't exist
        os.makedirs(self.models_folder, exist_ok=True)
        
        self.load_available_models()
    
    def load_available_models(self):
        """Load all available models from the models folder"""
        self.available_models = []
        if os.path.exists(self.models_folder):
            for file in os.listdir(self.models_folder):
                if file.endswith('.json'):
                    model_name = file[:-5]  # Remove .json extension
                    self.available_models.append(model_name)
        
        # Sort models alphabetically
        self.available_models.sort()
    
    def get_model_path(self, model_name):
        """Get the full path for a model file"""
        return os.path.join(self.models_folder, f"{model_name}.json")
    
    def create_model(self, name, description=""):
        """Create a new model with the given name and description"""
        if not name.strip():
            raise ValueError("Model name cannot be empty")
        
        if name in self.available_models:
            raise ValueError(f"Model '{name}' already exists")
        
        # Create model data structure
        model_data = {
            'name': name,
            'description': description,
            'created_at': str(os.path.getctime(__file__)),
            'qa_groups': []
        }
        
        # Save model file
        model_path = self.get_model_path(name)
        with open(model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        # Refresh available models
        self.load_available_models()
        return model_data
    
    def load_model(self, name):
        """Load a model by name"""
        if name not in self.available_models:
            raise ValueError(f"Model '{name}' not found")
        
        model_path = self.get_model_path(name)
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        
        self.current_model = name
        return model_data
    
    def save_model(self, name, qa_groups):
        """Save QA groups to a model"""
        model_path = self.get_model_path(name)
        
        # Load existing model data or create new
        if os.path.exists(model_path):
            with open(model_path, 'r') as f:
                model_data = json.load(f)
        else:
            model_data = {
                'name': name,
                'description': f"Model {name}",
                'created_at': str(os.path.getctime(__file__)),
                'qa_groups': []
            }
        
        # Update QA groups
        model_data['qa_groups'] = qa_groups
        model_data['updated_at'] = str(os.path.getctime(__file__))
        
        # Save model file
        with open(model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        return model_data
    
    def delete_model(self, name):
        """Delete a model"""
        if name not in self.available_models:
            raise ValueError(f"Model '{name}' not found")
        
        model_path = self.get_model_path(name)
        os.remove(model_path)
        self.load_available_models()
        
        # If we deleted the current model, clear it
        if self.current_model == name:
            self.current_model = None

class CreateModelDialog:
    def __init__(self, parent, on_create=None):
        self.on_create = on_create
        
        self.window = tk.Toplevel(parent)
        self.window.title("Create New Model")
        self.window.geometry("500x300")
        self.window.minsize(400, 250)
        self.window.configure(bg='#2d2d5a')
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window()
        
        self.setup_ui()
        
        self.window.bind('<Return>', lambda e: self.create_model())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.window.focus_set()
    
    def center_window(self):
        self.window.update_idletasks()
        parent = self.window.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window, bg='#2d2d5a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(
            main_frame,
            text="Create New AI Model",
            font=('Arial', 16, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w', pady=(0, 20))
        
        # Model name
        name_frame = tk.Frame(main_frame, bg='#2d2d5a')
        name_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            name_frame,
            text="Model Name:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w')
        
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(
            name_frame,
            textvariable=self.name_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.name_entry.pack(fill=tk.X, pady=(5, 0))
        self.name_entry.focus_set()
        
        # Description
        desc_frame = tk.Frame(main_frame, bg='#2d2d5a')
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        tk.Label(
            desc_frame,
            text="Description:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w')
        
        self.desc_text = scrolledtext.ScrolledText(
            desc_frame,
            height=6,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2d2d5a')
        button_frame.pack(fill=tk.X)
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="💾 Create Model",
            command=self.create_model,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
    
    def create_model(self):
        name = self.name_var.get().strip()
        description = self.desc_text.get('1.0', tk.END).strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter a model name.")
            self.name_entry.focus_set()
            return
        
        try:
            if self.on_create:
                self.on_create(name, description)
            self.window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            self.name_entry.focus_set()

class FollowUpEditor:
    def __init__(self, parent, followup_data=None, on_save=None):
        self.on_save = on_save
        self.followup_data = followup_data or []
        self.selected_node = None
        self.unsaved_changes = {}  # Track unsaved changes per node
        
        self.window = tk.Toplevel(parent)
        self.window.title("Follow-up Tree Editor")
        self.window.geometry("800x600")
        self.window.minsize(700, 500)
        self.window.configure(bg='#1a1a2e')
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window()
        
        self.setup_ui()
        if followup_data:
            self.load_data()
        
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def center_window(self):
        self.window.update_idletasks()
        parent = self.window.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)  # Header
        main_frame.rowconfigure(1, weight=1)  # Content
        main_frame.rowconfigure(2, weight=0)  # Buttons
        
        # Header
        header = tk.Frame(main_frame, bg='#1a1a2e')
        header.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        
        tk.Label(
            header,
            text="Follow-up Conversation Tree",
            font=('Arial', 16, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).pack(side=tk.LEFT)
        
        # Content area
        content = tk.Frame(main_frame, bg='#1a1a2e')
        content.grid(row=1, column=0, sticky='nsew', pady=(0, 15))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)
        
        # Tree panel
        self.setup_tree_panel(content)
        
        # Editor panel
        self.setup_editor_panel(content)
        
        # Action buttons
        self.setup_action_buttons(main_frame)
    
    def setup_tree_panel(self, parent):
        tree_frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        tree_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(1, weight=1)
        
        # Tree header with buttons
        tree_header = tk.Frame(tree_frame, bg='#252547')
        tree_header.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        
        tk.Label(
            tree_header,
            text="Conversation Flow",
            font=('Arial', 12, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(side=tk.LEFT)
        
        tree_buttons = tk.Frame(tree_header, bg='#252547')
        tree_buttons.pack(side=tk.RIGHT)
        
        tk.Button(
            tree_buttons,
            text="+ Root",
            command=self.add_root_node,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9),
            padx=12,
            pady=4
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            tree_buttons,
            text="+ Branch",
            command=self.add_child_node,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9),
            padx=12,
            pady=4
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            tree_buttons,
            text="− Delete",
            command=self.delete_node,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9),
            padx=12,
            pady=4
        ).pack(side=tk.LEFT)
        
        # Tree widget container
        tree_container = tk.Frame(tree_frame, bg='#252547')
        tree_container.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Style the treeview to match our theme
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview",
            background="#2d2d5a",
            foreground="white",
            fieldbackground="#2d2d5a",
            borderwidth=0)
        style.configure("Treeview.Heading",
            background="#252547",
            foreground="white")
        style.map('Treeview', background=[('selected', '#6c63ff')])
        
        self.tree = ttk.Treeview(tree_container, show='tree', style="Treeview")
        tree_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll.grid(row=0, column=1, sticky='ns')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
    
    def setup_editor_panel(self, parent):
        editor_frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        editor_frame.grid(row=0, column=1, sticky='nsew')
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(1, weight=1)
        editor_frame.rowconfigure(3, weight=1)
        
        # Node info header
        info_frame = tk.Frame(editor_frame, bg='#252547')
        info_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        
        self.node_title = tk.Label(
            info_frame,
            text="No node selected",
            font=('Arial', 13, 'bold'),
            bg='#252547',
            fg='white'
        )
        self.node_title.pack(anchor='w')
        
        self.node_info = tk.Label(
            info_frame,
            text="Select a node to edit its content",
            font=('Arial', 10),
            bg='#252547',
            fg='#b0b0d0'
        )
        self.node_info.pack(anchor='w', pady=(2, 0))
        
        # Question editor
        q_frame = tk.Frame(editor_frame, bg='#252547')
        q_frame.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 10))
        q_frame.columnconfigure(0, weight=1)
        q_frame.rowconfigure(1, weight=1)
        
        tk.Label(
            q_frame,
            text="User's Follow-up Question:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.question_text = scrolledtext.ScrolledText(
            q_frame,
            height=5,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.question_text.grid(row=1, column=0, sticky='nsew')
        
        # Answer editor
        a_frame = tk.Frame(editor_frame, bg='#252547')
        a_frame.grid(row=2, column=0, sticky='nsew', padx=15, pady=(0, 10))
        a_frame.columnconfigure(0, weight=1)
        a_frame.rowconfigure(1, weight=1)
        
        tk.Label(
            a_frame,
            text="AI's Response:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.answer_text = scrolledtext.ScrolledText(
            a_frame,
            height=5,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.answer_text.grid(row=1, column=0, sticky='nsew')
        
        # Update button
        update_frame = tk.Frame(editor_frame, bg='#252547')
        update_frame.grid(row=3, column=0, sticky='ew', padx=15, pady=(0, 12))
        
        tk.Button(
            update_frame,
            text="💾 Update Node",
            command=self.update_node,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
    
    def setup_action_buttons(self, parent):
        button_frame = tk.Frame(parent, bg='#1a1a2e')
        button_frame.grid(row=2, column=0, sticky='e')
        
        tk.Button(
            button_frame,
            text="💾 Save Tree",
            command=self.save_tree,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10
        ).pack(side=tk.RIGHT, padx=(15, 0))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10
        ).pack(side=tk.RIGHT)
    
    def add_root_node(self):
        item = self.tree.insert('', 'end', text="🌱 New Conversation Start", values=("", ""))
        self.tree.selection_set(item)
        self.tree.focus(item)
        self.on_tree_select()
    
    def add_child_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a parent node first to add a branch.")
            return
        
        parent = selected[0]
        item = self.tree.insert(parent, 'end', text="🌿 New Branch", values=("", ""))
        self.tree.selection_set(item)
        self.tree.focus(item)
        self.on_tree_select()
        # Expand parent to show new child
        self.tree.item(parent, open=True)
    
    def delete_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a node to delete.")
            return
        
        node_text = self.tree.item(selected[0], 'text')
        if messagebox.askyesno("Confirm Delete", 
                             f"Delete '{node_text}' and all its branches?\nThis cannot be undone."):
            # Remove from unsaved changes if present
            if selected[0] in self.unsaved_changes:
                del self.unsaved_changes[selected[0]]
            
            self.tree.delete(selected[0])
            self.selected_node = None
            self.node_title.config(text="No node selected")
            self.node_info.config(text="Select a node to edit its content")
            self.question_text.delete('1.0', tk.END)
            self.answer_text.delete('1.0', tk.END)
    
    def save_current_node_changes(self):
        """Save current editor content to unsaved changes"""
        if self.selected_node:
            question = self.question_text.get('1.0', tk.END).strip()
            answer = self.answer_text.get('1.0', tk.END).strip()
            self.unsaved_changes[self.selected_node] = (question, answer)
    
    def on_tree_select(self, event=None):
        # Save changes from current node before switching
        if self.selected_node:
            self.save_current_node_changes()
        
        selected = self.tree.selection()
        if not selected:
            self.selected_node = None
            self.node_title.config(text="No node selected")
            self.node_info.config(text="Select a node to edit its content")
            self.question_text.delete('1.0', tk.END)
            self.answer_text.delete('1.0', tk.END)
            return
        
        self.selected_node = selected[0]
        item_text = self.tree.item(self.selected_node, 'text')
        
        # Update header based on node level
        parent = self.tree.parent(self.selected_node)
        if parent == '':
            self.node_title.config(text="🗣️ Conversation Starter")
            self.node_info.config(text="This starts the follow-up conversation")
        else:
            self.node_title.config(text="🌿 Conversation Branch")
            self.node_info.config(text="Continues from previous response")
        
        # Load content from unsaved changes or tree values
        if self.selected_node in self.unsaved_changes:
            question, answer = self.unsaved_changes[self.selected_node]
        else:
            values = self.tree.item(self.selected_node, 'values')
            question, answer = values if values else ("", "")
        
        self.question_text.delete('1.0', tk.END)
        self.answer_text.delete('1.0', tk.END)
        self.question_text.insert('1.0', question)
        self.answer_text.insert('1.0', answer)
    
    def update_node(self):
        if not self.selected_node:
            messagebox.showwarning("Warning", "Please select a node to update.")
            return
        
        question = self.question_text.get('1.0', tk.END).strip()
        answer = self.answer_text.get('1.0', tk.END).strip()
        
        if not question:
            messagebox.showwarning("Warning", "Question cannot be empty.")
            self.question_text.focus_set()
            return
        
        if not answer:
            messagebox.showwarning("Warning", "Answer cannot be empty.")
            self.answer_text.focus_set()
            return
        
        # Update tree item with better display text
        display_text = f"💬 {question[:40]}..." if len(question) > 40 else f"💬 {question}"
        self.tree.item(self.selected_node, text=display_text, values=(question, answer))
        
        # Remove from unsaved changes since it's now saved
        if self.selected_node in self.unsaved_changes:
            del self.unsaved_changes[self.selected_node]
        
        messagebox.showinfo("Success", "Node updated successfully!")
    
    def load_data(self):
        def add_children(parent_item, children):
            for child in children:
                question = child.get('question', '')
                answer = child.get('answer', '')
                display_text = f"💬 {question[:40]}..." if len(question) > 40 else f"💬 {question}"
                item = self.tree.insert(parent_item, 'end', text=display_text, values=(question, answer))
                add_children(item, child.get('children', []))
        
        for item in self.followup_data:
            question = item.get('question', '')
            answer = item.get('answer', '')
            display_text = f"🌱 {question[:40]}..." if len(question) > 40 else f"🌱 {question}"
            root_item = self.tree.insert('', 'end', text=display_text, values=(question, answer))
            add_children(root_item, item.get('children', []))
    
    def save_tree(self):
        def get_children(parent_item):
            children = []
            for child_id in self.tree.get_children(parent_item):
                values = self.tree.item(child_id, 'values')
                question = values[0] if values else ""
                answer = values[1] if len(values) > 1 else ""
                children.append({
                    'question': question,
                    'answer': answer,
                    'children': get_children(child_id)
                })
            return children
        
        followup_data = []
        for root_id in self.tree.get_children(''):
            values = self.tree.item(root_id, 'values')
            question = values[0] if values else ""
            answer = values[1] if len(values) > 1 else ""
            followup_data.append({
                'question': question,
                'answer': answer,
                'children': get_children(root_id)
            })
        
        if self.on_save:
            self.on_save(followup_data)
        
        # Clear unsaved changes after saving
        self.unsaved_changes.clear()
        
        messagebox.showinfo("Success", "Follow-up tree saved successfully!")
        self.window.destroy()

class QuestionAnswerEditor:
    def __init__(self, parent, item_type="question", initial_text="", on_save=None):
        self.on_save = on_save
        self.item_type = item_type
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"{item_type.title()} Editor")
        self.window.geometry("500x400")
        self.window.minsize(400, 300)
        self.window.configure(bg='#2d2d5a')
        
        # Make dialog modal and center
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window()
        
        self.setup_ui(initial_text)
        
        # Bind Enter and Escape keys
        self.window.bind('<Return>', lambda e: self.save())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        
        # Set focus to text widget
        self.text_widget.focus_set()
    
    def center_window(self):
        self.window.update_idletasks()
        parent = self.window.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self, initial_text):
        # Main container with responsive grid
        main_frame = tk.Frame(self.window, bg='#2d2d5a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)  # Text area
        main_frame.rowconfigure(1, weight=0)  # Button area
        
        # Text area with scrollbar
        text_container = tk.Frame(main_frame, bg='#2d2d5a')
        text_container.grid(row=0, column=0, sticky='nsew', pady=(0, 10))
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)
        
        self.text_widget = scrolledtext.ScrolledText(
            text_container, 
            font=('Arial', 11),
            bg='#1a1a2e', 
            fg='white',
            insertbackground='white',
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.text_widget.grid(row=0, column=0, sticky='nsew')
        self.text_widget.insert('1.0', initial_text)
        
        # Button area - ensure it's always visible
        button_frame = tk.Frame(main_frame, bg='#2d2d5a')
        button_frame.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        
        # Configure button frame columns
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)
        
        # Status label
        self.status_label = tk.Label(
            button_frame,
            text=f"Editing {self.item_type}...",
            font=('Arial', 9),
            bg='#2d2d5a',
            fg='#b0b0d0'
        )
        self.status_label.grid(row=0, column=0, sticky='w')
        
        # Action buttons
        tk.Button(
            button_frame, 
            text="❌ Cancel", 
            command=self.window.destroy,
            bg='#ff4d7d', 
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=5,
            width=8
        ).grid(row=0, column=1, padx=(10, 5))
        
        tk.Button(
            button_frame, 
            text="💾 Save", 
            command=self.save,
            bg='#00ff88', 
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=5,
            width=8
        ).grid(row=0, column=2, padx=(5, 0))
    
    def save(self):
        text = self.text_widget.get('1.0', tk.END).strip()
        if text and self.on_save:
            self.on_save(text)
            self.window.destroy()
        elif not text:
            messagebox.showwarning("Empty", f"Please enter a {self.item_type}.")
            self.text_widget.focus_set()

# ... (GroupEditor class remains mostly the same, just updating the save_group to use model manager)

class TrainingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI Training")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg='#1a1a2e')
        
        # Initialize model manager
        self.model_manager = ModelManager(root, self.on_model_changed)
        self.chatbot = AdvancedChatbot()
        self.qa_groups = []
        
        # Check if we need to create first model
        if not self.model_manager.available_models:
            self.prompt_create_first_model()
        else:
            # Load the first model by default
            self.load_model(self.model_manager.available_models[0])
        
        self.setup_gui()
    
    def prompt_create_first_model(self):
        """Prompt user to create first model if none exist"""
        messagebox.showinfo("Welcome", "No AI models found. Let's create your first model!")
        self.create_new_model()
    
    def create_new_model(self):
        """Open dialog to create a new model"""
        def on_create(name, description):
            try:
                self.model_manager.create_model(name, description)
                self.load_model(name)
                self.update_model_dropdown()
                messagebox.showinfo("Success", f"Model '{name}' created successfully!")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        CreateModelDialog(self.root, on_create)
    
    def load_model(self, model_name):
        """Load a model by name"""
        try:
            model_data = self.model_manager.load_model(model_name)
            self.qa_groups = model_data.get('qa_groups', [])
            self.current_model = model_name
            self.refresh_groups()
            self.update_model_dropdown()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def save_current_model(self):
        """Save current QA groups to the current model"""
        if not self.current_model:
            messagebox.showwarning("Warning", "No model selected. Please create or load a model first.")
            return
        
        try:
            self.model_manager.save_model(self.current_model, self.qa_groups)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save model: {str(e)}")
            return False
    
    def on_model_changed(self, model_name):
        """Callback when model is changed"""
        if model_name and model_name != self.current_model:
            # Save current model if needed
            if self.current_model and self.qa_groups:
                if not messagebox.askyesno("Save Changes", f"Save changes to current model '{self.current_model}' before switching?"):
                    self.save_current_model()
            
            self.load_model(model_name)
    
    def update_model_dropdown(self):
        """Update the model dropdown with current available models"""
        if hasattr(self, 'model_combobox'):
            self.model_combobox['values'] = self.model_manager.available_models
            if self.current_model:
                self.model_combobox.set(self.current_model)
    
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header with model selection
        self.setup_header(main_frame)
        
        # Search and actions
        self.setup_toolbar(main_frame)
        
        # Groups list
        self.setup_groups_list(main_frame)
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.pack(fill=tk.X, pady=(0, 15))
        
        # Left side - Title
        left_frame = tk.Frame(header, bg='#1a1a2e')
        left_frame.pack(side=tk.LEFT)
        
        tk.Label(
            left_frame,
            text="Edgar AI Training",
            font=('Arial', 20, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).pack(side=tk.LEFT)
        
        # Right side - Model selection and stats
        right_frame = tk.Frame(header, bg='#1a1a2e')
        right_frame.pack(side=tk.RIGHT)
        
        # Model selection
        model_frame = tk.Frame(right_frame, bg='#1a1a2e')
        model_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(
            model_frame,
            text="Model:",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_combobox = ttk.Combobox(
            model_frame,
            values=self.model_manager.available_models,
            state="readonly",
            width=15
        )
        self.model_combobox.pack(side=tk.LEFT, padx=(0, 10))
        if self.current_model:
            self.model_combobox.set(self.current_model)
        self.model_combobox.bind('<<ComboboxSelected>>', 
                               lambda e: self.on_model_changed(self.model_combobox.get()))
        
        tk.Button(
            model_frame,
            text="+ New Model",
            command=self.create_new_model,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9),
            padx=10
        ).pack(side=tk.LEFT)
        
        # Stats
        stats_frame = tk.Frame(right_frame, bg='#1a1a2e')
        stats_frame.pack(side=tk.LEFT)
        
        self.stats_vars = {}
        stats = [("Groups", "0"), ("Questions", "0"), ("Answers", "0")]
        
        for label, value in stats:
            frame = tk.Frame(stats_frame, bg='#1a1a2e')
            frame.pack(side=tk.LEFT, padx=12)
            
            var = tk.StringVar(value=value)
            tk.Label(
                frame,
                textvariable=var,
                font=('Arial', 14, 'bold'),
                bg='#1a1a2e',
                fg='#6c63ff'
            ).pack()
            
            tk.Label(
                frame,
                text=label,
                font=('Arial', 8),
                bg='#1a1a2e',
                fg='#b0b0d0'
            ).pack()
            
            self.stats_vars[label] = var
    
    def setup_toolbar(self, parent):
        toolbar = tk.Frame(parent, bg='#1a1a2e')
        toolbar.pack(fill=tk.X, pady=(0, 15))
        
        # Search section - better organized
        search_container = tk.Frame(toolbar, bg='#1a1a2e')
        search_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Search label and entry in one line
        search_line = tk.Frame(search_container, bg='#1a1a2e')
        search_line.pack(fill=tk.X)
        
        tk.Label(
            search_line,
            text="Search:",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_line,
            textvariable=self.search_var,
            width=25,
            bg='#2d2d5a',
            fg='white',
            insertbackground='white',
            font=('Arial', 9)
        )
        search_entry.pack(side=tk.LEFT, padx=(5, 15))
        self.search_var.trace('w', self.on_search)
        
        # Search mode radio buttons - closer to search bar
        self.search_mode = tk.StringVar(value="both")
        mode_frame = tk.Frame(search_line, bg='#1a1a2e')
        mode_frame.pack(side=tk.LEFT)
        
        for text, value in [("Both", "both"), ("Name", "name"), ("Desc", "description")]:
            rb = tk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.search_mode,
                value=value,
                bg='#1a1a2e',
                fg='white',
                selectcolor='#6c63ff',
                font=('Arial', 9),
                command=self.on_search  # Update search when radio button changes
            )
            rb.pack(side=tk.LEFT, padx=(0, 8))
        
        # Actions
        actions = tk.Frame(toolbar, bg='#1a1a2e')
        actions.pack(side=tk.RIGHT)
        
        tk.Button(
            actions,
            text="Import JSON",
            command=self.import_json,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9),
            padx=12
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            actions,
            text="Export JSON",
            command=self.export_json,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9),
            padx=12
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            actions,
            text="+ New Group",
            command=self.new_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15
        ).pack(side=tk.LEFT)
    
    def setup_groups_list(self, parent):
        container = tk.Frame(parent, bg='#1a1a2e')
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(container, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.scroll_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel binding
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_search(self, *args):
        self.refresh_groups()
    
    def refresh_groups(self):
        # Clear current display
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Filter groups
        search_term = self.search_var.get().lower()
        search_mode = self.search_mode.get()
        
        filtered_groups = []
        for group in self.qa_groups:
            if not search_term:
                filtered_groups.append(group)
                continue
            
            if search_mode == "both":
                match = (search_term in group['group_name'].lower() or 
                        search_term in group.get('group_description', '').lower())
            elif search_mode == "name":
                match = search_term in group['group_name'].lower()
            else:  # description
                match = search_term in group.get('group_description', '').lower()
            
            if match:
                filtered_groups.append(group)
        
        # Display groups
        for i, group in enumerate(filtered_groups):
            self.create_group_card(group, i)
        
        # Update stats
        total_questions = sum(len(g['questions']) for g in self.qa_groups)
        total_answers = sum(len(g['answers']) for g in self.qa_groups)
        
        self.stats_vars["Groups"].set(str(len(self.qa_groups)))
        self.stats_vars["Questions"].set(str(total_questions))
        self.stats_vars["Answers"].set(str(total_answers))
        
        # Update canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def create_group_card(self, group, index):
        card = tk.Frame(self.scroll_frame, bg='#252547', relief='raised', bd=1)
        card.pack(fill=tk.X, pady=4, padx=2)
        
        content = tk.Frame(card, bg='#252547')
        content.pack(fill=tk.X, padx=12, pady=10)
        
        # Header
        header = tk.Frame(content, bg='#252547')
        header.pack(fill=tk.X, pady=(0, 6))
        
        # Title and description
        text_frame = tk.Frame(header, bg='#252547')
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            text_frame,
            text=group['group_name'],
            font=('Arial', 12, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(anchor='w')
        
        if group.get('group_description'):
            tk.Label(
                text_frame,
                text=group['group_description'],
                font=('Arial', 9),
                bg='#252547',
                fg='#b0b0d0'
            ).pack(anchor='w', pady=(1, 0))
        
        # Actions
        actions = tk.Frame(header, bg='#252547')
        actions.pack(side=tk.RIGHT)
        
        tk.Button(
            actions,
            text="Edit",
            command=lambda i=index: self.edit_group(i),
            bg='#6c63ff',
            fg='white',
            font=('Arial', 8),
            padx=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            actions,
            text="Delete",
            command=lambda i=index: self.delete_group(i),
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 8),
            padx=8
        ).pack(side=tk.LEFT)
        
        # Stats
        stats = tk.Frame(content, bg='#252547')
        stats.pack(fill=tk.X)
        
        followup_count = self.count_followup_nodes(group.get('follow_ups', []))
        stats_text = f"Questions: {len(group['questions'])} | Answers: {len(group['answers'])} | Topic: {group['topic']} | Follow-ups: {followup_count}"
        tk.Label(
            stats,
            text=stats_text,
            font=('Arial', 8),
            bg='#252547',
            fg='#b0b0d0'
        ).pack(anchor='w')
    
    def count_followup_nodes(self, data):
        count = 0
        for item in data:
            count += 1  # Count current node
            count += self.count_followup_nodes(item.get('children', []))  # Count children recursively
        return count
    
    def new_group(self):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        def on_save(group_data):
            self.qa_groups.append(group_data)
            self.save_current_model()
            self.refresh_groups()
        
        GroupEditor(self.root, on_save=on_save)
    
    def edit_group(self, index):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        def on_save(group_data):
            self.qa_groups[index] = group_data
            self.save_current_model()
            self.refresh_groups()
        
        GroupEditor(self.root, self.qa_groups[index], on_save)
    
    def delete_group(self, index):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        if messagebox.askyesno("Confirm", "Delete this group?"):
            self.qa_groups.pop(index)
            self.save_current_model()
            self.refresh_groups()
    
    def import_json(self):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                for i, qa in enumerate(data):
                    self.qa_groups.append({
                        'group_name': f"Imported {i+1}",
                        'group_description': "Imported from JSON",
                        'questions': qa.get('questions', []),
                        'answers': qa.get('answers', []),
                        'topic': qa.get('topic', 'general'),
                        'priority': qa.get('priority', 'medium'),
                        'follow_ups': qa.get('follow_ups', [])
                    })
                
                self.save_current_model()
                self.refresh_groups()
                messagebox.showinfo("Success", f"Imported {len(data)} groups")
                
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {str(e)}")
    
    def export_json(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            try:
                export_data = []
                for group in self.qa_groups:
                    export_data.append({
                        'questions': group['questions'],
                        'answers': group['answers'],
                        'topic': group['topic'],
                        'priority': group['priority'],
                        'follow_ups': group['follow_ups']
                    })
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                messagebox.showinfo("Success", "Data exported successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

def main():
    root = tk.Tk()
    app = TrainingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
