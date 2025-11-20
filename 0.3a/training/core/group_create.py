import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from .dialogs import BaseDialog, QuestionAnswerEditor, BranchNameDialog

class GroupEditor(BaseDialog):
    def __init__(self, parent, group_data=None, on_save=None):
        super().__init__(parent, "QA Group Editor", 800, 550)
        self.on_save = on_save
        self.group_data = group_data or {}
        self.available_topics = ["greeting", "programming", "ai", "gaming", "creative", "thanks", "general"]
        self.followup_data = []
        self.unsaved_changes = False
        self.original_data = {}
        self.saving = False  # Prevent multiple saves
        
        # Make window resizable and set minimum size
        self.window.minsize(800, 500)
        
        # Configure ttk styles for this window
        self.configure_ttk_styles()
        
        self.setup_scrollable_ui()
        
        if group_data:
            self.load_data()
        
        # Store original data for comparison
        self.save_original_state()
        
        # Set window close protocol
        self.window.protocol("WM_DELETE_WINDOW", self.confirm_close)
    
    def configure_ttk_styles(self):
        """Configure ttk styles to match the main application"""
        style = ttk.Style()
        
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
        # Configure combobox style
        style.configure('Dark.TCombobox',
            background='#2d2d5a',
            foreground='white',
            fieldbackground='#2d2d5a',
            selectbackground='#6c63ff',
            selectforeground='white',
            borderwidth=1,
            relief='flat',
            padding=5
        )
        
        style.map('Dark.TCombobox',
            fieldbackground=[('readonly', '#2d2d5a')],
            selectbackground=[('readonly', '#6c63ff')],
            selectforeground=[('readonly', 'white')]
        )
        
        # Configure combobox popdown (dropdown list)
        self.window.option_add('*TCombobox*Listbox.background', '#2d2d5a')
        self.window.option_add('*TCombobox*Listbox.foreground', 'white')
        self.window.option_add('*TCombobox*Listbox.selectBackground', '#6c63ff')
        self.window.option_add('*TCombobox*Listbox.selectForeground', 'white')
        self.window.option_add('*TCombobox*Listbox.font', ('Arial', 10))
    
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
        
        # Setup sections with proper horizontal expansion
        sections = [
            self.setup_header(self.scrollable_frame),
            self.setup_group_info(self.scrollable_frame),
            self.setup_qa_sections(self.scrollable_frame),
            self.setup_settings(self.scrollable_frame),
            self.setup_action_buttons(self.scrollable_frame)
        ]
        
        for i, section in enumerate(sections):
            section.grid(row=i, column=0, sticky='ew', padx=0, pady=(0, 10))
        
        # Make the QA sections area expand vertically if there's extra space
        self.scrollable_frame.grid_rowconfigure(2, weight=1)
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            header,
            text="QA Group Editor",
            font=('Arial', 16, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        return header
    
    def setup_group_info(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1, padx=15, pady=15)
        frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            frame,
            text="Group Name:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 12))
        
        self.name_var = tk.StringVar(value="New QA Group")
        self.name_entry = tk.Entry(
            frame,
            textvariable=self.name_var,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        )
        self.name_entry.grid(row=0, column=1, sticky='ew', pady=(0, 12), padx=(15, 0))
        
        # Fix: Set cursor to end instead of selecting all text
        self.name_entry.focus_set()
        self.name_entry.icursor(tk.END)
        
        # FIXED: Remove the Enter key binding that triggers save
        # Only bind KeyRelease for unsaved changes tracking
        self.name_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        
        tk.Label(
            frame,
            text="Description:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 12))
        
        self.desc_var = tk.StringVar()
        self.desc_entry = tk.Entry(
            frame,
            textvariable=self.desc_var,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        )
        self.desc_entry.grid(row=1, column=1, sticky='ew', padx=(15, 0), pady=(0, 12))
        
        # FIXED: Remove the Enter key binding that triggers save
        # Only bind KeyRelease for unsaved changes tracking
        self.desc_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        
        # NEW: Section selection
        tk.Label(
            frame,
            text="Section:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=(0, 0))
        
        self.section_var = tk.StringVar()
        # This will be populated when the dialog is shown
        self.section_combo = ttk.Combobox(
            frame,
            textvariable=self.section_var,
            state='readonly',
            width=20,
            style='Dark.TCombobox'
        )
        self.section_combo.grid(row=2, column=1, sticky='w', padx=(15, 0))
        self.section_combo.bind('<<ComboboxSelected>>', lambda e: self.mark_unsaved_changes())
        
        return frame
    
    def on_name_enter(self, event):
        """Handle Enter key in name/description fields - do nothing"""
        # FIXED: Completely removed the save functionality
        # Just return "break" to prevent any default behavior
        return "break"
    
    def setup_qa_sections(self, parent):
        container = tk.Frame(parent, bg='#1a1a2e')
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        questions_frame = self.create_qa_subsection(container, "Questions", 
                                                  self.add_question, self.edit_question, self.delete_question)
        questions_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        self.questions_list = questions_frame.winfo_children()[1].winfo_children()[0]
        
        answers_frame = self.create_qa_subsection(container, "Answers",
                                                self.add_answer, self.edit_answer, self.delete_answer)
        answers_frame.grid(row=0, column=1, sticky='nsew', padx=(8, 0))
        self.answers_list = answers_frame.winfo_children()[1].winfo_children()[0]
        
        return container
    
    def create_qa_subsection(self, parent, title, add_cmd, edit_cmd, delete_cmd):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
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
        
        tk.Button(
            header,
            text="+ Add",
            command=add_cmd,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=4
        ).grid(row=0, column=1, padx=(10, 0))
        
        list_container = tk.Frame(frame, bg='#252547')
        list_container.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 12))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)
        
        listbox = tk.Listbox(
            list_container,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            selectbackground='#6c63ff',
            activestyle='none'
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
        
        tk.Button(
            actions,
            text="Edit",
            command=edit_cmd,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            actions,
            text="Delete",
            command=delete_cmd,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=15,
            pady=4,
            width=8
        ).pack(side=tk.LEFT)
        
        return frame
    
    def setup_settings(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1, padx=15, pady=15)
        frame.grid_columnconfigure(0, weight=1)
        
        # Topic and Priority in a single row
        topic_priority_frame = tk.Frame(frame, bg='#252547')
        topic_priority_frame.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        topic_priority_frame.grid_columnconfigure(1, weight=1)
        topic_priority_frame.grid_columnconfigure(3, weight=1)
        
        tk.Label(
            topic_priority_frame,
            text="Topic:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.topic_var = tk.StringVar(value="greeting")
        topic_combo = ttk.Combobox(
            topic_priority_frame,
            textvariable=self.topic_var,
            values=self.available_topics,
            state='readonly',
            width=15,
            style='Dark.TCombobox'
        )
        topic_combo.grid(row=0, column=1, sticky='w', padx=(0, 30))
        topic_combo.bind('<<ComboboxSelected>>', lambda e: self.mark_unsaved_changes())
        
        tk.Label(
            topic_priority_frame,
            text="Priority:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=2, sticky='w', padx=(0, 10))
        
        self.priority_var = tk.StringVar(value="medium")
        priority_combo = ttk.Combobox(
            topic_priority_frame,
            textvariable=self.priority_var,
            values=["high", "medium", "low"],
            state='readonly',
            width=12,
            style='Dark.TCombobox'
        )
        priority_combo.grid(row=0, column=3, sticky='w')
        priority_combo.bind('<<ComboboxSelected>>', lambda e: self.mark_unsaved_changes())
        
        # Follow-up section
        followup_frame = tk.Frame(frame, bg='#252547')
        followup_frame.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        followup_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            followup_frame,
            text="Follow-up Conversation Tree:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 10))
        
        followup_info = tk.Frame(followup_frame, bg='#252547')
        followup_info.grid(row=1, column=0, sticky='ew', pady=(0, 8))
        followup_info.grid_columnconfigure(0, weight=1)
        
        self.followup_status = tk.Label(
            followup_info,
            text="No follow-up tree defined",
            font=('Arial', 9),
            bg='#252547',
            fg='#b0b0d0'
        )
        self.followup_status.grid(row=0, column=0, sticky='w')
        
        tk.Button(
            followup_info,
            text="🌳 Edit Follow-up Tree",
            command=self.edit_followup_tree,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=6
        ).grid(row=0, column=1, sticky='e')
        
        instructions = tk.Label(
            followup_frame,
            text="💡 Create branching conversations that continue after the main answer",
            font=('Arial', 9),
            bg='#252547',
            fg='#00d4ff',
            justify=tk.LEFT
        )
        instructions.grid(row=2, column=0, sticky='w', pady=(5, 0))
        
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
        
        # Main save button that changes state - changed from "Create" to "Save"
        self.save_btn = tk.Button(
            button_container,
            text="💾 Save Group",  # Always says "Save" now, not "Create"
            command=self.save_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10
        )
        self.save_btn.pack(side=tk.RIGHT)
        
        return frame
    
    def save_original_state(self):
        """Save the original state for comparison"""
        self.original_data = {
            'name': self.name_var.get(),
            'description': self.desc_var.get(),
            'questions': list(self.questions_list.get(0, tk.END)),
            'answers': list(self.answers_list.get(0, tk.END)),
            'topic': self.topic_var.get(),
            'priority': self.priority_var.get(),
            'section': self.section_var.get(),
            'followup_count': self.count_nodes(self.followup_data)
        }
    
    def has_changes(self):
        """Check if there are any changes from the original state"""
        current_data = {
            'name': self.name_var.get(),
            'description': self.desc_var.get(),
            'questions': list(self.questions_list.get(0, tk.END)),
            'answers': list(self.answers_list.get(0, tk.END)),
            'topic': self.topic_var.get(),
            'priority': self.priority_var.get(),
            'section': self.section_var.get(),
            'followup_count': self.count_nodes(self.followup_data)
        }
        
        return current_data != self.original_data
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        if not self.unsaved_changes and self.has_changes():
            self.unsaved_changes = True
            # Update save button to indicate unsaved changes
            self.save_btn.config(text="💾 Save Group *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag"""
        self.unsaved_changes = False
        self.save_original_state()
        # Reset save button
        self.save_btn.config(text="💾 Save Group", bg='#00ff88')
    
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
                if self.save_group():
                    self.window.destroy()
                return
            else:  # No - Close without Saving
                self.window.destroy()
        else:
            self.window.destroy()
    
    def add_question(self):
        def save_question(text):
            self.questions_list.insert(tk.END, text)
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
            self.mark_unsaved_changes()
        
        QuestionAnswerEditor(self.window, "question", current_text, save_question)
    
    def delete_question(self):
        selection = self.questions_list.curselection()
        if selection:
            self.questions_list.delete(selection[0])
            self.mark_unsaved_changes()
    
    def add_answer(self):
        def save_answer(text):
            self.answers_list.insert(tk.END, text)
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
            self.mark_unsaved_changes()
        
        QuestionAnswerEditor(self.window, "answer", current_text, save_answer)
    
    def delete_answer(self):
        selection = self.answers_list.curselection()
        if selection:
            self.answers_list.delete(selection[0])
            self.mark_unsaved_changes()
    
    def edit_followup_tree(self):
        from .follow_tree import FollowUpEditor
        
        def on_save(followup_data):
            self.followup_data = followup_data
            total_nodes = self.count_nodes(followup_data)
            if total_nodes > 0:
                self.followup_status.config(text=f"Follow-up tree: {total_nodes} conversation nodes")
            else:
                self.followup_status.config(text="No follow-up tree defined")
            self.mark_unsaved_changes()
        
        FollowUpEditor(self.window, self.followup_data, on_save)
    
    def count_nodes(self, data):
        count = 0
        for item in data:
            count += 1
            count += self.count_nodes(item.get('children', []))
        return count
    
    def load_data(self):
        if 'group_name' in self.group_data:
            self.name_var.set(self.group_data['group_name'])
        if 'group_description' in self.group_data:
            self.desc_var.set(self.group_data['group_description'])
        
        for question in self.group_data.get('questions', []):
            self.questions_list.insert(tk.END, question)
        
        for answer in self.group_data.get('answers', []):
            self.answers_list.insert(tk.END, answer)
        
        self.topic_var.set(self.group_data.get('topic', 'greeting'))
        self.priority_var.set(self.group_data.get('priority', 'medium'))
        
        # NEW: Load section
        if 'section' in self.group_data:
            self.section_var.set(self.group_data['section'])
        
        self.followup_data = self.group_data.get('follow_ups', [])
        total_nodes = self.count_nodes(self.followup_data)
        if total_nodes > 0:
            self.followup_status.config(text=f"Follow-up tree: {total_nodes} conversation nodes")
    
    def save_group(self):
        # Prevent multiple saves
        if self.saving:
            return False
            
        self.saving = True
        self.save_btn.config(state='disabled', text="Saving...")
        self.window.update()
        
        try:
            # Enforce group name requirement
            group_name = self.name_var.get().strip()
            if not group_name:
                messagebox.showwarning("Warning", "Group name is required.")
                self.name_entry.focus_set()
                return False
            
            group_data = {
                'group_name': group_name,
                'group_description': self.desc_var.get(),
                'questions': list(self.questions_list.get(0, tk.END)),
                'answers': list(self.answers_list.get(0, tk.END)),
                'topic': self.topic_var.get(),
                'priority': self.priority_var.get(),
                'follow_ups': self.followup_data,
                'section': self.section_var.get()  # NEW: Include section
            }
            
            if self.on_save:
                self.on_save(group_data)
            
            self.clear_unsaved_changes()
            messagebox.showinfo("Success", "Group saved successfully!")
            return True
        finally:
            self.saving = False
            self.save_btn.config(state='normal', text="💾 Save Group")
