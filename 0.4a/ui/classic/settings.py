# ui/classic/settings.py
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
import sys

class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.config = configparser.ConfigParser()
        self.load_config()
        
        # Classic theme colors
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
        
        self.setup_window()
    
    def load_config(self):
        """Load configuration from config file"""
        if os.path.exists("config.cfg"):
            self.config.read("config.cfg")
        else:
            # Create default config if it doesn't exist
            self.config['gui'] = {
                'theme': 'classic',
                'window_width': '1000',
                'window_height': '700',
                'streaming_enabled': 'True',
                'verbose_mode': 'False'
            }
    
    def save_config(self):
        """Save configuration to config file"""
        with open("config.cfg", 'w') as configfile:
            self.config.write(configfile)
    
    def setup_window(self):
        """Setup the settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Settings - Edgar AI Assistant")
        self.window.geometry("500x400")
        self.window.resizable(True, True)
        self.window.configure(bg=self.colors['bg_primary'])
        
        # Center the window on parent
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self.center_window()
        self.create_widgets()
    
    def center_window(self):
        """Center the window on the parent"""
        self.window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create the settings widgets"""
        # Main container with scrollbar
        main_frame = tk.Frame(self.window, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(main_frame, bg=self.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = tk.Label(
            scrollable_frame, 
            text="Settings", 
            font=('Arial', 18, 'bold'),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary']
        )
        title_label.pack(pady=(0, 20))
        
        # Theme Selection Section
        theme_frame = tk.Frame(
            scrollable_frame, 
            bg=self.colors['bg_secondary'],
            relief='flat',
            bd=1,
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        theme_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Theme header
        theme_header = tk.Label(
            theme_frame,
            text="THEME SELECTION",
            font=('Arial', 12, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        theme_header.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Theme description
        theme_desc = tk.Label(
            theme_frame,
            text="Choose the visual theme for the application. Changes will take effect after restart.",
            font=('Arial', 9),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            wraplength=400,
            justify='left'
        )
        theme_desc.pack(anchor='w', padx=15, pady=(0, 15))
        
        # Theme options frame
        theme_options_frame = tk.Frame(theme_frame, bg=self.colors['bg_secondary'])
        theme_options_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Current theme
        current_theme = self.config.get('gui', 'theme', fallback='classic')
        self.theme_var = tk.StringVar(value=current_theme)
        
        # Classic theme option
        classic_frame = tk.Frame(theme_options_frame, bg=self.colors['bg_secondary'])
        classic_frame.pack(fill=tk.X, pady=5)
        
        classic_radio = tk.Radiobutton(
            classic_frame,
            text="Classic Theme",
            variable=self.theme_var,
            value="classic",
            font=('Arial', 10),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_primary'],
            activebackground=self.colors['bg_secondary'],
            activeforeground=self.colors['text_primary']
        )
        classic_radio.pack(side=tk.LEFT)
        
        classic_desc = tk.Label(
            classic_frame,
            text="Dark blue theme with purple accents",
            font=('Arial', 9),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            justify='left'
        )
        classic_desc.pack(side=tk.LEFT, padx=(10, 0))
        
        # Modern theme option  
        modern_frame = tk.Frame(theme_options_frame, bg=self.colors['bg_secondary'])
        modern_frame.pack(fill=tk.X, pady=5)
        
        modern_radio = tk.Radiobutton(
            modern_frame,
            text="Modern Theme",
            variable=self.theme_var,
            value="modern",
            font=('Arial', 10),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_primary'],
            activebackground=self.colors['bg_secondary'],
            activeforeground=self.colors['text_primary']
        )
        modern_radio.pack(side=tk.LEFT)
        
        modern_desc = tk.Label(
            modern_frame,
            text="Dark gray theme with blue accents",
            font=('Arial', 9),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            justify='left'
        )
        modern_desc.pack(side=tk.LEFT, padx=(10, 0))
        
        # Current Settings Section
        current_frame = tk.Frame(
            scrollable_frame, 
            bg=self.colors['bg_secondary'],
            relief='flat',
            bd=1,
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        current_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Current settings header
        current_header = tk.Label(
            current_frame,
            text="CURRENT SETTINGS",
            font=('Arial', 12, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        current_header.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Display current settings
        settings_text = f"""Current Configuration:
• Theme: {current_theme.title()}
• Window Size: {self.config.get('gui', 'window_width', fallback='1000')}x{self.config.get('gui', 'window_height', fallback='700')}
• Streaming: {self.config.get('gui', 'streaming_enabled', fallback='True')}
• Verbose Mode: {self.config.get('gui', 'verbose_mode', fallback='False')}

All settings are stored in config.cfg"""
        
        current_settings = tk.Label(
            current_frame,
            text=settings_text,
            font=('Arial', 9),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            justify='left'
        )
        current_settings.pack(anchor='w', padx=15, pady=(0, 15))
        
        # Buttons frame
        buttons_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_primary'])
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Apply and Restart button
        apply_btn = tk.Button(
            buttons_frame,
            text="Apply and Restart",
            command=self.apply_and_restart,
            bg=self.colors['accent_primary'],
            fg=self.colors['text_primary'],
            font=('Arial', 10, 'bold'),
            relief='flat',
            bd=0,
            padx=30,
            pady=10,
            activebackground=self.colors['accent_primary'],
            activeforeground=self.colors['text_primary']
        )
        apply_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cancel button
        cancel_btn = tk.Button(
            buttons_frame,
            text="Cancel",
            command=self.window.destroy,
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            font=('Arial', 10),
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            activebackground=self.colors['bg_secondary'],
            activeforeground=self.colors['text_primary']
        )
        cancel_btn.pack(side=tk.RIGHT)
    
    def apply_and_restart(self):
        """Apply settings and restart the application"""
        selected_theme = self.theme_var.get()
        
        # Update config with selected theme
        if not self.config.has_section('gui'):
            self.config.add_section('gui')
        
        self.config.set('gui', 'theme', selected_theme)
        
        # Save config
        self.save_config()
        
        # Show confirmation message
        messagebox.showinfo(
            "Settings Applied", 
            f"Theme has been set to '{selected_theme.title()}'. The application will now restart to apply changes."
        )
        
        # Close settings window
        self.window.destroy()
        
        # Restart the application
        self.restart_application()
    
    def restart_application(self):
        """Restart the application"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

def open_settings(parent):
    """Open the settings window"""
    SettingsWindow(parent)

# For testing purposes
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window
    open_settings(root)
    root.mainloop()