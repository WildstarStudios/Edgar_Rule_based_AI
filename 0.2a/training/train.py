import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
from core.train_engine import TrainingEngine, ModelManager

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
        
        # Bind Shift+Enter for new line in description
        self.desc_text.bind('<Shift-Return>', lambda e: "break")  # Allow default behavior
        self.desc_text.bind('<Return>', self.on_description_enter)
        
        # Buttons frame
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=2, column=0, sticky='e', padx=20, pady=(0, 20))
        
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
        
        # Configure content frame row weights
        content_frame.grid_rowconfigure(3, weight=1)
    
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
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create model: {str(e)}")

class EditModelDialog(BaseDialog):
    def __init__(self, parent, model_data, on_save=None):
        super().__init__(parent, "Edit Model Information", 500, 450)
        self.on_save = on_save
        self.model_data = model_data
        self.setup_ui()
        self.load_data()
    
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
        tk.Entry(
            content_frame,
            textvariable=self.author_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        ).grid(row=1, column=1, sticky='ew', pady=(0, 15))
        
        # Version
        tk.Label(
            content_frame,
            text="Version:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=(0, 8))
        
        self.version_var = tk.StringVar()
        tk.Entry(
            content_frame,
            textvariable=self.version_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        ).grid(row=2, column=1, sticky='ew', pady=(0, 15))
        
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
        
        # Bind Shift+Enter for new line in description
        self.desc_text.bind('<Shift-Return>', lambda e: "break")
        self.desc_text.bind('<Return>', self.on_description_enter)
        
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
        
        content_frame.grid_rowconfigure(3, weight=1)
    
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
            self.window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

class BranchNameDialog(BaseDialog):
    def __init__(self, parent, current_name="", is_root=False, on_save=None):
        super().__init__(parent, "Name Branch" if not is_root else "Name Conversation Start", 450, 250)
        self.on_save = on_save
        self.is_root = is_root
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
        self.name_entry.bind('<Return>', lambda e: self.save_name())
        
        # Buttons
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=2, column=0, sticky='e', padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="💾 Save Name",
            command=self.save_name,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=6
        ).pack(side=tk.RIGHT)
    
    def save_name(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a branch name.")
            self.name_entry.focus_set()
            return
        
        if self.on_save:
            self.on_save(name)
        self.window.destroy()

class QuestionAnswerEditor(BaseDialog):
    def __init__(self, parent, item_type="question", initial_text="", on_save=None):
        super().__init__(parent, f"{item_type.title()} Editor", 500, 400)
        self.on_save = on_save
        self.item_type = item_type
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

class FollowUpEditor(BaseDialog):
    def __init__(self, parent, followup_data=None, on_save=None):
        super().__init__(parent, "Follow-up Tree Editor", 900, 650)
        self.on_save = on_save
        self.followup_data = followup_data or []
        self.selected_node = None
        self.setup_ui()
        
        if followup_data:
            self.load_data()
    
    def setup_ui(self):
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
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
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)
        
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
        
        # Use custom scrollbar
        tree_scroll = tk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview,
                                  bg='#2d2d5a', troughcolor='#1a1a2e', activebackground='#6c63ff')
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

