import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import tkinter.simpledialog
import os

class BaseDialog:
    """Base class for dialogs with common functionality"""
    def __init__(self, parent, title, width=500, height=400):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        self.window.configure(bg='#2d2d5a')
        self.window.minsize(400, 300)
        
        # Set window icon
        self.set_window_icon()
        
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window(parent)
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        
        # Set window close protocol to handle unsaved changes
        self.window.protocol("WM_DELETE_WINDOW", self.confirm_close)
    
    def set_window_icon(self):
        """Set the window icon for all dialogs"""
        try:
            # Try different possible locations for the icon
            icon_paths = [
                "icon/train.ico",
                "../icon/train.ico",
                "../../icon/train.ico",
                os.path.join(os.path.dirname(__file__), "icon/train.ico"),
                os.path.join(os.path.dirname(__file__), "../icon/train.ico"),
                os.path.join(os.path.dirname(__file__), "../../icon/train.ico")
            ]
            
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.window.iconbitmap(icon_path)
                    print(f"✅ Loaded icon from: {icon_path}")
                    break
            else:
                print("⚠️ Could not find train.ico in any expected location")
                
        except Exception as e:
            print(f"⚠️ Could not load window icon: {e}")
    
    def center_window(self, parent):
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def confirm_close(self):
        """Default close handler - can be overridden by subclasses"""
        self.window.destroy()

class SectionDeletionDialog(BaseDialog):
    def __init__(self, parent, section_name, groups_in_section, available_sections, on_confirm=None):
        super().__init__(parent, "Handle Groups in Section", 500, 350)
        self.section_name = section_name
        self.groups_in_section = groups_in_section
        self.available_sections = [s for s in available_sections if s != section_name]
        self.on_confirm = on_confirm
        self.setup_ui()
    
    def setup_ui(self):
        # Configure grid weights
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Title
        tk.Label(
            self.window,
            text=f"Deleting Section: {self.section_name}",
            font=('Arial', 16, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))
        
        # Description
        groups_count = len(self.groups_in_section)
        desc_text = f"This section contains {groups_count} group(s). What would you like to do with these groups?"
        
        tk.Label(
            self.window,
            text=desc_text,
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='#b0b0d0',
            wraplength=460,
            justify=tk.LEFT
        ).grid(row=1, column=0, sticky='w', padx=20, pady=(0, 15))
        
        # Main content frame
        content_frame = tk.Frame(self.window, bg='#2d2d5a')
        content_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Action selection
        self.action_var = tk.StringVar(value="move_to_uncategorized")
        
        # Option 1: Move to uncategorized
        move_uncat_frame = tk.Frame(content_frame, bg='#2d2d5a')
        move_uncat_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        tk.Radiobutton(
            move_uncat_frame,
            text="Move groups to 'Uncategorized'",
            variable=self.action_var,
            value="move_to_uncategorized",
            bg='#2d2d5a',
            fg='white',
            selectcolor='#2d2d5a',
            activebackground='#2d2d5a',
            activeforeground='white',
            font=('Arial', 10)
        ).pack(anchor='w')
        
        # Option 2: Delete groups
        delete_frame = tk.Frame(content_frame, bg='#2d2d5a')
        delete_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        tk.Radiobutton(
            delete_frame,
            text="Delete all groups in this section",
            variable=self.action_var,
            value="delete_groups",
            bg='#2d2d5a',
            fg='white',
            selectcolor='#2d2d5a',
            activebackground='#2d2d5a',
            activeforeground='white',
            font=('Arial', 10)
        ).pack(anchor='w')
        
        # Option 3: Move to another section
        move_section_frame = tk.Frame(content_frame, bg='#2d2d5a')
        move_section_frame.grid(row=2, column=0, sticky='ew', pady=(0, 15))
        move_section_frame.grid_columnconfigure(0, weight=1)
        
        tk.Radiobutton(
            move_section_frame,
            text="Move groups to another section:",
            variable=self.action_var,
            value="move_to_section",
            bg='#2d2d5a',
            fg='white',
            selectcolor='#2d2d5a',
            activebackground='#2d2d5a',
            activeforeground='white',
            font=('Arial', 10)
        ).grid(row=0, column=0, sticky='w')
        
        self.target_section_var = tk.StringVar()
        self.target_section_combo = ttk.Combobox(
            move_section_frame,
            textvariable=self.target_section_var,
            values=self.available_sections,
            state='readonly',
            width=20,
            style='Dark.TCombobox'
        )
        self.target_section_combo.grid(row=1, column=0, sticky='w', pady=(5, 0), padx=20)
        
        if self.available_sections:
            self.target_section_var.set(self.available_sections[0])
        
        # Warning for delete option
        warning_frame = tk.Frame(content_frame, bg='#2d2d5a')
        warning_frame.grid(row=3, column=0, sticky='ew', pady=(10, 0))
        
        self.warning_label = tk.Label(
            warning_frame,
            text="⚠️ This will permanently delete all groups in this section!",
            font=('Arial', 9, 'bold'),
            bg='#2d2d5a',
            fg='#ff6b6b',
            wraplength=460,
            justify=tk.LEFT
        )
        
        # Update warning visibility based on selection
        def update_warning(*args):
            if self.action_var.get() == "delete_groups":
                self.warning_label.grid(row=0, column=0, sticky='w')
            else:
                self.warning_label.grid_forget()
        
        self.action_var.trace('w', update_warning)
        update_warning()
        
        # Buttons frame
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=3, column=0, sticky='e', padx=20, pady=(0, 20))
        
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
            text="✅ Confirm",
            command=self.confirm_action,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
    
    def confirm_action(self):
        action = self.action_var.get()
        target_section = None
        
        if action == "move_to_section":
            target_section = self.target_section_var.get()
            if not target_section:
                messagebox.showwarning("Warning", "Please select a target section.")
                return
        
        if self.on_confirm:
            self.on_confirm(action, target_section)
        self.window.destroy()

