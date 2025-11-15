import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
from typing import List, Dict, Any

class QuestionAnswerEditor:
    """Text editor popup for questions (like in training app)"""
    
    def __init__(self, parent, item_type="question", initial_text="", on_save=None):
        self.window = tk.Toplevel(parent)
        self.window.title(f"{item_type.title()} Editor")
        self.window.geometry("500x400")
        self.window.configure(bg='#2d2d5a')
        self.window.minsize(400, 300)
        
        self.on_save = on_save
        self.item_type = item_type
        
        self.setup_ui(initial_text)
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self, initial_text):
        # Configure grid weights
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # Text widget
        self.text_widget = scrolledtext.ScrolledText(
            self.window, 
            font=('Arial', 11),
            bg='#1a1a2e', 
            fg='white',
            insertbackground='white',
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.text_widget.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        self.text_widget.insert('1.0', initial_text)
        
        # Focus and select all text
        self.text_widget.focus_set()
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        
        # Bind Shift+Enter for new line, Enter for submit
        self.text_widget.bind('<Shift-Return>', self.on_shift_enter)
        self.text_widget.bind('<Return>', self.on_enter)
        
        # Button frame
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=1, column=0, sticky='ew', padx=15, pady=(0, 15))
        button_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = tk.Label(
            button_frame,
            text=f"Editing {self.item_type}... (Shift+Enter for new line, Enter to save)",
            font=('Arial', 9),
            bg='#2d2d5a',
            fg='#b0b0d0'
        )
        self.status_label.grid(row=0, column=0, sticky='w')
        
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
        ).grid(row=0, column=2)
    
    def on_shift_enter(self, event):
        """Handle Shift+Enter - insert new line"""
        self.text_widget.insert(tk.INSERT, '\n')
        return 'break'
    
    def on_enter(self, event):
        """Handle Enter - submit"""
        self.save()
        return 'break'
    
    def save(self):
        text = self.text_widget.get('1.0', tk.END).strip()
        if text and self.on_save:
            self.on_save(text)
            self.window.destroy()
        elif not text:
            messagebox.showwarning("Empty", f"Please enter a {self.item_type}.")
            self.text_widget.focus_set()


