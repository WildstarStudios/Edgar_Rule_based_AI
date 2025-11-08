import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import sys
import os
import configparser

# Add the directory containing ai_engine.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_engine import AdvancedChatbot
    print("✅ Successfully imported AdvancedChatbot from ai_engine.py")
except ImportError as e:
    print(f"❌ Error importing AdvancedChatbot: {e}")
    print("Please make sure ai_engine.py is in the same directory")
    sys.exit(1)

class MiniChatWindow:
    def __init__(self, parent, chatbot, main_chat_display, main_add_message_method):
        self.parent = parent
        self.chatbot = chatbot
        self.main_chat_display = main_chat_display
        self.main_add_message = main_add_message_method
        self.is_processing = False
        
        # Color scheme (same as main window)
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
            'hover_primary': '#5750d3',
            'hover_secondary': '#35356a'
        }
        
        self.setup_mini_window()
    
    def setup_mini_window(self):
        # Create mini window
        self.mini_window = tk.Toplevel(self.parent)
        self.mini_window.title("Edgar Mini")
        self.mini_window.geometry("400x500")
        self.mini_window.configure(bg=self.colors['bg_primary'])
        self.mini_window.resizable(True, True)
        
        # Make window always on top
        self.mini_window.attributes('-topmost', True)
        
        # Set window position (top-right corner)
        self.mini_window.geometry("+{}+{}".format(
            self.mini_window.winfo_screenwidth() - 450,
            50
        ))
        
        # Mini window header
        header_frame = tk.Frame(self.mini_window, bg=self.colors['bg_secondary'])
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(header_frame, text="🤖 Edgar Mini", 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Restore button
        restore_btn = tk.Button(header_frame, text="↗️ Restore", 
                              command=self.restore_main_window,
                              bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                              font=('Arial', 8), relief='flat', bd=0, padx=8, pady=4,
                              activebackground=self.colors['hover_secondary'])
        restore_btn.pack(side=tk.RIGHT)
        
        # Chat display for mini window
        self.mini_chat_display = scrolledtext.ScrolledText(
            self.mini_window,
            wrap=tk.WORD,
            width=45,
            height=20,
            font=('Arial', 9),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['accent_secondary'],
            selectbackground=self.colors['accent_primary'],
            borderwidth=0,
            relief='flat',
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.mini_chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Configure tags for mini window
        self.mini_chat_display.tag_config('user_timestamp', 
                                        foreground=self.colors['text_tertiary'],
                                        justify='right',
                                        font=('Arial', 7))
        self.mini_chat_display.tag_config('user_header', 
                                        foreground=self.colors['accent_secondary'],
                                        justify='right',
                                        font=('Arial', 8, 'bold'))
        self.mini_chat_display.tag_config('user_msg', 
                                        foreground=self.colors['text_primary'],
                                        justify='right',
                                        font=('Arial', 9))
        
        self.mini_chat_display.tag_config('bot_timestamp', 
                                        foreground=self.colors['text_tertiary'],
                                        justify='left',
                                        font=('Arial', 7))
        self.mini_chat_display.tag_config('bot_header', 
                                        foreground=self.colors['accent_primary'],
                                        justify='left',
                                        font=('Arial', 8, 'bold'))
        self.mini_chat_display.tag_config('bot_msg', 
                                        foreground=self.colors['text_primary'],
                                        justify='left',
                                        font=('Arial', 9))
        
        self.mini_chat_display.tag_config('system', 
                                        foreground=self.colors['text_secondary'],
                                        justify='center',
                                        font=('Arial', 8, 'italic'))
        self.mini_chat_display.tag_config('thinking', 
                                        foreground=self.colors['accent_warning'],
                                        justify='left',
                                        font=('Arial', 8, 'italic'))
        self.mini_chat_display.tag_config('context', 
                                        foreground=self.colors['accent_success'],
                                        justify='left',
                                        font=('Arial', 7))
        self.mini_chat_display.tag_config('stats', 
                                        foreground=self.colors['accent_secondary'],
                                        justify='left',
                                        font=('Arial', 7))
        self.mini_chat_display.tag_config('error', 
                                        foreground=self.colors['accent_error'],
                                        justify='left',
                                        font=('Arial', 8))
        self.mini_chat_display.tag_config('separator', 
                                        foreground=self.colors['border'],
                                        justify='center',
                                        font=('Arial', 7))
        self.mini_chat_display.tag_config('match_info', 
                                        foreground=self.colors['accent_warning'],
                                        justify='left',
                                        font=('Arial', 7))
        self.mini_chat_display.tag_config('correction', 
                                        foreground=self.colors['accent_secondary'],
                                        justify='left',
                                        font=('Arial', 7))
        
        # Quick actions for mini window
        quick_frame = tk.Frame(self.mini_window, bg=self.colors['bg_primary'])
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        quick_actions = ["Help", "Python", "AI", "More"]
        commands = [
            "help", 
            "tell me more about Python", 
            "what is artificial intelligence?", 
            "tell me more"
        ]
        
        for i, (text, cmd) in enumerate(zip(quick_actions, commands)):
            btn = tk.Button(quick_frame, text=text, 
                          command=lambda c=cmd: self.quick_mini_action(c),
                          bg=self.colors['bg_tertiary'],
                          fg=self.colors['text_primary'],
                          font=('Arial', 8),
                          relief='flat',
                          bd=0,
                          padx=8,
                          pady=4,
                          activebackground=self.colors['hover_secondary'])
            btn.grid(row=0, column=i, padx=(0, 5))
        
        # Input area for mini window
        input_frame = tk.Frame(self.mini_window, bg=self.colors['bg_tertiary'])
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        self.mini_user_input = tk.Entry(
            input_frame,
            font=('Arial', 10),
            bg=self.colors['input_bg'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightcolor=self.colors['accent_primary']
        )
        self.mini_user_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(8, 8), pady=8)
        self.mini_user_input.bind('<Return>', lambda e: self.send_mini_message())
        
        self.mini_send_button = tk.Button(
            input_frame,
            text="➤",
            command=self.send_mini_message,
            bg=self.colors['accent_primary'],
            fg=self.colors['text_primary'],
            font=('Arial', 9, 'bold'),
            relief='flat',
            bd=0,
            padx=12,
            pady=8,
            activebackground=self.colors['hover_primary']
        )
        self.mini_send_button.grid(row=0, column=1, padx=(0, 8), pady=8)
        
        # Copy chat history from main window to mini window
        self.copy_chat_history_to_mini()
        
        # Handle window close
        self.mini_window.protocol("WM_DELETE_WINDOW", self.restore_main_window)
        
        self.mini_user_input.focus()
    
    def copy_chat_history_to_mini(self):
        """Copy chat history from main window to mini window with proper styling"""
        try:
            # Get all text from main chat display
            main_text = self.main_chat_display.get(1.0, tk.END)
            if main_text.strip():
                self.mini_chat_display.config(state=tk.NORMAL)
                self.mini_chat_display.delete(1.0, tk.END)
                self.mini_chat_display.insert(tk.END, main_text)
                
                # Apply tags based on content patterns
                self.apply_tags_to_mini_display()
                self.mini_chat_display.config(state=tk.DISABLED)
                self.mini_chat_display.see(tk.END)
            else:
                self.add_mini_message("system", "🌟 Edgar Mini Assistant\nAlways on top for quick help!")
        except Exception as e:
            self.add_mini_message("system", "🌟 Edgar Mini Assistant\nAlways on top for quick help!")
    
    def apply_tags_to_mini_display(self):
        """Apply proper tags to mini window display based on content patterns"""
        text_content = self.mini_chat_display.get(1.0, tk.END)
        lines = text_content.split('\n')
        
        self.mini_chat_display.config(state=tk.NORMAL)
        self.mini_chat_display.delete(1.0, tk.END)
        
        for line in lines:
            if not line.strip():
                continue
                
            if "You:" in line:
                # User message - right aligned
                parts = line.split("You:", 1)
                if len(parts) == 2:
                    timestamp_part = parts[0].strip()
                    message_part = parts[1].strip()
                    self.mini_chat_display.insert(tk.END, f"\n", 'system')
                    self.mini_chat_display.insert(tk.END, f"{timestamp_part} ", 'user_timestamp')
                    self.mini_chat_display.insert(tk.END, "You: ", 'user_header')
                    self.mini_chat_display.insert(tk.END, f"{message_part}\n", 'user_msg')
                    self.mini_chat_display.insert(tk.END, "─" * 40 + "\n", 'separator')
            elif "Edgar:" in line:
                # Bot message - left aligned
                parts = line.split("Edgar:", 1)
                if len(parts) == 2:
                    timestamp_part = parts[0].strip()
                    message_part = parts[1].strip()
                    self.mini_chat_display.insert(tk.END, f"\n", 'system')
                    self.mini_chat_display.insert(tk.END, f"{timestamp_part} ", 'bot_timestamp')
                    self.mini_chat_display.insert(tk.END, "Edgar: ", 'bot_header')
                    self.mini_chat_display.insert(tk.END, f"{message_part}\n", 'bot_msg')
                    self.mini_chat_display.insert(tk.END, "─" * 40 + "\n", 'separator')
            elif any(keyword in line for keyword in ["🎯", "✅", "⚠️", "🔍", "🧠", "❓"]):
                # Match information
                self.mini_chat_display.insert(tk.END, f"{line}\n", 'match_info')
            elif "Auto-corrected" in line:
                # Correction information
                self.mini_chat_display.insert(tk.END, f"{line}\n", 'correction')
            elif "🔍" in line or "Context:" in line:
                # Context information
                self.mini_chat_display.insert(tk.END, f"{line}\n", 'context')
            elif "📈" in line or "Statistics:" in line:
                # Stats information
                self.mini_chat_display.insert(tk.END, f"{line}\n", 'stats')
            elif "🤔" in line:
                # Thinking indicator
                self.mini_chat_display.insert(tk.END, f"{line}\n", 'thinking')
            elif "⚠️" in line and "Error" in line:
                # Error message
                self.mini_chat_display.insert(tk.END, f"{line}\n", 'error')
            else:
                # System message
                self.mini_chat_display.insert(tk.END, f"{line}\n", 'system')
        
        self.mini_chat_display.config(state=tk.DISABLED)
    
    def add_mini_message(self, sender, message, tag=None):
        """Add message to mini window with proper alignment and styling"""
        self.mini_chat_display.config(state=tk.NORMAL)
        
        timestamp = time.strftime("%H:%M")
        
        if sender == "user":
            # User message - RIGHT ALIGNED
            self.mini_chat_display.insert(tk.END, f"\n", 'system')
            self.mini_chat_display.insert(tk.END, f"[{timestamp}] ", 'user_timestamp')
            self.mini_chat_display.insert(tk.END, "You: ", 'user_header')
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'user_msg')
            self.mini_chat_display.insert(tk.END, "─" * 40 + "\n", 'separator')
            
        elif sender == "bot":
            # Bot message - LEFT ALIGNED
            self.mini_chat_display.insert(tk.END, f"\n", 'system')
            self.mini_chat_display.insert(tk.END, f"[{timestamp}] ", 'bot_timestamp')
            self.mini_chat_display.insert(tk.END, "Edgar: ", 'bot_header')
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'bot_msg')
            self.mini_chat_display.insert(tk.END, "─" * 40 + "\n", 'separator')
            
        elif sender == "system":
            self.mini_chat_display.insert(tk.END, f"\n{message}\n", 'system')
        elif sender == "thinking":
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'thinking')
        elif sender == "context":
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'context')
        elif sender == "stats":
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'stats')
        elif sender == "error":
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'error')
        elif sender == "match_info":
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'match_info')
        elif sender == "correction":
            self.mini_chat_display.insert(tk.END, f"{message}\n", 'correction')
        
        self.mini_chat_display.config(state=tk.DISABLED)
        self.mini_chat_display.see(tk.END)
        
        # Also update main window
        self.parent.after(0, lambda: self.main_add_message(sender, message, tag))
    
    def send_mini_message(self):
        user_text = self.mini_user_input.get().strip()
        if not user_text or self.is_processing:
            return
        
        # Clear input field
        self.mini_user_input.delete(0, tk.END)
        self.mini_send_button.config(state=tk.DISABLED)
        self.is_processing = True
        
        # Display user message in both windows
        self.add_mini_message("user", user_text)
        
        # Process message in separate thread
        threading.Thread(target=self.process_mini_message, args=(user_text,), daemon=True).start()
    
    def process_mini_message(self, user_text):
        try:
            # Show thinking indicator
            self.mini_window.after(0, lambda: self.add_mini_message("thinking", "🤔 Processing your request..."))
            
            # Process the message using the chatbot
            responses = self.chatbot.process_multiple_questions(user_text)
            
            # Clear thinking indicator
            self.mini_chat_display.config(state=tk.NORMAL)
            self.mini_chat_display.delete("end-2l", "end-1l")
            self.mini_chat_display.config(state=tk.DISABLED)
            
            # Update both windows with responses
            self.mini_window.after(0, lambda: self.display_mini_responses(responses))
            
        except Exception as e:
            self.mini_window.after(0, lambda: self.add_mini_message("error", f"An error occurred: {str(e)}"))
        finally:
            self.mini_window.after(0, self.mini_processing_complete)
    
    def display_mini_responses(self, responses):
        """Display chatbot responses in the GUI with all extra information"""
        for i, (original_question, answer, confidence, corrections, matched_question, match_type) in enumerate(responses, 1):
            
            # Show corrections if any
            if corrections:
                best_correction, best_score = corrections[0]
                correction_text = f"Auto-corrected to: '{best_correction}' (confidence: {best_score}%)"
                self.add_mini_message("correction", correction_text)
            
            # Display the answer using the chatbot's streaming
            if self.chatbot.streaming_speed > 0:
                # Use streaming for the answer
                self.add_mini_message("thinking", "💬 Streaming response...")
                self.mini_chat_display.config(state=tk.NORMAL)
                self.mini_chat_display.delete("end-2l", "end-1l")  # Remove thinking indicator
                self.mini_chat_display.config(state=tk.DISABLED)
                
                # Stream the response
                self.chatbot.stream_text(
                    answer, 
                    "🤖 ", 
                    self.chatbot.streaming_speed,
                    callback=lambda x: self.mini_window.after(0, lambda: self.stream_to_mini_display(x))
                )
            else:
                # Display immediately without streaming
                self.add_mini_message("bot", answer)
            
            # Show match information
            if matched_question and confidence > 0 and match_type != "follow_up":
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
                self.add_mini_message("match_info", match_info)
            
            # Show context summary if available
            context_summary = self.chatbot.get_context_summary()
            if context_summary and context_summary != "Minimal context":
                self.add_mini_message("context", context_summary)
    
    def stream_to_mini_display(self, text):
        """Stream text to mini display"""
        self.mini_chat_display.config(state=tk.NORMAL)
        self.mini_chat_display.insert(tk.END, text)
        self.mini_chat_display.config(state=tk.DISABLED)
        self.mini_chat_display.see(tk.END)
    
    def mini_processing_complete(self):
        self.is_processing = False
        self.mini_send_button.config(state=tk.NORMAL)
        self.mini_user_input.focus()
    
    def quick_mini_action(self, action):
        if action == "help":
            help_text = """Quick Commands:
• Ask about programming, AI, gaming
• Use 'tell me more' for details
• Type 'restore' for full window"""
            self.add_mini_message("system", help_text)
        else:
            self.mini_user_input.delete(0, tk.END)
            self.mini_user_input.insert(0, action)
            self.send_mini_message()
    
    def restore_main_window(self):
        # Copy mini window content back to main window before closing
        self.copy_mini_history_to_main()
        self.mini_window.destroy()
        self.parent.deiconify()  # Restore main window
        self.parent.lift()       # Bring to front
        self.parent.focus_force()
    
    def copy_mini_history_to_main(self):
        """Copy chat history from mini window back to main window with proper styling"""
        try:
            # Get all text from mini chat display
            mini_text = self.mini_chat_display.get(1.0, tk.END)
            if mini_text.strip():
                # Clear and rebuild main window with updated content
                self.main_chat_display.config(state=tk.NORMAL)
                self.main_chat_display.delete(1.0, tk.END)
                
                lines = mini_text.split('\n')
                for line in lines:
                    if not line.strip():
                        continue
                        
                    if "You:" in line:
                        # User message - right aligned
                        parts = line.split("You:", 1)
                        if len(parts) == 2:
                            timestamp_part = parts[0].strip()
                            message_part = parts[1].strip()
                            self.main_chat_display.insert(tk.END, f"\n", 'system')
                            self.main_chat_display.insert(tk.END, f"{timestamp_part} ", 'user_timestamp')
                            self.main_chat_display.insert(tk.END, "You: ", 'user_header')
                            self.main_chat_display.insert(tk.END, f"{message_part}\n", 'user_msg')
                            self.main_chat_display.insert(tk.END, "─" * 60 + "\n", 'separator')
                    elif "Edgar:" in line:
                        # Bot message - left aligned
                        parts = line.split("Edgar:", 1)
                        if len(parts) == 2:
                            timestamp_part = parts[0].strip()
                            message_part = parts[1].strip()
                            self.main_chat_display.insert(tk.END, f"\n", 'system')
                            self.main_chat_display.insert(tk.END, f"{timestamp_part} ", 'bot_timestamp')
                            self.main_chat_display.insert(tk.END, "Edgar: ", 'bot_header')
                            self.main_chat_display.insert(tk.END, f"{message_part}\n", 'bot_msg')
                            self.main_chat_display.insert(tk.END, "─" * 60 + "\n", 'separator')
                    elif any(keyword in line for keyword in ["🎯", "✅", "⚠️", "🔍", "🧠", "❓"]):
                        # Match information
                        self.main_chat_display.insert(tk.END, f"{line}\n", 'system')
                    elif "Auto-corrected" in line:
                        # Correction information
                        self.main_chat_display.insert(tk.END, f"{line}\n", 'system')
                    elif "🔍" in line or "Context:" in line:
                        # Context information
                        self.main_chat_display.insert(tk.END, f"{line}\n", 'context')
                    elif "📈" in line or "Statistics:" in line:
                        # Stats information
                        self.main_chat_display.insert(tk.END, f"{line}\n", 'stats')
                    elif "🤔" in line:
                        # Thinking indicator
                        self.main_chat_display.insert(tk.END, f"{line}\n", 'thinking')
                    elif "⚠️" in line and "Error" in line:
                        # Error message
                        self.main_chat_display.insert(tk.END, f"{line}\n", 'error')
                    else:
                        # System message
                        self.main_chat_display.insert(tk.END, f"{line}\n", 'system')
                
                self.main_chat_display.config(state=tk.DISABLED)
                self.main_chat_display.see(tk.END)
        except Exception as e:
            print(f"Error copying mini history to main: {e}")

class DarkChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI Assistant")
        
        # Load configuration
        self.config = self.load_configuration()
        
        # Set window size from config
        window_width = self.config.getint('gui', 'window_width', fallback=1000)
        window_height = self.config.getint('gui', 'window_height', fallback=700)
        self.root.geometry(f"{window_width}x{window_height}")
        
        self.root.configure(bg='#0f0f23')
        
        # Set window icon and theme (helps with Windows title bar)
        try:
            self.root.iconbitmap("edgar_icon.ico")  # You can add an icon file if desired
        except:
            pass
        
        # Color scheme
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
            'hover_primary': '#5750d3',
            'hover_secondary': '#35356a',
            'scrollbar_bg': '#1a1a2e',
            'scrollbar_slider': '#6c63ff',
            'scrollbar_hover': '#5750d3'
        }
        
        # Initialize chatbot with configuration from config file
        self.chatbot = AdvancedChatbot(
            config_file="config.cfg",
            auto_start_chat=False,  # Don't auto-start console chat in GUI
            streaming_callback=self.handle_streaming_text,  # NEW: Streaming callback
            thinking_callback=self.handle_thinking,         # NEW: Thinking callback
            response_complete_callback=self.handle_response_complete  # NEW: Response complete callback
        )
        
        # GUI variables
        self.is_processing = False
        self.mini_window = None
        self.current_streaming_text = ""
        self.is_streaming = False
        
        self.setup_gui()
    
    def load_configuration(self):
        """Load configuration from config file"""
        config = configparser.ConfigParser()
        
        # Default configuration
        defaults = {
            'gui': {
                'theme': 'dark',
                'window_width': '1000',
                'window_height': '700',
                'streaming_enabled': 'True'
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
    
    def handle_streaming_text(self, text):
        """Handle streaming text from the AI engine"""
        self.root.after(0, lambda: self.stream_to_display(text))
    
    def handle_thinking(self):
        """Handle thinking indicator from AI engine"""
        self.root.after(0, lambda: self.add_message("thinking", "🤔 Processing your request..."))
    
    def handle_response_complete(self):
        """Handle response complete from AI engine"""
        self.root.after(0, self.processing_complete)
    
    def stream_to_display(self, text):
        """Stream text to the main display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def setup_gui(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
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
        sidebar = tk.Frame(parent, bg=self.colors['bg_secondary'], width=200)
        sidebar.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W), padx=(0, 20))
        sidebar.grid_propagate(False)
        
        # Logo/Title area
        logo_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        logo_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(logo_frame, text="🤖", font=('Arial', 24), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack()
        tk.Label(logo_frame, text="Edgar AI", font=('Arial', 18, 'bold'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(pady=(5, 0))
        tk.Label(logo_frame, text="Your Personal Assistant", 
                font=('Arial', 11), bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack()
        
        # Separator
        separator = tk.Frame(sidebar, height=2, bg=self.colors['border'])
        separator.pack(fill=tk.X, padx=20, pady=10)
        
        # Controls section
        controls_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(controls_frame, text="CONTROLS", font=('Arial', 11),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(anchor='w')
        
        # Control buttons
        controls = [
            ("🧠 Context", self.show_context),
            ("📊 Statistics", self.show_statistics),
            ("🔄 New Chat", self.reset_chat),
            ("🪟 Mini Window", self.open_mini_window),
            ("⚙️ Settings", self.show_settings),
            ("❓ Help", self.show_help)
        ]
        
        for text, command in controls:
            btn = tk.Button(controls_frame, text=text, command=command, 
                          bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                          font=('Arial', 9), relief='flat', bd=0, padx=15, pady=8,
                          activebackground=self.colors['hover_secondary'],
                          activeforeground=self.colors['text_primary'])
            btn.pack(fill=tk.X, pady=5)
        
        # Streaming controls
        streaming_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        streaming_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(streaming_frame, text="STREAMING", font=('Arial', 11),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(anchor='w')
        
        # Streaming speed control
        speed_frame = tk.Frame(streaming_frame, bg=self.colors['bg_secondary'])
        speed_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(speed_frame, text="Speed:", font=('Arial', 9),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side=tk.LEFT)
        
        self.speed_var = tk.StringVar(value=str(self.chatbot.streaming_speed))
        speed_entry = tk.Entry(speed_frame, textvariable=self.speed_var, width=5,
                             font=('Arial', 9), bg=self.colors['input_bg'],
                             fg=self.colors['text_primary'])
        speed_entry.pack(side=tk.LEFT, padx=5)
        
        set_speed_btn = tk.Button(speed_frame, text="Set", 
                                command=self.set_streaming_speed,
                                bg=self.colors['accent_primary'],
                                fg=self.colors['text_primary'],
                                font=('Arial', 8), relief='flat')
        set_speed_btn.pack(side=tk.LEFT)
        
        # Streaming mode toggle
        mode_btn = tk.Button(streaming_frame, 
                           text="Toggle Letter Mode" if not self.chatbot.letter_streaming else "Toggle Word Mode",
                           command=self.toggle_streaming_mode,
                           bg=self.colors['bg_tertiary'],
                           fg=self.colors['text_primary'],
                           font=('Arial', 9), relief='flat')
        mode_btn.pack(fill=tk.X, pady=2)
        
        # Status section
        status_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=20)
        
        tk.Label(status_frame, text="STATUS", font=('Arial', 11),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(anchor='w')
        
        self.status_var = tk.StringVar()
        
        # Update status with streaming info
        streaming_mode = "letters" if self.chatbot.letter_streaming else "words"
        streaming_status = f"Streaming: {self.chatbot.streaming_speed} WPM ({streaming_mode})"
        self.status_var.set(streaming_status)
        
        status_label = tk.Label(status_frame, textvariable=self.status_var, 
                              font=('Arial', 9), bg=self.colors['bg_secondary'], 
                              fg=self.colors['text_secondary'])
        status_label.pack(anchor='w', pady=(5, 0))
        
    def set_streaming_speed(self):
        """Set streaming speed from GUI"""
        try:
            wpm = int(self.speed_var.get())
            self.chatbot.set_streaming_speed(wpm)
            
            # Update status
            streaming_mode = "letters" if self.chatbot.letter_streaming else "words"
            streaming_status = f"Streaming: {self.chatbot.streaming_speed} WPM ({streaming_mode})"
            self.status_var.set(streaming_status)
            
            messagebox.showinfo("Success", f"Streaming speed set to {wpm} WPM")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for WPM")
    
    def toggle_streaming_mode(self):
        """Toggle between letter and word streaming"""
        self.chatbot.toggle_letter_streaming()
        
        # Update status
        streaming_mode = "letters" if self.chatbot.letter_streaming else "words"
        streaming_status = f"Streaming: {self.chatbot.streaming_speed} WPM ({streaming_mode})"
        self.status_var.set(streaming_status)
        
        messagebox.showinfo("Success", f"Streaming mode changed to {streaming_mode.upper()} mode")
    
    def setup_main_content(self, parent):
        main_content = tk.Frame(parent, bg=self.colors['bg_primary'])
        main_content.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(0, weight=1)  # Chat display
        main_content.rowconfigure(1, weight=0)  # Quick actions
        main_content.rowconfigure(2, weight=0)  # Input area
        
        # Chat display area with custom scrollbar
        chat_frame = tk.Frame(main_content, bg=self.colors['bg_primary'])
        chat_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        # Create custom text widget with scrollbar
        self.chat_display = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=('Arial', 11),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['accent_secondary'],
            selectbackground=self.colors['accent_primary'],
            borderwidth=0,
            relief='flat',
            padx=20,
            pady=20,
            state=tk.DISABLED
        )
        
        # Create custom scrollbar
        self.scrollbar = tk.Scrollbar(
            chat_frame,
            orient=tk.VERTICAL,
            command=self.chat_display.yview,
            bg=self.colors['scrollbar_bg'],
            troughcolor=self.colors['scrollbar_bg'],
            activebackground=self.colors['scrollbar_hover']
        )
        
        # Configure the scrollbar style
        self.scrollbar.configure(
            bg=self.colors['scrollbar_bg'],
            troughcolor=self.colors['scrollbar_bg']
        )
        
        self.chat_display.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid the text and scrollbar
        self.chat_display.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure tags for different message types
        # User messages (RIGHT-ALIGNED)
        self.chat_display.tag_config('user_timestamp', 
                                   foreground=self.colors['text_tertiary'],
                                   justify='right',
                                   font=('Arial', 8))
        self.chat_display.tag_config('user_header', 
                                   foreground=self.colors['accent_secondary'],
                                   justify='right',
                                   font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('user_msg', 
                                   foreground=self.colors['text_primary'],
                                   justify='right',
                                   font=('Arial', 11))
        
        # Bot messages (LEFT-ALIGNED)  
        self.chat_display.tag_config('bot_timestamp', 
                                   foreground=self.colors['text_tertiary'],
                                   justify='left',
                                   font=('Arial', 8))
        self.chat_display.tag_config('bot_header', 
                                   foreground=self.colors['accent_primary'],
                                   justify='left',
                                   font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('bot_msg', 
                                   foreground=self.colors['text_primary'],
                                   justify='left',
                                   font=('Arial', 11))
        
        self.chat_display.tag_config('system', 
                                   foreground=self.colors['text_secondary'],
                                   justify='center',
                                   font=('Arial', 10, 'italic'))
        self.chat_display.tag_config('thinking', 
                                   foreground=self.colors['accent_warning'],
                                   justify='left',
                                   font=('Arial', 10, 'italic'))
        self.chat_display.tag_config('context', 
                                   foreground=self.colors['accent_success'],
                                   justify='left',
                                   font=('Arial', 9))
        self.chat_display.tag_config('stats', 
                                   foreground=self.colors['accent_secondary'],
                                   justify='left',
                                   font=('Arial', 9))
        self.chat_display.tag_config('error', 
                                   foreground=self.colors['accent_error'],
                                   justify='left',
                                   font=('Arial', 10))
        self.chat_display.tag_config('separator', 
                                   foreground=self.colors['border'],
                                   justify='center',
                                   font=('Arial', 8))
        
        # Quick actions
        quick_actions_frame = tk.Frame(main_content, bg=self.colors['bg_primary'])
        quick_actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        quick_actions = [
            ("Tell me more", "tell me more"),
            ("About Python", "tell me more about Python"),
            ("What is AI?", "what is artificial intelligence?"),
            ("Reset chat", "reset")
        ]
        
        for i, (label, command) in enumerate(quick_actions):
            btn = tk.Button(quick_actions_frame, text=label, 
                          command=lambda cmd=command: self.quick_action(cmd),
                          bg=self.colors['bg_tertiary'],
                          fg=self.colors['text_primary'],
                          font=('Arial', 9),
                          relief='flat',
                          bd=0,
                          padx=15,
                          pady=5,
                          activebackground=self.colors['hover_secondary'],
                          activeforeground=self.colors['text_primary'])
            btn.grid(row=0, column=i, padx=(0, 10))
        
        # Input area
        input_frame = tk.Frame(main_content, bg=self.colors['bg_primary'])
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        # User input with icon
        input_container = tk.Frame(input_frame, bg=self.colors['bg_tertiary'])
        input_container.pack(fill=tk.X, side=tk.LEFT, expand=True)
        input_container.columnconfigure(0, weight=1)
        
        self.user_input = tk.Entry(
            input_container,
            font=('Arial', 12),
            bg=self.colors['input_bg'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            relief='flat',
            bd=2,
            highlightthickness=1,
            highlightcolor=self.colors['accent_primary'],
            highlightbackground=self.colors['border']
        )
        self.user_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(10, 10), pady=10)
        self.user_input.bind('<Return>', lambda e: self.send_message())
        
        # Send button
        self.send_button = tk.Button(
            input_container,
            text="Send →",
            command=self.send_message,
            bg=self.colors['accent_primary'],
            fg=self.colors['text_primary'],
            font=('Arial', 10, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            activebackground=self.colors['hover_primary'],
            activeforeground=self.colors['text_primary']
        )
        self.send_button.grid(row=0, column=1, padx=(0, 10), pady=10)
        
        # Focus on input field
        self.user_input.focus()
    
    def open_mini_window(self):
        """Open the mini always-on-top window"""
        self.root.withdraw()  # Hide main window
        self.mini_window = MiniChatWindow(self.root, self.chatbot, self.chat_display, self.add_message)
    
    def quick_action(self, action):
        if action == "reset":
            self.reset_chat()
        else:
            self.user_input.delete(0, tk.END)
            self.user_input.insert(0, action)
            self.send_message()
    
    def display_welcome(self):
        welcome_text = """🌟 Welcome to Edgar AI Assistant

I'm your intelligent companion designed to help with programming, 
AI concepts, game development, and much more.

I remember our conversations and can provide detailed explanations 
when you ask me to "tell me more" about any topic.

How can I assist you today?"""
        
        self.add_message("system", welcome_text)
    
    def add_message(self, sender, message, tag=None):
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = time.strftime("%H:%M")
        
        if sender == "user":
            # User message - RIGHT ALIGNED
            self.chat_display.insert(tk.END, f"\n", 'system')
            # Header with timestamp and "You:" on the RIGHT
            self.chat_display.insert(tk.END, f"[{timestamp}] ", 'user_timestamp')
            self.chat_display.insert(tk.END, "You: ", 'user_header')
            self.chat_display.insert(tk.END, f"{message}\n", 'user_msg')
            self.chat_display.insert(tk.END, "─" * 60 + "\n", 'separator')
            
        elif sender == "bot":
            # Bot message - LEFT ALIGNED  
            self.chat_display.insert(tk.END, f"\n", 'system')
            # Header with timestamp and "Edgar:" on the LEFT
            self.chat_display.insert(tk.END, f"[{timestamp}] ", 'bot_timestamp')
            self.chat_display.insert(tk.END, "Edgar: ", 'bot_header')
            self.chat_display.insert(tk.END, f"{message}\n", 'bot_msg')
            self.chat_display.insert(tk.END, "─" * 60 + "\n", 'separator')
            
        elif sender == "system":
            self.chat_display.insert(tk.END, f"\n{message}\n", 'system')
        elif sender == "thinking":
            self.chat_display.insert(tk.END, f"{message}", 'thinking')
        elif sender == "context":
            self.chat_display.insert(tk.END, f"🔍 {message}\n", 'context')
        elif sender == "stats":
            self.chat_display.insert(tk.END, f"📈 {message}\n", 'stats')
        elif sender == "error":
            self.chat_display.insert(tk.END, f"⚠️ {message}\n", 'error')
        elif sender == "match_info":
            self.chat_display.insert(tk.END, f"{message}\n", 'system')
        elif sender == "correction":
            self.chat_display.insert(tk.END, f"{message}\n", 'system')
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_message(self):
        user_text = self.user_input.get().strip()
        if not user_text or self.is_processing:
            return
        
        # Clear input field
        self.user_input.delete(0, tk.END)
        self.send_button.config(state=tk.DISABLED)
        self.is_processing = True
        self.status_var.set("Processing your message...")
        
        # Display user message
        self.add_message("user", user_text)
        
        # Process message in separate thread to keep GUI responsive
        threading.Thread(target=self.process_message, args=(user_text,), daemon=True).start()
    
    def process_message(self, user_text):
        try:
            # Use the AI engine's streaming capabilities
            if self.chatbot.streaming_speed > 0:
                # Show thinking indicator
                self.root.after(0, lambda: self.add_message("thinking", "🤔 Processing your request..."))
                
                # Process with streaming
                responses = self.chatbot.process_multiple_questions(user_text)
                
                # Clear thinking indicator
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete("end-2l", "end-1l")
                self.chat_display.config(state=tk.DISABLED)
                
                # Display responses with streaming
                self.root.after(0, lambda: self.display_responses_with_streaming(responses))
            else:
                # Process without streaming (immediate display)
                responses = self.chatbot.process_multiple_questions(user_text)
                self.root.after(0, lambda: self.display_responses(responses))
            
        except Exception as e:
            self.root.after(0, lambda: self.add_message("error", f"An error occurred: {str(e)}"))
        finally:
            self.root.after(0, self.processing_complete)
    
    def display_responses_with_streaming(self, responses):
        """Display responses using the AI engine's streaming"""
        for i, (original_question, answer, confidence, corrections, matched_group, match_type) in enumerate(responses, 1):
            
            # Show corrections if any
            if corrections:
                best_correction, best_score = corrections[0]
                correction_text = f"Auto-corrected to: '{best_correction}' (confidence: {best_score}%)"
                self.add_message("correction", correction_text)
            
            # Display the answer using streaming
            if answer:
                # Add bot message header
                timestamp = time.strftime("%H:%M")
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, f"\n", 'system')
                self.chat_display.insert(tk.END, f"[{timestamp}] ", 'bot_timestamp')
                self.chat_display.insert(tk.END, "Edgar: ", 'bot_header')
                self.chat_display.config(state=tk.DISABLED)
                
                # Stream the response using the AI engine
                self.chatbot.stream_text(
                    answer, 
                    "",  # No prefix since we already added the header
                    self.chatbot.streaming_speed,
                    callback=lambda x: self.root.after(0, lambda: self.stream_to_display(x))
                )
                
                # Add separator after streaming completes
                self.root.after(100, lambda: self.add_message("system", "─" * 60))
            
            # Show match information
            if matched_group and confidence > 0 and match_type != "follow_up":
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
            
            # Show context summary if available
            context_summary = self.chatbot.get_context_summary()
            if context_summary and context_summary != "Minimal context":
                self.add_message("context", context_summary)
    
    def display_responses(self, responses):
        """Display responses immediately without streaming"""
        for i, (original_question, answer, confidence, corrections, matched_group, match_type) in enumerate(responses, 1):
            
            # Show corrections if any
            if corrections:
                best_correction, best_score = corrections[0]
                correction_text = f"Auto-corrected to: '{best_correction}' (confidence: {best_score}%)"
                self.add_message("correction", correction_text)
            
            # Display the answer immediately
            if answer:
                self.add_message("bot", answer)
            
            # Show match information
            if matched_group and confidence > 0 and match_type != "follow_up":
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
            
            # Show context summary if available
            context_summary = self.chatbot.get_context_summary()
            if context_summary and context_summary != "Minimal context":
                self.add_message("context", context_summary)
    
    def processing_complete(self):
        """Called when message processing is complete"""
        self.is_processing = False
        self.send_button.config(state=tk.NORMAL)
        
        # Update status with current streaming info
        streaming_mode = "letters" if self.chatbot.letter_streaming else "words"
        streaming_status = f"Streaming: {self.chatbot.streaming_speed} WPM ({streaming_mode})"
        self.status_var.set(streaming_status)
        
        self.user_input.focus()
    
    def show_context(self):
        """Display current conversation context"""
        context_summary = self.chatbot.get_context_summary()
        self.add_message("system", f"Current Context: {context_summary}")
    
    def show_statistics(self):
        """Display chatbot statistics"""
        stats = self.chatbot.performance_stats
        total = stats['total_questions']
        
        if total == 0:
            self.add_message("stats", "No questions processed yet.")
            return
        
        success_rate = stats['successful_matches'] / total
        
        stats_text = f"""Conversation Statistics:
• Total questions: {total}
• Success rate: {success_rate:.1%}
• Follow-up requests: {stats['follow_up_requests']}
• Context assists: {stats['context_helps']}"""
        
        self.add_message("stats", stats_text)
    
    def reset_chat(self):
        """Reset the conversation"""
        if messagebox.askyesno("New Chat", "Start a new conversation? Current context will be cleared."):
            # Reset chatbot context
            self.chatbot.conversation_context = {
                'current_topic': None,
                'previous_topics': self.chatbot.conversation_context['previous_topics'],
                'mentioned_entities': self.chatbot.conversation_context['mentioned_entities'],
                'user_preferences': {},
                'conversation_history': self.chatbot.conversation_context['conversation_history'],
                'current_goal': None,
                'last_successful_match': None,
                'conversation_mood': 'neutral',
                'topic_consistency_score': 1.0,
                'recent_subjects': self.chatbot.conversation_context['recent_subjects'],
                'last_detailed_topic': None,
                'available_follow_ups': {},
            }
            
            # Clear chat display
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            # Show welcome message again
            self.display_welcome()
            
            self.status_var.set("New chat started")
    
    def show_settings(self):
        """Show settings dialog"""
        settings_text = f"""Current Settings:

AI Engine:
• Streaming Speed: {self.chatbot.streaming_speed} WPM
• Streaming Mode: {'Letter-by-Letter' if self.chatbot.letter_streaming else 'Word-by-Word'}
• Additional Info Speed: {self.chatbot.additional_info_speed} WPM
• Model: {self.chatbot.current_model}

GUI:
• Window Size: {self.config.get('gui', 'window_width')}x{self.config.get('gui', 'window_height')}
• Theme: {self.config.get('gui', 'theme')}

All settings are stored in config.cfg"""
        
        messagebox.showinfo("Settings", settings_text)
    
    def show_help(self):
        """Show help information"""
        help_text = """🤖 Edgar AI Assistant - Help

Quick Commands:
• 'tell me more' - Get detailed information
• 'tell me more about [topic]' - Specific details
• Ask about programming, AI, game development

Features:
• Context-aware conversations
• Intelligent question matching
• Detailed follow-up information
• Conversation statistics
• Mini window (always on top)
• Real-time text streaming

Tips:
• Use the quick action buttons for common questions
• The assistant maintains context across messages
• Press Enter to send messages quickly
• Use 'Mini Window' for always-on-top assistance
• Adjust streaming speed in the sidebar"""

        messagebox.showinfo("Assistant Help", help_text)

def main():
    try:
        # Create root window
        root = tk.Tk()
        
        # Try to set Windows dark title bar (Windows 10/11)
        try:
            # This uses Windows API to set dark mode for title bar
            if os.name == 'nt':  # Windows
                import ctypes
                # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
                hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
                value = 2  # Dark mode
                set_window_attribute(hwnd, 20, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int))
        except:
            pass  # Fall back to default title bar if this fails
        
        app = DarkChatbotGUI(root)
        
        # Center the window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()