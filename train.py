import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from ai_engine import AdvancedChatbot

class TrainingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI - Training Module")
        self.root.geometry("900x700")
        self.root.configure(bg='#1a1a2e')
        
        self.chatbot = AdvancedChatbot()
        self.current_qa_index = 0
        
        # Color scheme
        self.colors = {
            'bg_primary': '#1a1a2e',
            'bg_secondary': '#252547',
            'bg_tertiary': '#2d2d5a',
            'accent_primary': '#6c63ff',
            'accent_secondary': '#00d4ff',
            'accent_success': '#00ff88',
            'accent_warning': '#ffaa00',
            'accent_error': '#ff4d7d',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0d0',
            'text_tertiary': '#8080a0',
            'border': '#404080',
            'input_bg': '#2d2d5a',
            'tab_bg': '#252547',
            'tab_active_bg': '#6c63ff',
            'tab_fg': '#ffffff',
            'combobox_bg': '#2d2d5a',
            'combobox_fg': '#ffffff',
            'combobox_field_bg': '#2d2d5a'
        }
        
        self.setup_ttk_styles()
        self.setup_gui()
        self.load_database_info()
    
    def setup_ttk_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        
        # Use clam theme as base for better customization
        style.theme_use('clam')
        
        # Configure Notebook style
        style.configure('Custom.TNotebook', 
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                       background=self.colors['tab_bg'],
                       foreground=self.colors['tab_fg'],
                       padding=[20, 5],
                       focuscolor=self.colors['tab_active_bg'])
        
        # Map tab states for hover and selection
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', self.colors['tab_active_bg']),
                           ('active', self.colors['accent_primary'])],
                 foreground=[('selected', self.colors['text_primary']),
                           ('active', self.colors['text_primary'])])
        
        # Configure Combobox style
        style.configure('Custom.TCombobox',
                       fieldbackground=self.colors['combobox_field_bg'],
                       background=self.colors['combobox_bg'],
                       foreground=self.colors['combobox_fg'],
                       selectbackground=self.colors['accent_primary'],
                       selectforeground=self.colors['text_primary'],
                       arrowcolor=self.colors['combobox_fg'],
                       bordercolor=self.colors['border'],
                       focuscolor=self.colors['border'])
        
        # Configure Combobox popdown menu
        self.root.option_add('*TCombobox*Listbox.background', self.colors['combobox_bg'])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors['combobox_fg'])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors['accent_primary'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.colors['text_primary'])
    
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(title_frame, text="🤖 Edgar AI Training Module", 
                font=('Arial', 18, 'bold'), bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary']).pack()
        
        tk.Label(title_frame, text="Train your chatbot with multiple questions mapping to the same answers",
                font=('Arial', 11), bg=self.colors['bg_primary'], 
                fg=self.colors['text_secondary']).pack(pady=(5, 0))
        
        # Database info frame
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='raised', bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.info_label = tk.Label(info_frame, text="Loading database info...", 
                                  font=('Arial', 10), bg=self.colors['bg_secondary'], 
                                  fg=self.colors['text_primary'], justify=tk.LEFT)
        self.info_label.pack(padx=15, pady=10)
        
        # Create notebook for tabs with custom style
        notebook = ttk.Notebook(main_frame, style='Custom.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Add QA Pair
        add_tab = tk.Frame(notebook, bg=self.colors['bg_primary'])
        notebook.add(add_tab, text="Add QA Pair")
        self.setup_add_tab(add_tab)
        
        # Tab 2: Quick Training
        train_tab = tk.Frame(notebook, bg=self.colors['bg_primary'])
        notebook.add(train_tab, text="Quick Training")
        self.setup_train_tab(train_tab)
        
        # Tab 3: View Database
        view_tab = tk.Frame(notebook, bg=self.colors['bg_primary'])
        notebook.add(view_tab, text="View Database")
        self.setup_view_tab(view_tab)
    
    def setup_add_tab(self, parent):
        # Form frame
        form_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Questions (multiple)
        tk.Label(form_frame, text="Questions (one per line, multiple variations):", bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.questions_text = scrolledtext.ScrolledText(form_frame, width=80, height=3, font=('Arial', 10),
                                                       bg=self.colors['input_bg'], fg=self.colors['text_primary'],
                                                       insertbackground=self.colors['text_primary'],
                                                       selectbackground=self.colors['accent_primary'])
        self.questions_text.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # Add example questions
        example_questions = "hello\nhi\nhey\ngreetings"
        self.questions_text.insert('1.0', example_questions)
        
        # Answers (multiple)
        tk.Label(form_frame, text="Answers (one per line, will be randomly selected):", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=(0, 5))
        self.answers_text = scrolledtext.ScrolledText(form_frame, width=80, height=4, font=('Arial', 10),
                                                     bg=self.colors['input_bg'], fg=self.colors['text_primary'],
                                                     insertbackground=self.colors['text_primary'],
                                                     selectbackground=self.colors['accent_primary'])
        self.answers_text.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # Add example answers
        example_answers = "Hello! How can I help you today?\nHi there! Nice to meet you!\nHey! I'm here to assist you!"
        self.answers_text.insert('1.0', example_answers)
        
        # Topic and Priority
        topic_frame = tk.Frame(form_frame, bg=self.colors['bg_primary'])
        topic_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        tk.Label(topic_frame, text="Topic:", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w')
        self.topic_var = tk.StringVar(value="greeting")
        topic_combo = ttk.Combobox(topic_frame, textvariable=self.topic_var, width=20, style='Custom.TCombobox',
                                  values=["greeting", "programming", "ai", "gaming", "creative", "thanks", "general"])
        topic_combo.grid(row=0, column=1, padx=(10, 30), sticky='w')
        
        tk.Label(topic_frame, text="Priority:", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky='w')
        self.priority_var = tk.StringVar(value="medium")
        priority_combo = ttk.Combobox(topic_frame, textvariable=self.priority_var, width=15, style='Custom.TCombobox',
                                     values=["high", "medium", "low"])
        priority_combo.grid(row=0, column=3, padx=(10, 0), sticky='w')
        
        # Keywords
        tk.Label(form_frame, text="Keywords (comma separated):", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky='w', pady=(0, 5))
        self.keywords_entry = tk.Entry(form_frame, width=80, font=('Arial', 10),
                                      bg=self.colors['input_bg'], fg=self.colors['text_primary'],
                                      insertbackground=self.colors['text_primary'],
                                      selectbackground=self.colors['accent_primary'])
        self.keywords_entry.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # Add example keywords
        self.keywords_entry.insert(0, "hello, hi, hey, greetings")
        
        # Follow-up Info
        tk.Label(form_frame, text="Detailed Follow-up Information:", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary'], font=('Arial', 10, 'bold')).grid(row=7, column=0, sticky='w', pady=(0, 5))
        self.followup_text = scrolledtext.ScrolledText(form_frame, width=80, height=6, font=('Arial', 10),
                                                      bg=self.colors['input_bg'], fg=self.colors['text_primary'],
                                                      insertbackground=self.colors['text_primary'],
                                                      selectbackground=self.colors['accent_primary'])
        self.followup_text.grid(row=8, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        # Add example follow-up info
        example_followup = "I'm an advanced chatbot with context awareness and intelligent matching. I can help with programming, AI, game development, and much more!"
        self.followup_text.insert('1.0', example_followup)
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg=self.colors['bg_primary'])
        button_frame.grid(row=9, column=0, columnspan=2, pady=10)
        
        tk.Button(button_frame, text="Add QA Pair", command=self.add_qa_pair,
                 bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                 font=('Arial', 10, 'bold'), padx=20, pady=8,
                 activebackground=self.colors['accent_secondary'],
                 activeforeground=self.colors['text_primary']).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Clear Form", command=self.clear_form,
                 bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                 font=('Arial', 10), padx=20, pady=8,
                 activebackground=self.colors['bg_tertiary'],
                 activeforeground=self.colors['text_primary']).pack(side=tk.LEFT)
        
        # Configure grid weights
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=1)
    
    def setup_train_tab(self, parent):
        content_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Quick Training Options", 
                font=('Arial', 14, 'bold'), bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary']).pack(pady=(0, 20))
        
        # Sample data training
        sample_frame = tk.Frame(content_frame, bg=self.colors['bg_secondary'], relief='raised', bd=1)
        sample_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(sample_frame, text="Sample Data Training", 
                font=('Arial', 12, 'bold'), bg=self.colors['bg_secondary'], 
                fg=self.colors['text_primary']).pack(padx=15, pady=10, anchor='w')
        
        tk.Label(sample_frame, text="Load the chatbot with pre-defined sample questions and answers covering various topics. Includes multiple question variations and random answers.", 
                font=('Arial', 10), bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                wraplength=600, justify=tk.LEFT).pack(padx=15, pady=(0, 10), anchor='w')
        
        tk.Button(sample_frame, text="Load Sample Data", command=self.train_with_sample_data,
                 bg=self.colors['accent_success'], fg=self.colors['text_primary'],
                 font=('Arial', 10, 'bold'), padx=20, pady=8,
                 activebackground=self.colors['accent_secondary']).pack(padx=15, pady=(0, 15), anchor='w')
        
        # Import/Export
        import_frame = tk.Frame(content_frame, bg=self.colors['bg_secondary'], relief='raised', bd=1)
        import_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(import_frame, text="Import/Export Data", 
                font=('Arial', 12, 'bold'), bg=self.colors['bg_secondary'], 
                fg=self.colors['text_primary']).pack(padx=15, pady=10, anchor='w')
        
        tk.Label(import_frame, text="Import QA pairs from JSON file or export current database to JSON.", 
                font=('Arial', 10), bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
                wraplength=600, justify=tk.LEFT).pack(padx=15, pady=(0, 10), anchor='w')
        
        io_button_frame = tk.Frame(import_frame, bg=self.colors['bg_secondary'])
        io_button_frame.pack(padx=15, pady=(0, 15), anchor='w')
        
        tk.Button(io_button_frame, text="Import from JSON", command=self.import_from_json,
                 bg=self.colors['accent_primary'], fg=self.colors['text_primary'],
                 font=('Arial', 10), padx=15, pady=6,
                 activebackground=self.colors['accent_secondary']).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(io_button_frame, text="Export to JSON", command=self.export_to_json,
                 bg=self.colors['accent_secondary'], fg=self.colors['text_primary'],
                 font=('Arial', 10), padx=15, pady=6,
                 activebackground=self.colors['accent_primary']).pack(side=tk.LEFT)
    
    def setup_view_tab(self, parent):
        content_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search frame
        search_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="Search:", bg=self.colors['bg_primary'],
                fg=self.colors['text_primary']).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30,
                               bg=self.colors['input_bg'], fg=self.colors['text_primary'],
                               insertbackground=self.colors['text_primary'],
                               selectbackground=self.colors['accent_primary'])
        search_entry.pack(side=tk.LEFT, padx=(10, 10))
        search_entry.bind('<KeyRelease>', self.search_qa_pairs)
        
        # QA pairs list
        self.qa_listbox = tk.Listbox(content_frame, width=80, height=20,
                                    bg=self.colors['input_bg'], fg=self.colors['text_primary'],
                                    selectbackground=self.colors['accent_primary'],
                                    selectforeground=self.colors['text_primary'])
        self.qa_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.qa_listbox.bind('<<ListboxSelect>>', self.on_qa_select)
        
        # Details frame
        details_frame = tk.Frame(content_frame, bg=self.colors['bg_secondary'])
        details_frame.pack(fill=tk.X)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, width=80, height=8,
                                                     bg=self.colors['input_bg'], fg=self.colors['text_primary'],
                                                     insertbackground=self.colors['text_primary'],
                                                     selectbackground=self.colors['accent_primary'])
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.details_text.config(state=tk.DISABLED)
        
        # Refresh button
        tk.Button(content_frame, text="Refresh List", command=self.refresh_qa_list,
                 bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                 font=('Arial', 10), padx=15, pady=5,
                 activebackground=self.colors['bg_tertiary']).pack(pady=10)
        
        self.refresh_qa_list()
    
    def load_database_info(self):
        """Load and display database information"""
        total_pairs = len(self.chatbot.qa_pairs)
        
        # Count by topic
        topics = {}
        total_questions = 0
        total_answers = 0
        
        for qa in self.chatbot.qa_pairs:
            topic = qa.get('topic', 'unknown')
            if topic not in topics:
                topics[topic] = 0
            topics[topic] += 1
            
            # Count questions and answers
            questions = qa.get('questions', [qa.get('question', '')])
            total_questions += len(questions)
            total_answers += len(qa.get('answers', []))
        
        info_text = f"Database: {self.chatbot.database_file}\n"
        info_text += f"Total QA Pairs: {total_pairs}\n"
        info_text += f"Total Questions: {total_questions}\n"
        info_text += f"Total Answers: {total_answers}\n"
        info_text += "Topics: " + ", ".join([f"{topic}({count})" for topic, count in topics.items()])
        
        self.info_label.config(text=info_text)
    
    def add_qa_pair(self):
        """Add a new QA pair from the form"""
        questions_text = self.questions_text.get(1.0, tk.END).strip()
        if not questions_text:
            messagebox.showerror("Error", "At least one question is required!")
            return
        
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        
        answers_text = self.answers_text.get(1.0, tk.END).strip()
        if not answers_text:
            messagebox.showerror("Error", "At least one answer is required!")
            return
        
        answers = [answer.strip() for answer in answers_text.split('\n') if answer.strip()]
        
        # Check for duplicate questions
        existing_questions = []
        for qa in self.chatbot.qa_pairs:
            existing_questions.extend(qa.get('questions', [qa.get('question', '')]))
        
        duplicate_questions = [q for q in questions if q.lower() in [eq.lower() for eq in existing_questions]]
        if duplicate_questions:
            messagebox.showerror("Error", f"These questions already exist: {', '.join(duplicate_questions[:3])}")
            return
        
        # Create QA pair
        qa_pair = {
            "questions": questions,
            "answers": answers,
            "topic": self.topic_var.get(),
            "priority": self.priority_var.get(),
            "context_sensitive": True,
            "keywords": [kw.strip() for kw in self.keywords_entry.get().split(',') if kw.strip()],
            "follow_up_info": self.followup_text.get(1.0, tk.END).strip()
        }
        
        # Add to chatbot
        self.chatbot.add_qa_pair(qa_pair)
        
        messagebox.showinfo("Success", f"QA pair added successfully!\nQuestions: {', '.join(questions[:3])}{'...' if len(questions) > 3 else ''}")
        self.clear_form()
        self.load_database_info()
        self.refresh_qa_list()
    
    def clear_form(self):
        """Clear all form fields"""
        self.questions_text.delete(1.0, tk.END)
        self.answers_text.delete(1.0, tk.END)
        self.topic_var.set("greeting")
        self.priority_var.set("medium")
        self.keywords_entry.delete(0, tk.END)
        self.followup_text.delete(1.0, tk.END)
        
        # Add back the examples
        self.questions_text.insert('1.0', "hello\nhi\nhey\ngreetings")
        self.answers_text.insert('1.0', "Hello! How can I help you today?\nHi there! Nice to meet you!\nHey! I'm here to assist you!")
        self.keywords_entry.insert(0, "hello, hi, hey, greetings")
        self.followup_text.insert('1.0', "I'm an advanced chatbot with context awareness and intelligent matching. I can help with programming, AI, game development, and much more!")
    
    def train_with_sample_data(self):
        """Train chatbot with sample data"""
        if self.chatbot.qa_pairs:
            response = messagebox.askyesno("Confirm", 
                                         "This will add sample data to your existing database. Continue?")
            if not response:
                return
        
        sample_data = create_sample_data()
        added_count = 0
        
        for qa_pair in sample_data:
            # Check if any question already exists
            existing_questions = []
            for existing_qa in self.chatbot.qa_pairs:
                existing_questions.extend(existing_qa.get('questions', [existing_qa.get('question', '')]))
            
            new_questions = qa_pair.get('questions', [qa_pair.get('question', '')])
            if not any(q.lower() in [eq.lower() for eq in existing_questions] for q in new_questions):
                self.chatbot.add_qa_pair(qa_pair)
                added_count += 1
        
        messagebox.showinfo("Success", f"Added {added_count} new QA pairs from sample data!")
        self.load_database_info()
        self.refresh_qa_list()
    
    def import_from_json(self):
        """Import QA pairs from JSON file"""
        filename = filedialog.askopenfilename(
            title="Import QA Pairs",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            if not isinstance(imported_data, list):
                messagebox.showerror("Error", "Invalid JSON format. Expected a list of QA pairs.")
                return
            
            added_count = 0
            for qa_pair in imported_data:
                # Validate required fields
                if not (('questions' in qa_pair or 'question' in qa_pair) and 'answers' in qa_pair):
                    continue
                
                # Convert old format to new format if needed
                if 'question' in qa_pair and 'questions' not in qa_pair:
                    qa_pair['questions'] = [qa_pair['question']]
                    del qa_pair['question']
                
                # Check for duplicates
                existing_questions = []
                for existing_qa in self.chatbot.qa_pairs:
                    existing_questions.extend(existing_qa.get('questions', [existing_qa.get('question', '')]))
                
                new_questions = qa_pair.get('questions', [])
                if not any(q.lower() in [eq.lower() for eq in existing_questions] for q in new_questions):
                    self.chatbot.add_qa_pair(qa_pair)
                    added_count += 1
            
            messagebox.showinfo("Success", f"Imported {added_count} new QA pairs!")
            self.load_database_info()
            self.refresh_qa_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")
    
    def export_to_json(self):
        """Export current database to JSON file"""
        filename = filedialog.asksaveasfilename(
            title="Export QA Pairs",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.chatbot.qa_pairs, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Database exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def refresh_qa_list(self):
        """Refresh the QA pairs list"""
        self.qa_listbox.delete(0, tk.END)
        for qa in self.chatbot.qa_pairs:
            questions = qa.get('questions', [qa.get('question', 'Unknown')])
            primary_question = questions[0] if questions else 'Unknown'
            self.qa_listbox.insert(tk.END, primary_question)
    
    def search_qa_pairs(self, event=None):
        """Search QA pairs based on search term"""
        search_term = self.search_var.get().lower()
        self.qa_listbox.delete(0, tk.END)
        
        for qa in self.chatbot.qa_pairs:
            questions = qa.get('questions', [qa.get('question', '')])
            answers = qa.get('answers', [])
            keywords = qa.get('keywords', [])
            
            # Search in questions, answers, and keywords
            if (any(search_term in question.lower() for question in questions) or
                any(search_term in answer.lower() for answer in answers) or
                any(search_term in keyword.lower() for keyword in keywords)):
                primary_question = questions[0] if questions else 'Unknown'
                self.qa_listbox.insert(tk.END, primary_question)
    
    def on_qa_select(self, event):
        """Show details of selected QA pair"""
        selection = self.qa_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        qa = self.chatbot.qa_pairs[index]
        
        questions = qa.get('questions', [qa.get('question', 'Unknown')])
        answers = qa.get('answers', [])
        
        details = f"Primary Question: {questions[0]}\n"
        if len(questions) > 1:
            details += f"Alternative Questions: {', '.join(questions[1:])}\n"
        details += f"Topic: {qa.get('topic', 'N/A')}\n"
        details += f"Priority: {qa.get('priority', 'N/A')}\n"
        details += f"Keywords: {', '.join(qa.get('keywords', []))}\n\n"
        details += f"Answers ({len(answers)} available, randomly selected):\n"
        for i, answer in enumerate(answers, 1):
            details += f"  {i}. {answer}\n"
        
        if qa.get('follow_up_info'):
            details += f"\nFollow-up Info:\n{qa['follow_up_info']}"
        
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)

def create_sample_data():
    """Create sample data for the chatbot with multiple questions per answer set"""
    sample_data = [
        # ===== GREETINGS & BASIC =====
        {
            "questions": ["hello", "hi", "hey", "greetings"],
            "answers": [
                "Hello! How can I help you today?",
                "Hi there! Nice to meet you!",
                "Hey! I'm here to assist you!",
                "Greetings! What can I do for you?",
                "Hello! Ready to chat!",
            ],
            "topic": "greeting",
            "priority": "high",
            "context_sensitive": False,
            "keywords": ["hello", "hi", "hey", "greetings"],
            "follow_up_info": "I'm an advanced chatbot with context awareness, streaming responses, and intelligent matching. I can help with programming, AI, game development, and much more!"
        },
        {
            "questions": ["how are you", "how are you doing", "how's it going"],
            "answers": [
                "I'm functioning well, thank you! How are you?",
                "I'm doing great! Ready to help you!",
                "I'm running smoothly! What can I help with?",
                "All systems operational! How can I assist you today?",
            ],
            "topic": "greeting",
            "priority": "medium",
            "context_sensitive": False,
            "keywords": ["how", "are", "you", "doing"],
            "follow_up_info": "As an AI, I don't have feelings, but I'm optimized for conversation and context awareness. I'm always learning and improving to provide better assistance!"
        },
        
        # ===== THANKS & COURTESY =====
        {
            "questions": ["thank you", "thanks", "thank you very much", "thanks a lot"],
            "answers": [
                "You're welcome! Happy to help!",
                "My pleasure! Let me know if you need anything else!",
                "You're welcome! Is there anything more I can assist with?",
                "Glad I could help! Feel free to ask more questions!",
            ],
            "topic": "thanks",
            "priority": "high",
            "context_sensitive": False,
            "keywords": ["thank", "thanks", "appreciate"],
            "follow_up_info": "I'm always here to help! I can provide detailed explanations, compare technologies, or help you learn new concepts. Just let me know what you're interested in!"
        },
        
        # ===== PROGRAMMING & TECH =====
        {
            "questions": ["Tell me about Python", "What is Python", "Python information", "Explain Python"],
            "answers": [
                "Python is a versatile programming language great for beginners and experts!",
                "Python is known for its simplicity and extensive libraries!",
                "Python's clean syntax makes it excellent for rapid development!",
                "Python is a high-level language used for web development, data science, and AI!",
            ],
            "topic": "programming",
            "priority": "medium",
            "context_sensitive": True,
            "keywords": ["python", "programming", "language"],
            "follow_up_info": """Python Details:
• Created by Guido van Rossum in 1991
• Used for: web development (Django, Flask), data science (Pandas, NumPy), AI/ML (TensorFlow, PyTorch)
• Key features: dynamic typing, automatic memory management, extensive standard library
• Popular in: scientific computing, automation, web development, and education"""
        },
        {
            "questions": ["What is machine learning", "Explain machine learning", "ML definition", "What is ML"],
            "answers": [
                "Machine learning enables computers to learn from data without explicit programming!",
                "ML algorithms improve automatically through experience and data!",
                "Machine learning powers modern AI applications and intelligent systems!",
                "ML is a subset of AI that focuses on algorithms that learn from data!",
            ],
            "topic": "ai",
            "priority": "medium",
            "context_sensitive": True,
            "keywords": ["machine", "learning", "ai", "algorithm"],
            "follow_up_info": """Machine Learning Types:
• Supervised Learning: Training with labeled data (classification, regression)
• Unsupervised Learning: Finding patterns in unlabeled data (clustering, dimensionality reduction)
• Reinforcement Learning: Learning through trial and error with rewards/punishments

Common Algorithms:
• Linear Regression, Decision Trees, Neural Networks
• K-Means Clustering, Principal Component Analysis
• Q-Learning, Deep Q-Networks

Applications: Recommendation systems, image recognition, natural language processing, autonomous vehicles"""
        },
        {
            "questions": ["What is Godot", "Tell me about Godot", "Godot engine", "Explain Godot"],
            "answers": [
                "Godot is a free, open-source game engine for 2D and 3D development!",
                "Godot Engine is known for its flexible scene system and ease of use!",
                "It's a popular game engine alternative with great community support!",
                "Godot is a powerful game development engine that's completely free!",
            ],
            "topic": "gaming",
            "priority": "medium",
            "context_sensitive": True,
            "keywords": ["godot", "game", "engine", "development"],
            "follow_up_info": """Godot Engine Features:
• Scene System: Flexible node-based architecture
• Scripting: GDScript (Python-like), C#, VisualScript
• 2D/3D: Built-in support for both 2D and 3D game development
• Export: Cross-platform to Windows, Mac, Linux, Android, iOS, Web
• Community: Active open-source community with extensive asset library

Advantages:
• Completely free and open-source (MIT license)
• No royalties or subscription fees
• Lightweight and fast
• Great for indie developers and prototyping"""
        },
        {
            "questions": ["What is artificial intelligence", "Define AI", "Explain artificial intelligence", "What is AI"],
            "answers": [
                "AI is the simulation of human intelligence in machines!",
                "Artificial intelligence enables machines to think, learn, and reason!",
                "AI includes machine learning, natural language processing, and computer vision!",
                "AI systems can perform tasks that typically require human intelligence!",
            ],
            "topic": "ai",
            "priority": "medium",
            "context_sensitive": True,
            "keywords": ["artificial", "intelligence", "ai", "machine"],
            "follow_up_info": """AI Branches:
• Machine Learning: Algorithms that learn from data
• Natural Language Processing: Understanding and generating human language
• Computer Vision: Interpreting and understanding visual information
• Robotics: Intelligent control of physical systems
• Expert Systems: Rule-based decision making

Current Applications:
• Virtual assistants (Siri, Alexa)
• Image and speech recognition
• Autonomous vehicles
• Medical diagnosis systems
• Game AI and procedural content generation"""
        },
        
        # ===== ADDITIONAL TOPICS =====
        {
            "questions": ["What is Blender", "Tell me about Blender", "Blender software", "Explain Blender"],
            "answers": [
                "Blender is a free and open-source 3D creation suite!",
                "Blender is used for 3D modeling, animation, visual effects, and more!",
                "It's a powerful alternative to commercial 3D software packages!",
                "Blender is a complete 3D creation toolset that's completely free!",
            ],
            "topic": "creative",
            "priority": "medium",
            "context_sensitive": True,
            "keywords": ["blender", "3d", "modeling", "animation"],
            "follow_up_info": """Blender Features:
• 3D Modeling: Polygon modeling, sculpting, retopology
• Animation: Character animation, rigging, shape keys
• Rendering: Cycles (ray-tracing) and Eevee (real-time) renderers
• VFX: Compositing, motion tracking, simulation
• Game Development: Game engine (though deprecated in newer versions)

Advantages:
• Completely free and open-source
• Active development and large community
• All-in-one solution for 3D pipeline
• Used in professional studios and indie projects alike"""
        },
    ]
    
    return sample_data

def main():
    """Main function - GUI only"""
    try:
        root = tk.Tk()
        app = TrainingGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"GUI Error: {e}")
        messagebox.showerror("Error", f"Failed to start training interface: {e}")

if __name__ == "__main__":
    main()