class SectionManagerDialog(BaseDialog):
    def __init__(self, parent, sections, qa_groups, on_save=None):
        super().__init__(parent, "Manage Sections", 500, 400)
        self.on_save = on_save
        self.sections = sections.copy() if sections else []
        self.qa_groups = qa_groups
        self.unsaved_changes = False
        self.original_sections = sections.copy() if sections else []
        self.setup_ui()
    
    def setup_ui(self):
        # Configure grid weights
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Title
        tk.Label(
            self.window,
            text="Manage Sections",
            font=('Arial', 16, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))
        
        # Description
        tk.Label(
            self.window,
            text="Create and manage sections to organize your QA groups",
            font=('Arial', 10),
            bg='#2d2d5a',
            fg='#b0b0d0',
            wraplength=400,
            justify=tk.LEFT
        ).grid(row=1, column=0, sticky='w', padx=20, pady=(0, 10))
        
        # Main content frame
        content_frame = tk.Frame(self.window, bg='#2d2d5a')
        content_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Add section frame
        add_frame = tk.Frame(content_frame, bg='#2d2d5a')
        add_frame.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        add_frame.grid_columnconfigure(0, weight=1)
        
        self.new_section_var = tk.StringVar()
        new_section_entry = tk.Entry(
            add_frame,
            textvariable=self.new_section_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            width=30
        )
        new_section_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        new_section_entry.bind('<Return>', lambda e: self.add_section())
        
        tk.Button(
            add_frame,
            text="+ Add Section",
            command=self.add_section,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=5
        ).grid(row=0, column=1)
        
        # Sections list
        list_frame = tk.Frame(content_frame, bg='#2d2d5a')
        list_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 15))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Listbox with scrollbar
        self.sections_listbox = tk.Listbox(
            list_frame,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            selectbackground='#6c63ff',
            activestyle='none',
            height=8
        )
        self.sections_listbox.grid(row=0, column=0, sticky='nsew')
        
        list_scrollbar = tk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.sections_listbox.yview,
            bg='#2d2d5a',
            troughcolor='#1a1a2e'
        )
        list_scrollbar.grid(row=0, column=1, sticky='ns')
        self.sections_listbox.config(yscrollcommand=list_scrollbar.set)
        
        # Action buttons for list
        list_actions = tk.Frame(content_frame, bg='#2d2d5a')
        list_actions.grid(row=2, column=0, sticky='ew', pady=(0, 15))
        list_actions.grid_columnconfigure(0, weight=1)
        
        tk.Button(
            list_actions,
            text="✏️ Rename",
            command=self.rename_section,
            bg='#00d4ff',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=4
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Button(
            list_actions,
            text="🗑️ Delete",
            command=self.delete_section,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=4
        ).pack(side=tk.LEFT)
        
        # Buttons frame
        button_frame = tk.Frame(self.window, bg='#2d2d5a')
        button_frame.grid(row=3, column=0, sticky='e', padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.confirm_close,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Main save button that changes state
        self.save_button = tk.Button(
            button_frame,
            text="💾 Save Sections",
            command=self.save_sections,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        )
        self.save_button.pack(side=tk.RIGHT)
        
        # Load existing sections
        self.refresh_sections_list()
    
    def refresh_sections_list(self):
        self.sections_listbox.delete(0, tk.END)
        for section in self.sections:
            groups_count = len([g for g in self.qa_groups if g.get('section') == section])
            display_text = f"{section} ({groups_count} groups)"
            self.sections_listbox.insert(tk.END, display_text)
    
    def add_section(self):
        section_name = self.new_section_var.get().strip()
        if not section_name:
            messagebox.showwarning("Warning", "Please enter a section name.")
            return
        
        if section_name in self.sections:
            messagebox.showwarning("Warning", f"Section '{section_name}' already exists.")
            return
        
        self.sections.append(section_name)
        self.new_section_var.set("")
        self.refresh_sections_list()
        self.mark_unsaved_changes()
    
    def rename_section(self):
        selection = self.sections_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a section to rename.")
            return
        
        index = selection[0]
        old_name = self.sections[index]
        
        new_name = tk.simpledialog.askstring(
            "Rename Section",
            "Enter new section name:",
            initialvalue=old_name,
            parent=self.window
        )
        
        if new_name and new_name.strip() and new_name != old_name:
            if new_name in self.sections:
                messagebox.showwarning("Warning", f"Section '{new_name}' already exists.")
                return
            
            self.sections[index] = new_name.strip()
            self.refresh_sections_list()
            self.mark_unsaved_changes()
    
    def delete_section(self):
        selection = self.sections_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a section to delete.")
            return
        
        index = selection[0]
        section_name = self.sections[index]
        groups_in_section = [g for g in self.qa_groups if g.get('section') == section_name]
        
        if groups_in_section:
            # Show the section deletion dialog
            def handle_deletion(action, target_section):
                # Remove the section from the list
                self.sections.pop(index)
                self.refresh_sections_list()
                self.mark_unsaved_changes()
                
                # Notify parent about the groups that need handling
                if self.on_save:
                    # We'll pass the section deletion info so the parent can handle the groups
                    self.on_save(self.sections, section_name, action, target_section)
            
            SectionDeletionDialog(
                self.window, 
                section_name, 
                groups_in_section, 
                self.sections,
                on_confirm=handle_deletion
            )
        else:
            # No groups in section, just delete it
            self.sections.pop(index)
            self.refresh_sections_list()
            self.mark_unsaved_changes()
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        if not self.unsaved_changes:
            self.unsaved_changes = True
            self.save_button.config(text="💾 Save Sections *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag"""
        self.unsaved_changes = False
        self.save_button.config(text="💾 Save Sections", bg='#00ff88')
    
    def confirm_close(self):
        """Confirm closing if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes to sections. Do you want to save before closing?\n\n"
                "Yes - Save and Close\n"
                "No - Close without Saving\n"
                "Cancel - Return to Dialog"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Save and Close
                self.save_sections()
                return
            else:  # No - Close without Saving
                self.window.destroy()
        else:
            self.window.destroy()
    
    def save_sections(self):
        if self.on_save:
            self.on_save(self.sections)
        self.clear_unsaved_changes()
        self.window.destroy()

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
            command=self.confirm_close,
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
    
    def confirm_close(self):
        """Confirm closing if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?\n\n"
                "Yes - Save and Close\n"
                "No - Close without Saving\n"
                "Cancel - Return to Dialog"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Save and Close
                self.create_model()
                return
            else:  # No - Close without Saving
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
            command=self.confirm_close,
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
    
    def confirm_close(self):
        """Confirm closing if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?\n\n"
                "Yes - Save and Close\n"
                "No - Close without Saving\n"
                "Cancel - Return to Dialog"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Save and Close
                self.save_model()
                return
            else:  # No - Close without Saving
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
            version = "1..0.0"
        
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
            command=self.confirm_close,
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
    
    def confirm_close(self):
        """Confirm closing if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?\n\n"
                "Yes - Save and Close\n"
                "No - Close without Saving\n"
                "Cancel - Return to Dialog"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Save and Close
                self.save_name()
                return
            else:  # No - Close without Saving
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
            command=self.confirm_close,
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
                self.save()
                return
            else:  # No - Close without Saving
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