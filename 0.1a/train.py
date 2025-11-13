import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import datetime
import time

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
    
    def create_model(self, name, description="", author="", version="1.0.0"):
        """Create a new model with the given name and description"""
        if not name.strip():
            raise ValueError("Model name cannot be empty")
        
        if name in self.available_models:
            raise ValueError(f"Model '{name}' already exists")
        
        # Create model data structure
        model_data = {
            'name': name,
            'description': description,
            'author': author,
            'version': version,
            'created_at': datetime.datetime.now().isoformat(),
            'qa_groups': []
        }
        
        # Save model file
        model_path = self.get_model_path(name)
        with open(model_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
        
        # Refresh available models
        self.load_available_models()
        
        # Set as current model
        self.current_model = name
        
        return model_data
    
    def load_model(self, name):
        """Load a model by name"""
        if name not in self.available_models:
            raise ValueError(f"Model '{name}' not found")
        
        model_path = self.get_model_path(name)
        with open(model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        self.current_model = name
        
        return model_data
    
    def update_model_info(self, name, description="", author="", version=""):
        """Update model information"""
        if name not in self.available_models:
            raise ValueError(f"Model '{name}' not found")
        
        model_path = self.get_model_path(name)
        with open(model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        # Update fields
        if description is not None:
            model_data['description'] = description
        if author is not None:
            model_data['author'] = author
        if version is not None:
            model_data['version'] = version
        
        model_data['updated_at'] = datetime.datetime.now().isoformat()
        
        # Save updated model
        with open(model_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
        
        return model_data
    
    def save_model(self, name, qa_groups):
        """Save QA groups to a model"""
        model_path = self.get_model_path(name)
        
        # Load existing model data or create new
        if os.path.exists(model_path):
            with open(model_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
        else:
            model_data = {
                'name': name,
                'description': f"Model {name}",
                'author': "",
                'version': "1.0.0",
                'created_at': datetime.datetime.now().isoformat(),
                'qa_groups': []
            }
        
        # Update QA groups
        model_data['qa_groups'] = qa_groups
        model_data['updated_at'] = datetime.datetime.now().isoformat()
        
        # Save model file
        with open(model_path, 'w', encoding='utf-8') as f:
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
        self.creating = False  # Flag to prevent multiple creations
        
        self.window = tk.Toplevel(parent)
        self.window.title("Create New Model")
        self.window.geometry("500x450")
        self.window.minsize(450, 400)
        self.window.configure(bg='#2d2d5a')
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        
        self.setup_ui()
        
        # Bind Enter key only to specific widgets, not the whole window
        self.name_entry.bind('<Return>', lambda e: self.create_model())
        self.author_entry.bind('<Return>', lambda e: self.create_model())
        self.version_entry.bind('<Return>', lambda e: self.create_model())
        
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.window.focus_set()
    
    def center_window(self, parent):
        self.window.update_idletasks()
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
        
        # Author
        author_frame = tk.Frame(main_frame, bg='#2d2d5a')
        author_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            author_frame,
            text="Author:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w')
        
        self.author_var = tk.StringVar()
        self.author_entry = tk.Entry(
            author_frame,
            textvariable=self.author_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.author_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Version
        version_frame = tk.Frame(main_frame, bg='#2d2d5a')
        version_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            version_frame,
            text="Version:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w')
        
        self.version_var = tk.StringVar(value="1.0.0")
        self.version_entry = tk.Entry(
            version_frame,
            textvariable=self.version_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.version_entry.pack(fill=tk.X, pady=(5, 0))
        
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
            height=4,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2d2d5a')
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.create_button = tk.Button(
            button_frame,
            text="💾 Create Model",
            command=self.create_model,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        )
        self.create_button.pack(side=tk.RIGHT)
        
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
        
        self.window.update_idletasks()
    
    def create_model(self):
        # Prevent multiple clicks
        if self.creating:
            return
            
        self.creating = True
        self.create_button.config(state='disabled', text="Creating...")
        self.window.update()
        
        try:
            name = self.name_var.get().strip()
            description = self.desc_text.get('1.0', tk.END).strip()
            author = self.author_var.get().strip()
            version = self.version_var.get().strip()
            
            if not name:
                messagebox.showwarning("Warning", "Please enter a model name.")
                self.name_entry.focus_set()
                return
            
            if not version:
                version = "1.0.0"
            
            if self.on_create:
                # Use after to allow UI to update
                self.window.after(10, lambda: self.execute_create(name, description, author, version))
            else:
                messagebox.showerror("Error", "No create callback defined!")
        finally:
            self.creating = False
            self.create_button.config(state='normal', text="💾 Create Model")
    
    def execute_create(self, name, description, author, version):
        """Execute the create callback and handle the result"""
        try:
            self.on_create(name, description, author, version)
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create model: {str(e)}")

class EditModelDialog:
    def __init__(self, parent, model_data, on_save=None):
        self.on_save = on_save
        self.model_data = model_data
        
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Model Information")
        self.window.geometry("500x450")
        self.window.minsize(450, 400)
        self.window.configure(bg='#2d2d5a')
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        
        self.setup_ui()
        self.load_data()
        
        self.window.bind('<Return>', lambda e: self.save_model())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.window.focus_set()
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window, bg='#2d2d5a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(
            main_frame,
            text="Edit Model Information",
            font=('Arial', 16, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w', pady=(0, 20))
        
        # Model name (read-only)
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
        name_display = tk.Label(
            name_frame,
            textvariable=self.name_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            anchor='w',
            relief='sunken',
            bd=1,
            padx=8,
            pady=6
        )
        name_display.pack(fill=tk.X, pady=(5, 0))
        
        # Author
        author_frame = tk.Frame(main_frame, bg='#2d2d5a')
        author_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            author_frame,
            text="Author:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w')
        
        self.author_var = tk.StringVar()
        tk.Entry(
            author_frame,
            textvariable=self.author_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        ).pack(fill=tk.X, pady=(5, 0))
        
        # Version
        version_frame = tk.Frame(main_frame, bg='#2d2d5a')
        version_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            version_frame,
            text="Version:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w')
        
        self.version_var = tk.StringVar()
        tk.Entry(
            version_frame,
            textvariable=self.version_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        ).pack(fill=tk.X, pady=(5, 0))
        
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
            height=4,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2d2d5a')
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
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
            text="💾 Save Changes",
            command=self.save_model,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
        
        self.window.update_idletasks()
    
    def load_data(self):
        """Load current model data into the form"""
        self.name_var.set(self.model_data.get('name', ''))
        self.author_var.set(self.model_data.get('author', ''))
        self.version_var.set(self.model_data.get('version', '1.0.0'))
        self.desc_text.delete('1.0', tk.END)
        self.desc_text.insert('1.0', self.model_data.get('description', ''))
    
    def save_model(self):
        description = self.desc_text.get('1.0', tk.END).strip()
        author = self.author_var.get().strip()
        version = self.version_var.get().strip()
        
        if not version:
            version = "1.0.0"
        
        try:
            if self.on_save:
                self.on_save(description, author, version)
            self.window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

class BranchNameDialog:
    def __init__(self, parent, current_name="", is_root=False, on_save=None):
        self.on_save = on_save
        self.is_root = is_root
        
        self.window = tk.Toplevel(parent)
        self.window.title("Name Branch" if not is_root else "Name Conversation Start")
        self.window.geometry("450x250")
        self.window.minsize(400, 220)
        self.window.configure(bg='#2d2d5a')
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        
        self.setup_ui(current_name)
        
        self.window.bind('<Return>', lambda e: self.save_name())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.window.focus_set()
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self, current_name):
        main_frame = tk.Frame(self.window, bg='#2d2d5a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_text = "Name Conversation Start" if self.is_root else "Name Branch"
        tk.Label(
            main_frame,
            text=title_text,
            font=('Arial', 14, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w', pady=(0, 15))
        
        # Description
        desc_text = "Give this conversation start a meaningful name for organization:" if self.is_root else "Give this branch a meaningful name:"
        tk.Label(
            main_frame,
            text=desc_text,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='#b0b0d0',
            wraplength=400,
            justify=tk.LEFT
        ).pack(anchor='w', pady=(0, 15))
        
        # Name entry
        name_frame = tk.Frame(main_frame, bg='#2d2d5a')
        name_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            name_frame,
            text="Branch Name:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).pack(anchor='w')
        
        self.name_var = tk.StringVar(value=current_name)
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
        self.name_entry.select_range(0, tk.END)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2d2d5a')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Configure button frame columns
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)
        
        # Spacer
        tk.Label(button_frame, bg='#2d2d5a').grid(row=0, column=0, sticky='ew')
        
        # Cancel button
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        ).grid(row=0, column=1, padx=(10, 5))
        
        # Save button
        tk.Button(
            button_frame,
            text="💾 Save Name",
            command=self.save_name,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        ).grid(row=0, column=2)
    
    def save_name(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a branch name.")
            self.name_entry.focus_set()
            return
        
        if self.on_save:
            self.on_save(name)
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
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        
        self.setup_ui(initial_text)
        
        self.window.bind('<Return>', lambda e: self.save())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self, initial_text):
        main_frame = tk.Frame(self.window, bg='#2d2d5a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
        
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
        
        self.text_widget.focus_set()
        if not initial_text.strip():
            self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
            self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
        
        button_frame = tk.Frame(main_frame, bg='#2d2d5a')
        button_frame.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)
        
        self.status_label = tk.Label(
            button_frame,
            text=f"Editing {self.item_type}...",
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
        ).grid(row=0, column=2, padx=(5, 0))
    
    def save(self):
        text = self.text_widget.get('1.0', tk.END).strip()
        if text and self.on_save:
            self.on_save(text)
            self.window.destroy()
        elif not text:
            messagebox.showwarning("Empty", f"Please enter a {self.item_type}.")
            self.text_widget.focus_set()

class FollowUpEditor:
    def __init__(self, parent, followup_data=None, on_save=None):
        self.on_save = on_save
        self.followup_data = followup_data or []
        self.selected_node = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Follow-up Tree Editor")
        self.window.geometry("900x650")
        self.window.minsize(800, 550)
        self.window.configure(bg='#1a1a2e')
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        
        self.setup_ui()
        if followup_data:
            self.load_data()
        
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=0)
        
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
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(0, weight=1)
        
        # Tree panel
        self.setup_tree_panel(content)
        
        # Editor panel
        self.setup_editor_panel(content)
        
        # Action buttons
        self.setup_action_buttons(main_frame)
    
    def setup_tree_panel(self, parent):
        tree_frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        tree_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 15))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(1, weight=1)
        
        # Tree header with buttons
        tree_header = tk.Frame(tree_frame, bg='#252547')
        tree_header.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        tree_header.columnconfigure(0, weight=1)
        
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
            padx=20,
            pady=6,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            tree_buttons,
            text="+ Branch",
            command=self.add_child_node,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=20,
            pady=6,
            width=10
        ).pack(side=tk.LEFT)
        
        # Tree widget container
        tree_container = tk.Frame(tree_frame, bg='#252547')
        tree_container.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 15))
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Style the treeview
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
        self.tree.bind('<Double-1>', self.on_tree_double_click)
    
    def setup_editor_panel(self, parent):
        editor_frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        editor_frame.grid(row=0, column=1, sticky='nsew')
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=0)
        editor_frame.rowconfigure(1, weight=0)
        editor_frame.rowconfigure(2, weight=1)
        editor_frame.rowconfigure(3, weight=1)
        editor_frame.rowconfigure(4, weight=0)
        
        # Branch name section
        name_frame = tk.Frame(editor_frame, bg='#252547')
        name_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=12)
        name_frame.columnconfigure(0, weight=1)
        
        # Title and edit button
        title_edit_frame = tk.Frame(name_frame, bg='#252547')
        title_edit_frame.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        title_edit_frame.columnconfigure(0, weight=1)
        
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
        q_frame.grid(row=2, column=0, sticky='nsew', padx=15, pady=(0, 10))
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
        a_frame.grid(row=3, column=0, sticky='nsew', padx=15, pady=(0, 10))
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
        update_frame.grid(row=4, column=0, sticky='ew', padx=15, pady=(0, 12))
        
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

