import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from .dialogs import BaseDialog, BranchNameDialog, QuestionAnswerEditor

class FollowUpEditor(BaseDialog):
    def __init__(self, parent, followup_data=None, on_save=None):
        super().__init__(parent, "Follow-up Tree Editor", 900, 650)
        self.on_save = on_save
        self.followup_data = followup_data or []
        self.selected_node = None
        
        # Make window resizable
        self.window.minsize(700, 500)
        
        # Configure ttk styles
        self.configure_ttk_styles()
        
        self.setup_ui()
        
        if followup_data:
            self.load_data()
    
    def configure_ttk_styles(self):
        """Configure ttk styles to match the main application"""
        style = ttk.Style()
        
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
        # Configure treeview style
        style.configure("Custom.Treeview",
            background="#2d2d5a",
            foreground="white",
            fieldbackground="#2d2d5a",
            borderwidth=0,
            font=('Arial', 10)
        )
        
        style.configure("Custom.Treeview.Heading",
            background="#252547",
            foreground="white",
            relief='flat',
            font=('Arial', 10, 'bold')
        )
        
        style.map('Custom.Treeview', 
            background=[('selected', '#6c63ff')],
            foreground=[('selected', 'white')]
        )
        
        # Configure combobox popdown
        self.window.option_add('*TCombobox*Listbox.background', '#2d2d5a')
        self.window.option_add('*TCombobox*Listbox.foreground', 'white')
        self.window.option_add('*TCombobox*Listbox.selectBackground', '#6c63ff')
        self.window.option_add('*TCombobox*Listbox.selectForeground', 'white')
    
    def setup_ui(self):
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        tk.Label(
            main_frame,
            text="Follow-up Conversation Tree",
            font=('Arial', 16, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 15))
        
        # Tree panel
        self.setup_tree_panel(main_frame)
        
        # Editor panel
        self.setup_editor_panel(main_frame)
        
        # Action buttons
        self.setup_action_buttons(main_frame)
    
    def setup_tree_panel(self, parent):
        tree_frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        tree_frame.grid(row=1, column=0, sticky='nsew', padx=(0, 15))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(1, weight=1)
        
        # Tree header with buttons
        tree_header = tk.Frame(tree_frame, bg='#252547')
        tree_header.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        tree_header.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            tree_header,
            text="Conversation Flow",
            font=('Arial', 12, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        tree_buttons = tk.Frame(tree_header, bg='#252547')
        tree_buttons.grid(row=0, column=1, sticky='e')
        
        tk.Button(
            tree_buttons,
            text="+ Root",
            command=self.add_root_node,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            tree_buttons,
            text="+ Branch",
            command=self.add_child_node,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4
        ).pack(side=tk.LEFT)
        
        # Tree widget container
        tree_container = tk.Frame(tree_frame, bg='#252547')
        tree_container.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 15))
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)
        
        # Create treeview with custom style
        self.tree = ttk.Treeview(tree_container, show='tree', style="Custom.Treeview")
        
        # Use custom scrollbar
        tree_scroll = tk.Scrollbar(
            tree_container, 
            orient=tk.VERTICAL, 
            command=self.tree.yview,
            bg='#2d2d5a', 
            troughcolor='#1a1a2e', 
            activebackground='#6c63ff',
            width=14
        )
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll.grid(row=0, column=1, sticky='ns')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
    
    def setup_editor_panel(self, parent):
        editor_frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        editor_frame.grid(row=1, column=1, sticky='nsew')
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(3, weight=1)
        editor_frame.grid_rowconfigure(4, weight=1)
        
        # Branch name section
        name_frame = tk.Frame(editor_frame, bg='#252547')
        name_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        name_frame.grid_columnconfigure(0, weight=1)
        
        # Title and edit button
        title_edit_frame = tk.Frame(name_frame, bg='#252547')
        title_edit_frame.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        title_edit_frame.grid_columnconfigure(0, weight=1)
        
        self.node_title = tk.Label(
            title_edit_frame,
            text="No node selected",
            font=('Arial', 13, 'bold'),
            bg='#252547',
            fg='white'
        )
        self.node_title.grid(row=0, column=0, sticky='w')
        
        # Edit Name button
        self.edit_name_button = tk.Button(
            title_edit_frame,
            text="✏️ Edit Name",
            command=self.edit_branch_name,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=4,
            state='disabled'
        )
        self.edit_name_button.grid(row=0, column=1, sticky='e', padx=(0, 8))
        
        # Delete button
        self.delete_button = tk.Button(
            title_edit_frame,
            text="🗑️ Delete",
            command=self.delete_node,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=4,
            state='disabled'
        )
        self.delete_button.grid(row=0, column=2, sticky='e')
        
        # Branch name display
        self.branch_name_display = tk.Label(
            name_frame,
            text="Select a node to view details",
            font=('Arial', 10),
            bg='#252547',
            fg='#b0b0d0'
        )
        self.branch_name_display.grid(row=1, column=0, sticky='w', pady=(2, 0))
        
        # Node info
        self.node_info = tk.Label(
            name_frame,
            text="Select a node to edit its content",
            font=('Arial', 9),
            bg='#252547',
            fg='#b0b0d0'
        )
        self.node_info.grid(row=2, column=0, sticky='w', pady=(2, 0))
        
        # Question editor
        q_frame = tk.Frame(editor_frame, bg='#252547')
        q_frame.grid(row=3, column=0, sticky='nsew', padx=15, pady=(0, 10))
        q_frame.grid_columnconfigure(0, weight=1)
        q_frame.grid_rowconfigure(1, weight=1)
        
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
        
        # Bind Shift+Enter for new line in question
        self.question_text.bind('<Shift-Return>', self.on_shift_enter)
        self.question_text.bind('<Return>', self.on_enter)
        
        # Answer editor
        a_frame = tk.Frame(editor_frame, bg='#252547')
        a_frame.grid(row=4, column=0, sticky='nsew', padx=15, pady=(0, 10))
        a_frame.grid_columnconfigure(0, weight=1)
        a_frame.grid_rowconfigure(1, weight=1)
        
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
        
        # Bind Shift+Enter for new line in answer
        self.answer_text.bind('<Shift-Return>', self.on_shift_enter)
        self.answer_text.bind('<Return>', self.on_enter)
        
        # Update button
        update_frame = tk.Frame(editor_frame, bg='#252547')
        update_frame.grid(row=5, column=0, sticky='e', padx=15, pady=(0, 12))
        
        self.update_button = tk.Button(
            update_frame,
            text="💾 Update Node",
            command=self.update_node,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8,
            state='disabled'
        )
        self.update_button.pack(side=tk.RIGHT)
    
    def on_shift_enter(self, event):
        """Handle Shift+Enter - insert new line"""
        event.widget.insert(tk.INSERT, '\n')
        return 'break'
    
    def on_enter(self, event):
        """Handle Enter - move focus to update button"""
        self.update_button.focus_set()
        return 'break'
    
    def setup_action_buttons(self, parent):
        button_frame = tk.Frame(parent, bg='#1a1a2e')
        button_frame.grid(row=2, column=0, columnspan=2, sticky='e', pady=(15, 0))
        
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
        def save_name(branch_name):
            item = self.tree.insert('', 'end', text=f"🌱 {branch_name}", values=(branch_name, "", ""))
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.on_tree_select()
        
        BranchNameDialog(self.window, "New Conversation Start", is_root=True, on_save=save_name)
    
    def add_child_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a parent node first to add a branch.")
            return
        
        def save_name(branch_name):
            parent = selected[0]
            item = self.tree.insert(parent, 'end', text=f"🌿 {branch_name}", values=(branch_name, "", ""))
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.on_tree_select()
            self.tree.item(parent, open=True)
        
        BranchNameDialog(self.window, "New Branch", is_root=False, on_save=save_name)
    
    def edit_branch_name(self):
        if not self.selected_node:
            return
        
        current_values = self.tree.item(self.selected_node, 'values')
        current_name = current_values[0] if current_values else ""
        
        def save_name(new_name):
            current_values = list(self.tree.item(self.selected_node, 'values'))
            if len(current_values) >= 1:
                current_values[0] = new_name
                parent = self.tree.parent(self.selected_node)
                prefix = "🌱 " if parent == '' else "🌿 "
                self.tree.item(self.selected_node, text=f"{prefix}{new_name}", values=tuple(current_values))
                self.on_tree_select()
        
        BranchNameDialog(self.window, current_name, is_root=(self.tree.parent(self.selected_node) == ''), on_save=save_name)
    
    def on_tree_double_click(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self.tree.selection_set(item)
            self.selected_node = item
            self.edit_branch_name()
    
    def delete_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a node to delete.")
            return
        
        node_text = self.tree.item(selected[0], 'text')
        if messagebox.askyesno("Confirm Delete", 
                             f"Delete '{node_text}' and all its branches?\nThis cannot be undone."):
            self.tree.delete(selected[0])
            self.selected_node = None
            self.node_title.config(text="No node selected")
            self.branch_name_display.config(text="Select a node to view details")
            self.node_info.config(text="Select a node to edit its content")
            self.delete_button.config(state='disabled')
            self.edit_name_button.config(state='disabled')
            self.update_button.config(state='disabled')
            self.question_text.delete('1.0', tk.END)
            self.answer_text.delete('1.0', tk.END)
    
    def on_tree_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            self.selected_node = None
            self.node_title.config(text="No node selected")
            self.branch_name_display.config(text="Select a node to view details")
            self.node_info.config(text="Select a node to edit its content")
            self.delete_button.config(state='disabled')
            self.edit_name_button.config(state='disabled')
            self.update_button.config(state='disabled')
            self.question_text.delete('1.0', tk.END)
            self.answer_text.delete('1.0', tk.END)
            return
        
        self.selected_node = selected[0]
        item_text = self.tree.item(self.selected_node, 'text')
        values = self.tree.item(self.selected_node, 'values')
        
        parent = self.tree.parent(self.selected_node)
        if parent == '':
            self.node_title.config(text="🗣️ Conversation Starter")
            self.node_info.config(text="This starts the follow-up conversation")
        else:
            self.node_title.config(text="🌿 Conversation Branch")
            self.node_info.config(text="Continues from previous response")
        
        self.delete_button.config(state='normal')
        self.edit_name_button.config(state='normal')
        self.update_button.config(state='normal')
        
        branch_name = values[0] if values else "Unnamed"
        self.branch_name_display.config(text=f"Branch: {branch_name}")
        
        self.question_text.delete('1.0', tk.END)
        self.answer_text.delete('1.0', tk.END)
        
        if values and len(values) >= 3:
            question, answer = values[1], values[2]
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
        
        current_values = list(self.tree.item(self.selected_node, 'values'))
        branch_name = current_values[0] if current_values else "Unnamed"
        
        parent = self.tree.parent(self.selected_node)
        prefix = "🌱 " if parent == '' else "🌿 "
        self.tree.item(self.selected_node, text=f"{prefix}{branch_name}", values=(branch_name, question, answer))
        
        messagebox.showinfo("Success", "Node updated successfully!")
    
    def load_data(self):
        def add_children(parent_item, children):
            for child in children:
                branch_name = child.get('branch_name', 'Unnamed Branch')
                question = child.get('question', '')
                answer = child.get('answer', '')
                display_text = f"🌿 {branch_name}"
                item = self.tree.insert(parent_item, 'end', text=display_text, values=(branch_name, question, answer))
                add_children(item, child.get('children', []))
        
        for item in self.followup_data:
            branch_name = item.get('branch_name', 'Conversation Start')
            question = item.get('question', '')
            answer = item.get('answer', '')
            display_text = f"🌱 {branch_name}"
            root_item = self.tree.insert('', 'end', text=display_text, values=(branch_name, question, answer))
            add_children(root_item, item.get('children', []))
    
    def save_tree(self):
        def get_children(parent_item):
            children = []
            for child_id in self.tree.get_children(parent_item):
                values = self.tree.item(child_id, 'values')
                branch_name = values[0] if values else "Unnamed"
                question = values[1] if len(values) > 1 else ""
                answer = values[2] if len(values) > 2 else ""
                children.append({
                    'branch_name': branch_name,
                    'question': question,
                    'answer': answer,
                    'children': get_children(child_id)
                })
            return children
        
        followup_data = []
        for root_id in self.tree.get_children(''):
            values = self.tree.item(root_id, 'values')
            branch_name = values[0] if values else "Conversation Start"
            question = values[1] if len(values) > 1 else ""
            answer = values[2] if len(values) > 2 else ""
            followup_data.append({
                'branch_name': branch_name,
                'question': question,
                'answer': answer,
                'children': get_children(root_id)
            })
        
        if self.on_save:
            self.on_save(followup_data)
        
        messagebox.showinfo("Success", "Follow-up tree saved successfully!")
        self.window.destroy()
