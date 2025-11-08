import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from ai_engine import AdvancedChatbot

class QuestionAnswerEditor:
    def __init__(self, parent, item_type="question", initial_text="", on_save=None):
        self.on_save = on_save
        self.item_type = item_type
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"{item_type.title()} Editor")
        self.window.geometry("600x400")
        self.window.minsize(500, 300)
        self.window.configure(bg='#2d2d5a')
        
        # Center window
        self.window.transient(parent)
        self.center_window()
        
        self.setup_ui(initial_text)
    
    def center_window(self):
        self.window.update_idletasks()
        x = self.window.winfo_screenwidth() // 2 - self.window.winfo_width() // 2
        y = self.window.winfo_screenheight() // 2 - self.window.winfo_height() // 2
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self, initial_text):
        # Main container
        main_frame = tk.Frame(self.window, bg='#2d2d5a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Text area
        text_frame = tk.Frame(main_frame, bg='#2d2d5a')
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.text_widget = scrolledtext.ScrolledText(
            text_frame, 
            font=('Arial', 12),
            bg='#1a1a2e', 
            fg='white',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.insert('1.0', initial_text)
        self.text_widget.focus_set()
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2d2d5a')
        button_frame.pack(fill=tk.X)
        
        tk.Button(
            button_frame, 
            text="Save", 
            command=self.save,
            bg='#00ff88', 
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(
            button_frame, 
            text="Cancel", 
            command=self.window.destroy,
            bg='#ff4d7d', 
            fg='white',
            font=('Arial', 11),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
    
    def save(self):
        text = self.text_widget.get('1.0', tk.END).strip()
        if text and self.on_save:
            self.on_save(text)
            self.window.destroy()
        elif not text:
            messagebox.showwarning("Empty", f"Please enter a {self.item_type}.")

class GroupEditor:
    def __init__(self, parent, group_data=None, on_save=None):
        self.on_save = on_save
        self.group_data = group_data or {}
        self.available_topics = ["greeting", "programming", "ai", "gaming", "creative", "thanks", "general"]
        
        self.window = tk.Toplevel(parent)
        self.window.title("QA Group Editor")
        self.window.geometry("1000x700")
        self.window.minsize(800, 600)
        self.window.configure(bg='#1a1a2e')
        
        # Window properties
        self.window.transient(parent)
        self.center_window()
        
        self.setup_ui()
        if group_data:
            self.load_data()
    
    def center_window(self):
        self.window.update_idletasks()
        x = self.window.winfo_screenwidth() // 2 - self.window.winfo_width() // 2
        y = self.window.winfo_screenheight() // 2 - self.window.winfo_height() // 2
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.setup_header(main_frame)
        
        # Group info
        self.setup_group_info(main_frame)
        
        # Questions and Answers
        self.setup_qa_sections(main_frame)
        
        # Settings
        self.setup_settings(main_frame)
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            header,
            text="QA Group Editor",
            font=('Arial', 18, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = tk.Frame(header, bg='#1a1a2e')
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(
            btn_frame,
            text="Save Group",
            command=self.save_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.window.destroy,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 11),
            padx=15
        ).pack(side=tk.LEFT)
    
    def setup_group_info(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Group name
        name_frame = tk.Frame(frame, bg='#252547')
        name_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            name_frame,
            text="Group Name:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(anchor='w')
        
        self.name_var = tk.StringVar(value="New QA Group")
        tk.Entry(
            name_frame,
            textvariable=self.name_var,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        ).pack(fill=tk.X, pady=(5, 0))
        
        # Description
        desc_frame = tk.Frame(frame, bg='#252547')
        desc_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(
            desc_frame,
            text="Description:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(anchor='w')
        
        self.desc_var = tk.StringVar()
        tk.Entry(
            desc_frame,
            textvariable=self.desc_var,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        ).pack(fill=tk.X, pady=(5, 0))
    
    def setup_qa_sections(self, parent):
        container = tk.Frame(parent, bg='#1a1a2e')
        container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Configure grid
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)
        
        # Questions
        self.setup_questions_section(container)
        
        # Answers
        self.setup_answers_section(container)
    
    def setup_questions_section(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # Header
        header = tk.Frame(frame, bg='#252547')
        header.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            header,
            text="Questions",
            font=('Arial', 14, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(side=tk.LEFT)
        
        tk.Button(
            header,
            text="+ Add",
            command=self.add_question,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.RIGHT)
        
        # Listbox
        list_frame = tk.Frame(frame, bg='#252547')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.questions_list = tk.Listbox(
            list_frame,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            selectbackground='#6c63ff'
        )
        self.questions_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.questions_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.questions_list.yview)
        
        # Actions
        actions = tk.Frame(frame, bg='#252547')
        actions.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Button(
            actions,
            text="Edit",
            command=self.edit_question,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            actions,
            text="Delete",
            command=self.delete_question,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT)
    
    def setup_answers_section(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        # Header
        header = tk.Frame(frame, bg='#252547')
        header.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            header,
            text="Answers",
            font=('Arial', 14, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(side=tk.LEFT)
        
        tk.Button(
            header,
            text="+ Add",
            command=self.add_answer,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.RIGHT)
        
        # Listbox
        list_frame = tk.Frame(frame, bg='#252547')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.answers_list = tk.Listbox(
            list_frame,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            selectbackground='#6c63ff'
        )
        self.answers_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.answers_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.answers_list.yview)
        
        # Actions
        actions = tk.Frame(frame, bg='#252547')
        actions.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Button(
            actions,
            text="Edit",
            command=self.edit_answer,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            actions,
            text="Delete",
            command=self.delete_answer,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT)
    
    def setup_settings(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        frame.pack(fill=tk.X)
        
        content = tk.Frame(frame, bg='#252547')
        content.pack(fill=tk.X, padx=15, pady=15)
        
        # Topic
        topic_frame = tk.Frame(content, bg='#252547')
        topic_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            topic_frame,
            text="Topic:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(side=tk.LEFT)
        
        self.topic_var = tk.StringVar(value="greeting")
        ttk.Combobox(
            topic_frame,
            textvariable=self.topic_var,
            values=self.available_topics,
            state='normal'
        ).pack(side=tk.LEFT, padx=(10, 20))
        
        # Priority
        tk.Label(
            topic_frame,
            text="Priority:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(side=tk.LEFT)
        
        self.priority_var = tk.StringVar(value="medium")
        ttk.Combobox(
            topic_frame,
            textvariable=self.priority_var,
            values=["high", "medium", "low"]
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Keywords
        keywords_frame = tk.Frame(content, bg='#252547')
        keywords_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            keywords_frame,
            text="Keywords:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(anchor='w')
        
        self.keywords_var = tk.StringVar()
        tk.Entry(
            keywords_frame,
            textvariable=self.keywords_var,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        ).pack(fill=tk.X, pady=(5, 0))
        
        # Follow-up info
        followup_frame = tk.Frame(content, bg='#252547')
        followup_frame.pack(fill=tk.X)
        
        tk.Label(
            followup_frame,
            text="Follow-up Info:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(anchor='w')
        
        self.followup_text = scrolledtext.ScrolledText(
            followup_frame,
            height=3,
            font=('Arial', 11),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        )
        self.followup_text.pack(fill=tk.X, pady=(5, 0))
    
    def add_question(self):
        def save_question(text):
            self.questions_list.insert(tk.END, text)
        
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
        
        QuestionAnswerEditor(self.window, "question", current_text, save_question)
    
    def delete_question(self):
        selection = self.questions_list.curselection()
        if selection:
            self.questions_list.delete(selection[0])
    
    def add_answer(self):
        def save_answer(text):
            self.answers_list.insert(tk.END, text)
        
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
        
        QuestionAnswerEditor(self.window, "answer", current_text, save_answer)
    
    def delete_answer(self):
        selection = self.answers_list.curselection()
        if selection:
            self.answers_list.delete(selection[0])
    
    def load_data(self):
        # Basic info
        if 'group_name' in self.group_data:
            self.name_var.set(self.group_data['group_name'])
        if 'group_description' in self.group_data:
            self.desc_var.set(self.group_data['group_description'])
        
        # Questions and answers
        for question in self.group_data.get('questions', []):
            self.questions_list.insert(tk.END, question)
        
        for answer in self.group_data.get('answers', []):
            self.answers_list.insert(tk.END, answer)
        
        # Settings
        self.topic_var.set(self.group_data.get('topic', 'greeting'))
        self.priority_var.set(self.group_data.get('priority', 'medium'))
        self.keywords_var.set(', '.join(self.group_data.get('keywords', [])))
        self.followup_text.delete('1.0', tk.END)
        self.followup_text.insert('1.0', self.group_data.get('follow_up_info', ''))
    
    def save_group(self):
        # Validate
        if self.questions_list.size() == 0:
            messagebox.showerror("Error", "At least one question is required.")
            return
        
        if self.answers_list.size() == 0:
            messagebox.showerror("Error", "At least one answer is required.")
            return
        
        # Collect data
        group_data = {
            'group_name': self.name_var.get(),
            'group_description': self.desc_var.get(),
            'questions': list(self.questions_list.get(0, tk.END)),
            'answers': list(self.answers_list.get(0, tk.END)),
            'topic': self.topic_var.get(),
            'priority': self.priority_var.get(),
            'keywords': [k.strip() for k in self.keywords_var.get().split(',') if k.strip()],
            'follow_up_info': self.followup_text.get('1.0', tk.END).strip()
        }
        
        if self.on_save:
            self.on_save(group_data)
        
        self.window.destroy()

class TrainingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI Training")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1a1a2e')
        
        self.chatbot = AdvancedChatbot()
        self.qa_groups = []
        
        self.setup_gui()
        self.load_data()
    
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.setup_header(main_frame)
        
        # Search and actions
        self.setup_toolbar(main_frame)
        
        # Groups list
        self.setup_groups_list(main_frame)
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            header,
            text="Edgar AI Training",
            font=('Arial', 24, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).pack(side=tk.LEFT)
        
        # Stats
        stats_frame = tk.Frame(header, bg='#1a1a2e')
        stats_frame.pack(side=tk.RIGHT)
        
        self.stats_vars = {}
        stats = [("Groups", "0"), ("Questions", "0"), ("Answers", "0")]
        
        for label, value in stats:
            frame = tk.Frame(stats_frame, bg='#1a1a2e')
            frame.pack(side=tk.LEFT, padx=15)
            
            var = tk.StringVar(value=value)
            tk.Label(
                frame,
                textvariable=var,
                font=('Arial', 16, 'bold'),
                bg='#1a1a2e',
                fg='#6c63ff'
            ).pack()
            
            tk.Label(
                frame,
                text=label,
                font=('Arial', 9),
                bg='#1a1a2e',
                fg='#b0b0d0'
            ).pack()
            
            self.stats_vars[label] = var
    
    def setup_toolbar(self, parent):
        toolbar = tk.Frame(parent, bg='#1a1a2e')
        toolbar.pack(fill=tk.X, pady=(0, 15))
        
        # Search
        search_frame = tk.Frame(toolbar, bg='#1a1a2e')
        search_frame.pack(side=tk.LEFT)
        
        tk.Label(
            search_frame,
            text="Search:",
            bg='#1a1a2e',
            fg='white'
        ).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        tk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=30,
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        ).pack(side=tk.LEFT, padx=(10, 0))
        self.search_var.trace('w', self.on_search)
        
        # Search mode
        self.search_mode = tk.StringVar(value="both")
        mode_frame = tk.Frame(toolbar, bg='#1a1a2e')
        mode_frame.pack(side=tk.LEFT, padx=20)
        
        for text, value in [("Both", "both"), ("Name", "name"), ("Desc", "description")]:
            tk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.search_mode,
                value=value,
                bg='#1a1a2e',
                fg='white',
                selectcolor='#6c63ff'
            ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Actions
        actions = tk.Frame(toolbar, bg='#1a1a2e')
        actions.pack(side=tk.RIGHT)
        
        tk.Button(
            actions,
            text="Import JSON",
            command=self.import_json,
            bg='#6c63ff',
            fg='white'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            actions,
            text="Export JSON",
            command=self.export_json,
            bg='#00d4ff',
            fg='black'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            actions,
            text="New Group",
            command=self.new_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold')
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
    
    def load_data(self):
        self.qa_groups = []
        for qa in self.chatbot.qa_pairs:
            self.qa_groups.append({
                'group_name': f"Group {len(self.qa_groups) + 1}",
                'group_description': "Imported QA pair",
                'questions': qa.get('questions', []),
                'answers': qa.get('answers', []),
                'topic': qa.get('topic', 'general'),
                'priority': qa.get('priority', 'medium'),
                'keywords': qa.get('keywords', []),
                'follow_up_info': qa.get('follow_up_info', '')
            })
        self.refresh_groups()
    
    def save_data(self):
        self.chatbot.qa_pairs = []
        for group in self.qa_groups:
            self.chatbot.qa_pairs.append({
                'questions': group['questions'],
                'answers': group['answers'],
                'topic': group['topic'],
                'priority': group['priority'],
                'context_sensitive': True,
                'keywords': group['keywords'],
                'follow_up_info': group['follow_up_info']
            })
        self.chatbot.save_data()
    
    def new_group(self):
        def on_save(group_data):
            self.qa_groups.append(group_data)
            self.save_data()
            self.refresh_groups()
        
        GroupEditor(self.root, on_save=on_save)
    
    def edit_group(self, index):
        def on_save(group_data):
            self.qa_groups[index] = group_data
            self.save_data()
            self.refresh_groups()
        
        GroupEditor(self.root, self.qa_groups[index], on_save)
    
    def delete_group(self, index):
        if messagebox.askyesno("Confirm", "Delete this group?"):
            self.qa_groups.pop(index)
            self.save_data()
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
        card.pack(fill=tk.X, pady=5, padx=5)
        
        content = tk.Frame(card, bg='#252547')
        content.pack(fill=tk.X, padx=15, pady=10)
        
        # Header
        header = tk.Frame(content, bg='#252547')
        header.pack(fill=tk.X, pady=(0, 8))
        
        # Title and description
        text_frame = tk.Frame(header, bg='#252547')
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            text_frame,
            text=group['group_name'],
            font=('Arial', 14, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(anchor='w')
        
        if group.get('group_description'):
            tk.Label(
                text_frame,
                text=group['group_description'],
                font=('Arial', 10),
                bg='#252547',
                fg='#b0b0d0'
            ).pack(anchor='w', pady=(2, 0))
        
        # Actions
        actions = tk.Frame(header, bg='#252547')
        actions.pack(side=tk.RIGHT)
        
        tk.Button(
            actions,
            text="Edit",
            command=lambda i=index: self.edit_group(i),
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            actions,
            text="Delete",
            command=lambda i=index: self.delete_group(i),
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)
        
        # Stats
        stats = tk.Frame(content, bg='#252547')
        stats.pack(fill=tk.X)
        
        stats_text = f"Questions: {len(group['questions'])} | Answers: {len(group['answers'])} | Topic: {group['topic']}"
        tk.Label(
            stats,
            text=stats_text,
            font=('Arial', 9),
            bg='#252547',
            fg='#b0b0d0'
        ).pack(anchor='w')
    
    def import_json(self):
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
                        'keywords': qa.get('keywords', []),
                        'follow_up_info': qa.get('follow_up_info', '')
                    })
                
                self.save_data()
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
                        'keywords': group['keywords'],
                        'follow_up_info': group['follow_up_info']
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