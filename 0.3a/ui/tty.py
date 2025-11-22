#!/usr/bin/env python3
"""
TTY Interface for Edgar AI Assistant

Provides a terminal interface to interact with the AI engine and modules
without requiring a GUI.
"""

import sys
import os
import time
import threading
from typing import List, Dict, Any, Tuple

# Add the project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # Go up one level from ui folder
sys.path.insert(0, project_root)  # Add project root to path

try:
    from core.layer import create_streaming_layer
    print("✅ Successfully imported StreamingLayer from core.layer")
except ImportError as e:
    print(f"❌ Error importing StreamingLayer: {e}")
    print(f"Current Python path: {sys.path}")
    print(f"Looking for core in: {project_root}")
    sys.exit(1)


class TTYInterface:
    """
    Terminal interface for Edgar AI Assistant.
    Provides all the functionality of the GUI but in terminal form.
    """
    
    def __init__(self):
        self.is_processing = False
        self.current_response = ""
        self.streaming_complete = threading.Event()
        self.current_question = ""
        
        # Initialize streaming layer with terminal callbacks
        self.streaming_layer = create_streaming_layer(
            config_file=os.path.join(project_root, "config.cfg"),
            streaming_callback=self._handle_streaming,
            thinking_callback=self._handle_thinking,
            response_complete_callback=self._handle_response_complete,
            status_update_callback=self._handle_status_update,
            error_callback=self._handle_error
        )
        
        print("🤖 Edgar AI Assistant - TTY Mode")
        print("=" * 50)
    
    # ===== STREAMING LAYER CALLBACKS =====
    
    def _handle_streaming(self, text: str):
        """Handle streaming text - print directly to terminal"""
        print(text, end='', flush=True)
        self.current_response += text
    
    def _handle_thinking(self, text: str):
        """Handle thinking indicators"""
        print(f"\n🤔 {text}")
    
    def _handle_response_complete(self):
        """Handle response completion"""
        self.is_processing = False
        self.streaming_complete.set()
        print()  # Add newline after response
    
    def _handle_status_update(self, status: str):
        """Handle status updates"""
        print(f"📡 {status}")
    
    def _handle_error(self, error: str):
        """Handle errors"""
        print(f"❌ {error}")
        self.is_processing = False
        self.streaming_complete.set()
    
    # ===== COMMAND PROCESSING =====
    
    def process_command(self, user_input: str) -> bool:
        """
        Process user input as a command or regular message.
        Returns True if the input was a command, False if it should be processed as a message.
        """
        user_input_lower = user_input.lower().strip()
        
        if user_input_lower in ['quit', 'exit', 'bye']:
            print("👋 Goodbye! Thanks for chatting!")
            return True
        
        elif user_input_lower == 'stats':
            self.show_statistics()
            return True
        
        elif user_input_lower == 'context':
            self.show_context()
            return True
        
        elif user_input_lower == 'reset':
            self.reset_conversation()
            return True
        
        elif user_input_lower == 'models':
            self.list_models()
            return True
        
        elif user_input_lower.startswith('model '):
            model_name = user_input[6:].strip()
            self.change_model(model_name)
            return True
        
        elif user_input_lower == 'modules':
            self.list_modules()
            return True
        
        elif user_input_lower == 'config':
            self.show_configuration()
            return True
        
        elif user_input_lower == 'help':
            self.show_help()
            return True
        
        # Not a command, process as regular message
        return False
    
    def process_message(self, user_input: str):
        """Process a regular user message through the streaming layer"""
        if self.is_processing:
            print("⏳ Please wait for the current response to complete.")
            return
        
        self.is_processing = True
        self.current_response = ""
        self.current_question = user_input
        self.streaming_complete.clear()
        
        # Display user message
        print(f"\n💬 You: {user_input}")
        
        # Process in a separate thread to keep terminal responsive
        def process_thread():
            try:
                # This will trigger the streaming callbacks automatically
                responses = self.streaming_layer.process_message(user_input)
                
                # If streaming didn't happen (fallback), display directly
                if not self.current_response and responses:
                    self.display_responses_directly(responses)
                    self.is_processing = False
                    self.streaming_complete.set()
                    
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                self.is_processing = False
                self.streaming_complete.set()
        
        threading.Thread(target=process_thread, daemon=True).start()
        
        # Wait for streaming to complete
        self.streaming_complete.wait()
    
    def display_responses_directly(self, responses: List[Tuple]):
        """Display responses directly (fallback if streaming didn't work)"""
        for i, response in enumerate(responses, 1):
            print(f"\n--- Response {i} ---")
            
            # Handle different response formats
            if len(response) == 6:
                # AI Engine format
                original_question, answer, confidence, corrections, matched_group, match_type = response
                
                if corrections:
                    best_correction, best_score = corrections[0]
                    print(f"🔧 Auto-corrected to: '{best_correction}' (confidence: {best_score}%)")
                
                # Use streaming layer to stream the answer
                print("🤖 ", end='', flush=True)
                self.streaming_layer.stream_text(answer, "")
                
                if matched_group and confidence > 0:
                    match_type_display = {
                        "exact": "🎯 Exact match",
                        "high_confidence": "✅ High confidence", 
                        "medium_confidence": "⚠️  Medium confidence",
                        "low_confidence": "🔍 Low confidence",
                        "semantic": "🧠 Semantic match"
                    }
                    display_type = match_type_display.get(match_type, match_type)
                    print(f"💡 {display_type} from '{matched_group}' (confidence: {confidence:.2f})")
                    
            elif len(response) == 3:
                # Module routing format
                answer, confidence, source = response
                
                # Use streaming layer to stream the answer
                print("🤖 ", end='', flush=True)
                self.streaming_layer.stream_text(answer, "")
                print(f"🔄 Routed via: {source} (confidence: {confidence:.2f})")
            
            else:
                # Unknown format
                print(f"🤖 {response}")
    
    # ===== COMMAND IMPLEMENTATIONS =====
    
    def show_help(self):
        """Show help information"""
        help_text = """
🤖 Edgar AI Assistant - TTY Mode

💡 Commands:
  quit, exit, bye - Exit the chat
  stats - Show conversation statistics
  context - Show current context
  reset - Reset conversation context
  models - List available models
  model <name> - Switch to another model
  modules - List available modules
  config - Show current configuration
  help - Show this help

💡 Features:
  • Context-aware conversations
  • Intelligent question matching  
  • Module routing system
  • Real-time text streaming
  • Multiple AI models support

💡 Examples:
  Just type your question naturally!
  "What is Python?"
  "Tell me about artificial intelligence"
  "How do I create a game in Unity?"
"""
        print(help_text)
    
    def show_statistics(self):
        """Show conversation statistics"""
        stats = self.streaming_layer.get_statistics()
        total = stats['total_questions']
        
        if total == 0:
            print("📊 No questions processed yet.")
            return
        
        success_rate = stats['successful_matches'] / total
        
        print("📊 Conversation Statistics:")
        print(f"   • Total questions: {total}")
        print(f"   • Success rate: {success_rate:.1%}")
        print(f"   • Follow-up requests: {stats['follow_up_requests']}")
        print(f"   • Tree entries: {stats['tree_entries']}")
        print(f"   • Tree navigations: {stats['tree_navigations']}")
        print(f"   • Tree exits: {stats['tree_exits']}")
        print(f"   • Confidence rejections: {stats['confidence_rejections']}")
        
        # Show model info
        current_model = self.streaming_layer.get_current_model()
        qa_groups = self.streaming_layer.get_qa_groups_count()
        print(f"   • Current model: {current_model}")
        print(f"   • QA groups in model: {qa_groups}")
    
    def show_context(self):
        """Show current conversation context"""
        context_summary = self.streaming_layer.get_context_summary()
        print(f"🧠 Current Context: {context_summary}")
    
    def reset_conversation(self):
        """Reset conversation context"""
        self.streaming_layer.reset_conversation()
        print("🔄 Conversation context reset!")
    
    def list_models(self):
        """List available models"""
        models = self.streaming_layer.get_available_models()
        current_model = self.streaming_layer.get_current_model()
        
        if not models:
            print("❌ No models found in 'models' folder.")
            return
        
        print("🤖 Available Models:")
        for i, model in enumerate(models, 1):
            current_indicator = " ← CURRENT" if model == current_model else ""
            print(f"   {i}. {model}{current_indicator}")
        
        print(f"\n💡 Use 'model <name>' to switch models")
    
    def change_model(self, model_name: str):
        """Change to a different model"""
        models = self.streaming_layer.get_available_models()
        
        if model_name not in models:
            print(f"❌ Model '{model_name}' not found.")
            print("💡 Available models:")
            for model in models:
                print(f"   • {model}")
            return
        
        success = self.streaming_layer.change_model(model_name)
        if success:
            qa_groups = self.streaming_layer.get_qa_groups_count()
            print(f"✅ Switched to model: {model_name}")
            print(f"📊 Model contains {qa_groups} QA groups")
        else:
            print(f"❌ Failed to switch to model: {model_name}")
    
    def list_modules(self):
        """List available modules"""
        modules = self.streaming_layer.get_available_modules()
        routing_stats = self.streaming_layer.get_routing_stats()
        
        print("🔧 Available Modules:")
        if not modules:
            print("   No modules found in core/modules folder")
        else:
            for module in modules:
                print(f"   • {module}")
        
        print(f"\n📡 Routing System:")
        print(f"   • Routing groups: {routing_stats['total_groups']}")
        print(f"   • Total questions: {routing_stats['total_questions']}")
        print(f"   • Active modules: {routing_stats['active_modules']}")
        
        if routing_stats['modules_list']:
            print(f"   • Configured modules: {', '.join(routing_stats['modules_list'])}")
    
    def show_configuration(self):
        """Show current configuration"""
        config = self.streaming_layer.get_configuration()
        
        print("⚙️ Current Configuration:")
        print(f"   • Current Model: {config['current_model']}")
        print(f"   • QA Groups: {config['qa_groups_count']}")
        print(f"   • Streaming Speed: {config['streaming_speed']} WPM")
        print(f"   • Streaming Mode: {'Letter-by-Letter' if config['letter_streaming'] else 'Word-by-Word'}")
        print(f"   • Additional Info Speed: {config['additional_info_speed']} WPM")
        print(f"   • Confidence Requirement: {config['confidence_requirement']:.2f}")
        print(f"   • Speed Limiting: {'Enabled' if config['speed_limit'] else 'Disabled'}")
        print(f"   • Available Models: {len(config['available_modules'])}")
        print(f"   • Routing Groups: {config['routing_groups_count']}")
        print(f"   • Routing Questions: {config['routing_questions_count']}")
        print(f"   • Routing Threshold: {config['routing_threshold']}")
        print(f"   • Active Modules: {config['active_modules_count']}")
    
    def show_welcome(self):
        """Show welcome message"""
        current_model = self.streaming_layer.get_current_model()
        qa_groups = self.streaming_layer.get_qa_groups_count()
        routing_stats = self.streaming_layer.get_routing_stats()
        
        welcome_text = f"""
🌟 Welcome to Edgar AI Assistant - TTY Mode

🤖 Current Model: {current_model}
📊 Knowledge Base: {qa_groups} QA groups
🔧 Routing System: {routing_stats['total_groups']} groups, {routing_stats['total_questions']} questions
💨 Streaming: {self.streaming_layer.streaming_speed} WPM ({'Word-by-Word' if not self.streaming_layer.letter_streaming else 'Letter-by-Letter'})

I'm your intelligent companion designed to help with programming, 
AI concepts, game development, and much more.

Type 'help' to see available commands, or just ask me anything!
"""
        print(welcome_text)
    
    def run(self):
        """Main chat loop"""
        self.show_welcome()
        
        try:
            while True:
                try:
                    # Show prompt
                    if self.is_processing:
                        # Don't show prompt while processing
                        time.sleep(0.1)
                        continue
                    else:
                        user_input = input("💬 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Process command or message
                    if not self.process_command(user_input):
                        self.process_message(user_input)
                        
                except KeyboardInterrupt:
                    print("\n\n🛑 Interrupted. Type 'quit' to exit or continue chatting.")
                except EOFError:
                    print("\n👋 Goodbye!")
                    break
                    
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


def main():
    """Main entry point for TTY interface"""
    try:
        # Check if models folder exists
        models_path = os.path.join(project_root, "models")
        if not os.path.exists(models_path):
            print("❌ 'models' folder not found.")
            print("💡 Please run the training GUI first to create models, or")
            print("   create a 'models' folder with your model JSON files.")
            return
        
        # Create and run TTY interface
        tty_interface = TTYInterface()
        tty_interface.run()
        
    except Exception as e:
        print(f"❌ Error starting TTY interface: {e}")
        print("💡 Make sure you're running this from the project root directory.")


if __name__ == "__main__":
    main()