import tkinter as tk
from tkinter import messagebox
import configparser
import os
import sys

def load_theme_config():
    """Load theme configuration from config file"""
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
            if not config.has_option(section, key):
                config.set(section, key, value)
    
    # Load from file if exists
    if os.path.exists("config.cfg"):
        config.read("config.cfg")
        print("✅ Loaded configuration from config.cfg")
    else:
        print("⚠️  config.cfg not found, using default configuration")
        # Create default config file
        with open("config.cfg", 'w') as f:
            config.write(f)
    
    return config

def launch_chat_interface():
    """Launch the appropriate chat interface based on theme config"""
    config = load_theme_config()
    theme = config.get('gui', 'theme', fallback='classic')
    
    print(f"🎨 Launching {theme} theme interface...")
    
    try:
        if theme == 'classic':
            from ui.classic.chat import main as classic_main
            classic_main()
        elif theme == 'modern':
            from ui.modern.chat import main as modern_main
            modern_main()
        else:
            print(f"❌ Unknown theme: {theme}. Falling back to classic.")
            from ui.classic.chat import main as classic_main
            classic_main()
            
    except ImportError as e:
        print(f"❌ Error importing theme module: {e}")
        messagebox.showerror("Launch Error", f"Could not launch {theme} theme: {e}")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    launch_chat_interface()