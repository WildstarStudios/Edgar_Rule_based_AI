import customtkinter as ctk
from customtkinter import CTk, CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkTextbox, CTkScrollbar, CTkComboBox, StringVar
import threading
import time
import sys
import os
import configparser

# Add the core directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
core_dir = os.path.join(project_root, 'core')
sys.path.insert(0, core_dir)

try:
    from core.layer import create_streaming_layer
    print("✅ Successfully imported StreamingLayer from core.layer")
except ImportError as e:
    print(f"❌ Error importing StreamingLayer: {e}")
    print("Please make sure core/layer.py exists")
    sys.exit(1)

# Import local settings
from .settings import open_settings

# Set appearance mode and theme to match classic colors
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ClassicChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI Assistant - Classic")
        
        # Load configuration
        self.config = self.load_configuration()
        
        # Set window size from config
        window_width = self.config.getint('gui', 'window_width', fallback=1000)
        window_height = self.config.getint('gui', 'window_height', fallback=700)
        
        # Center the window on screen
        self.center_window(window_width, window_height)
        
        # Classic color scheme
        self.colors = {
            'bg_primary': '#0f0f23',
            'bg_secondary': '#1a1a2e',
            'bg_tertiary': '#252547',
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
            'input_bg_disabled': '#1a1a3a',
            'text_disabled': '#8080a0',
            'hover_primary': '#5750d3',
            'hover_secondary': '#35356a',
            'scrollbar_bg': '#1a1a2e',
            'scrollbar_slider': '#6c63ff',
            'scrollbar_hover': '#5750d3'
        }
        
        # Configure customtkinter to use classic colors
        self.configure_ctk_theme()
        
        # Initialize streaming layer with configuration
        self.streaming_layer = create_streaming_layer(
            config_file="config.cfg",
            streaming_callback=self._handle_streaming,
            thinking_callback=self._handle_thinking,
            response_complete_callback=self._handle_response_complete,
            status_update_callback=self._handle_status_update,
            error_callback=self._handle_error
        )
        
        # GUI variables
        self.is_processing = False
        self.current_streaming_text = ""
        self.is_streaming = False
        
        # Verbose mode setting
        self.verbose_mode = self.config.getboolean('gui', 'verbose_mode', fallback=False)
        
        # Thinking animation variables
        self.thinking_animation_active = False
        self.thinking_animation_job = None
        self.thinking_dots = 0
        self.thinking_label = None
        
        self.setup_gui()
    
    def center_window(self, width, height):
        """Center the window on the screen"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set window geometry
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def configure_ctk_theme(self):
        """Configure CustomTkinter to use classic theme colors"""
        # Set main background
        self.root.configure(fg_color=self.colors['bg_primary'])
        
    # ===== STREAMING LAYER CALLBACKS =====
    
    def _handle_streaming(self, text: str):
        """Handle streaming text from the layer"""
        self.stream_to_display(text)
    
    def _handle_thinking(self, text: str):
        """Handle thinking indicators from the layer"""
        if self.verbose_mode:
            self.add_message("thinking", text)
    
    def _handle_response_complete(self):
        """Handle response completion from the layer"""
        self.processing_complete()
    
    def _handle_status_update(self, status: str):
        """Handle status updates from the layer"""
        self.status_var.set(status)
    
    def _handle_error(self, error: str):
        """Handle errors from the layer"""
        self.add_message("error", error)
        CTkMessagebox.show_error("Error", error)
    
    def load_configuration(self):
        """Load configuration from config file"""
        config = configparser.ConfigParser()
        
        # Default configuration
        defaults = {
            'gui': {
                'theme': 'classic',
                'window_width': '1000',
                'window_height': '700',
                'streaming_enabled': 'True',
                'verbose_mode': 'False'
            }
        }
        
        # Set defaults
        for section, options in defaults.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in options.items():
                config.set(section, key, value)
        
        # Load from file if exists
        if os.path.exists("config.cfg"):
            config.read("config.cfg")
            print("✅ Loaded GUI configuration from config.cfg")
        else:
            print("⚠️  config.cfg not found, using default GUI configuration")
        
        return config
    
    def get_available_models(self):
        """Get list of available models from streaming layer"""
        return self.streaming_layer.get_available_models()
    
    def setup_gui(self):
        # Main container
        main_container = CTkFrame(self.root, fg_color=self.colors['bg_primary'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configure grid weights
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(0, weight=1)
        
        # Sidebar
        self.setup_sidebar(main_container)
        
        # Main content area
        self.setup_main_content(main_container)
        
        # Display welcome message
        self.display_welcome()
        
    def setup_sidebar(self, parent):
        sidebar = CTkFrame(parent, fg_color=self.colors['bg_secondary'], width=200)
        sidebar.pack_propagate(False)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        sidebar.grid_propagate(False)
        
        # Logo/Title area
        logo_frame = CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=20)
        
        CTkLabel(logo_frame, text="🤖", font=('Arial', 24), 
                text_color=self.colors['text_primary']).pack()
        CTkLabel(logo_frame, text="Edgar AI", font=('Arial', 18, 'bold'),
                text_color=self.colors['text_primary']).pack(pady=(5, 0))
        CTkLabel(logo_frame, text="Classic Theme", 
                font=('Arial', 11), text_color=self.colors['text_secondary']).pack()
        
        # MODEL SELECTION DROPDOWN
        model_frame = CTkFrame(sidebar, fg_color="transparent")
        model_frame.pack(fill="x", padx=20, pady=(15, 0))
        
        CTkLabel(model_frame, text="MODEL", font=('Arial', 11),
                text_color=self.colors['text_secondary']).pack(anchor='w')
        
        # Get available models
        self.available_models = self.get_available_models()
        
        # Create dropdown with classic styling
        self.model_var = StringVar()
        self.model_dropdown = CTkComboBox(
            model_frame,
            variable=self.model_var,
            values=self.available_models,
            state="readonly",
            dropdown_fg_color=self.colors['bg_tertiary'],
            dropdown_text_color=self.colors['text_primary'],
            dropdown_hover_color=self.colors['hover_secondary'],
            button_color=self.colors['accent_primary'],
            button_hover_color=self.colors['hover_primary'],
            fg_color=self.colors['input_bg'],
            border_color=self.colors['border'],
            text_color=self.colors['text_primary']
        )
        
        self.model_dropdown.pack(fill="x", pady=(5, 0))
        
        # Set current model if available
        if self.available_models:
            current_model = self.streaming_layer.get_current_model()
            if current_model in self.available_models:
                self.model_var.set(current_model)
            else:
                self.model_var.set(self.available_models[0])
                self.change_model(self.available_models[0])
        
        # Bind selection event
        self.model_dropdown.bind('<<ComboboxSelected>>', self.on_model_selected)
        
        # Separator
        separator = CTkFrame(sidebar, fg_color=self.colors['border'], height=2)
        separator.pack(fill="x", padx=20, pady=10)
        
        # Controls section
        controls_frame = CTkFrame(sidebar, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        CTkLabel(controls_frame, text="CONTROLS", font=('Arial', 11),
                text_color=self.colors['text_secondary']).pack(anchor='w')
        
        # Control buttons
        controls = [
            ("🧠 Context", self.show_context),
            ("📊 Statistics", self.show_statistics),
            ("🔄 New Chat", self.reset_chat),
            ("🔄 Refresh Models", self.refresh_models),
            ("⚙️ Settings", self.show_settings),
            ("❓ Help", self.show_help)
        ]
        
        for text, command in controls:
            btn = CTkButton(controls_frame, text=text, command=command,
                          fg_color=self.colors['bg_tertiary'],
                          hover_color=self.colors['hover_secondary'],
                          text_color=self.colors['text_primary'],
                          font=('Arial', 9))
            btn.pack(fill="x", pady=5)
        
        # Status section
        status_frame = CTkFrame(sidebar, fg_color="transparent")
        status_frame.pack(fill="x", side="bottom", padx=20, pady=20)
        
        CTkLabel(status_frame, text="STATUS", font=('Arial', 11),
                text_color=self.colors['text_secondary']).pack(anchor='w')
        
        self.status_var = StringVar()
        self.status_var.set("Ready to assist")
        CTkLabel(status_frame, textvariable=self.status_var, 
                font=('Arial', 9), text_color=self.colors['text_secondary']).pack(anchor='w', pady=(5, 0))
        
    def on_model_selected(self, event):
        """Handle model selection from dropdown"""
        selected_model = self.model_var.get()
        if selected_model and selected_model in self.available_models:
            self.change_model(selected_model)

    def change_model(self, model_name):
        """Change the current model using streaming layer"""
        try:
            success = self.streaming_layer.change_model(model_name)
            
            if success:
                # Add system message
                self.add_message("system", f"✅ Switched to model: {model_name}")
                
                # Show model info
                group_count = self.streaming_layer.get_qa_groups_count()
                self.add_message("system", f"📊 Model contains {group_count} QA groups")
            else:
                self.status_var.set("Model load failed")
                
        except Exception as e:
            error_msg = f"Error loading model {model_name}: {str(e)}"
            self.status_var.set("Model load failed")
            self.add_message("error", error_msg)
            CTkMessagebox.show_error("Model Error", error_msg)

    def refresh_models(self):
        """Refresh the list of available models using streaming layer"""
        try:
            previous_models = set(self.available_models)
            self.available_models = self.streaming_layer.refresh_models()
            current_models = set(self.available_models)
            
            # Update dropdown
            self.model_dropdown.configure(values=self.available_models)
            
            # Check for changes
            new_models = current_models - previous_models
            removed_models = previous_models - current_models
            
            if new_models:
                self.add_message("system", f"✅ New models detected: {', '.join(new_models)}")
            if removed_models:
                self.add_message("system", f"❌ Models removed: {', '.join(removed_models)}")
            
            if not new_models and not removed_models:
                self.add_message("system", "✅ Model list is up to date")
            
            self.status_var.set(f"Models refreshed: {len(self.available_models)} available")
            
        except Exception as e:
            self.add_message("error", f"Error refreshing models: {str(e)}")
        
    def setup_main_content(self, parent):
        main_content = CTkFrame(parent, fg_color=self.colors['bg_primary'])
        main_content.grid(row=0, column=1, sticky="nsew")
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(0, weight=1)  # Chat display
        main_content.rowconfigure(1, weight=0)  # Quick actions
        main_content.rowconfigure(2, weight=0)  # Input area
        
        # Chat display area
        chat_frame = CTkFrame(main_content, fg_color=self.colors['bg_primary'])
        chat_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        # Create text widget with custom styling to match classic theme
        self.chat_display = CTkTextbox(
            chat_frame,
            wrap="word",
            width=80,
            height=25,
            font=('Arial', 11),
            fg_color=self.colors['bg_primary'],
            text_color=self.colors['text_primary'],
            border_width=0,
            scrollbar_button_color=self.colors['scrollbar_slider'],
            scrollbar_button_hover_color=self.colors['scrollbar_hover']
        )
        
        # Configure tags for different message types using the underlying tkinter text widget
        self.text_widget = self.chat_display._textbox
        
        # User messages (RIGHT-ALIGNED)
        self.text_widget.tag_config('user_timestamp', 
                                   foreground=self.colors['text_tertiary'],
                                   justify='right')
        self.text_widget.tag_config('user_header', 
                                   foreground=self.colors['accent_secondary'],
                                   justify='right')
        self.text_widget.tag_config('user_msg', 
                                   foreground=self.colors['text_primary'],
                                   justify='right')
        
        # Bot messages (LEFT-ALIGNED)  
        self.text_widget.tag_config('bot_timestamp', 
                                   foreground=self.colors['text_tertiary'],
                                   justify='left')
        self.text_widget.tag_config('bot_header', 
                                   foreground=self.colors['accent_primary'],
                                   justify='left')
        self.text_widget.tag_config('bot_msg', 
                                   foreground=self.colors['text_primary'],
                                   justify='left')
        
        self.text_widget.tag_config('system', 
                                   foreground=self.colors['text_secondary'],
                                   justify='center')
        self.text_widget.tag_config('thinking', 
                                   foreground=self.colors['accent_warning'],
                                   justify='left')
        self.text_widget.tag_config('context', 
                                   foreground=self.colors['accent_success'],
                                   justify='left')
        self.text_widget.tag_config('stats', 
                                   foreground=self.colors['accent_secondary'],
                                   justify='left')
        self.text_widget.tag_config('error', 
                                   foreground=self.colors['accent_error'],
                                   justify='left')
        self.text_widget.tag_config('separator', 
                                   foreground=self.colors['border'],
                                   justify='center')
        
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        
        # Create thinking animation label (initially hidden)
        self.thinking_label = CTkLabel(
            chat_frame,
            text="",
            font=('Arial', 10, 'italic'),
            text_color=self.colors['accent_warning'],
            justify='left'
        )
        self.thinking_label.grid(row=1, column=0, sticky='w', padx=20, pady=(0, 10))
        self.thinking_label.grid_remove()  # Hide initially
        
        # Quick actions
        quick_actions_frame = CTkFrame(main_content, fg_color="transparent")
        quick_actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        quick_actions = [
            ("Tell me more", "tell me more"),
            ("About Python", "tell me more about Python"),
            ("What is AI?", "what is artificial intelligence?"),
            ("Reset chat", "reset")
        ]
        
        for i, (label, command) in enumerate(quick_actions):
            btn = CTkButton(quick_actions_frame, text=label, 
                          command=lambda cmd=command: self.quick_action(cmd),
                          fg_color=self.colors['bg_tertiary'],
                          hover_color=self.colors['hover_secondary'],
                          text_color=self.colors['text_primary'],
                          font=('Arial', 9))
            btn.grid(row=0, column=i, padx=(0, 10))
        
        # Input area
        input_frame = CTkFrame(main_content, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        
        # User input with icon
        input_container = CTkFrame(input_frame, fg_color=self.colors['bg_tertiary'])
        input_container.pack(fill="x", side="left", expand=True)
        input_container.columnconfigure(0, weight=1)
        
        self.user_input = CTkEntry(
            input_container,
            font=('Arial', 12),
            placeholder_text="Type your message here...",
            fg_color=self.colors['input_bg'],
            text_color=self.colors['text_primary'],
            border_color=self.colors['border'],
            placeholder_text_color=self.colors['text_tertiary']
        )
        self.user_input.grid(row=0, column=0, sticky="ew", padx=(10, 10), pady=10)
        self.user_input.bind('<Return>', lambda e: self.send_message())
        
        # Send button
        self.send_button = CTkButton(
            input_container,
            text="Send →",
            command=self.send_message,
            fg_color=self.colors['accent_primary'],
            hover_color=self.colors['hover_primary'],
            text_color=self.colors['text_primary'],
            font=('Arial', 10, 'bold')
        )
        self.send_button.grid(row=0, column=1, padx=(0, 10), pady=10)
        
        # Focus on input field
        self.user_input.focus()
    
    def start_thinking_animation(self):
        """Start the thinking animation (only when verbose mode is off)"""
        if self.verbose_mode or self.thinking_animation_active:
            return
            
        self.thinking_animation_active = True
        self.thinking_dots = 0
        self.thinking_label.grid()  # Show the label
        self._update_thinking_animation()
    
    def _update_thinking_animation(self):
        """Update the thinking animation dots"""
        if not self.thinking_animation_active:
            return
            
        self.thinking_dots = (self.thinking_dots + 1) % 4
        dots = "." * self.thinking_dots
        self.thinking_label.configure(text=f"Thinking{dots}")
        
        # Schedule next update
        self.thinking_animation_job = self.root.after(500, self._update_thinking_animation)
    
    def stop_thinking_animation(self):
        """Stop the thinking animation"""
        self.thinking_animation_active = False
        if self.thinking_animation_job:
            self.root.after_cancel(self.thinking_animation_job)
            self.thinking_animation_job = None
        self.thinking_label.grid_remove()  # Hide the label
        self.thinking_label.configure(text="")
    
    def quick_action(self, action):
        if action == "reset":
            self.reset_chat()
        else:
            self.user_input.delete(0, "end")
            self.user_input.insert(0, action)
            self.send_message()
    
    def display_welcome(self):
        current_model = self.streaming_layer.get_current_model()
        group_count = self.streaming_layer.get_qa_groups_count()
        
        welcome_text = f"""🌟 Welcome to Edgar AI Assistant - Classic Theme