class GroupEditor:
    def __init__(self, parent, group_data=None, on_save=None):
        self.on_save = on_save
        self.group_data = group_data or {}
        self.available_topics = ["greeting", "programming", "ai", "gaming", "creative", "thanks", "general"]
        self.followup_data = []
        
        self.window = tk.Toplevel(parent)
        self.window.title("QA Group Editor")
        self.window.geometry("900x650")
        self.window.minsize(700, 500)
        self.window.configure(bg='#1a1a2e')
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        
        self.setup_ui()
        if group_data:
            self.load_data()
        
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.window.focus_set()
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=0)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=0)
        main_frame.rowconfigure(4, weight=0)
        
        self.setup_header(main_frame).grid(row=0, column=0, sticky='ew', pady=(0, 10))
        self.setup_group_info(main_frame).grid(row=1, column=0, sticky='ew', pady=(0, 10))
        self.setup_qa_sections(main_frame).grid(row=2, column=0, sticky='nsew', pady=(0, 10))
        self.setup_settings(main_frame).grid(row=3, column=0, sticky='ew', pady=(0, 10))
        self.setup_action_buttons(main_frame).grid(row=4, column=0, sticky='e')
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.columnconfigure(0, weight=1)
        
        tk.Label(
            header,
            text="QA Group Editor",
            font=('Arial', 16, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        return header
    
    def setup_group_info(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        
        tk.Label(
            frame,
            text="Group Name:",
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.name_var = tk.StringVar(value="New QA Group")
        name_entry = tk.Entry(
            frame,
            textvariable=self.name_var,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        )
        name_entry.grid(row=0, column=1, sticky='ew', pady=(0, 8))
        
        tk.Label(
            frame,
            text="Description:",
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        self.desc_var = tk.StringVar()
        desc_entry = tk.Entry(
            frame,
            textvariable=self.desc_var,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        )
        desc_entry.grid(row=1, column=1, sticky='ew')
        
        return frame
    
    def setup_qa_sections(self, parent):
        container = tk.Frame(parent, bg='#1a1a2e')
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)
        
        questions_frame = self.create_qa_subsection(container, "Questions", 
                                                  self.add_question, self.edit_question, self.delete_question)
        questions_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        self.questions_list = questions_frame.winfo_children()[1].winfo_children()[0]
        
        answers_frame = self.create_qa_subsection(container, "Answers",
                                                self.add_answer, self.edit_answer, self.delete_answer)
        answers_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        self.answers_list = answers_frame.winfo_children()[1].winfo_children()[0]
        
        return container
    
    def create_qa_subsection(self, parent, title, add_cmd, edit_cmd, delete_cmd):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        header = tk.Frame(frame, bg='#252547')
        header.grid(row=0, column=0, sticky='ew', padx=10, pady=8)
        header.columnconfigure(0, weight=1)
        
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
            font=('Arial', 9),
            padx=8
        ).grid(row=0, column=1)
        
        list_container = tk.Frame(frame, bg='#252547')
        list_container.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 8))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        listbox = tk.Listbox(
            list_container,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            selectbackground='#6c63ff',
            activestyle='none'
        )
        listbox.grid(row=0, column=0, sticky='nsew')
        
        scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL)
        scrollbar.grid(row=0, column=1, sticky='ns')
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        actions = tk.Frame(frame, bg='#252547')
        actions.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 8))
        
        tk.Button(
            actions,
            text="Edit",
            command=edit_cmd,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9),
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            actions,
            text="Delete",
            command=delete_cmd,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9),
            width=8
        ).pack(side=tk.LEFT)
        
        return frame
    
    def setup_settings(self, parent):
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        
        topic_priority_frame = tk.Frame(frame, bg='#252547')
        topic_priority_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        tk.Label(
            topic_priority_frame,
            text="Topic:",
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.topic_var = tk.StringVar(value="greeting")
        topic_combo = ttk.Combobox(
            topic_priority_frame,
            textvariable=self.topic_var,
            values=self.available_topics,
            state='readonly',
            width=12
        )
        topic_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(
            topic_priority_frame,
            text="Priority:",
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.priority_var = tk.StringVar(value="medium")
        priority_combo = ttk.Combobox(
            topic_priority_frame,
            textvariable=self.priority_var,
            values=["high", "medium", "low"],
            state='readonly',
            width=10
        )
        priority_combo.pack(side=tk.LEFT)
        
        followup_frame = tk.Frame(frame, bg='#252547')
        followup_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        
        tk.Label(
            followup_frame,
            text="Follow-up Conversation Tree:",
            font=('Arial', 11, 'bold'),
            bg='#252547',
            fg='white'
        ).pack(anchor='w', pady=(0, 8))
        
        followup_info = tk.Frame(followup_frame, bg='#252547')
        followup_info.pack(fill=tk.X, pady=(0, 8))
        
        self.followup_status = tk.Label(
            followup_info,
            text="No follow-up tree defined",
            font=('Arial', 9),
            bg='#252547',
            fg='#b0b0d0'
        )
        self.followup_status.pack(side=tk.LEFT)
        
        tk.Button(
            followup_info,
            text="🌳 Edit Follow-up Tree",
            command=self.edit_followup_tree,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        ).pack(side=tk.RIGHT)
        
        instructions = tk.Label(
            followup_frame,
            text="💡 Create branching conversations that continue after the main answer",
            font=('Arial', 9),
            bg='#252547',
            fg='#00d4ff',
            justify=tk.LEFT
        )
        instructions.pack(anchor='w')
        
        return frame
    
    def setup_action_buttons(self, parent):
        frame = tk.Frame(parent, bg='#1a1a2e')
        
        tk.Button(
            frame,
            text="💾 Save Group",
            command=self.save_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10
        ).pack(side=tk.RIGHT, padx=(15, 0))
        
        tk.Button(
            frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=25,
            pady=10
        ).pack(side=tk.RIGHT)
        
        return frame
    
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
    
    def edit_followup_tree(self):
        def on_save(followup_data):
            self.followup_data = followup_data
            total_nodes = self.count_nodes(followup_data)
            if total_nodes > 0:
                self.followup_status.config(text=f"Follow-up tree: {total_nodes} conversation nodes")
            else:
                self.followup_status.config(text="No follow-up tree defined")
        
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
        
        self.followup_data = self.group_data.get('follow_ups', [])
        total_nodes = self.count_nodes(self.followup_data)
        if total_nodes > 0:
            self.followup_status.config(text=f"Follow-up tree: {total_nodes} conversation nodes")
    
    def save_group(self):
        if self.questions_list.size() == 0:
            messagebox.showerror("Error", "At least one question is required.")
            return
        
        if self.answers_list.size() == 0:
            messagebox.showerror("Error", "At least one answer is required.")
            return
        
        group_data = {
            'group_name': self.name_var.get(),
            'group_description': self.desc_var.get(),
            'questions': list(self.questions_list.get(0, tk.END)),
            'answers': list(self.answers_list.get(0, tk.END)),
            'topic': self.topic_var.get(),
            'priority': self.priority_var.get(),
            'follow_ups': self.followup_data
        }
        
        if self.on_save:
            self.on_save(group_data)
        
        self.window.destroy()

class TrainingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI Training")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg='#1a1a2e')
        
        self.current_model = None
        self.qa_groups = []
        self.scroll_frame = None
        self.model_changing = False  # Flag to prevent recursion
        
        self.model_manager = ModelManager(root)
        
        self.configure_ttk_styles()
        self.setup_gui()
        
        if not self.model_manager.available_models:
            self.root.after(100, self.prompt_create_first_model)
        else:
            # Load the first model without triggering save dialog
            self.model_changing = True
            self.load_model(self.model_manager.available_models[0])
            self.model_changing = False
    
    def configure_ttk_styles(self):
        style = ttk.Style()
        
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
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
        
        style.configure('Dark.Vertical.TScrollbar',
            background='#252547',
            troughcolor='#1a1a2e',
            borderwidth=0,
            relief='flat'
        )
        
        style.map('Dark.Vertical.TScrollbar',
            background=[('active', '#6c63ff')]
        )
    
    def prompt_create_first_model(self):
        messagebox.showinfo("Welcome", "No AI models found. Let's create your first model!")
        self.create_new_model()
    
    def create_new_model(self):
        def on_create(name, description, author, version):
            try:
                # Set flag to prevent save dialog during initial model creation
                self.model_changing = True
                self.model_manager.create_model(name, description, author, version)
                self.load_model(name)
                self.update_model_dropdown()
                self.model_changing = False
                messagebox.showinfo("Success", f"Model '{name}' created successfully!")
            except Exception as e:
                self.model_changing = False
                messagebox.showerror("Error", f"Failed to create model: {str(e)}")
        
        CreateModelDialog(self.root, on_create)
    
    def edit_current_model(self):
        if not self.current_model:
            messagebox.showwarning("Warning", "No model selected.")
            return
        
        try:
            model_data = self.model_manager.load_model(self.current_model)
            
            def on_save(description, author, version):
                try:
                    updated_model = self.model_manager.update_model_info(
                        self.current_model, description, author, version
                    )
                    self.update_model_dropdown()
                    messagebox.showinfo("Success", "Model information updated successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update model: {str(e)}")
            
            EditModelDialog(self.root, model_data, on_save)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
    
    def load_model(self, model_name):
        """Load a model without triggering the save dialog"""
        try:
            model_data = self.model_manager.load_model(model_name)
            self.qa_groups = model_data.get('qa_groups', [])
            self.current_model = model_name
            if hasattr(self, 'scroll_frame'):
                self.refresh_groups()
            self.update_model_dropdown()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
    
    def save_current_model(self):
        if not self.current_model:
            messagebox.showwarning("Warning", "No model selected. Please create or load a model first.")
            return False
        
        try:
            self.model_manager.save_model(self.current_model, self.qa_groups)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save model: {str(e)}")
            return False
    
    def on_model_switch_request(self, model_name):
        """Handle model switching with save confirmation"""
        if self.model_changing:
            return
            
        if model_name and model_name != self.current_model:
            # Check if we have unsaved changes
            has_unsaved_changes = bool(self.current_model and self.qa_groups)
            
            if has_unsaved_changes:
                response = messagebox.askyesnocancel(
                    "Save Changes", 
                    f"Save changes to current model '{self.current_model}' before switching?"
                )
                
                if response is None:  # Cancel
                    # Reset combobox to current model
                    self.model_combobox.set(self.current_model)
                    return
                elif response:  # Yes
                    if not self.save_current_model():
                        # Save failed, don't switch
                        self.model_combobox.set(self.current_model)
                        return
            
            # Proceed with model switch
            self.model_changing = True
            self.load_model(model_name)
            self.model_changing = False
    
    def update_model_dropdown(self):
        if hasattr(self, 'model_combobox'):
            current_selection = self.model_combobox.get()
            self.model_combobox['values'] = self.model_manager.available_models
            if self.current_model:
                self.model_combobox.set(self.current_model)
            elif self.model_manager.available_models:
                self.model_combobox.set(self.model_manager.available_models[0])
    
    def setup_gui(self):
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.setup_header(main_frame)
        self.setup_toolbar(main_frame)
        self.setup_groups_list(main_frame)
    
    def setup_header(self, parent):
        header = tk.Frame(parent, bg='#1a1a2e')
        header.pack(fill=tk.X, pady=(0, 15))
        
        left_frame = tk.Frame(header, bg='#1a1a2e')
        left_frame.pack(side=tk.LEFT)
        
        tk.Label(
            left_frame,
            text="Edgar AI Training",
            font=('Arial', 20, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).pack(side=tk.LEFT)
        
        right_frame = tk.Frame(header, bg='#1a1a2e')
        right_frame.pack(side=tk.RIGHT)
        
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
            width=15,
            style='Dark.TCombobox'
        )
        self.model_combobox.pack(side=tk.LEFT, padx=(0, 10))
        if self.current_model:
            self.model_combobox.set(self.current_model)
        elif self.model_manager.available_models:
            self.model_combobox.set(self.model_manager.available_models[0])
            
        self.model_combobox.bind('<<ComboboxSelected>>', 
                               lambda e: self.on_model_switch_request(self.model_combobox.get()))
        
        tk.Button(
            model_frame,
            text="✏️ Edit",
            command=self.edit_current_model,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9),
            padx=10
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            model_frame,
            text="+ New Model",
            command=self.create_new_model,
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9),
            padx=10
        ).pack(side=tk.LEFT)
        
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
        
        search_container = tk.Frame(toolbar, bg='#1a1a2e')
        search_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
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
                command=self.on_search
            )
            rb.pack(side=tk.LEFT, padx=(0, 8))
        
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
        
        self.canvas = tk.Canvas(container, bg='#1a1a2e', highlightthickness=0)
        
        scrollbar = ttk.Scrollbar(
            container, 
            orient=tk.VERTICAL, 
            command=self.canvas.yview,
            style='Dark.Vertical.TScrollbar'
        )
        
        self.scroll_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.scroll_frame.bind("<MouseWheel>", self.on_mousewheel)
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_search(self, *args):
        self.refresh_groups()
    
    def refresh_groups(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
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
            else:
                match = search_term in group.get('group_description', '').lower()
            
            if match:
                filtered_groups.append(group)
        
        for i, group in enumerate(filtered_groups):
            self.create_group_card(group, i)
        
        total_questions = sum(len(g['questions']) for g in self.qa_groups)
        total_answers = sum(len(g['answers']) for g in self.qa_groups)
        
        self.stats_vars["Groups"].set(str(len(self.qa_groups)))
        self.stats_vars["Questions"].set(str(total_questions))
        self.stats_vars["Answers"].set(str(total_answers))
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def create_group_card(self, group, index):
        card = tk.Frame(self.scroll_frame, bg='#252547', relief='raised', bd=1)
        card.pack(fill=tk.X, pady=4, padx=2)
        
        content = tk.Frame(card, bg='#252547')
        content.pack(fill=tk.X, padx=12, pady=10)
        
        header = tk.Frame(content, bg='#252547')
        header.pack(fill=tk.X, pady=(0, 6))
        
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
            count += 1
            count += self.count_followup_nodes(item.get('children', []))
        return count
    
    def new_group(self):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        def on_save(group_data):
            self.qa_groups.append(group_data)
            if self.save_current_model():
                self.refresh_groups()
        
        GroupEditor(self.root, on_save=on_save)
    
    def edit_group(self, index):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        def on_save(group_data):
            self.qa_groups[index] = group_data
            if self.save_current_model():
                self.refresh_groups()
        
        GroupEditor(self.root, self.qa_groups[index], on_save)
    
    def delete_group(self, index):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        if messagebox.askyesno("Confirm", "Delete this group?"):
            self.qa_groups.pop(index)
            if self.save_current_model():
                self.refresh_groups()
    
    def import_json(self):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both array format and object format
                if isinstance(data, list):
                    imported_groups = data
                else:
                    imported_groups = [data]
                
                for i, qa in enumerate(imported_groups):
                    self.qa_groups.append({
                        'group_name': qa.get('group_name', f"Imported {i+1}"),
                        'group_description': qa.get('group_description', "Imported from JSON"),
                        'questions': qa.get('questions', []),
                        'answers': qa.get('answers', []),
                        'topic': qa.get('topic', 'general'),
                        'priority': qa.get('priority', 'medium'),
                        'follow_ups': qa.get('follow_ups', [])
                    })
                
                if self.save_current_model():
                    self.refresh_groups()
                    messagebox.showinfo("Success", f"Imported {len(imported_groups)} groups")
                
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {str(e)}")
    
    def export_json(self):
        if not self.qa_groups:
            messagebox.showwarning("Warning", "No data to export.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            try:
                export_data = []
                for group in self.qa_groups:
                    export_data.append({
                        'group_name': group['group_name'],
                        'group_description': group.get('group_description', ''),
                        'questions': group['questions'],
                        'answers': group['answers'],
                        'topic': group['topic'],
                        'priority': group['priority'],
                        'follow_ups': group.get('follow_ups', [])
                    })
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", "Data exported successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

def main():
    root = tk.Tk()
    app = TrainingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
