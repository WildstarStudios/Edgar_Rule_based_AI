import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import sys
import os

# Add the directory containing edgar_1.0.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_engine import AdvancedChatbot
    print("✅ Successfully imported AdvancedChatbot from edgar_1.0.py")
except ImportError as e:
    print(f"❌ Error importing AdvancedChatbot: {e}")
    print("Please make sure edgar_1.0.py is in the same directory")
    sys.exit(1)

class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Edgar AI Chatbot")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Initialize chatbot
        self.chatbot = AdvancedChatbot()
        
        # GUI variables
        self.is_processing = False
        self.current_streaming_text = ""
        self.streaming_index = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 Edgar AI Chatbot", 
                               font=('Arial', 16, 'bold'), foreground='#3498db')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=25,
            font=('Arial', 10),
            bg='#ecf0f1',
            fg='#2c3e50',
            state=tk.DISABLED
        )
        self.chat_display.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure tags for different message types
        self.chat_display.tag_config('user', foreground='#2980b9', justify='right')
        self.chat_display.tag_config('bot', foreground='#27ae60', justify='left')
        self.chat_display.tag_config('system', foreground='#e74c3c', justify='center')
        self.chat_display.tag_config('thinking', foreground='#f39c12', justify='left')
        self.chat_display.tag_config('context', foreground='#8e44ad', justify='left')
        self.chat_display.tag_config('stats', foreground='#16a085', justify='left')
        
        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        # User input
        self.user_input = ttk.Entry(
            input_frame, 
            font=('Arial', 12),
            width=60
        )
        self.user_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))  # Fixed: padright to padx
        self.user_input.bind('<Return>', lambda e: self.send_message())
        
        # Send button
        self.send_button = ttk.Button(
            input_frame, 
            text="Send", 
            command=self.send_message,
            state=tk.NORMAL
        )
        self.send_button.grid(row=0, column=1, padx=(5, 0))  # Fixed: padleft to padx
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Control buttons
        ttk.Button(control_frame, text="🧠 Show Context", command=self.show_context).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="📊 Statistics", command=self.show_statistics).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="🔄 Reset Chat", command=self.reset_chat).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="❓ Help", command=self.show_help).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="🚪 Exit", command=self.root.quit).grid(row=0, column=4, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to chat! Type your message and press Enter.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Focus on input field
        self.user_input.focus()
        
        # Display welcome message
        self.display_welcome()
    
    def display_welcome(self):
        welcome_text = """🤖 Welcome to Edgar AI Chatbot!

I'm an advanced chatbot with context awareness and intelligent matching. 
I can help with programming, AI, game development, and much more!

Try these commands:
• 'tell me more about Python' - Get detailed information
• 'what is machine learning?' - Ask about AI concepts
• 'tell me more' - Get more details about the current topic

You can also use the buttons below for additional functions."""
        
        self.add_message("system", welcome_text)
    
    def add_message(self, sender, message, tag=None):
        self.chat_display.config(state=tk.NORMAL)
        
        if sender == "user":
            self.chat_display.insert(tk.END, f"\n👤 You: ", 'user')
            self.chat_display.insert(tk.END, f"{message}\n", 'user')
        elif sender == "bot":
            self.chat_display.insert(tk.END, f"\n🤖 Edgar: ", 'bot')
            self.chat_display.insert(tk.END, f"{message}\n", tag or 'bot')
        elif sender == "system":
            self.chat_display.insert(tk.END, f"\n{message}\n", 'system')
        elif sender == "thinking":
            self.chat_display.insert(tk.END, f"{message}", 'thinking')
        elif sender == "context":
            self.chat_display.insert(tk.END, f"🧠 {message}\n", 'context')
        elif sender == "stats":
            self.chat_display.insert(tk.END, f"📊 {message}\n", 'stats')
        
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
            # Show thinking indicator
            self.root.after(0, lambda: self.add_message("thinking", "🤔 Thinking..."))
            
            # Process the message using the chatbot
            responses = self.chatbot.process_multiple_questions(user_text)
            
            # Update GUI with responses
            self.root.after(0, lambda: self.display_responses(responses))
            
        except Exception as e:
            self.root.after(0, lambda: self.add_message("bot", f"Error: {str(e)}"))
        finally:
            self.root.after(0, self.processing_complete)
    
    def display_responses(self, responses):
        """Display chatbot responses in the GUI"""
        for i, (original_question, answer, confidence, corrections, matched_question, match_type) in enumerate(responses, 1):
            
            # Show corrections if any
            if corrections:
                best_correction, best_score = corrections[0]
                correction_text = f"Auto-corrected to: '{best_correction}' (confidence: {best_score}%)"
                self.add_message("system", correction_text)
            
            # Display the answer
            self.add_message("bot", answer)
            
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
                match_info = f"{display_type}: '{matched_question}' (confidence: {confidence:.2f})"
                self.add_message("system", match_info)
            
            # Show context summary if available
            context_summary = self.chatbot.get_context_summary()
            if context_summary and context_summary != "Minimal context":
                self.add_message("context", context_summary)
    
    def processing_complete(self):
        """Called when message processing is complete"""
        self.is_processing = False
        self.send_button.config(state=tk.NORMAL)
        self.status_var.set("Ready for your next message...")
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
        
        stats_text = f"""Performance Statistics:
• Total questions: {total}
• Success rate: {success_rate:.1%}
• Follow-up requests: {stats['follow_up_requests']}
• Failed matches: {stats['failed_matches']}
• Low confidence matches: {stats['low_confidence_matches']}"""
        
        self.add_message("stats", stats_text)
    
    def reset_chat(self):
        """Reset the conversation"""
        if messagebox.askyesno("Reset Chat", "Are you sure you want to reset the conversation?"):
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
            
            self.status_var.set("Chat reset successfully!")
    
    def show_help(self):
        """Show help information"""
        help_text = """📖 Edgar AI Chatbot Help

Available Commands in Chat:
• 'tell me more' - Get detailed information about current topic
• 'tell me more about [subject]' - Get details about specific subject
• Ask about: Python, machine learning, Godot, Blender, AI, etc.

Button Functions:
• 🧠 Show Context - Display current conversation context
• 📊 Statistics - Show chatbot performance statistics  
• 🔄 Reset Chat - Clear conversation history and start fresh
• ❓ Help - Show this help message
• 🚪 Exit - Close the application

Tips:
• Press Enter to send messages quickly
• The chatbot maintains context across conversations
• Use 'tell me more' to get comprehensive information"""
        
        messagebox.showinfo("Chatbot Help", help_text)

def main():
    try:
        root = tk.Tk()
        app = ChatbotGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()