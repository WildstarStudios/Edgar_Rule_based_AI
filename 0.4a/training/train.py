import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import datetime
import os
from core.train_engine import TrainingEngine, ModelManager
from core.group_create import GroupEditor
from core.follow_tree import FollowUpEditor
from core.dialogs import CreateModelDialog, EditModelDialog, SectionManagerDialog, SectionDeletionDialog

class TrainingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI Training")
        self.root.geometry("1200x800")
        self.root.minsize(350, 300)
        self.root.configure(bg='#1a1a2e')
        # Set window icon and theme
        try:
            self.root.iconbitmap("icon/train.ico")
        except:
            pass
        
        # Initialize backend engine
        self.engine = TrainingEngine()
        self.engine.initialize_model_manager(root)
        
        self.scroll_frame = None
        self.model_changing = False
        self.group_cards = []
        self.unsaved_changes = False
        
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
        
        # Ensure models folder exists (same as 0.1a)
        os.makedirs("models", exist_ok=True)
        
        # Set window close protocol for unsaved changes protection
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)
        
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
    
    def delete_current_model(self):
        """Delete the current model after confirmation"""
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "No model selected.")
            return
        
        model_name = self.engine.current_model
        groups_count = len(self.engine.get_qa_groups())
        
        # Create confirmation message
        message = f"Are you sure you want to delete the model '{model_name}'?"
        if groups_count > 0:
            message += f"\n\nThis will also delete {groups_count} QA groups."
        
        if messagebox.askyesno("Confirm Delete", message + "\n\nThis action cannot be undone!"):
            try:
                # Get next available model to switch to
                available_models = self.engine.available_models
                next_model = None
                if len(available_models) > 1:
                    # Find the next model that isn't the one being deleted
                    for model in available_models:
                        if model != model_name:
                            next_model = model
                            break
                
                # Delete the model
                self.engine.model_manager.delete_model(model_name)
                
                # Update interface
                self.update_model_dropdown()
                
                if next_model:
                    self.load_model(next_model)
                    messagebox.showinfo("Success", f"Model '{model_name}' deleted successfully!")
                else:
                    # No models left - clear everything and prompt for new model
                    self.engine.current_model = None
                    self.engine.qa_groups = []
                    self.refresh_groups()
                    
                    # Clear the model combobox text
                    if hasattr(self, 'model_combobox'):
                        self.model_combobox.set('')
                    
                    messagebox.showinfo("Success", f"Model '{model_name}' deleted successfully!\n\nNo models remaining - create a new model to continue.")
                    
                    # Prompt to create a new model
                    self.root.after(100, self.prompt_create_first_model)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete model: {str(e)}")
    
    def load_model(self, model_name):
        try:
            self.engine.load_model(model_name)
            if hasattr(self, 'scroll_frame'):
                self.refresh_groups()
            self.update_model_dropdown()
            self.update_section_filters()
            self.clear_unsaved_changes()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
    
    def save_current_model(self):
        try:
            self.engine.save_current_model()
            self.clear_unsaved_changes()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save model: {str(e)}")
            return False
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        if not self.unsaved_changes:
            self.unsaved_changes = True
            # Update window title and save button to indicate unsaved changes
            original_title = "Edgar AI Training"
            if not self.root.title().endswith(" *"):
                self.root.title(f"{original_title} *")
            # Update save button appearance
            self.save_btn.config(text="💾 Save *", bg='#ffa500')
    
    def clear_unsaved_changes(self):
        """Clear unsaved changes flag"""
        self.unsaved_changes = False
        # Restore original window title and save button
        self.root.title("Edgar AI Training")
        self.save_btn.config(text="💾 Save", bg='#00ff88')
    
    def confirm_exit(self):
        """Confirm exit if there are unsaved changes"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before exiting?\n\n"
                "Yes - Save and Exit\n"
                "No - Exit without Saving\n"
                "Cancel - Return to Application"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Save and Exit
                if self.save_current_model():
                    self.root.destroy()
                return
            else:  # No - Exit without Saving
                self.root.destroy()
        else:
            self.root.destroy()
    
    def on_model_switch_request(self, model_name):
        if self.model_changing:
            return
            
        # If no model selected (empty string), don't switch
        if not model_name:
            return
            
        if model_name != self.engine.current_model:
            # Check for unsaved changes
            if self.unsaved_changes:
                response = messagebox.askyesnocancel(
                    "Unsaved Changes", 
                    f"You have unsaved changes in '{self.engine.current_model}'. Save before switching?\n\n"
                    "Yes - Save and Switch\n"
                    "No - Switch without Saving\n"
                    "Cancel - Stay on Current Model"
                )
                
                if response is None:  # Cancel
                    self.model_combobox.set(self.engine.current_model)
                    return
                elif response:  # Yes - Save and Switch
                    if not self.save_current_model():
                        self.model_combobox.set(self.engine.current_model)
                        return
            
            self.model_changing = True
            self.load_model(model_name)
            self.model_changing = False
    
    def update_model_dropdown(self):
        """Update the model dropdown with current available models"""
        if hasattr(self, 'model_combobox'):
            available_models = self.engine.available_models
            self.model_combobox['values'] = available_models
            
            # Set the current value appropriately
            if self.engine.current_model and self.engine.current_model in available_models:
                self.model_combobox.set(self.engine.current_model)
            elif available_models:
                # Set to first available model
                self.model_combobox.set(available_models[0])
            else:
                # No models available - clear the selection
                self.model_combobox.set('')
    
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
        
        # Set initial value
        if self.engine.current_model:
            self.model_combobox.set(self.engine.current_model)
        elif self.engine.available_models:
            self.model_combobox.set(self.engine.available_models[0])
            
        self.model_combobox.bind('<<ComboboxSelected>>', 
                               lambda e: self.on_model_switch_request(self.model_combobox.get()))
        
        # NEW ORDER: Save, Edit, New Model, Delete Model
        self.save_btn = tk.Button(
            model_frame,
            text="💾 Save",
            command=self.save_current_model,
            bg='#00ff88',
            fg='black',
            font=('Arial', 9, 'bold'),
            padx=12
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
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
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # NEW: Delete Model button
        tk.Button(
            model_frame,
            text="🗑️ Delete Model",
            command=self.delete_current_model,
            bg='#ff4d7d',
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
        
        # NEW: Section filter dropdown
        tk.Label(
            search_frame,
            text="Section:",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.section_filter = tk.StringVar(value="All Sections")
        self.section_combo = ttk.Combobox(
            search_frame,
            textvariable=self.section_filter,
            state="readonly",
            width=15,
            style='Dark.TCombobox'
        )
        self.section_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.section_combo.bind('<<ComboboxSelected>>', lambda e: self.on_section_filter())
        
        # Bind search events for real-time filtering
        self.search_var.trace('w', self.on_search)
        self.search_mode.trace('w', self.on_search)
        
        # Action buttons
        actions = tk.Frame(toolbar, bg='#1a1a2e')
        actions.grid(row=0, column=1, sticky='e')
        
        # NEW: Manage Sections button
        tk.Button(
            actions,
            text="📁 Manage Sections",
            command=self.manage_sections,
            bg='#a78bfa',
            fg='white',
            font=('Arial', 9),
            padx=12
        ).pack(side=tk.LEFT, padx=(0, 8))
        
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
    
    def manage_sections(self):
        """Open section management dialog"""
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
        
        def on_save(sections):
            self.engine.update_sections(sections)
            if self.save_current_model():
                self.update_section_filters()
                self.refresh_groups()
            else:
                self.mark_unsaved_changes()
        
        SectionManagerDialog(self.root, self.engine.get_sections(), self.engine.get_qa_groups(), on_save)
    
    def update_section_filters(self):
        """Update the section filter dropdown with current sections"""
        sections = self.engine.get_sections()
        section_values = ["All Sections", "Uncategorized"] + sections
        self.section_combo['values'] = section_values
        
        # Also update any open group editor dialogs
        self.update_open_editors()
    
    def update_open_editors(self):
        """Update section combobox in any open group editors"""
        # This would need to be implemented if you want to update open dialogs
        # For now, we'll just refresh the main interface
        pass
    
    def on_section_filter(self):
        """Handle section filter change"""
        self.on_search()
    
    def on_search(self, *args):
        """Optimized real-time search with caching and section filtering"""
        search_term = self.search_var.get().lower()
        search_mode = self.search_mode.get().lower()
        section_filter = self.section_filter.get()
        
        # Use cache if search hasn't changed
        cache_key = f"{search_term}|{search_mode}|{section_filter}"
        if cache_key in self.search_cache:
            filtered_groups = self.search_cache[cache_key]
        else:
            # Perform search with section filter
            if search_mode == "all":
                filtered_groups = self.engine.search_qa_groups(search_term, "both", section_filter)
            else:
                filtered_groups = self.engine.search_qa_groups(search_term, search_mode, section_filter)
            
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
        section_filter = self.section_filter.get()
        
        if search_mode == "all":
            filtered_groups = self.engine.search_qa_groups(search_term, "both", section_filter)
        else:
            filtered_groups = self.engine.search_qa_groups(search_term, search_mode, section_filter)
        
        self.display_filtered_groups(filtered_groups)
    
    def create_group_card(self, group):
        """Create a modern group card widget with improved layout including section"""
        card = tk.Frame(
            self.groups_container, 
            bg='#252547', 
            relief='raised', 
            bd=1,
            width=self.min_card_width,
            height=160  # Slightly taller to accommodate section
        )
        card.pack_propagate(False)
        
        # Main content with padding
        content = tk.Frame(card, bg='#252547')
        content.pack(fill='both', expand=True, padx=12, pady=12)
        
        # Header with priority and section
        header = tk.Frame(content, bg='#252547')
        header.pack(fill='x', pady=(0, 8))
        
        # Topic badge (left side)
        topic = group.get('topic', 'general')
        topic_color = self.get_topic_color(topic)
        topic_badge = tk.Label(
            header,
            text=topic.upper(),
            font=('Arial', 7, 'bold'),
            bg=topic_color,
            fg='white',
            padx=4,
            pady=1,
            relief='raised',
            bd=1
        )
        topic_badge.pack(side='left')
        
        # Spacer to push section and priority to right
        tk.Frame(header, bg='#252547').pack(side='left', expand=True)
        
        # Section badge (right side, before priority)
        section = group.get('section', '')
        if section:
            section_color = self.get_section_color(section)
            section_badge = tk.Label(
                header,
                text=section[:12] + "..." if len(section) > 12 else section,
                font=('Arial', 7, 'bold'),
                bg=section_color,
                fg='white',
                padx=4,
                pady=1,
                relief='raised',
                bd=1
            )
            section_badge.pack(side='right', padx=(0, 5))
        
        # Priority indicator (far right)
        priority = group.get('priority', 'medium')
        priority_color = self.get_priority_color(priority)
        priority_dot = tk.Label(
            header,
            text="●",
            font=('Arial', 12),
            bg='#252547',
            fg=priority_color
        )
        priority_dot.pack(side='right')
        
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
        
        # Button order: Edit, Move, Delete (with Move in the middle)
        edit_btn = tk.Button(
            actions,
            text="✏️ Edit",
            command=lambda: self.edit_group(self.engine.get_qa_groups().index(group_ref)),
            bg='#6c63ff',
            fg='white',
            font=('Arial', 8, 'bold'),
            padx=8,
            pady=2,
            width=6
        )
        edit_btn.pack(side=tk.LEFT, expand=True)
        
        # Move button in the middle
        move_btn = tk.Button(
            actions,
            text="📂 Move",
            command=lambda: self.move_group(self.engine.get_qa_groups().index(group_ref)),
            bg='#a78bfa',
            fg='white',
            font=('Arial', 8, 'bold'),
            padx=8,
            pady=2,
            width=6
        )
        move_btn.pack(side=tk.LEFT, expand=True)
        
        delete_btn = tk.Button(
            actions,
            text="🗑️ Delete",
            command=lambda: self.delete_group(self.engine.get_qa_groups().index(group_ref)),
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 8, 'bold'),
            padx=8,
            pady=2,
            width=6
        )
        delete_btn.pack(side=tk.RIGHT, expand=True)
        
        return card
    
    def get_section_color(self, section):
        """Return color for section badge"""
        # Generate consistent color based on section name
        import hashlib
        hash_obj = hashlib.md5(section.encode())
        hash_int = int(hash_obj.hexdigest()[:8], 16)
        
        colors = [
            '#00d4ff', '#6c63ff', '#ff6b9d', '#00ff88', '#ffd166',
            '#a78bfa', '#94a3b8', '#f97316', '#10b981', '#8b5cf6'
        ]
        
        return colors[hash_int % len(colors)]
    
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
        
        # Use a mutable object to track the group index for subsequent saves
        group_index = [None]
        
        def on_save(group_data, is_new=True):
            if is_new:
                # First save - create new group
                self.engine.add_qa_group(group_data)
                group_index[0] = len(self.engine.get_qa_groups()) - 1
            else:
                # Subsequent saves - update existing group
                if group_index[0] is not None:
                    self.engine.update_qa_group(group_index[0], group_data)
                else:
                    # Fallback: find the group by name and update it
                    for i, group in enumerate(self.engine.get_qa_groups()):
                        if (group.get('group_name') == group_data['group_name'] and 
                            group.get('group_description') == group_data.get('group_description', '')):
                            self.engine.update_qa_group(i, group_data)
                            group_index[0] = i
                            break
            
            if self.save_current_model():
                self.refresh_groups()
            else:
                self.mark_unsaved_changes()
        
        editor = GroupEditor(self.root, on_save=on_save, is_new_group=True)
        # Update the section combobox in the editor
        self.update_editor_sections(editor)
    
    def edit_group(self, index):
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        def on_save(group_data, is_new=False):
            # Always update the existing group when editing
            self.engine.update_qa_group(index, group_data)
            if self.save_current_model():
                self.refresh_groups()
            else:
                self.mark_unsaved_changes()
        
        editor = GroupEditor(self.root, self.engine.get_qa_groups()[index], on_save, is_new_group=False)
        # Update the section combobox in the editor
        self.update_editor_sections(editor)
    
    def update_editor_sections(self, editor):
        """Update the section combobox in a group editor"""
        sections = self.engine.get_sections()
        if hasattr(editor, 'section_combo') and sections:
            editor.section_combo['values'] = sections
            # Set default section if not already set
            if not editor.section_var.get() and sections:
                editor.section_var.set(sections[0])
    
    def move_group(self, index):
        """Move group to different section"""
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
        
        group = self.engine.get_qa_groups()[index]
        current_section = group.get('section', '')
        sections = self.engine.get_sections()
        
        if not sections:
            messagebox.showwarning("Warning", "No sections available. Please create sections first.")
            return
        
        # Create simple dialog for section selection
        move_window = tk.Toplevel(self.root)
        move_window.title("Move Group to Section")
        move_window.geometry("300x150")
        move_window.configure(bg='#2d2d5a')
        move_window.transient(self.root)
        move_window.grab_set()
        
        # Center the window
        move_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (move_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (move_window.winfo_height() // 2)
        move_window.geometry(f"+{x}+{y}")
        
        tk.Label(
            move_window,
            text=f"Move '{group['group_name']}' to section:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white',
            wraplength=280
        ).pack(pady=15)
        
        section_var = tk.StringVar(value=current_section if current_section else sections[0])
        section_combo = ttk.Combobox(
            move_window,
            textvariable=section_var,
            values=sections,
            state='readonly',
            width=20,
            style='Dark.TCombobox'
        )
        section_combo.pack(pady=10)
        
        def do_move():
            new_section = section_var.get()
            self.engine.move_group_to_section(index, new_section)
            if self.save_current_model():
                self.refresh_groups()
                move_window.destroy()
            else:
                self.mark_unsaved_changes()
        
        button_frame = tk.Frame(move_window, bg='#2d2d5a')
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="Move",
            command=do_move,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=move_window.destroy,
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 10),
            padx=15
        ).pack(side=tk.LEFT)
    
    def delete_group(self, index):
        if not self.engine.current_model:
            messagebox.showwarning("Warning", "Please create or select a model first.")
            return
            
        if messagebox.askyesno("Confirm", "Delete this group?"):
            self.engine.delete_qa_group(index)
            if self.save_current_model():
                self.refresh_groups()
            else:
                self.mark_unsaved_changes()
    
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
                else:
                    self.mark_unsaved_changes()
                
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {str(e)}")
    
    def export_json(self):
        if not self.engine.get_qa_groups():
            messagebox.showwarning("Warning", "No data to export.")
            return
        
        # Generate automatic filename using model name
        if self.engine.current_model:
            # Clean the model name for filename use
            clean_name = "".join(c for c in self.engine.current_model if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_name = clean_name.replace(' ', '_')
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{clean_name}_{timestamp}.json"
        else:
            default_filename = f"export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=default_filename  # This sets the preset filename
        )
        
        if filename:
            try:
                self.engine.export_to_json(filename)
                messagebox.showinfo("Success", f"Data exported successfully to:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

def main():
    root = tk.Tk()
    app = TrainingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