class RoutingGroupEditor:
    """Dialog for editing routing groups with improved UI"""
    
    def __init__(self, parent, group_data=None, on_save=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Routing Group Editor")
        self.window.geometry("700x650")
        self.window.configure(bg='#2d2d5a')
        self.window.minsize(600, 550)
        
        self.on_save = on_save
        self.group_data = group_data or {}
        
        # Confidence thresholds (same as AI engine)
        self.CONFIDENCE_THRESHOLDS = {
            'exact_match': 0.95,
            'high_confidence': 0.75,
            'medium_confidence': 0.60,
            'low_confidence': 0.45,
            'min_acceptable': 0.35
        }
        
        self.questions = []
        self.validation_errors = []
        
        self.setup_ui()
        
        if group_data:
            self.load_data()
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def get_available_modules(self):
        """Get available modules from core/modules folder"""
        modules_folder = "core/modules"
        modules = []
        
        if os.path.exists(modules_folder):
            for file in os.listdir(modules_folder):
                if file.endswith('.py') and not file.startswith('_'):
                    module_name = file[:-3]  # Remove .py extension
                    modules.append(module_name)
        
        return sorted(modules)
    
    def calculate_max_question_words(self):
        """Calculate the maximum word count in questions"""
        if not self.questions:
            return 0
        
        max_words = 0
        for question in self.questions:
            word_count = len(question.split())
            if word_count > max_words:
                max_words = word_count
        
        return max_words
    
    def setup_ui(self):
        # Configure grid weights
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Title
        tk.Label(
            self.window,
            text="Routing Group Editor",
            font=('Arial', 16, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))
        
        # Main content frame
        content_frame = tk.Frame(self.window, bg='#2d2d5a')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Group name
        tk.Label(
            content_frame,
            text="Group Name:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(
            content_frame,
            textvariable=self.name_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.name_entry.grid(row=0, column=1, sticky='ew', pady=(0, 15))
        self.name_entry.focus_set()
        
        # Module selection (dropdown)
        tk.Label(
            content_frame,
            text="Module:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        self.module_var = tk.StringVar()
        available_modules = self.get_available_modules()
        
        # Create custom style for combobox
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure combobox colors
        style.configure('Custom.TCombobox',
            background='#1a1a2e',
            foreground='white',
            fieldbackground='#1a1a2e',
            selectbackground='#6c63ff',
            selectforeground='white',
            borderwidth=1,
            relief='flat',
            padding=5
        )
        
        style.map('Custom.TCombobox',
            fieldbackground=[('readonly', '#1a1a2e')],
            selectbackground=[('readonly', '#6c63ff')],
            selectforeground=[('readonly', 'white')],
            background=[('readonly', '#1a1a2e')]
        )
        
        self.module_combo = ttk.Combobox(
            content_frame,
            textvariable=self.module_var,
            values=["None"] + available_modules,
            state="readonly",
            font=('Arial', 11),
            style='Custom.TCombobox'
        )
        self.module_combo.grid(row=1, column=1, sticky='ew', pady=(0, 15))
        self.module_combo.set("None")
        
        # Confidence threshold (dropdown)
        tk.Label(
            content_frame,
            text="Confidence Threshold:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=(0, 8))
        
        self.threshold_var = tk.DoubleVar(value=0.75)
        
        # Confidence threshold options for dropdown
        threshold_options = [
            ("Exact Match", 0.95),
            ("High Confidence", 0.75),
            ("Medium Confidence", 0.60),
            ("Low Confidence", 0.45),
            ("Custom", 0.75)
        ]
        
        threshold_display = [f"{name} ({value})" for name, value in threshold_options[:-1]] + ["Custom..."]
        threshold_values = [value for _, value in threshold_options]
        
        self.threshold_combo = ttk.Combobox(
            content_frame,
            values=threshold_display,
            state="readonly",
            font=('Arial', 11),
            style='Custom.TCombobox'
        )
        self.threshold_combo.grid(row=2, column=1, sticky='ew', pady=(0, 15))
        self.threshold_combo.set("High Confidence (0.75)")
        
        # Custom threshold entry (hidden by default)
        self.custom_threshold_frame = tk.Frame(content_frame, bg='#2d2d5a')
        self.custom_threshold_frame.grid(row=3, column=1, sticky='ew', pady=(0, 15))
        self.custom_threshold_frame.grid_remove()  # Hidden initially
        
        tk.Label(
            self.custom_threshold_frame,
            text="Custom Threshold:",
            font=('Arial', 10, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.custom_threshold_var = tk.DoubleVar(value=0.75)
        self.custom_threshold_entry = tk.Entry(
            self.custom_threshold_frame,
            textvariable=self.custom_threshold_var,
            width=8,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.custom_threshold_entry.pack(side=tk.LEFT)
        
        # Word limit settings
        word_limit_frame = tk.Frame(content_frame, bg='#2d2d5a')
        word_limit_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        word_limit_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            word_limit_frame,
            text="Word Limit Settings:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        # Enable word limit checkbox
        self.word_limit_enabled = tk.BooleanVar(value=False)
        word_limit_check = tk.Checkbutton(
            word_limit_frame,
            text="Enable Word Limit",
            variable=self.word_limit_enabled,
            command=self.toggle_word_limit,
            bg='#2d2d5a',
            fg='white',
            selectcolor='#6c63ff',
            activebackground='#2d2d5a',
            activeforeground='white',
            font=('Arial', 10)
        )
        word_limit_check.grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        # Word limit controls (initially disabled)
        self.word_limit_controls = tk.Frame(word_limit_frame, bg='#2d2d5a')
        self.word_limit_controls.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 8))
        self.word_limit_controls.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            self.word_limit_controls,
            text="Max Words:",
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='#b0b0d0'
        ).grid(row=0, column=0, sticky='w', padx=(20, 10))
        
        self.max_words_var = tk.IntVar(value=10)
        self.max_words_spinbox = tk.Spinbox(
            self.word_limit_controls,
            from_=1,
            to=100,
            textvariable=self.max_words_var,
            width=8,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            buttonbackground='#6c63ff'
        )
        self.max_words_spinbox.grid(row=0, column=1, sticky='w')
        
        tk.Label(
            self.word_limit_controls,
            text="Penalty per extra word:",
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='#b0b0d0'
        ).grid(row=1, column=0, sticky='w', padx=(20, 10), pady=(5, 0))
        
        self.penalty_per_word_var = tk.DoubleVar(value=0.02)
        self.penalty_spinbox = tk.Spinbox(
            self.word_limit_controls,
            from_=0.01,
            to=0.5,
            increment=0.01,
            textvariable=self.penalty_per_word_var,
            width=8,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            buttonbackground='#6c63ff',
            format="%.2f"
        )
        self.penalty_spinbox.grid(row=1, column=1, sticky='w', pady=(5, 0))
        
        # Word limit validation label
        self.word_limit_validation = tk.Label(
            self.word_limit_controls,
            text="",
            font=('Arial', 9),
            bg='#2d2d5a',
            fg='#ff6b6b',
            wraplength=400
        )
        self.word_limit_validation.grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 0), padx=(20, 0))
        
        # Initially disable word limit controls
        self.toggle_word_limit()
        
        # Questions section (like training app)
        questions_frame = tk.Frame(content_frame, bg='#252547', relief='raised', bd=1)
        questions_frame.grid(row=5, column=0, columnspan=2, sticky='nsew', pady=(0, 15))
        questions_frame.grid_columnconfigure(0, weight=1)
        questions_frame.grid_rowconfigure(1, weight=1)
        
        # Questions header
        questions_header = tk.Frame(questions_frame, bg='#252547')
        questions_header.grid(row=0, column=0, sticky='ew', padx=10, pady=8)
        questions_header.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            questions_header,
            text="Questions",
            font=('Arial', 12, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        tk.Button(
            questions_header,
            text="+ Add Question",
            command=self.add_question,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9),
            padx=8
        ).grid(row=0, column=1)
        
        # Questions list container
        list_container = tk.Frame(questions_frame, bg='#252547')
        list_container.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 8))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)
        
        self.questions_listbox = tk.Listbox(
            list_container,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            selectbackground='#6c63ff',
            activestyle='none',
            height=6
        )
        self.questions_listbox.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbar for questions
        questions_scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL, 
                                         command=self.questions_listbox.yview,
                                         bg='#2d2d5a', troughcolor='#1a1a2e', 
                                         activebackground='#6c63ff')
        self.questions_listbox.config(yscrollcommand=questions_scrollbar.set)
        questions_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Question actions
        question_actions = tk.Frame(questions_frame, bg='#252547')
        question_actions.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 8))
        
        tk.Button(
            question_actions,
            text="Edit",
            command=self.edit_question,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9),
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            question_actions,
            text="Delete",
            command=self.delete_question,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9),
            width=8
        ).pack(side=tk.LEFT)
        
        # Validation error display
        self.validation_frame = tk.Frame(content_frame, bg='#2d2d5a')
        self.validation_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        self.validation_label = tk.Label(
            self.validation_frame,
            text="",
            font=('Arial', 9),
            bg='#2d2d5a',
            fg='#ff6b6b',
            wraplength=600,
            justify=tk.LEFT
        )
        self.validation_label.pack(anchor='w')
        
        # Instructions
        instructions_frame = tk.Frame(content_frame, bg='#2d2d5a')
        instructions_frame.grid(row=7, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        instructions = tk.Label(
            instructions_frame,
            text="💡 Questions will be matched against user input. If confidence meets the threshold,\nthe request will be routed to the specified module. Word limits reduce confidence for longer inputs.",
            font=('Arial', 9),
            bg='#2d2d5a',
            fg='#b0b0d0',
            justify=tk.LEFT
        )
        instructions.pack(anchor='w')
        
        # Buttons frame
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=2, column=0, sticky='e', padx=20, pady=(0, 20))
        
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
        
        self.save_button = tk.Button(
            button_frame,
            text="💾 Save Group",
            command=self.save_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        )
        self.save_button.pack(side=tk.RIGHT)
        
        # Configure content frame row weights
        content_frame.grid_rowconfigure(5, weight=1)
        
        # Bind events
        self.threshold_combo.bind('<<ComboboxSelected>>', self.on_threshold_selected)
        self.custom_threshold_var.trace('w', self.on_custom_threshold_changed)
        self.max_words_var.trace('w', self.validate_word_limit)
        self.name_var.trace('w', self.validate_form)
    
    def toggle_word_limit(self):
        """Enable/disable word limit controls"""
        if self.word_limit_enabled.get():
            # Enable controls
            self.max_words_spinbox.config(state='normal', bg='#1a1a2e', fg='white')
            self.penalty_spinbox.config(state='normal', bg='#1a1a2e', fg='white')
            self.word_limit_controls.grid()
            self.validate_word_limit()
        else:
            # Disable controls
            self.max_words_spinbox.config(state='disabled', bg='#2d2d5a', fg='#8080a0')
            self.penalty_spinbox.config(state='disabled', bg='#2d2d5a', fg='#8080a0')
            self.word_limit_controls.grid_remove()
            self.word_limit_validation.config(text="")
    
    def validate_word_limit(self, *args):
        """Validate word limit settings"""
        if not self.word_limit_enabled.get():
            return True
        
        try:
            max_words = int(self.max_words_var.get())
            max_question_words = self.calculate_max_question_words()
            
            if max_words < max_question_words:
                self.word_limit_validation.config(
                    text=f"❌ Max words ({max_words}) cannot be less than longest question ({max_question_words} words)"
                )
                return False
            else:
                self.word_limit_validation.config(
                    text=f"✅ Minimum {max_question_words} words required (longest question)"
                )
                return True
        except ValueError:
            self.word_limit_validation.config(text="❌ Please enter a valid number for max words")
            return False
    
    def validate_form(self, *args):
        """Validate the entire form"""
        errors = []
        
        # Check group name
        if not self.name_var.get().strip():
            errors.append("Group name is required")
        
        # Check questions
        if not self.questions:
            errors.append("At least one question is required")
        
        # Check word limit if enabled
        if self.word_limit_enabled.get():
            if not self.validate_word_limit():
                errors.append("Word limit settings are invalid")
        
        # Update validation display
        if errors:
            self.validation_label.config(text=" • " + "\n • ".join(errors))
            self.save_button.config(state='disabled', bg='#8080a0')
        else:
            self.validation_label.config(text="")
            self.save_button.config(state='normal', bg='#00ff88')
        
        return len(errors) == 0
    
    def on_threshold_selected(self, event):
        """Handle threshold selection from dropdown"""
        selection = self.threshold_combo.get()
        
        if selection == "Custom...":
            self.custom_threshold_frame.grid()
            # Set threshold to custom value
            self.threshold_var.set(self.custom_threshold_var.get())
        else:
            self.custom_threshold_frame.grid_remove()
            # Extract value from selection text
            if "Exact Match" in selection:
                self.threshold_var.set(0.95)
            elif "High Confidence" in selection:
                self.threshold_var.set(0.75)
            elif "Medium Confidence" in selection:
                self.threshold_var.set(0.60)
            elif "Low Confidence" in selection:
                self.threshold_var.set(0.45)
    
    def on_custom_threshold_changed(self, *args):
        """Update threshold when custom value changes"""
        if self.threshold_combo.get() == "Custom...":
            try:
                custom_val = float(self.custom_threshold_var.get())
                if 0.35 <= custom_val <= 1.0:
                    self.threshold_var.set(custom_val)
            except:
                pass
    
    def add_question(self):
        """Add a new question using text editor popup"""
        def save_question(text):
            self.questions.append(text)
            self.refresh_questions_list()
            self.validate_form()
            self.validate_word_limit()
        
        QuestionAnswerEditor(self.window, "question", on_save=save_question)
    
    def edit_question(self):
        """Edit selected question using text editor popup"""
        selection = self.questions_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        current_text = self.questions[index]
        
        def save_question(text):
            self.questions[index] = text
            self.refresh_questions_list()
            self.validate_form()
            self.validate_word_limit()
        
        QuestionAnswerEditor(self.window, "question", current_text, save_question)
    
    def delete_question(self):
        """Delete selected question"""
        selection = self.questions_listbox.curselection()
        if selection:
            index = selection[0]
            self.questions.pop(index)
            self.refresh_questions_list()
            self.validate_form()
            self.validate_word_limit()
    
    def refresh_questions_list(self):
        """Refresh the questions listbox"""
        self.questions_listbox.delete(0, tk.END)
        for question in self.questions:
            # Truncate long questions for display
            display_text = question[:60] + "..." if len(question) > 60 else question
            self.questions_listbox.insert(tk.END, display_text)
    
    def load_data(self):
        if 'group_name' in self.group_data:
            self.name_var.set(self.group_data['group_name'])
        if 'engine' in self.group_data:
            module = self.group_data['engine']
            if module and module != "None":
                self.module_var.set(module)
        
        # Load confidence threshold
        if 'confidence_threshold' in self.group_data:
            threshold = self.group_data['confidence_threshold']
            self.threshold_var.set(threshold)
            self.custom_threshold_var.set(threshold)
            
            # Set appropriate dropdown selection
            if threshold == 0.95:
                self.threshold_combo.set("Exact Match (0.95)")
            elif threshold == 0.75:
                self.threshold_combo.set("High Confidence (0.75)")
            elif threshold == 0.60:
                self.threshold_combo.set("Medium Confidence (0.60)")
            elif threshold == 0.45:
                self.threshold_combo.set("Low Confidence (0.45)")
            else:
                self.threshold_combo.set("Custom...")
                self.custom_threshold_frame.grid()
        
        # Load word limit settings
        if 'word_limit_enabled' in self.group_data:
            self.word_limit_enabled.set(self.group_data['word_limit_enabled'])
        if 'max_words' in self.group_data:
            self.max_words_var.set(self.group_data['max_words'])
        if 'penalty_per_word' in self.group_data:
            self.penalty_per_word_var.set(self.group_data['penalty_per_word'])
        
        self.toggle_word_limit()
        
        # Load questions
        if 'questions' in self.group_data:
            self.questions = self.group_data['questions']
            self.refresh_questions_list()
        
        self.validate_form()
    
    def save_group(self):
        if not self.validate_form():
            return
        
        group_name = self.name_var.get().strip()
        module = self.module_var.get()
        threshold = self.threshold_var.get()
        
        # Module is optional now - can be "None"
        if not module:
            module = "None"
        
        group_data = {
            'group_name': group_name,
            'engine': module,
            'confidence_threshold': threshold,
            'word_limit_enabled': self.word_limit_enabled.get(),
            'max_words': self.max_words_var.get() if self.word_limit_enabled.get() else 0,
            'penalty_per_word': self.penalty_per_word_var.get() if self.word_limit_enabled.get() else 0.0,
            'questions': self.questions
        }
        
        if self.on_save:
            self.on_save(group_data)
        
        self.window.destroy()