class GroupEditor(BaseDialog):
    def __init__(self, parent, group_data=None, on_save=None):
        super().__init__(parent, "QA Group Editor", 900, 650)
        self.on_save = on_save
        self.group_data = group_data or {}
        self.available_topics = ["greeting", "programming", "ai", "gaming", "creative", "thanks", "general"]
        self.followup_data = []
        self.setup_ui()
        
        if group_data:
            self.load_data()
    
    def setup_ui(self):
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        self.setup_header(main_frame).grid(row=0, column=0, sticky='ew', pady=(0, 10))
        self.setup_group_info(main_frame).grid(row=1, column=0, sticky='ew', pady=(0, 10))
        self.setup_qa_sections(main_frame).grid(row=2, column=0, sticky='nsew', pady=(0, 10))
        self.setup_settings(main_frame).grid(row=3, column=0, sticky='ew', pady=(0, 10))
        self.setup_action_buttons(main_frame).grid(row=4, column=0, sticky='e')
    
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
        frame = tk.Frame(parent, bg='#252547', relief='raised', bd=1, padx=10, pady=10)
        frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            frame,
            text="Group Name:",
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.name_var = tk.StringVar(value="New QA Group")
        self.name_entry = tk.Entry(
            frame,
            textvariable=self.name_var,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        )
        self.name_entry.grid(row=0, column=1, sticky='ew', pady=(0, 8))
        
        # Fix: Set cursor to end instead of selecting all text
        self.name_entry.focus_set()
        self.name_entry.icursor(tk.END)
        
        self.name_entry.bind('<Return>', lambda e: self.save_group())
        
        tk.Label(
            frame,
            text="Description:",
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        self.desc_var = tk.StringVar()
        self.desc_entry = tk.Entry(
            frame,
            textvariable=self.desc_var,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='white',
            insertbackground='white'
        )
        self.desc_entry.grid(row=1, column=1, sticky='ew')
        self.desc_entry.bind('<Return>', lambda e: self.save_group())
        
        return frame
    
    def setup_qa_sections(self, parent):
        container = tk.Frame(parent, bg='#1a1a2e')
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
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
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        header = tk.Frame(frame, bg='#252547')
        header.grid(row=0, column=0, sticky='ew', padx=10, pady=8)
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
            font=('Arial', 9),
            padx=8
        ).grid(row=0, column=1)
        
        list_container = tk.Frame(frame, bg='#252547')
        list_container.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 8))
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
        
        # Use custom scrollbar
        scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL, command=listbox.yview,
                                bg='#2d2d5a', troughcolor='#1a1a2e', activebackground='#6c63ff')
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
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
        frame.grid_columnconfigure(1, weight=1)
        
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
        # Remove requirement for questions and answers
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
        self.root.geometry("1200x800")
        self.root.minsize(350, 300)
        self.root.configure(bg='#1a1a2e')
        
        # Initialize backend engine
        self.engine = TrainingEngine()
        self.engine.initialize_model_manager(root)
        
        self.scroll_frame = None
        self.model_changing = False
        self.group_cards = []
        
        # Responsive layout variables
        self.current_columns = 4
        self.min_card_width = 280
        self.card_padding = 16  # 8px on each side
        
        # Search optimization
        self.search_cache = {}
        self.last_search_term = ""
        self.last_search_mode = ""
        
        self.configure_ttk_styles()
        self.setup_gui()
        
        if not self.engine.available_models:
            self.root.after(100, self.prompt_create_first_model)
        else:
            self.model_changing = True
            self.load_model(self.engine.available_models[0])
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
    
    def prompt_create_first_model(self):
        messagebox.showinfo("Welcome", "No AI models found. Let's create your first model!")
        self.create_new_model()
    
    def create_new_model(self):
        def on_create(name, description, author, version):
            try:
                self.model_changing = True
                self.engine.create_model(name, description, author, version)
                self.load_model(name)
                self.update_model_dropdown()
                self.model_changing = False
                messagebox.showinfo("Success", f"Model '{name}' created successfully!")
            except Exception as e:
                self.model_changing = False
                messagebox.showerror("Error", f"Failed to create model: {str(e)}")
        
        CreateModelDialog(self.root, on_create)
    
    def edit_current_model(self):
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "No model selected.")
            return
        
        try:
            model_data = self.engine.model_manager.load_model(self.engine.current_model)
            
            def on_save(description, author, version):
                try:
                    self.engine.update_model_info(description, author, version)
                    self.update_model_dropdown()
                    messagebox.showinfo("Success", "Model information updated successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update model: {str(e)}")
            
            EditModelDialog(self.root, model_data, on_save)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
    
    def load_model(self, model_name):
        try:
            self.engine.load_model(model_name)
            if hasattr(self, 'scroll_frame'):
                self.refresh_groups()
            self.update_model_dropdown()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
    
    def save_current_model(self):
        try:
            self.engine.save_current_model()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save model: {str(e)}")
            return False
    
    def on_model_switch_request(self, model_name):
        if self.model_changing:
            return
            
        if model_name and model_name != self.engine.current_model:
            has_unsaved_changes = bool(self.engine.current_model and self.engine.qa_groups)
            
            if has_unsaved_changes:
                response = messagebox.askyesnocancel(
                    "Save Changes", 
                    f"Save changes to current model '{self.engine.current_model}' before switching?"
                )
                
                if response is None:
                    self.model_combobox.set(self.engine.current_model)
                    return
                elif response:
                    if not self.save_current_model():
                        self.model_combobox.set(self.engine.current_model)
                        return
            
            self.model_changing = True
            self.load_model(model_name)
            self.model_changing = False
    
    def update_model_dropdown(self):
        if hasattr(self, 'model_combobox'):
            self.model_combobox['values'] = self.engine.available_models
            if self.engine.current_model:
                self.model_combobox.set(self.engine.current_model)
            elif self.engine.available_models:
                self.model_combobox.set(self.engine.available_models[0])
    
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
        header.grid_columnconfigure(1, weight=1)
        
        # Title
        tk.Label(
            header,
            text="Edgar AI Training",
            font=('Arial', 20, 'bold'),
            bg='#1a1a2e',
            fg='white'
        ).grid(row=0, column=0, sticky='w')
        
        # Model selection area
        model_frame = tk.Frame(header, bg='#1a1a2e')
        model_frame.grid(row=0, column=1, sticky='e')
        
        tk.Label(
            model_frame,
            text="Model:",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_combobox = ttk.Combobox(
            model_frame,
            values=self.engine.available_models,
            state="readonly",
            width=15,
            style='Dark.TCombobox'
        )
        self.model_combobox.pack(side=tk.LEFT, padx=(0, 10))
        if self.engine.current_model:
            self.model_combobox.set(self.engine.current_model)
        elif self.engine.available_models:
            self.model_combobox.set(self.engine.available_models[0])
            
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
        
        # Stats area
        stats_frame = tk.Frame(header, bg='#1a1a2e')
        stats_frame.grid(row=1, column=0, columnspan=2, sticky='w', pady=(10, 0))
        
        self.stats_vars = {}
        stats = [("Groups", "0"), ("Questions", "0"), ("Answers", "0")]
        
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
        
        # Search filter dropdown
        tk.Label(
            search_frame,
            text="Filter:",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_mode = tk.StringVar(value="all")
        search_filter = ttk.Combobox(
            search_frame,
            textvariable=self.search_mode,
            values=["All", "Name", "Description", "Questions", "Answers"],
            state="readonly",
            width=12,
            style='Dark.TCombobox'
        )
        search_filter.pack(side=tk.LEFT, padx=(0, 15))
        
        # Bind search events for real-time filtering
        self.search_var.trace('w', self.on_search)
        self.search_mode.trace('w', self.on_search)
        
        # Action buttons
        actions = tk.Frame(toolbar, bg='#1a1a2e')
        actions.grid(row=0, column=1, sticky='e')
        
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
    
    def setup_groups_grid(self, parent):
        """Setup responsive groups display with dynamic column layout"""
        container = tk.Frame(parent, bg='#1a1a2e')
        container.grid(row=2, column=0, sticky='nsew')
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(container, bg='#1a1a2e', highlightthickness=0)
        
        # Use custom scrollbar with theme colors
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
        
        # Bind to update scroll region when window is fully loaded
        self.root.after(100, self.update_scroll_region)
    
    def update_scroll_region(self):
        """Update scroll region after window is fully loaded"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_resize(self, event):
        """Handle canvas resize to adjust grid columns"""
        if hasattr(self, 'groups_container') and self.groups_container.winfo_children():
            self.refresh_groups_layout()
        # Update scroll region after resize
        self.root.after(50, self.update_scroll_region)
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_search(self, *args):
        """Optimized real-time search with caching"""
        search_term = self.search_var.get().lower()
        search_mode = self.search_mode.get().lower()
        
        # Use cache if search hasn't changed
        cache_key = f"{search_term}|{search_mode}"
        if cache_key in self.search_cache:
            filtered_groups = self.search_cache[cache_key]
        else:
            # Perform search
            if search_mode == "all":
                filtered_groups = self.engine.search_qa_groups(search_term, "both")
            else:
                filtered_groups = self.engine.search_qa_groups(search_term, search_mode)
            
            # Cache results
            self.search_cache[cache_key] = filtered_groups
            # Limit cache size
            if len(self.search_cache) > 50:
                self.search_cache.pop(next(iter(self.search_cache)))
        
        self.display_filtered_groups(filtered_groups)
    
    def display_filtered_groups(self, filtered_groups):
        """Display filtered groups without full refresh"""
        # Clear existing cards
        for card in self.group_cards:
            card.destroy()
        self.group_cards = []
        
        # Calculate responsive columns
        columns = self.calculate_columns()
        
        # Clear and reconfigure grid
        for widget in self.groups_container.grid_slaves():
            widget.grid_forget()
        
        for i in range(columns):
            self.groups_container.grid_columnconfigure(i, weight=1)
        
        # Create group cards for filtered groups
        for i, group in enumerate(filtered_groups):
            card = self.create_group_card(group)
            self.group_cards.append(card)
            
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
        
        # Update stats for filtered results
        total_questions = sum(len(g['questions']) for g in filtered_groups)
        total_answers = sum(len(g['answers']) for g in filtered_groups)
        
        self.stats_vars["Groups"].set(str(len(filtered_groups)))
        self.stats_vars["Questions"].set(str(total_questions))
        self.stats_vars["Answers"].set(str(total_answers))
        
        # Update scroll region
        self.update_scroll_region()
    
    def calculate_columns(self):
        """Calculate optimal number of columns based on available width"""
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return 4
        
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:  # Canvas not yet rendered
            return 4
        
        # Calculate how many cards fit with minimum width and padding
        available_width = canvas_width - 40  # Account for container padding
        card_total_width = self.min_card_width + self.card_padding
        max_columns = max(1, available_width // card_total_width)
        
        return max_columns
    
    def refresh_groups_layout(self):
        """Refresh just the layout without recreating cards"""
        if not self.group_cards:
            return
            
        columns = self.calculate_columns()
        
        # Clear current grid
        for widget in self.groups_container.grid_slaves():
            widget.grid_forget()
        
        # Reconfigure grid columns
        for i in range(columns):
            self.groups_container.grid_columnconfigure(i, weight=1)
        
        # Rearrange existing cards
        for i, card in enumerate(self.group_cards):
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
        self.update_scroll_region()
    
    def refresh_groups(self):
        """Refresh groups display with responsive layout"""
        # Clear cache on full refresh
        self.search_cache.clear()
        
        search_term = self.search_var.get().lower()
        search_mode = self.search_mode.get().lower()
        
        if search_mode == "all":
            filtered_groups = self.engine.search_qa_groups(search_term, "both")
        else:
            filtered_groups = self.engine.search_qa_groups(search_term, search_mode)
        
        self.display_filtered_groups(filtered_groups)
    
    def create_group_card(self, group):
        """Create a modern group card widget with improved layout"""
        card = tk.Frame(
            self.groups_container, 
            bg='#252547', 
            relief='raised', 
            bd=1,
            width=self.min_card_width,
            height=140
        )
        card.pack_propagate(False)
        
        # Main content with padding
        content = tk.Frame(card, bg='#252547')
        content.pack(fill='both', expand=True, padx=12, pady=12)
        
        # Header with title and badge
        header = tk.Frame(content, bg='#252547')
        header.pack(fill='x', pady=(0, 8))
        
        # Topic badge
        topic = group.get('topic', 'general')
        topic_color = self.get_topic_color(topic)
        topic_badge = tk.Label(
            header,
            text=topic.upper(),
            font=('Arial', 8, 'bold'),
            bg=topic_color,
            fg='white',
            padx=6,
            pady=2,
            relief='raised',
            bd=1
        )
        topic_badge.pack(side='left')
        
        # Priority indicator
        priority = group.get('priority', 'medium')
        priority_color = self.get_priority_color(priority)
        priority_dot = tk.Label(
            header,
            text="●",
            font=('Arial', 12),
            bg='#252547',
            fg=priority_color
        )
        priority_dot.pack(side='right', padx=(5, 0))
        
        # Group name (centered and prominent)
        group_name = group['group_name']
        if len(group_name) > 25:
            group_name = group_name[:22] + "..."
        
        name_frame = tk.Frame(content, bg='#252547')
        name_frame.pack(fill='x', pady=(0, 6))
        
        name_label = tk.Label(
            name_frame,
            text=group_name,
            font=('Arial', 13, 'bold'),
            bg='#252547',
            fg='white',
            anchor='center'
        )
        name_label.pack(fill='x')
        
        # Group description
        if group.get('group_description'):
            desc = group['group_description']
            if len(desc) > 60:
                desc = desc[:57] + "..."
            
            desc_label = tk.Label(
                content,
                text=desc,
                font=('Arial', 9),
                bg='#252547',
                fg='#b0b0d0',
                anchor='w',
                wraplength=240,
                justify=tk.LEFT
            )
            desc_label.pack(fill='x', pady=(0, 8))
        
        # Stats bar
        stats_frame = tk.Frame(content, bg='#252547')
        stats_frame.pack(fill='x', side='bottom')
        
        # Questions count
        q_count = len(group['questions'])
        a_count = len(group['answers'])
        followup_count = self.engine.count_followup_nodes(group.get('follow_ups', []))
        
        stats_text = f"❓{q_count}   💬{a_count}   🌿{followup_count}"
        
        stats_label = tk.Label(
            stats_frame,
            text=stats_text,
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='#b0b0d0',
            anchor='center'
        )
        stats_label.pack(fill='x')
        
        # Action buttons (centered at bottom)
        actions = tk.Frame(content, bg='#252547')
        actions.pack(fill='x', side='bottom', pady=(8, 0))
        
        # Store group reference for callbacks
        group_ref = group
        
        edit_btn = tk.Button(
            actions,
            text="✏️ Edit",
            command=lambda: self.edit_group(self.engine.get_qa_groups().index(group_ref)),
            bg='#6c63ff',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=3,
            width=8
        )
        edit_btn.pack(side='left', expand=True)
        
        delete_btn = tk.Button(
            actions,
            text="🗑️ Delete",
            command=lambda: self.delete_group(self.engine.get_qa_groups().index(group_ref)),
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=3,
            width=8
        )
        delete_btn.pack(side='right', expand=True)
        
        return card
    
    def get_topic_color(self, topic):
        """Return color for topic badge"""
        colors = {
            'greeting': '#00d4ff',
            'programming': '#6c63ff',
            'ai': '#ff6b9d',
            'gaming': '#00ff88',
            'creative': '#ffd166',
            'thanks': '#a78bfa',
            'general': '#94a3b8'
        }
        return colors.get(topic, '#94a3b8')
    
    def get_priority_color(self, priority):
        """Return color for priority indicator"""
        colors = {
            'high': '#ff4d7d',
            'medium': '#ffd166',
            'low': '#00ff88'
        }
        return colors.get(priority, '#ffd166')
    
    def new_group(self):
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        def on_save(group_data):
            self.engine.add_qa_group(group_data)
            if self.save_current_model():
                self.refresh_groups()
        
        GroupEditor(self.root, on_save=on_save)
    
    def edit_group(self, index):
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        def on_save(group_data):
            self.engine.update_qa_group(index, group_data)
            if self.save_current_model():
                self.refresh_groups()
        
        GroupEditor(self.root, self.engine.get_qa_groups()[index], on_save)
    
    def delete_group(self, index):
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        if messagebox.askyesno("Confirm", "Delete this group?"):
            self.engine.delete_qa_group(index)
            if self.save_current_model():
                self.refresh_groups()
    
    def import_json(self):
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                count = self.engine.import_from_json(filename)
                if self.save_current_model():
                    self.refresh_groups()
                    messagebox.showinfo("Success", f"Imported {count} groups")
                
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {str(e)}")
    
    def export_json(self):
        if not self.engine.get_qa_groups():
            messagebox.showwarning("Warning", "No data to export.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            try:
                self.engine.export_to_json(filename)
                messagebox.showinfo("Success", "Data exported successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

def main():
    root = tk.Tk()
    app = TrainingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()