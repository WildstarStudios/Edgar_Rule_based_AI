import customtkinter as ctk
from customtkinter import CTk, CTkToplevel, CTkFrame, CTkLabel, CTkButton, CTkScrollableFrame, CTkRadioButton, StringVar
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
            'hover_secondary': '#35356a'
        }
        
        # Configure CTk theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        
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
        self.window = CTkToplevel(self.parent)
        self.window.title("Settings - Edgar AI Assistant")
        self.window.geometry("500x400")
        self.window.resizable(True, True)
        self.window.configure(fg_color=self.colors['bg_primary'])
        
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
        main_frame = CTkScrollableFrame(
            self.window, 
            fg_color=self.colors['bg_primary'],
            scrollbar_button_color=self.colors['accent_primary'],
            scrollbar_button_hover_color=self.colors['hover_primary']
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = CTkLabel(
            main_frame, 
            text="Settings", 
            font=('Arial', 18, 'bold'),
            text_color=self.colors['text_primary']
        )
        title_label.pack(pady=(0, 20))
        
        # Theme Selection Section
        theme_frame = CTkFrame(
            main_frame, 
            fg_color=self.colors['bg_secondary'],
            border_color=self.colors['border'],
            border_width=1
        )
        theme_frame.pack(fill="x", pady=(0, 20))
        
        # Theme header
        theme_header = CTkLabel(
            theme_frame,
            text="THEME SELECTION",
            font=('Arial', 12, 'bold'),
            text_color=self.colors['text_primary']
        )
        theme_header.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Theme description
        theme_desc = CTkLabel(
            theme_frame,
            text="Choose the visual theme for the application. Changes will take effect after restart.",
            font=('Arial', 9),
            text_color=self.colors['text_primary'],
            wraplength=400,
            justify='left'
        )
        theme_desc.pack(anchor='w', padx=15, pady=(0, 15))
        
        # Theme options frame
        theme_options_frame = CTkFrame(theme_frame, fg_color="transparent")
        theme_options_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Current theme
        current_theme = self.config.get('gui', 'theme', fallback='classic')
        self.theme_var = StringVar(value=current_theme)
        
        # Classic theme option
        classic_frame = CTkFrame(theme_options_frame, fg_color="transparent")
        classic_frame.pack(fill="x", pady=5)
        
        classic_radio = CTkRadioButton(
            classic_frame,
            text="Classic Theme",
            variable=self.theme_var,
            value="classic",
            font=('Arial', 10),
            fg_color=self.colors['accent_primary'],
            hover_color=self.colors['hover_primary'],
            text_color=self.colors['text_primary']
        )
        classic_radio.pack(side="left")
        
        classic_desc = CTkLabel(
            classic_frame,
            text="Dark blue theme with purple accents",
            font=('Arial', 9),
            text_color=self.colors['text_primary'],
            justify='left'
        )
        classic_desc.pack(side="left", padx=(10, 0))
        
        # Modern theme option  
        modern_frame = CTkFrame(theme_options_frame, fg_color="transparent")
        modern_frame.pack(fill="x", pady=5)
        
        modern_radio = CTkRadioButton(
            modern_frame,
            text="Modern Theme",
            variable=self.theme_var,
            value="modern",
            font=('Arial', 10),
            fg_color=self.colors['accent_primary'],
            hover_color=self.colors['hover_primary'],
            text_color=self.colors['text_primary']
        )
        modern_radio.pack(side="left")
        
        modern_desc = CTkLabel(
            modern_frame,
            text="Dark gray theme with blue accents",
            font=('Arial', 9),
            text_color=self.colors['text_primary'],
            justify='left'
        )
        modern_desc.pack(side="left", padx=(10, 0))
        
        # Current Settings Section
        current_frame = CTkFrame(
            main_frame, 
            fg_color=self.colors['bg_secondary'],
            border_color=self.colors['border'],
            border_width=1
        )
        current_frame.pack(fill="x", pady=(0, 20))
        
        # Current settings header
        current_header = CTkLabel(
            current_frame,
            text="CURRENT SETTINGS",
            font=('Arial', 12, 'bold'),
            text_color=self.colors['text_primary']
        )
        current_header.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Display current settings
        settings_text = f"""Current Configuration:
• Theme: {current_theme.title()}
• Window Size: {self.config.get('gui', 'window_width', fallback='1000')}x{self.config.get('gui', 'window_height', fallback='700')}
• Streaming: {self.config.get('gui', 'streaming_enabled', fallback='True')}
• Verbose Mode: {self.config.get('gui', 'verbose_mode', fallback='False')}

All settings are stored in config.cfg"""
        
        current_settings = CTkLabel(
            current_frame,
            text=settings_text,
            font=('Arial', 9),
            text_color=self.colors['text_primary'],
            justify='left'
        )
        current_settings.pack(anchor='w', padx=15, pady=(0, 15))
        
        # Buttons frame
        buttons_frame = CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Apply and Restart button
        apply_btn = CTkButton(
            buttons_frame,
            text="Apply and Restart",
            command=self.apply_and_restart,
            fg_color=self.colors['accent_primary'],
            hover_color=self.colors['hover_primary'],
            text_color=self.colors['text_primary'],
            font=('Arial', 10, 'bold')
        )
        apply_btn.pack(side="right", padx=(10, 0))
        
        # Cancel button
        cancel_btn = CTkButton(
            buttons_frame,
            text="Cancel",
            command=self.window.destroy,
            fg_color=self.colors['bg_secondary'],
            hover_color=self.colors['hover_secondary'],
            text_color=self.colors['text_primary'],
            font=('Arial', 10)
        )
        cancel_btn.pack(side="right")
    
    def apply_and_restart(self):
        """Apply settings and restart the application"""
        selected_theme = self.theme_var.get()
        
        # Update config with selected theme
        if not self.config.has_section('gui'):
            self.config.add_section('gui')
        
        self.config.set('gui', 'theme', selected_theme)
        
        # Save config
        self.save_config()
        
        # Show confirmation message using CTkMessagebox
        CTkMessagebox.show_info(
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

# CTkMessagebox implementation for CustomTkinter
class CTkMessagebox:
    @staticmethod
    def show_info(title, message):
        # For now, use tkinter messagebox as fallback
        # In production, you might want to create a proper CTk dialog
        import tkinter.messagebox as mb
        mb.showinfo(title, message)

def open_settings(parent):
    """Open the settings window"""
    SettingsWindow(parent)

# For testing purposes
if __name__ == "__main__":
    root = CTk()
    root.withdraw()  # Hide main window
    open_settings(root)
    root.mainloop()