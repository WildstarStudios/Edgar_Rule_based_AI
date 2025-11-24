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
            'window_height': '700'
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

def show_error_dialog(title, message, theme):
    """Show error dialog using the appropriate theme's libraries"""
    if theme == 'classic':
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showerror(title, message)
        root.destroy()
    else:
        # For modern theme, create a proper CTk error dialog
        import customtkinter as ctk
        from customtkinter import CTk, CTkToplevel, CTkLabel, CTkButton
        
        class ModernErrorDialog:
            def __init__(self, title, message):
                self.dialog = CTkToplevel()
                self.dialog.title(title)
                self.dialog.geometry("400x200")
                self.dialog.resizable(False, False)
                self.dialog.configure(fg_color='#1a1a2e')
                self.dialog.transient(None)
                self.dialog.grab_set()
                
                # Center dialog on screen
                self.dialog.update_idletasks()
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                x = (screen_width - 400) // 2
                y = (screen_height - 200) // 2
                self.dialog.geometry(f"+{x}+{y}")
                
                # Error icon and message
                CTkLabel(self.dialog, text="❌", font=('Arial', 24),
                        text_color='#ff4d7d').pack(pady=(20, 10))
                
                CTkLabel(self.dialog, text=title, font=('Arial', 16, 'bold'),
                        text_color='#ffffff').pack()
                
                CTkLabel(self.dialog, text=message, font=('Arial', 11),
                        text_color='#ffffff', wraplength=350, 
                        justify='left').pack(expand=True, padx=20, pady=10)
                
                # OK button
                CTkButton(self.dialog, text="OK", command=self.dialog.destroy,
                         fg_color='#6c63ff', hover_color='#5750d3',
                         text_color='#ffffff').pack(pady=(0, 20))
                
                self.dialog.mainloop()
        
        ModernErrorDialog(title, message)

def launch_chat_interface():
    """Launch the appropriate chat interface based on theme config"""
    config = load_theme_config()
    theme = config.get('gui', 'theme', fallback='classic')
    
    print(f"🎨 Launching {theme} theme interface...")
    
    try:
        if theme == 'classic':
            # Only import classic libraries
            from ui.classic.classic_tkinter import main as classic_main
            classic_main()
        elif theme == 'modern':
            # Only import modern libraries  
            from ui.modern.modern_tkinter import main as modern_main
            modern_main()
        else:
            print(f"❌ Unknown theme: {theme}. Falling back to classic.")
            from ui.classic.classic_tkinter import main as classic_main
            classic_main()
            
    except ImportError as e:
        print(f"❌ Error importing theme module: {e}")
        show_error_dialog("Launch Error", f"Could not launch {theme} theme: {e}", theme)
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        show_error_dialog("Error", f"Failed to start application: {e}", theme)

if __name__ == "__main__":
    launch_chat_interface()