class RoutingTrainerGUI:
    """Main routing trainer GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI - Routing Trainer")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1a1a2e')
        self.root.minsize(1000, 600)  # More strict minimum size
        
        self.routing_file = "resources/route.json"
        self.routing_groups = []
        self.current_columns = 4
        self.min_card_width = 300  # Wider for rectangular tiles
        self.min_card_height = 140  # Slightly taller for more info
        self.card_padding = 12
        self.group_name_limit = 35  # Character limit for group names
        
        # Ensure resources folder exists and create default config
        self.ensure_resources_folder()
        self.load_routing_data()
        self.setup_gui()
        self.refresh_groups()
    
    def ensure_resources_folder(self):
        """Ensure resources folder exists and create default config if needed"""
        os.makedirs("resources", exist_ok=True)
        
        # Create default config if it doesn't exist
        if not os.path.exists(self.routing_file):
            default_config = {
                "routing_groups": [],
                "available_engines": [],
                "version": "1.0"
            }
            try:
                with open(self.routing_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                print("✅ Created default routing configuration")
            except Exception as e:
                print(f"❌ Error creating default config: {e}")
    
    def load_routing_data(self):
        """Load routing configuration from file"""
        if os.path.exists(self.routing_file):
            try:
                with open(self.routing_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.routing_groups = config.get('routing_groups', [])
                print(f"✅ Loaded {len(self.routing_groups)} routing groups")
            except Exception as e:
                print(f"❌ Error loading routing config: {e}")
                self.routing_groups = []
        else:
            print("⚠️  No routing config found, starting fresh")
            self.routing_groups = []
    
    def save_routing_data(self):
        """Save routing configuration to file"""
        config = {
            "routing_groups": self.routing_groups,
            "available_engines": list(set(group['engine'] for group in self.routing_groups if group['engine'] != "None")),
            "version": "1.0"
        }
        
        try:
            with open(self.routing_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print("✅ Routing configuration saved")
            return True
        except Exception as e:
            print(f"❌ Error saving routing config: {e}")
            return False
    
    def setup_gui(self):
        # Configure main window grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        self.setup_header(main_frame)
        self.setup_toolbar(main_frame)
        self.setup_groups_grid(main_frame)
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        header.grid_columnconfigure(0, weight=1)
        
        # Title
        tk.Label(
            header,
            text="🚦 Routing Configuration",
            font=('Arial', 20, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        # Stats area
        stats_frame = tk.Frame(header, bg='#1a1a2e')
        stats_frame.grid(row=1, column=0, sticky='w', pady=(10, 0))
        
        self.stats_vars = {}
        stats = [("Routing Groups", "0"), ("Active Modules", "0"), ("Total Questions", "0")]
        
        for i, (label, value) in enumerate(stats):
            frame = tk.Frame(stats_frame, bg='#1a1a2e')
            frame.grid(row=0, column=i, padx=12)
            
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
        toolbar.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        toolbar.grid_columnconfigure(1, weight=1)
        
        # Search area
        search_frame = tk.Frame(toolbar, bg='#1a1a2e')
        search_frame.grid(row=0, column=0, sticky='w')
        
        tk.Label(
            search_frame,
            text="Search:",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=25,
            bg='#2d2d5a',
            fg='white',
            insertbackground='white',
            font=('Arial', 9)
        )
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Bind search for real-time filtering
        self.search_var.trace('w', self.on_search)
        
        # Action buttons
        actions = tk.Frame(toolbar, bg='#1a1a2e')
        actions.grid(row=0, column=1, sticky='e')
        
        tk.Button(
            actions,
            text="🔄 Refresh",
            command=self.refresh_groups,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9),
            padx=12
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            actions,
            text="+ New Routing Group",
            command=self.new_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15
        ).pack(side=tk.LEFT)
    
    def setup_groups_grid(self, parent):
        """Setup responsive groups display"""
        container = tk.Frame(parent, bg='#1a1a2e')
        container.grid(row=2, column=0, sticky='nsew')
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(container, bg='#1a1a2e', highlightthickness=0)
        
        # Scrollbar
        self.scrollbar = tk.Scrollbar(
            container, 
            orient=tk.VERTICAL, 
            command=self.canvas.yview,
            bg='#2d2d5a', 
            troughcolor='#1a1a2e', 
            activebackground='#6c63ff',
            width=16
        )
        
        # Main scrollable frame
        self.scroll_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Groups container inside scroll frame
        self.groups_container = tk.Frame(self.scroll_frame, bg='#1a1a2e')
        self.groups_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Bind resize event for responsive layout
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.scroll_frame.bind("<MouseWheel>", self.on_mousewheel)
        self.groups_container.bind("<MouseWheel>", self.on_mousewheel)
    
    def on_canvas_resize(self, event):
        """Handle canvas resize to adjust grid columns"""
        if hasattr(self, 'groups_container') and self.groups_container.winfo_children():
            self.refresh_groups_layout()
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_search(self, *args):
        """Handle real-time search"""
        search_term = self.search_var.get().lower()
        filtered_groups = []
        
        for group in self.routing_groups:
            # Search in group name, engine, and questions
            if (search_term in group['group_name'].lower() or
                search_term in group['engine'].lower() or
                any(search_term in q.lower() for q in group['questions'])):
                filtered_groups.append(group)
        
        self.display_filtered_groups(filtered_groups if search_term else self.routing_groups)
    
    def display_filtered_groups(self, filtered_groups):
        """Display filtered groups"""
        # Clear existing cards
        for widget in self.groups_container.winfo_children():
            widget.destroy()
        
        # Calculate responsive columns
        columns = self.calculate_columns()
        
        # Configure grid columns
        for i in range(columns):
            self.groups_container.grid_columnconfigure(i, weight=1)
        
        # Create group cards
        for i, group in enumerate(filtered_groups):
            card = self.create_group_card(group)
            
            # Arrange in responsive grid
            row = i // columns
            col = i % columns
            card.grid(
                row=row, 
                column=col, 
                sticky='nsew', 
                padx=8, 
                pady=8
            )
        
        self.current_columns = columns
        
        # Update stats
        total_questions = sum(len(g['questions']) for g in filtered_groups)
        active_modules = set(g['engine'] for g in filtered_groups if g['engine'] != "None")
        
        self.stats_vars["Routing Groups"].set(str(len(filtered_groups)))
        self.stats_vars["Active Modules"].set(str(len(active_modules)))
        self.stats_vars["Total Questions"].set(str(total_questions))
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def calculate_columns(self):
        """Calculate optimal number of columns based on available width"""
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return 3
        
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:  # Canvas not yet rendered
            return 3
        
        # Calculate how many cards fit with minimum width and padding
        available_width = canvas_width - 40  # Account for container padding
        card_total_width = self.min_card_width + self.card_padding
        max_columns = max(1, available_width // card_total_width)
        
        return max_columns
    
    def refresh_groups_layout(self):
        """Refresh just the layout without recreating cards"""
        if not self.groups_container.winfo_children():
            return
            
        columns = self.calculate_columns()
        
        # Clear current grid
        for widget in self.groups_container.grid_slaves():
            widget.grid_forget()
        
        # Reconfigure grid columns
        for i in range(columns):
            self.groups_container.grid_columnconfigure(i, weight=1)
        
        # Rearrange existing cards
        cards = self.groups_container.winfo_children()
        for i, card in enumerate(cards):
            row = i // columns
            col = i % columns
            card.grid(
                row=row, 
                column=col, 
                sticky='nsew', 
                padx=8, 
                pady=8
            )
        
        self.current_columns = columns
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def refresh_groups(self):
        """Refresh groups display"""
        self.display_filtered_groups(self.routing_groups)
    
    def create_group_card(self, group):
        """Create a rectangular routing group card widget"""
        card = tk.Frame(
            self.groups_container, 
            bg='#252547', 
            relief='raised', 
            bd=1,
            width=self.min_card_width,
            height=self.min_card_height
        )
        card.pack_propagate(False)
        
        # Main content with padding
        content = tk.Frame(card, bg='#252547')
        content.pack(fill='both', expand=True, padx=12, pady=10)
        content.grid_columnconfigure(0, weight=1)  # Group name column
        content.grid_columnconfigure(1, weight=0)  # Buttons column
        
        # Header row - Group name (left) and buttons (top right)
        header_frame = tk.Frame(content, bg='#252547')
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 8))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Group name (left aligned)
        group_name = group['group_name']
        if len(group_name) > self.group_name_limit:
            group_name = group_name[:self.group_name_limit - 3] + "..."
        
        name_label = tk.Label(
            header_frame,
            text=group_name,
            font=('Arial', 12, 'bold'),
            bg='#252547',
            fg='white',
            anchor='w'
        )
        name_label.grid(row=0, column=0, sticky='w')
        
        # Action buttons (top right)
        button_frame = tk.Frame(header_frame, bg='#252547')
        button_frame.grid(row=0, column=1, sticky='e')
        
        # Store group reference for callbacks
        group_ref = group
        
        edit_btn = tk.Button(
            button_frame,
            text="✏️",
            command=lambda: self.edit_group(self.routing_groups.index(group_ref)),
            bg='#6c63ff',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=8,
            pady=2,
            width=3,
            relief='flat'
        )
        edit_btn.pack(side=tk.LEFT, padx=(2, 0))
        
        delete_btn = tk.Button(
            button_frame,
            text="🗑️",
            command=lambda: self.delete_group(self.routing_groups.index(group_ref)),
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=8,
            pady=2,
            width=3,
            relief='flat'
        )
        delete_btn.pack(side=tk.LEFT, padx=(2, 0))
        
        # Module and confidence row
        info_frame = tk.Frame(content, bg='#252547')
        info_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 6))
        
        # Module badge
        module = group['engine']
        if module == "None":
            module_text = "NO MODULE"
            module_color = '#94a3b8'  # Gray for no module
        else:
            module_text = module.upper()
            module_color = self.get_module_color(module)
            
        module_badge = tk.Label(
            info_frame,
            text=module_text,
            font=('Arial', 8, 'bold'),
            bg=module_color,
            fg='white',
            padx=6,
            pady=2,
            relief='raised',
            bd=1
        )
        module_badge.pack(side=tk.LEFT)
        
        # Confidence indicator
        threshold = group['confidence_threshold']
        confidence_color = self.get_confidence_color(threshold)
        confidence_text = self.get_confidence_text(threshold)
        
        confidence_label = tk.Label(
            info_frame,
            text=f"● {confidence_text} ({threshold:.2f})",
            font=('Arial', 8, 'bold'),
            bg='#252547',
            fg=confidence_color
        )
        confidence_label.pack(side=tk.RIGHT)
        
        # Stats row
        stats_frame = tk.Frame(content, bg='#252547')
        stats_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 6))
        
        # Questions count
        q_count = len(group['questions'])
        questions_text = f"❓ {q_count} question{'s' if q_count != 1 else ''}"
        
        questions_label = tk.Label(
            stats_frame,
            text=questions_text,
            font=('Arial', 9, 'bold'),
            bg='#252547',
            fg='#b0b0d0',
            anchor='w'
        )
        questions_label.pack(side=tk.LEFT)
        
        # Word limit indicator (if enabled)
        if group.get('word_limit_enabled', False):
            max_words = group.get('max_words', 0)
            word_limit_text = f"📏 {max_words}w"
            
            word_limit_label = tk.Label(
                stats_frame,
                text=word_limit_text,
                font=('Arial', 9, 'bold'),
                bg='#252547',
                fg='#ffd166',  # Yellow for word limit
                anchor='e'
            )
            word_limit_label.pack(side=tk.RIGHT)
        
        # Additional info row
        info_frame2 = tk.Frame(content, bg='#252547')
        info_frame2.grid(row=3, column=0, columnspan=2, sticky='ew')
        
        # Calculate longest question for word limit validation hint
        if group.get('word_limit_enabled', False):
            max_question_words = max(len(q.split()) for q in group['questions']) if group['questions'] else 0
            min_words_text = f"Min: {max_question_words}w"
            
            min_words_label = tk.Label(
                info_frame2,
                text=min_words_text,
                font=('Arial', 8),
                bg='#252547',
                fg='#8080a0',
                anchor='w'
            )
            min_words_label.pack(side=tk.LEFT)
        
        # Penalty info if word limit enabled
        if group.get('word_limit_enabled', False):
            penalty = group.get('penalty_per_word', 0.0)
            penalty_text = f"Penalty: -{penalty:.2f}/word"
            
            penalty_label = tk.Label(
                info_frame2,
                text=penalty_text,
                font=('Arial', 8),
                bg='#252547',
                fg='#8080a0',
                anchor='e'
            )
            penalty_label.pack(side=tk.RIGHT)
        
        return card
    
    def get_module_color(self, module):
        """Return color for module badge"""
        # Generate consistent color based on module name
        colors = ['#00d4ff', '#6c63ff', '#ff6b9d', '#00ff88', '#ffd166', '#a78bfa']
        hash_val = sum(ord(c) for c in module)
        return colors[hash_val % len(colors)]
    
    def get_confidence_color(self, threshold):
        """Return color for confidence indicator"""
        if threshold >= 0.95:
            return '#00ff88'  # Green for exact match
        elif threshold >= 0.75:
            return '#00d4ff'  # Blue for high confidence
        elif threshold >= 0.60:
            return '#ffd166'  # Yellow for medium confidence
        else:
            return '#ff6b6b'  # Red for low confidence
    
    def get_confidence_text(self, threshold):
        """Return text description for confidence level"""
        if threshold >= 0.95:
            return "Exact"
        elif threshold >= 0.75:
            return "High"
        elif threshold >= 0.60:
            return "Medium"
        else:
            return "Low"
    
    def new_group(self):
        """Create a new routing group"""
        def on_save(group_data):
            self.routing_groups.append(group_data)
            if self.save_routing_data():
                self.refresh_groups()
        
        RoutingGroupEditor(self.root, on_save=on_save)
    
    def edit_group(self, index):
        """Edit an existing routing group"""
        def on_save(group_data):
            self.routing_groups[index] = group_data
            if self.save_routing_data():
                self.refresh_groups()
        
        RoutingGroupEditor(self.root, self.routing_groups[index], on_save)
    
    def delete_group(self, index):
        """Delete a routing group"""
        group_name = self.routing_groups[index]['group_name']
        
        # Use a less intrusive confirmation
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Delete routing group '{group_name}'?",
            parent=self.root
        )
        
        if confirm:
            self.routing_groups.pop(index)
            if self.save_routing_data():
                self.refresh_groups()


def main():
    """Main function to run the routing trainer"""
    root = tk.Tk()
    app = RoutingTrainerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()