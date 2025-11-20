import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from .dialogs import BaseDialog, BranchNameDialog, QuestionAnswerEditor

class FollowUpEditor(BaseDialog):
    def __init__(self, parent, followup_data=None, on_save=None):
        super().__init__(parent, "Follow-up Tree Editor", 850, 550)
        self.on_save = on_save
        self.followup_data = followup_data or []
        self.selected_node = None
        self.unsaved_changes = False
        self.current_node_has_changes = False
        self.ignore_selection_event = False  # Add this flag
        
        # Make window resizable
        self.window.minsize(700, 500)
        
        # Configure ttk styles
        self.configure_ttk_styles()
        
        self.setup_scrollable_ui()
        
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
    
    def setup_scrollable_ui(self):
        # Create main container with proper padding
        main_container = tk.Frame(self.window, bg='#1a1a2e')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Create a frame for the scrollable area with the scrollbar inside
        scroll_container = tk.Frame(main_container, bg='#1a1a2e')
        scroll_container.pack(fill='both', expand=True)
        
        # Create canvas and scrollbar - scrollbar is part of the content
        self.canvas = tk.Canvas(scroll_container, bg='#1a1a2e', highlightthickness=0)
        
        # Use themed scrollbar that matches the application
        self.scrollbar = tk.Scrollbar(
            scroll_container, 
            orient=tk.VERTICAL, 
            command=self.canvas.yview,
            bg='#2d2d5a', 
            troughcolor='#1a1a2e', 
            activebackground='#6c63ff',
            width=14
        )
        
        # Pack canvas and scrollbar to fill the scroll container
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # Create scrollable frame
        self.scrollable_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        
        # Configure the scrollable frame to expand horizontally
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas that expands to fill available width
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Make the canvas window expand horizontally
        def configure_canvas(event):
            # Update the scroll region to encompass the inner frame
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Make the inner frame expand to the canvas width
            self.canvas.itemconfig(self.canvas_frame, width=event.width)
        
        self.canvas.bind("<Configure>", configure_canvas)
        
        # Bind mousewheel to the entire window and all child widgets
        self.bind_mousewheel_to_all()
        
        # Setup the actual UI content in the scrollable frame
        self.setup_ui_content()
    
    def bind_mousewheel_to_all(self):
        """Bind mousewheel to the window and all child widgets for consistent scrolling"""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind to main window and all widgets
        self.window.bind("<MouseWheel>", on_mousewheel)
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        
        # Store the function to use later
        self.on_mousewheel = on_mousewheel
    
    def setup_ui_content(self):
        # Configure scrollable frame grid to expand horizontally
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Setup header first
        header = self.setup_header(self.scrollable_frame)
        header.grid(row=0, column=0, sticky='ew', padx=0, pady=(0, 10))
        
        # Create a horizontal container for tree and QA sections
        content_container = tk.Frame(self.scrollable_frame, bg='#1a1a2e')
        content_container.grid(row=1, column=0, sticky='nsew', padx=0, pady=(0, 10))
        
        # Configure the content container to expand both horizontally and vertically
        content_container.grid_columnconfigure(0, weight=1)  # Tree column
        content_container.grid_columnconfigure(1, weight=1)  # QA column
        content_container.grid_rowconfigure(0, weight=1)     # Single row
        
        # Setup tree panel on the LEFT
        tree_panel = self.setup_tree_panel(content_container)
        tree_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 8), pady=0)
        
        # Setup QA sections on the RIGHT
        qa_sections = self.setup_qa_sections(content_container)
        qa_sections.grid(row=0, column=1, sticky='nsew', padx=(8, 0), pady=0)
        
        # Setup action buttons at the bottom
        action_buttons = self.setup_action_buttons(self.scrollable_frame)
        action_buttons.grid(row=2, column=0, sticky='ew', padx=0, pady=(10, 0))
        
        # Make the content container expand vertically if there's extra space
        self.scrollable_frame.grid_rowconfigure(1, weight=1)
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            header,
            text="Follow-up Conversation Tree Editor",
            font=('Arial', 16, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        return header
    
    def setup_tree_panel(self, parent):
        tree_frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(1, weight=1)  # Make tree area expandable
        
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
        
        # Save Node button first (leftmost)
        self.save_node_btn = tk.Button(
            tree_buttons,
            text="💾 Save Node",
            command=self.save_current_node,
            bg='#00ff88',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4,
            state='disabled'  # Initially disabled
        )
        self.save_node_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.add_root_btn = tk.Button(
            tree_buttons,
            text="+ Root",
            command=self.add_root_node,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4
        )
        self.add_root_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.add_branch_btn = tk.Button(
            tree_buttons,
            text="+ Branch",
            command=self.add_child_node,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4
        )
        self.add_branch_btn.pack(side=tk.LEFT)
        
        # Tree widget container - made expandable
        tree_container = tk.Frame(tree_frame, bg='#252547')
        tree_container.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 15))
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)  # Tree expands vertically
        
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
        
        return tree_frame
    
    def setup_qa_sections(self, parent):
        container = tk.Frame(parent, bg='#1a1a2e')
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)  # Questions row
        container.grid_rowconfigure(1, weight=1)  # Answers row
        
        # Questions section on top
        questions_frame = self.create_qa_subsection(container, "Follow-up Questions", 
                                                  self.add_question, self.edit_question, self.delete_question)
        questions_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 8))
        self.questions_list = questions_frame.winfo_children()[1].winfo_children()[0]
        
        # Store question buttons for enabling/disabling
        self.question_buttons = questions_frame.winfo_children()[2].winfo_children()
        self.add_question_btn = questions_frame.winfo_children()[0].winfo_children()[1]
        
        # Answers section on bottom
        answers_frame = self.create_qa_subsection(container, "Follow-up Answers",
                                                self.add_answer, self.edit_answer, self.delete_answer)
        answers_frame.grid(row=1, column=0, sticky='nsew', pady=(8, 0))
        self.answers_list = answers_frame.winfo_children()[1].winfo_children()[0]
        
        # Store answer buttons for enabling/disabling
        self.answer_buttons = answers_frame.winfo_children()[2].winfo_children()
        self.add_answer_btn = answers_frame.winfo_children()[0].winfo_children()[1]
        
        return container
    
    def create_qa_subsection(self, parent, title, add_cmd, edit_cmd, delete_cmd):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)  # Make list area expandable
        
        header = tk.Frame(frame, bg='#252547')
        header.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        header.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            header,
            text=title,
            font=('Arial', 12, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        add_btn = tk.Button(
            header,
            text="+ Add",
            command=add_cmd,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=4,
            state='disabled'  # Initially disabled
        )
        add_btn.grid(row=0, column=1, padx=(10, 0))
        
        list_container = tk.Frame(frame, bg='#252547')
        list_container.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 12))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)  # Listbox expands
        
        listbox = tk.Listbox(
            list_container,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            selectbackground='#6c63ff',
            activestyle='none',
            state='disabled'  # Initially disabled
        )
        listbox.grid(row=0, column=0, sticky='nsew')
        
        # Use themed scrollbar for listbox
        list_scrollbar = tk.Scrollbar(
            list_container, 
            orient=tk.VERTICAL, 
            command=listbox.yview,
            bg='#2d2d5a',
            troughcolor='#1a1a2e',
            activebackground='#6c63ff',
            width=12
        )
        listbox.config(yscrollcommand=list_scrollbar.set)
        list_scrollbar.grid(row=0, column=1, sticky='ns')
        
        actions = tk.Frame(frame, bg='#252547')
        actions.grid(row=2, column=0, sticky='ew', padx=15, pady=(0, 12))
        
        edit_btn = tk.Button(
            actions,
            text="Edit",
            command=edit_cmd,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4,
            width=8,
            state='disabled'  # Initially disabled
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        delete_btn = tk.Button(
            actions,
            text="Delete",
            command=delete_cmd,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4,
            width=8,
            state='disabled'  # Initially disabled
        )
        delete_btn.pack(side=tk.LEFT)
        
        return frame
    
    def setup_action_buttons(self, parent):
        frame = tk.Frame(parent, bg='#1a1a2e')
        frame.grid_columnconfigure(0, weight=1)
        
        button_container = tk.Frame(frame, bg='#1a1a2e')
        button_container.grid(row=0, column=0, sticky='e')
        
        tk.Button(
            button_container,
            text="❌ Cancel",
            command=self.confirm_close,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10
        ).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Main save tree button that changes state
        self.save_tree_btn = tk.Button(
            button_container,
            text="💾 Save Tree",
            command=self.save_tree,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10
        )
        self.save_tree_btn.pack(side=tk.RIGHT)
        
        return frame
    
    def enable_qa_controls(self, enable=True):
        """Enable or disable QA controls based on node selection"""
        state = 'normal' if enable else 'disabled'
        list_state = 'normal' if enable else 'disabled'
        
        # Enable/disable question controls
        self.add_question_btn.config(state=state)
        self.questions_list.config(state=list_state)
        for btn in self.question_buttons:
            btn.config(state=state)
        
        # Enable/disable answer controls
        self.add_answer_btn.config(state=state)
        self.answers_list.config(state=list_state)
        for btn in self.answer_buttons:
            btn.config(state=state)
        
        # Enable/disable save node button
        self.save_node_btn.config(state=state)
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes in the current node"""
        self.unsaved_changes = True
        self.current_node_has_changes = True
        # Update save node button to indicate unsaved changes
        self.save_node_btn.config(text="💾 Save Node *", bg='#ffa500')
        # Also update save tree button
        self.save_tree_btn.config(text="💾 Save Tree *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag for current node and tree"""
        self.unsaved_changes = False
        self.current_node_has_changes = False
        # Reset save node button
        self.save_node_btn.config(text="💾 Save Node", bg='#00ff88')
        # Reset save tree button
        self.save_tree_btn.config(text="💾 Save Tree", bg='#00ff88')
    
    def save_current_node(self):
        """Save the current node's questions and answers"""
        if not self.selected_node:
            return
        
        self.update_node_qa()
        self.clear_unsaved_changes()
        messagebox.showinfo("Saved", "Node saved successfully!")
    
    def confirm_close(self):
        """Confirm closing if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?\n\n"
                "Yes - Save and Close\n"
                "No - Close without Saving\n"
                "Cancel - Return to Editor"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Save and Close
                if self.save_tree():
                    self.window.destroy()
                return
            else:  # No - Close without Saving
                self.window.destroy()
        else:
            self.window.destroy()
    
    def confirm_node_switch(self):
        """Confirm switching nodes if there are unsaved changes"""
        if self.current_node_has_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes in the current node. Save before switching?\n\n"
                "Yes - Save and Switch\n"
                "No - Switch without Saving\n"
                "Cancel - Stay on Current Node"
            )
            
            if result is None:  # Cancel
                return False
            elif result:  # Yes - Save and Switch
                self.save_current_node()
            
            # Clear the flag regardless of save choice
            self.current_node_has_changes = False
        
        return True
    
    def add_root_node(self):
        # Check for unsaved changes before adding new root
        if not self.confirm_node_switch():
            return
        
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
        
        # Check for unsaved changes before adding new branch
        if not self.confirm_node_switch():
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
                self.mark_unsaved_changes()
        
        BranchNameDialog(self.window, current_name, is_root=(self.tree.parent(self.selected_node) == ''), on_save=save_name)
    
    def on_tree_double_click(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if item:
            # Check for unsaved changes before switching nodes
            if not self.confirm_node_switch():
                return
            
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
            self.clear_qa_lists()
            self.enable_qa_controls(False)
    
    def on_tree_select(self, event=None):
        # If we're ignoring selection events (to prevent infinite loop), return early
        if self.ignore_selection_event:
            self.ignore_selection_event = False
            return
        
        # Check for unsaved changes before switching nodes
        if self.selected_node and self.current_node_has_changes:
            if not self.confirm_node_switch():
                # Cancel the selection change and set flag to prevent infinite loop
                self.ignore_selection_event = True
                self.tree.selection_set(self.selected_node)
                return
        
        selected = self.tree.selection()
        if not selected:
            self.selected_node = None
            self.clear_qa_lists()
            self.enable_qa_controls(False)
            return
        
        # If we're selecting the same node, just return
        if self.selected_node == selected[0]:
            return
        
        self.selected_node = selected[0]
        values = self.tree.item(self.selected_node, 'values')
        
        self.clear_qa_lists()
        self.enable_qa_controls(True)
        
        if values and len(values) >= 3:
            questions = values[1].split('|') if values[1] else []
            answers = values[2].split('|') if values[2] else []
            
            for question in questions:
                if question.strip():
                    self.questions_list.insert(tk.END, question.strip())
            
            for answer in answers:
                if answer.strip():
                    self.answers_list.insert(tk.END, answer.strip())
        
        # Clear unsaved changes flag when loading a node
        self.clear_unsaved_changes()
    
    def clear_qa_lists(self):
        """Clear both question and answer lists"""
        self.questions_list.delete(0, tk.END)
        self.answers_list.delete(0, tk.END)
    
    def add_question(self):
        def save_question(text):
            self.questions_list.insert(tk.END, text)
            self.update_node_qa()
            self.mark_unsaved_changes()
        
        QuestionAnswerEditor(self.window, "question", on_save=save_question)
    
    def edit_question(self):
        selection = self.questions_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a question to edit.")
            return
        
        index = selection[0]
        current_text = self.questions_list.get(index)
        
        def save_question(text):
            self.questions_list.delete(index)
            self.questions_list.insert(index, text)
            self.update_node_qa()
            self.mark_unsaved_changes()
        
        QuestionAnswerEditor(self.window, "question", current_text, save_question)
    
    def delete_question(self):
        selection = self.questions_list.curselection()
        if selection:
            self.questions_list.delete(selection[0])
            self.update_node_qa()
            self.mark_unsaved_changes()
    
    def add_answer(self):
        def save_answer(text):
            self.answers_list.insert(tk.END, text)
            self.update_node_qa()
            self.mark_unsaved_changes()
        
        QuestionAnswerEditor(self.window, "answer", on_save=save_answer)
    
    def edit_answer(self):
        selection = self.answers_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an answer to edit.")
            return
        
        index = selection[0]
        current_text = self.answers_list.get(index)
        
        def save_answer(text):
            self.answers_list.delete(index)
            self.answers_list.insert(index, text)
            self.update_node_qa()
            self.mark_unsaved_changes()
        
        QuestionAnswerEditor(self.window, "answer", current_text, save_answer)
    
    def delete_answer(self):
        selection = self.answers_list.curselection()
        if selection:
            self.answers_list.delete(selection[0])
            self.update_node_qa()
            self.mark_unsaved_changes()
    
    def update_node_qa(self):
        """Update the current node with questions and answers from lists"""
        if not self.selected_node:
            return
        
        questions = list(self.questions_list.get(0, tk.END))
        answers = list(self.answers_list.get(0, tk.END))
        
        current_values = list(self.tree.item(self.selected_node, 'values'))
        branch_name = current_values[0] if current_values else "Unnamed"
        
        # Join questions and answers with pipe separator for storage
        questions_str = '|'.join(questions) if questions else ""
        answers_str = '|'.join(answers) if answers else ""
        
        parent = self.tree.parent(self.selected_node)
        prefix = "🌱 " if parent == '' else "🌿 "
        self.tree.item(self.selected_node, text=f"{prefix}{branch_name}", 
                      values=(branch_name, questions_str, answers_str))
    
    def load_data(self):
        def add_children(parent_item, children):
            for child in children:
                branch_name = child.get('branch_name', 'Unnamed Branch')
                questions = child.get('questions', [])
                answers = child.get('answers', [])
                
                # Convert lists to pipe-separated strings for tree storage
                questions_str = '|'.join(questions) if questions else ""
                answers_str = '|'.join(answers) if answers else ""
                
                display_text = f"🌿 {branch_name}"
                item = self.tree.insert(parent_item, 'end', text=display_text, 
                                      values=(branch_name, questions_str, answers_str))
                add_children(item, child.get('children', []))
        
        for item in self.followup_data:
            branch_name = item.get('branch_name', 'Conversation Start')
            questions = item.get('questions', [])
            answers = item.get('answers', [])
            
            # Convert lists to pipe-separated strings for tree storage
            questions_str = '|'.join(questions) if questions else ""
            answers_str = '|'.join(answers) if answers else ""
            
            display_text = f"🌱 {branch_name}"
            root_item = self.tree.insert('', 'end', text=display_text, 
                                       values=(branch_name, questions_str, answers_str))
            add_children(root_item, item.get('children', []))
    
    def save_tree(self):
        def get_children(parent_item):
            children = []
            for child_id in self.tree.get_children(parent_item):
                values = self.tree.item(child_id, 'values')
                branch_name = values[0] if values else "Unnamed"
                
                # Convert pipe-separated strings back to lists
                questions_str = values[1] if len(values) > 1 else ""
                answers_str = values[2] if len(values) > 2 else ""
                
                questions = questions_str.split('|') if questions_str else []
                answers = answers_str.split('|') if answers_str else []
                
                # Filter out empty strings
                questions = [q for q in questions if q.strip()]
                answers = [a for a in answers if a.strip()]
                
                children.append({
                    'branch_name': branch_name,
                    'questions': questions,
                    'answers': answers,
                    'children': get_children(child_id)
                })
            return children
        
        followup_data = []
        for root_id in self.tree.get_children(''):
            values = self.tree.item(root_id, 'values')
            branch_name = values[0] if values else "Conversation Start"
            
            # Convert pipe-separated strings back to lists
            questions_str = values[1] if len(values) > 1 else ""
            answers_str = values[2] if len(values) > 2 else ""
            
            questions = questions_str.split('|') if questions_str else []
            answers = answers_str.split('|') if answers_str else []
            
            # Filter out empty strings
            questions = [q for q in questions if q.strip()]
            answers = [a for a in answers if a.strip()]
            
            followup_data.append({
                'branch_name': branch_name,
                'questions': questions,
                'answers': answers,
                'children': get_children(root_id)
            })
        
        if self.on_save:
            self.on_save(followup_data)
        
        self.clear_unsaved_changes()
        messagebox.showinfo("Success", "Follow-up tree saved successfully!")
        return True
