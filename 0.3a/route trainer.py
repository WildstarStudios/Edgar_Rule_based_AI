import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
from typing import List, Dict, Any

class RoutingGroupEditor:
    """Dialog for editing routing groups"""
    
    def __init__(self, parent, group_data=None, on_save=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Routing Group Editor")
        self.window.geometry("700x600")
        self.window.configure(bg='#2d2d5a')
        self.window.minsize(600, 500)
        
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
        
        # Engine name
        tk.Label(
            content_frame,
            text="Engine Name:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 8))
        
        self.engine_var = tk.StringVar()
        self.engine_entry = tk.Entry(
            content_frame,
            textvariable=self.engine_var,
            font=('Arial', 11),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white'
        )
        self.engine_entry.grid(row=1, column=1, sticky='ew', pady=(0, 15))
        
        # Confidence threshold
        tk.Label(
            content_frame,
            text="Confidence Threshold:",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=(0, 8))
        
        threshold_frame = tk.Frame(content_frame, bg='#2d2d5a')
        threshold_frame.grid(row=2, column=1, sticky='ew', pady=(0, 15))
        
        self.threshold_var = tk.DoubleVar(value=0.75)  # Default to high_confidence
        
        # Create radio buttons for each threshold
        thresholds = [
            ("Exact Match (0.95)", 0.95),
            ("High Confidence (0.75)", 0.75),
            ("Medium Confidence (0.60)", 0.60),
            ("Low Confidence (0.45)", 0.45)
        ]
        
        for text, value in thresholds:
            tk.Radiobutton(threshold_frame, text=text, variable=self.threshold_var,
                         value=value, bg='#2d2d5a', fg='white', 
                         selectcolor='#6c63ff', font=('Arial', 10)).pack(anchor='w')
        
        # Custom threshold
        custom_frame = tk.Frame(threshold_frame, bg='#2d2d5a')
        custom_frame.pack(anchor='w', pady=(5, 0))
        
        tk.Radiobutton(custom_frame, text="Custom:", variable=self.threshold_var,
                     value=0.75, bg='#2d2d5a', fg='white', 
                     selectcolor='#6c63ff', font=('Arial', 10)).pack(side=tk.LEFT)
        
        self.custom_threshold_var = tk.DoubleVar(value=0.75)
        self.custom_threshold_entry = tk.Entry(custom_frame, textvariable=self.custom_threshold_var,
                                             width=6, font=('Arial', 10), bg='#1a1a2e', 
                                             fg='white', insertbackground='white')
        self.custom_threshold_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Update threshold when custom entry changes
        def update_custom_threshold(*args):
            try:
                custom_val = float(self.custom_threshold_var.get())
                if 0.35 <= custom_val <= 1.0:
                    self.threshold_var.set(custom_val)
            except:
                pass
        
        self.custom_threshold_var.trace('w', update_custom_threshold)
        
        # Questions
        tk.Label(
            content_frame,
            text="Questions (one per line):",
            font=('Arial', 11, 'bold'),
            bg='#2d2d5a',
            fg='white'
        ).grid(row=3, column=0, sticky='nw', pady=(0, 8))
        
        self.questions_text = scrolledtext.ScrolledText(
            content_frame,
            height=12,
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.questions_text.grid(row=3, column=1, sticky='nsew', pady=(0, 15))
        
        # Instructions
        instructions_frame = tk.Frame(content_frame, bg='#2d2d5a')
        instructions_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        instructions = tk.Label(
            instructions_frame,
            text="💡 Questions will be matched against user input. If confidence meets the threshold,\nthe request will be routed to the specified engine.",
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
        
        tk.Button(
            button_frame,
            text="💾 Save Group",
            command=self.save_group,
            bg='#00ff88',
            fg='black',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
        
        # Configure content frame row weights
        content_frame.grid_rowconfigure(3, weight=1)
    
    def load_data(self):
        if 'group_name' in self.group_data:
            self.name_var.set(self.group_data['group_name'])
        if 'engine' in self.group_data:
            self.engine_var.set(self.group_data['engine'])
        if 'confidence_threshold' in self.group_data:
            threshold = self.group_data['confidence_threshold']
            self.threshold_var.set(threshold)
            self.custom_threshold_var.set(threshold)
        
        # Load questions
        if 'questions' in self.group_data:
            self.questions_text.delete('1.0', tk.END)
            self.questions_text.insert('1.0', '\n'.join(self.group_data['questions']))
    
    def save_group(self):
        group_name = self.name_var.get().strip()
        engine = self.engine_var.get().strip()
        threshold = self.threshold_var.get()
        
        # Get questions from text widget
        questions_text = self.questions_text.get('1.0', tk.END).strip()
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        
        # Validation
        if not group_name:
            messagebox.showwarning("Warning", "Group name is required.")
            self.name_entry.focus_set()
            return
        
        if not engine:
            messagebox.showwarning("Warning", "Engine name is required.")
            self.engine_entry.focus_set()
            return
        
        if not questions:
            messagebox.showwarning("Warning", "At least one question is required.")
            self.questions_text.focus_set()
            return
        
        # Validate threshold
        if not self.CONFIDENCE_THRESHOLDS['min_acceptable'] <= threshold <= 1.0:
            messagebox.showwarning("Warning", 
                                f"Confidence threshold must be between {self.CONFIDENCE_THRESHOLDS['min_acceptable']} and 1.0")
            return
        
        group_data = {
            'group_name': group_name,
            'engine': engine,
            'confidence_threshold': threshold,
            'questions': questions
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
        
        self.routing_file = "resources/route.json"
        self.routing_groups = []
        self.current_columns = 4
        self.min_card_width = 280
        self.card_padding = 16
        
        # Ensure resources folder exists
        os.makedirs("resources", exist_ok=True)
        
        self.load_routing_data()
        self.setup_gui()
        self.refresh_groups()
    
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
            "available_engines": list(set(group['engine'] for group in self.routing_groups)),
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
        stats = [("Routing Groups", "0"), ("Engines", "0"), ("Total Questions", "0")]
        
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
        engines = set(g['engine'] for g in filtered_groups)
        
        self.stats_vars["Routing Groups"].set(str(len(filtered_groups)))
        self.stats_vars["Engines"].set(str(len(engines)))
        self.stats_vars["Total Questions"].set(str(total_questions))
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
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
        """Create a routing group card widget"""
        card = tk.Frame(
            self.groups_container, 
            bg='#252547', 
            relief='raised', 
            bd=1,
            width=self.min_card_width,
            height=160
        )
        card.pack_propagate(False)
        
        # Main content with padding
        content = tk.Frame(card, bg='#252547')
        content.pack(fill='both', expand=True, padx=12, pady=12)
        
        # Header with title and engine badge
        header = tk.Frame(content, bg='#252547')
        header.pack(fill='x', pady=(0, 8))
        
        # Engine badge
        engine = group['engine']
        engine_color = self.get_engine_color(engine)
        engine_badge = tk.Label(
            header,
            text=engine.upper(),
            font=('Arial', 8, 'bold'),
            bg=engine_color,
            fg='white',
            padx=6,
            pady=2,
            relief='raised',
            bd=1
        )
        engine_badge.pack(side='left')
        
        # Confidence indicator
        threshold = group['confidence_threshold']
        confidence_color = self.get_confidence_color(threshold)
        confidence_text = self.get_confidence_text(threshold)
        
        confidence_label = tk.Label(
            header,
            text=f"● {confidence_text}",
            font=('Arial', 8, 'bold'),
            bg='#252547',
            fg=confidence_color
        )
        confidence_label.pack(side='right', padx=(5, 0))
        
        # Group name
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
        
        # Confidence value
        confidence_value = tk.Label(
            content,
            text=f"Threshold: {threshold:.2f}",
            font=('Arial', 9),
            bg='#252547',
            fg='#b0b0d0',
            anchor='center'
        )
        confidence_value.pack(fill='x', pady=(0, 8))
        
        # Stats bar
        stats_frame = tk.Frame(content, bg='#252547')
        stats_frame.pack(fill='x', side='bottom')
        
        # Questions count
        q_count = len(group['questions'])
        stats_text = f"❓ {q_count} question{'s' if q_count != 1 else ''}"
        
        stats_label = tk.Label(
            stats_frame,
            text=stats_text,
            font=('Arial', 10, 'bold'),
            bg='#252547',
            fg='#b0b0d0',
            anchor='center'
        )
        stats_label.pack(fill='x')
        
        # Action buttons
        actions = tk.Frame(content, bg='#252547')
        actions.pack(fill='x', side='bottom', pady=(8, 0))
        
        # Store group reference for callbacks
        group_ref = group
        
        edit_btn = tk.Button(
            actions,
            text="✏️ Edit",
            command=lambda: self.edit_group(self.routing_groups.index(group_ref)),
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
            command=lambda: self.delete_group(self.routing_groups.index(group_ref)),
            bg='#ff4d7d',
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=12,
            pady=3,
            width=8
        )
        delete_btn.pack(side='right', expand=True)
        
        return card
    
    def get_engine_color(self, engine):
        """Return color for engine badge"""
        # Generate consistent color based on engine name
        colors = ['#00d4ff', '#6c63ff', '#ff6b9d', '#00ff88', '#ffd166', '#a78bfa', '#94a3b8']
        hash_val = sum(ord(c) for c in engine)
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
            return '#ff6b9d'  # Pink for low confidence
    
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
                messagebox.showinfo("Success", "Routing group created successfully!")
        
        RoutingGroupEditor(self.root, on_save=on_save)
    
    def edit_group(self, index):
        """Edit an existing routing group"""
        def on_save(group_data):
            self.routing_groups[index] = group_data
            if self.save_routing_data():
                self.refresh_groups()
                messagebox.showinfo("Success", "Routing group updated successfully!")
        
        RoutingGroupEditor(self.root, self.routing_groups[index], on_save)
    
    def delete_group(self, index):
        """Delete a routing group"""
        group_name = self.routing_groups[index]['group_name']
        
        if messagebox.askyesno("Confirm Delete", f"Delete routing group '{group_name}'?"):
            self.routing_groups.pop(index)
            if self.save_routing_data():
                self.refresh_groups()
                messagebox.showinfo("Success", "Routing group deleted successfully!")


def main():
    """Main function to run the routing trainer"""
    root = tk.Tk()
    app = RoutingTrainerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()