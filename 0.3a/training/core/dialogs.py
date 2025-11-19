import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

class BaseDialog:
    """Base class for dialogs with common functionality"""
    def __init__(self, parent, title, width=500, height=400):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        self.window.configure(bg='#2d2d5a')
        self.window.minsize(400, 300)
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

class CreateModelDialog(BaseDialog):
    def __init__(self, parent, on_create=None):
        super().__init__(parent, "Create New Model", 500, 450)
        self.on_create = on_create
        self.creating = False
        self.unsaved_changes = False
        self.setup_ui()
        self.name_entry.focus_set()
    
    def setup_ui(self):
        # Configure grid weights
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Title
        tk.Label(
            self.window,
            text="Create New AI Model",
            font=('Arial', 16, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))
        
        # Main content frame
        content_frame = tk.Frame(self.window, bg='#2d2d5a')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Model name
        tk.Label(
            content_frame,
            text="Model Name:",
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
        self.name_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        self.name_entry.bind('<Return>', lambda e: self.create_model())
        
        # Author
        tk.Label(
            content_frame,
            text="Author:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        self.author_var = tk.StringVar()
        self.author_entry = tk.Entry(
            content_frame,
            textvariable=self.author_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.author_entry.grid(row=1, column=1, sticky='ew', pady=(0, 15))
        self.author_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        self.author_entry.bind('<Return>', lambda e: self.create_model())
        
        # Version
        tk.Label(
            content_frame,
            text="Version:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=(0, 8))
        
        self.version_var = tk.StringVar(value="1.0.0")
        self.version_entry = tk.Entry(
            content_frame,
            textvariable=self.version_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.version_entry.grid(row=2, column=1, sticky='ew', pady=(0, 15))
        self.version_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        self.version_entry.bind('<Return>', lambda e: self.create_model())
        
        # Description
        tk.Label(
            content_frame,
            text="Description:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=3, column=0, sticky='nw', pady=(0, 8))
        
        self.desc_text = scrolledtext.ScrolledText(
            content_frame,
            height=4,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.desc_text.grid(row=3, column=1, sticky='nsew', pady=(0, 15))
        self.desc_text.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        
        # Bind Shift+Enter for new line in description
        self.desc_text.bind('<Shift-Return>', lambda e: "break")  # Allow default behavior
        self.desc_text.bind('<Return>', self.on_description_enter)
        
        # Buttons frame
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=2, column=0, sticky='e', padx=20, pady=(0, 20))
        
        # Main create button that changes state
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
            command=self.confirm_cancel,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Configure content frame row weights
        content_frame.grid_rowconfigure(3, weight=1)
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        if not self.unsaved_changes:
            self.unsaved_changes = True
            # Update create button to indicate unsaved changes
            self.create_button.config(text="💾 Create Model *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag"""
        self.unsaved_changes = False
        # Reset create button
        self.create_button.config(text="💾 Create Model", bg='#00ff88')
    
    def confirm_cancel(self):
        """Confirm cancellation if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?\n\n"
                "Yes - Discard Changes\n"
                "No - Continue Editing\n"
                "Cancel - Return to Dialog"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Discard Changes
                self.window.destroy()
        else:
            self.window.destroy()
    
    def on_description_enter(self, event):
        """Handle Enter key in description - submit on Enter, new line on Shift+Enter"""
        if event.state & 0x1:  # Shift key is pressed
            return  # Allow default behavior (new line)
        else:
            self.create_model()
            return "break"  # Prevent default behavior
    
    def create_model(self):
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
                self.window.after(10, lambda: self.execute_create(name, description, author, version))
            else:
                messagebox.showerror("Error", "No create callback defined!")
        finally:
            self.creating = False
            self.create_button.config(state='normal', text="💾 Create Model")
    
    def execute_create(self, name, description, author, version):
        try:
            self.on_create(name, description, author, version)
            self.clear_unsaved_changes()
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create model: {str(e)}")

class EditModelDialog(BaseDialog):
    def __init__(self, parent, model_data, on_save=None):
        super().__init__(parent, "Edit Model Information", 500, 450)
        self.on_save = on_save
        self.model_data = model_data
        self.unsaved_changes = False
        self.original_data = {}
        self.setup_ui()
        self.load_data()
        self.save_original_state()
    
    def setup_ui(self):
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Title
        tk.Label(
            self.window,
            text="Edit Model Information",
            font=('Arial', 16, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))
        
        # Main content frame
        content_frame = tk.Frame(self.window, bg='#2d2d5a')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Model name (read-only)
        tk.Label(
            content_frame,
            text="Model Name:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.name_var = tk.StringVar()
        name_display = tk.Label(
            content_frame,
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
        name_display.grid(row=0, column=1, sticky='ew', pady=(0, 15))
        
        # Author
        tk.Label(
            content_frame,
            text="Author:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        self.author_var = tk.StringVar()
        self.author_entry = tk.Entry(
            content_frame,
            textvariable=self.author_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.author_entry.grid(row=1, column=1, sticky='ew', pady=(0, 15))
        self.author_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        
        # Version
        tk.Label(
            content_frame,
            text="Version:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=(0, 8))
        
        self.version_var = tk.StringVar()
        self.version_entry = tk.Entry(
            content_frame,
            textvariable=self.version_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.version_entry.grid(row=2, column=1, sticky='ew', pady=(0, 15))
        self.version_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        
        # Description
        tk.Label(
            content_frame,
            text="Description:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=3, column=0, sticky='nw', pady=(0, 8))
        
        self.desc_text = scrolledtext.ScrolledText(
            content_frame,
            height=4,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.desc_text.grid(row=3, column=1, sticky='nsew', pady=(0, 15))
        self.desc_text.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        
        # Bind Shift+Enter for new line in description
        self.desc_text.bind('<Shift-Return>', lambda e: "break")
        self.desc_text.bind('<Return>', self.on_description_enter)
        
        # Buttons frame
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=2, column=0, sticky='e', padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.confirm_cancel,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Main save button that changes state
        self.save_button = tk.Button(
            button_frame,
            text="💾 Save Changes",
            command=self.save_model,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        )
        self.save_button.pack(side=tk.RIGHT)
        
        content_frame.grid_rowconfigure(3, weight=1)
    
    def save_original_state(self):
        """Save the original state for comparison"""
        self.original_data = {
            'author': self.author_var.get(),
            'version': self.version_var.get(),
            'description': self.desc_text.get('1.0', tk.END).strip()
        }
    
    def has_changes(self):
        """Check if there are any changes from the original state"""
        current_data = {
            'author': self.author_var.get(),
            'version': self.version_var.get(),
            'description': self.desc_text.get('1.0', tk.END).strip()
        }
        
        return current_data != self.original_data
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        if not self.unsaved_changes and self.has_changes():
            self.unsaved_changes = True
            # Update save button to indicate unsaved changes
            self.save_button.config(text="💾 Save Changes *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag"""
        self.unsaved_changes = False
        self.save_original_state()
        # Reset save button
        self.save_button.config(text="💾 Save Changes", bg='#00ff88')
    
    def confirm_cancel(self):
        """Confirm cancellation if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?\n\n"
                "Yes - Discard Changes\n"
                "No - Continue Editing\n"
                "Cancel - Return to Dialog"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Discard Changes
                self.window.destroy()
        else:
            self.window.destroy()
    
    def on_description_enter(self, event):
        """Handle Enter key in description - submit on Enter, new line on Shift+Enter"""
        if event.state & 0x1:  # Shift key is pressed
            return  # Allow default behavior (new line)
        else:
            self.save_model()
            return "break"  # Prevent default behavior
    
    def load_data(self):
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
            self.clear_unsaved_changes()
            self.window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

class BranchNameDialog(BaseDialog):
    def __init__(self, parent, current_name="", is_root=False, on_save=None):
        super().__init__(parent, "Name Branch" if not is_root else "Name Conversation Start", 450, 250)
        self.on_save = on_save
        self.is_root = is_root
        self.unsaved_changes = False
        self.original_name = current_name
        self.setup_ui(current_name)
        self.name_entry.focus_set()
        self.name_entry.select_range(0, tk.END)
    
    def setup_ui(self, current_name):
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Title
        title_text = "Name Conversation Start" if self.is_root else "Name Branch"
        tk.Label(
            self.window,
            text=title_text,
            font=('Arial', 14, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))
        
        # Content frame
        content_frame = tk.Frame(self.window, bg='#2d2d5a')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Description
        desc_text = "Give this conversation start a meaningful name for organization:" if self.is_root else "Give this branch a meaningful name:"
        tk.Label(
            content_frame,
            text=desc_text,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='#b0b0d0',
            wraplength=400,
            justify=tk.LEFT
        ).grid(row=0, column=0, sticky='w', pady=(0, 15))
        
        # Name entry
        tk.Label(
            content_frame,
            text="Branch Name:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        self.name_var = tk.StringVar(value=current_name)
        self.name_entry = tk.Entry(
            content_frame,
            textvariable=self.name_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.name_entry.grid(row=2, column=0, sticky='ew', pady=(0, 20))
        self.name_entry.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        self.name_entry.bind('<Return>', lambda e: self.save_name())
        
        # Buttons
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=2, column=0, sticky='e', padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.confirm_cancel,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Main save button that changes state
        self.save_button = tk.Button(
            button_frame,
            text="💾 Save Name",
            command=self.save_name,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        )
        self.save_button.pack(side=tk.RIGHT)
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        current_name = self.name_var.get().strip()
        if not self.unsaved_changes and current_name != self.original_name:
            self.unsaved_changes = True
            # Update save button to indicate unsaved changes
            self.save_button.config(text="💾 Save Name *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag"""
        self.unsaved_changes = False
        # Reset save button
        self.save_button.config(text="💾 Save Name", bg='#00ff88')
    
    def confirm_cancel(self):
        """Confirm cancellation if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?\n\n"
                "Yes - Discard Changes\n"
                "No - Continue Editing\n"
                "Cancel - Return to Dialog"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Discard Changes
                self.window.destroy()
        else:
            self.window.destroy()
    
    def save_name(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a branch name.")
            self.name_entry.focus_set()
            return
        
        if self.on_save:
            self.on_save(name)
        self.clear_unsaved_changes()
        self.window.destroy()

class QuestionAnswerEditor(BaseDialog):
    def __init__(self, parent, item_type="question", initial_text="", on_save=None):
        super().__init__(parent, f"{item_type.title()} Editor", 500, 400)
        self.on_save = on_save
        self.item_type = item_type
        self.unsaved_changes = False
        self.original_text = initial_text
        self.setup_ui(initial_text)
        self.text_widget.focus_set()
        
        # Set cursor to end instead of selecting all text
        self.text_widget.mark_set(tk.INSERT, tk.END)
        self.text_widget.see(tk.INSERT)
    
    def setup_ui(self, initial_text):
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
        self.text_widget.bind('<KeyRelease>', lambda e: self.mark_unsaved_changes())
        
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
            command=self.confirm_cancel,
            bg='#ff4d7d', 
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=5,
            width=8
        ).grid(row=0, column=1, padx=(10, 5))
        
        # Main save button that changes state
        self.save_button = tk.Button(
            button_frame, 
            text="💾 Save", 
            command=self.save,
            bg='#00ff88', 
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=5,
            width=8
        )
        self.save_button.grid(row=0, column=2)
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        current_text = self.text_widget.get('1.0', tk.END).strip()
        if not self.unsaved_changes and current_text != self.original_text:
            self.unsaved_changes = True
            # Update save button to indicate unsaved changes
            self.save_button.config(text="💾 Save *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag"""
        self.unsaved_changes = False
        # Reset save button
        self.save_button.config(text="💾 Save", bg='#00ff88')
    
    def confirm_cancel(self):
        """Confirm cancellation if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?\n\n"
                "Yes - Discard Changes\n"
                "No - Continue Editing\n"
                "Cancel - Return to Editor"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Discard Changes
                self.window.destroy()
        else:
            self.window.destroy()
    
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
            self.clear_unsaved_changes()
            self.window.destroy()
        elif not text:
            messagebox.showwarning("Empty", f"Please enter a {self.item_type}.")
            self.text_widget.focus_set()