Current Model: {current_model}
Knowledge Base: {group_count} QA groups

I'm your intelligent companion designed to help with programming, 
AI concepts, game development, and much more.

I remember our conversations and can provide detailed explanations 
when you ask me to "tell me more" about any topic.

How can I assist you today?"""
        
        self.add_message("system", welcome_text)
    
    def add_message(self, sender, message, tag=None):
        self.chat_display.configure(state="normal")
        
        timestamp = time.strftime("%H:%M")
        current_model = self.streaming_layer.get_current_model()
        
        if sender == "user":
            # User message - RIGHT ALIGNED
            self.text_widget.insert("end", f"\n")
            self.text_widget.insert("end", f"[{timestamp}] ", 'user_timestamp')
            self.text_widget.insert("end", "You: ", 'user_header')
            self.text_widget.insert("end", f"{message}\n", 'user_msg')
            
        elif sender == "bot":
            # Bot message - LEFT ALIGNED  
            self.text_widget.insert("end", f"\n")
            self.text_widget.insert("end", f"[{timestamp}] ", 'bot_timestamp')
            self.text_widget.insert("end", f"{current_model}: ", 'bot_header')
            self.text_widget.insert("end", f"{message}\n", 'bot_msg')
            
        elif sender == "system":
            self.text_widget.insert("end", f"\n{message}\n", 'system')
        elif sender == "thinking":
            self.text_widget.insert("end", f"{message}", 'thinking')
        elif sender == "context":
            self.text_widget.insert("end", f"🔍 {message}\n", 'context')
        elif sender == "stats":
            self.text_widget.insert("end", f"📈 {message}\n", 'stats')
        elif sender == "error":
            self.text_widget.insert("end", f"⚠️ {message}\n", 'error')
        elif sender == "match_info":
            self.text_widget.insert("end", f"{message}\n", 'system')
        elif sender == "correction":
            self.text_widget.insert("end", f"{message}\n", 'system')
        
        self.chat_display.configure(state="disabled")
        self.text_widget.see("end")
    
    def send_message(self):
        user_text = self.user_input.get().strip()
        if not user_text or self.is_processing:
            return
        
        # Clear input field and disable input
        self.user_input.delete(0, "end")
        self.user_input.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.is_processing = True
        self.status_var.set("Processing your message...")
        
        # Display user message
        self.add_message("user", user_text)
        
        # Start thinking animation if verbose mode is off
        if not self.verbose_mode:
            self.start_thinking_animation()
        
        # Process message in separate thread to keep GUI responsive
        threading.Thread(target=self.process_message, args=(user_text,), daemon=True).start()
    
    def process_message(self, user_text):
        try:
            # Show thinking indicator only in verbose mode
            if self.verbose_mode:
                self.root.after(0, lambda: self.add_message("thinking", "🤔 Processing your request..."))
            
            # Process the message using the streaming layer
            responses = self.streaming_layer.process_message(user_text)
            
            # Stop thinking animation if it's running
            if not self.verbose_mode:
                self.root.after(0, self.stop_thinking_animation)
            
            # Clear thinking indicator if shown
            if self.verbose_mode:
                self.chat_display.configure(state="normal")
                self.text_widget.delete("end-2l", "end-1l")
                self.chat_display.configure(state="disabled")
            
            # Check if we got any responses
            if not responses:
                self.root.after(0, lambda: self.add_message("bot", "I'm not sure how to respond to that. Could you try rephrasing your question?"))
                self.root.after(0, self.processing_complete)
                return
            
            # Update GUI with responses using proper streaming
            self.root.after(0, lambda: self.display_responses_with_streaming(responses))
            
        except Exception as e:
            # Stop thinking animation on error
            if not self.verbose_mode:
                self.root.after(0, self.stop_thinking_animation)
                
            self.root.after(0, lambda: self.add_message("error", f"An error occurred: {str(e)}"))
            self.root.after(0, self.processing_complete)
    
    def display_responses_with_streaming(self, responses):
        """Display responses using the streaming layer"""
        def show_additional_info_and_continue(current_index):
            """Show context after streaming completes (only in verbose mode)"""
            # Show context summary if available and in verbose mode
            if self.verbose_mode:
                context_summary = self.streaming_layer.get_context_summary()
                if context_summary and context_summary != "Minimal context":
                    self.add_message("context", context_summary)
            
            # Move to next response
            self.root.after(100, lambda: stream_next_response(current_index + 1))
        
        def stream_next_response(index=0):
            if index >= len(responses):
                # All responses processed
                self.root.after(100, self.processing_complete)
                return
            
            # Handle both response formats (AI engine vs module routing)
            response = responses[index]
            
            # Check response format and unpack accordingly
            if len(response) == 6:
                # AI Engine format: (original_question, answer, confidence, corrections, matched_group, match_type)
                original_question, answer, confidence, corrections, matched_group, match_type = response
                
                # Show corrections if any and in verbose mode
                if self.verbose_mode and corrections:
                    best_correction, best_score = corrections[0]
                    correction_text = f"Auto-corrected to: '{best_correction}' (confidence: {best_score}%)"
                    self.add_message("correction", correction_text)
                    
                # Show match information for AI engine responses (only in verbose mode)
                if self.verbose_mode and matched_group and confidence > 0 and match_type != "follow_up":
                    match_type_display = {
                        "exact": "🎯 Exact match",
                        "high_confidence": "✅ High confidence", 
                        "medium_confidence": "⚠️ Medium confidence",
                        "low_confidence": "🔍 Low confidence",
                        "semantic": "🧠 Semantic match",
                        "unknown": "❓ Unknown question"
                    }
                    display_type = match_type_display.get(match_type, match_type)
                    match_info = f"{display_type} (confidence: {confidence:.2f})"
                    self.add_message("match_info", match_info)
                    
            elif len(response) == 3:
                # Module routing format: (answer, confidence, source)
                answer, confidence, source = response
                
                # Show module routing info (only in verbose mode)
                if self.verbose_mode:
                    self.add_message("match_info", f"🔄: {source} (confidence: {confidence:.2f})")
                
            else:
                # Unknown format, try to handle gracefully
                print(f"⚠️ Unexpected response format: {response}")
                if len(response) >= 1:
                    answer = response[0] if isinstance(response[0], str) else str(response[0])
                else:
                    answer = "No response received"
                confidence = 0.0
            
            # Display the answer using streaming
            if answer:
                # Add bot message header
                timestamp = time.strftime("%H:%M")
                current_model = self.streaming_layer.get_current_model()
                self.chat_display.configure(state="normal")
                self.text_widget.insert("end", f"\n")
                self.text_widget.insert("end", f"[{timestamp}] ", 'bot_timestamp')
                self.text_widget.insert("end", f"{current_model}: ", 'bot_header')
                self.chat_display.configure(state="disabled")
                
                # Stream the response using the streaming layer
                def stream_response():
                    self.streaming_layer.stream_text(
                        answer, 
                        "",  # No prefix since we already added the header
                        self.streaming_layer.streaming_speed
                    )
                    
                    # After streaming completes, show additional info and move to next response
                    self.root.after(100, lambda: show_additional_info_and_continue(index))
                
                # Start streaming in a separate thread
                threading.Thread(target=stream_response, daemon=True).start()
            else:
                # No answer, move to next response immediately
                self.root.after(100, lambda: stream_next_response(index + 1))
        
        # Start streaming the first response
        stream_next_response()
    
    def stream_to_display(self, text):
        """Stream text to the main display"""
        self.chat_display.configure(state="normal")
        self.text_widget.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.text_widget.see("end")
    
    def processing_complete(self):
        """Called when message processing is complete"""
        self.is_processing = False
        self.user_input.configure(state="normal")
        self.send_button.configure(state="normal")
        self.status_var.set("Ready to assist")
        self.user_input.focus()
    
    def show_context(self):
        """Display current conversation context"""
        context_summary = self.streaming_layer.get_context_summary()
        self.add_message("system", f"Current Context: {context_summary}")
    
    def show_statistics(self):
        """Display chatbot statistics"""
        stats = self.streaming_layer.get_statistics()
        total = stats['total_questions']
        
        if total == 0:
            self.add_message("stats", "No questions processed yet.")
            return
        
        success_rate = stats['successful_matches'] / total
        
        stats_text = f"""Conversation Statistics:
• Total questions: {total}
• Success rate: {success_rate:.1%}
• Follow-up requests: {stats['follow_up_requests']}
• Tree entries: {stats['tree_entries']}"""
        
        self.add_message("stats", stats_text)
    
    def reset_chat(self):
        """Reset the conversation"""
        # Use CTkMessagebox for consistency
        if CTkMessagebox.ask_yesno("New Chat", "Start a new conversation? Current context will be cleared."):
            # Save current model
            current_model = self.streaming_layer.get_current_model()
            
            # Reset conversation context using streaming layer
            self.streaming_layer.reset_conversation()
            
            # Clear chat display
            self.chat_display.configure(state="normal")
            self.text_widget.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            
            # Show welcome message again
            self.display_welcome()
            
            # Update status with model info
            if current_model:
                self.status_var.set(f"New chat started - Model: {current_model}")
            else:
                self.status_var.set("New chat started")
    
    def show_settings(self):
        """Show settings dialog using the new settings window"""
        try:
            open_settings(self.root)
        except Exception as e:
            CTkMessagebox.show_error("Error", f"Cannot open settings: {e}")
    
    def show_help(self):
        """Show help information"""
        help_text = """🤖 Edgar AI Assistant - Classic Theme - Help

Quick Commands:
• 'tell me more' - Get detailed information
• 'tell me more about [topic]' - Specific details
• Ask about programming, AI, game development

Features:
• Context-aware conversations
• Intelligent question matching
• Detailed follow-up information
• Conversation statistics
• Real-time text streaming
• Model selection dropdown

Tips:
• Use the quick action buttons for common questions
• The assistant maintains context across messages
• Press Enter to send messages quickly
• Switch models using the dropdown in the sidebar"""

        CTkMessagebox.show_info("Assistant Help", help_text)

# Custom messagebox implementation for CTk
class CTkMessagebox:
    @staticmethod
    def show_error(title, message):
        # For now, use tkinter messagebox as fallback
        # In a production app, you'd create a custom CTk dialog
        import tkinter.messagebox as mb
        mb.showerror(title, message)
    
    @staticmethod
    def show_info(title, message):
        import tkinter.messagebox as mb
        mb.showinfo(title, message)
    
    @staticmethod
    def ask_yesno(title, message):
        import tkinter.messagebox as mb
        return mb.askyesno(title, message)

def main():
    try:
        # Create root window
        root = CTk()
        
        app = ClassicChatbotGUI(root)
        
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        CTkMessagebox.show_error("Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()