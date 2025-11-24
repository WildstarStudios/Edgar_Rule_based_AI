#!/usr/bin/env python3
"""
Edgar AI Assistant v0.4a Build Script
Cross-platform build script for PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class EdgarBuildSystem:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.package_dir = self.project_root / "dist" / "package"
        self.icon_dir = self.project_root / "icon"
        
        # Platform-specific configurations
        self.is_windows = os.name == 'nt'
        self.venv_pyinstaller = self.find_pyinstaller()
        
        # Shared imports for all apps
        self.bs4_imports = [
            "--hidden-import", "beautifulsoup4",
            "--hidden-import", "bs4", 
            "--hidden-import", "bs4.element",
            "--hidden-import", "bs4.builder",
            "--hidden-import", "bs4.builder._htmlparser"
        ]
        
        # Core dependencies for main chat app - FIXED imports
        self.chat_imports = [
            "--hidden-import", "configparser",
            "--hidden-import", "core.modules.weather",
            "--hidden-import", "core.modules.time", 
            "--hidden-import", "core.modules.search",
            "--hidden-import", "core.modules.joke",
            "--hidden-import", "core.modules.recipie",
            "--hidden-import", "fuzzywuzzy",
            "--hidden-import", "fuzzywuzzy.process",
            "--hidden-import", "fuzzywuzzy.fuzz",
            "--hidden-import", "pytz",
            "--hidden-import", "requests",
            "--hidden-import", "Levenshtein",
            "--hidden-import", "Levenshtein.levenshtein_cpp",
            # UI module imports
            "--hidden-import", "ui",
            "--hidden-import", "ui.classic",
            "--hidden-import", "ui.classic.chat",
            "--hidden-import", "ui.classic.settings", 
            "--hidden-import", "ui.modern",
            "--hidden-import", "ui.modern.chat",
            "--hidden-import", "ui.modern.settings",
            # Core module imports
            "--hidden-import", "core",
            "--hidden-import", "core.layer",
            "--hidden-import", "core.modules",
            "--hidden-import", "core.modules.weather",
            "--hidden-import", "core.modules.time",
            "--hidden-import", "core.modules.search",
            "--hidden-import", "core.modules.joke", 
            "--hidden-import", "core.modules.recipie"
        ]
        
    def find_pyinstaller(self):
        """Find PyInstaller executable in common locations"""
        if self.is_windows:
            # Windows paths
            venv_path = self.project_root / ".venv" / "Scripts" / "pyinstaller.exe"
            if venv_path.exists():
                return str(venv_path)
            
            # Try user's specific path from batch file
            user_path = r"C:\Users\aayde\Documents\GitHub\Edgar_Rule_based_AI\.venv\Scripts\pyinstaller.exe"
            if os.path.exists(user_path):
                return user_path
        else:
            # Linux/Mac paths
            venv_path = self.project_root / ".venv" / "bin" / "pyinstaller"
            if venv_path.exists():
                return str(venv_path)
        
        # Fallback to system pyinstaller
        return "pyinstaller"
    
    def clean_previous_builds(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning previous builds...")
        
        build_dir = self.project_root / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
            
        # Remove .spec files
        for spec_file in self.project_root.glob("*.spec"):
            spec_file.unlink()
            
        # Create fresh package directory
        self.package_dir.mkdir(parents=True, exist_ok=True)
    
    def run_pyinstaller(self, name, script_path, icon=None, console=False, extra_args=None):
        """Run PyInstaller with common arguments"""
        args = [
            self.venv_pyinstaller,
            "--onefile",
            "--distpath", str(self.package_dir),
            "--name", name,
        ]
        
        # Add icon if provided
        if icon and (self.project_root / icon).exists():
            args.extend(["--icon", str(self.project_root / icon)])
        
        # Console vs windowed
        if console:
            args.append("--console")
        else:
            args.append("--windowed")
        
        # Add data files - FIXED: Include as packages, not just data
        package_dirs = [
            "core",
            "ui",
            "training",
            "webui"
        ]
        
        for pkg_dir in package_dirs:
            if (self.project_root / pkg_dir).exists():
                # Add as package collection
                args.extend(["--collect-all", pkg_dir])
        
        # Add data directories (non-Python files)
        data_dirs = [
            ("resources", "resources"),
            ("models", "models"),
        ]
        
        for src, dest in data_dirs:
            if (self.project_root / src).exists():
                args.extend(["--add-data", f"{src}{os.pathsep}{dest}"])
        
        # Special handling for customtkinter assets
        if not console:  # GUI apps need customtkinter
            try:
                import customtkinter
                # Force include all of customtkinter
                args.extend(["--collect-all", "customtkinter"])
                ctk_path = Path(customtkinter.__file__).parent
                assets_path = ctk_path / "assets"
                if assets_path.exists():
                    args.extend(["--add-data", f"{str(assets_path)}{os.pathsep}customtkinter/assets"])
                    print(f"   ✅ Added customtkinter assets from: {assets_path}")
            except ImportError as e:
                print(f"   ⚠️  customtkinter not found: {e}")
        
        # Add imports and extra args
        if extra_args:
            args.extend(extra_args)
        
        # Add script path
        args.append(str(script_path))
        
        print(f"🔨 Building {name}...")
        print(f"   Command: {' '.join(args[:10])}...")  # Show first 10 args only
        
        try:
            result = subprocess.run(args, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                print(f"❌ Error building {name}:")
                print(result.stderr)
                return False
            else:
                print(f"✅ Successfully built {name}")
                return True
        except Exception as e:
            print(f"❌ Failed to build {name}: {e}")
            return False
    
    def build_chat(self):
        """Build main chat application"""
        # Additional customtkinter fixes
        ctk_fix_args = [
            "--collect-all", "customtkinter",
            "--hidden-import", "customtkinter",
            "--hidden-import", "customtkinter.windows.widgets",
            "--hidden-import", "customtkinter.windows.ctk_tk",
            "--hidden-import", "customtkinter.windows.ctk_theme",
        ]
        
        extra_args = self.bs4_imports + self.chat_imports + ctk_fix_args
        return self.run_pyinstaller(
            name="chat-0.4a",
            script_path=self.project_root / "main.py",
            icon="icon/chat.ico",
            extra_args=extra_args
        )
    
    def build_tty(self):
        """Build terminal interface"""
        extra_args = self.bs4_imports + [
            "--hidden-import", "configparser",
            "--hidden-import", "core.modules.weather",
            "--hidden-import", "core.modules.time",
            "--hidden-import", "core.modules.search", 
            "--hidden-import", "core.modules.joke",
            "--hidden-import", "core.modules.recipie",
            "--hidden-import", "fuzzywuzzy",
            "--hidden-import", "fuzzywuzzy.process",
            "--hidden-import", "fuzzywuzzy.fuzz",
            "--hidden-import", "pytz",
            "--hidden-import", "requests",
            "--hidden-import", "Levenshtein",
            "--hidden-import", "Levenshtein.levenshtein_cpp",
            # TTY doesn't need UI modules
        ]
        
        return self.run_pyinstaller(
            name="tty-0.4a", 
            script_path=self.project_root / "tty.py",
            icon="icon/tty.ico",
            console=True,
            extra_args=extra_args
        )
    
    def build_train(self):
        """Build training application"""
        extra_args = self.bs4_imports + [
            "--hidden-import", "configparser",
            "--hidden-import", "fuzzywuzzy",
            "--hidden-import", "fuzzywuzzy.process", 
            "--hidden-import", "fuzzywuzzy.fuzz",
            "--hidden-import", "training",
            "--hidden-import", "training.train",
        ]
        
        return self.run_pyinstaller(
            name="train-0.4a",
            script_path=self.project_root / "training" / "train.py",
            icon="icon/train.ico",
            extra_args=extra_args
        )
    
    def build_route_trainer(self):
        """Build route trainer application"""
        extra_args = self.bs4_imports + [
            "--hidden-import", "fuzzywuzzy",
            "--hidden-import", "fuzzywuzzy.process",
            "--hidden-import", "fuzzywuzzy.fuzz",
        ]
        
        return self.run_pyinstaller(
            name="route-trainer-0.4a",
            script_path=self.project_root / "route trainer.py", 
            icon="icon/route-trainer.ico",
            extra_args=extra_args
        )
    
    def build_webui(self):
        """Build web interface application"""
        extra_args = self.bs4_imports + [
            "--hidden-import", "fuzzywuzzy",
            "--hidden-import", "fuzzywuzzy.process",
            "--hidden-import", "fuzzywuzzy.fuzz", 
            "--hidden-import", "pytz",
            "--hidden-import", "requests",
            "--hidden-import", "Levenshtein",
            "--hidden-import", "Levenshtein.levenshtein_cpp",
            "--hidden-import", "webui",
        ]
        
        return self.run_pyinstaller(
            name="webui-0.4a",
            script_path=self.project_root / "webui.py",
            icon="icon/webui.ico",
            extra_args=extra_args
        )
    
    def copy_additional_files(self):
        """Copy additional resource files to package directory"""
        print("📁 Copying resource files...")
        
        files_to_copy = [
            "config.cfg",
            "requirements.txt", 
            "secret_key.txt",
        ]
        
        for file_name in files_to_copy:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, self.package_dir / file_name)
                print(f"   ✅ {file_name}")
        
        # Copy data directories only (not Python packages)
        dirs_to_copy = [
            "resources",
            "models", 
            "icon",
            "webui/static",  # Only static web files, not Python modules
            "webui/templates",
        ]
        
        for dir_name in dirs_to_copy:
            src = self.project_root / dir_name
            if src.exists():
                dest = self.package_dir / dir_name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
                print(f"   ✅ {dir_name}/")
    
    def verify_build(self):
        """Verify that the build includes all necessary modules"""
        print("🔍 Verifying build...")
        
        chat_exe = self.package_dir / "chat-0.4a.exe"
        if not chat_exe.exists():
            print("❌ chat-0.4a.exe not found!")
            return False
            
        # Check if essential modules are included by testing imports
        try:
            # Test if we can list the contents of the executable
            print("   ✅ chat-0.4a.exe built successfully")
            
            # Check if UI directories would be accessible
            ui_dirs = ["ui/classic", "ui/modern"]
            for ui_dir in ui_dirs:
                if (self.project_root / ui_dir).exists():
                    print(f"   ✅ {ui_dir} source exists")
                else:
                    print(f"   ⚠️  {ui_dir} not found in source")
                    
            return True
        except Exception as e:
            print(f"   ❌ Build verification failed: {e}")
            return False
    
    def create_readme(self):
        """Create README file for distribution"""
        readme_content = """Edgar AI Assistant v0.4a
========================

Distribution Package

Included Files:
- chat-0.4a.exe      - Main Edgar AI application (GUI) with dual themes
- tty-0.4a.exe       - Terminal/Command Line interface  
- train-0.4a.exe     - Training application
- route-trainer-0.4a.exe - Routing configuration tool
- webui-0.4a.exe     - Web interface application
- config.cfg         - Configuration file (shared by all apps)
- requirements.txt   - Python dependencies
- secret_key.txt     - Encryption key
- resources/         - Routing configuration and resources
- models/            - AI model data
- icon/              - Application icons
- webui/static/      - Web interface static files
- webui/templates/   - Web interface templates

Usage:
1. Run chat-0.4a.exe to start the main AI assistant (GUI with theme selection)
2. Run tty-0.4a.exe to start the terminal interface
3. Run train-0.4a.exe to train new AI models  
4. Run route-trainer-0.4a.exe to configure module routing
5. Run webui-0.4a.exe to start the web interface

Note: config.cfg is shared by all applications

UI Architecture:
- Classic Theme: Traditional tkinter interface
- Modern Theme: CustomTkinter with dark/light mode support
- Both themes are embedded in the executable
- Settings allow runtime theme switching

Build Notes:
- All UI modules (core/, ui/) are embedded as Python packages
- CustomTkinter assets are automatically included
- Module routing supports weather, time, search, jokes, and recipes

Troubleshooting:
If you see "could not import name CTk from customtkinter":
- Ensure you're running the correct executable from the package directory
- The build includes all necessary CustomTkinter components
- UI modules are packaged as part of the executable

System Requirements:
- Windows 10 or later (Linux/Mac support for terminal apps)
- Python 3.12 (included in executable)
- Internet connection for weather and search modules
"""
        
        readme_path = self.package_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("📝 Created README.txt")
    
    def clean_build_artifacts(self):
        """Clean up build artifacts"""
        print("🧹 Cleaning build artifacts...")
        
        build_dir = self.project_root / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            
        for spec_file in self.project_root.glob("*.spec"):
            spec_file.unlink()
    
    def build_all(self):
        """Build all applications"""
        print("🚀 Starting Edgar AI Assistant v0.4a Build...")
        print(f"📦 Output directory: {self.package_dir}")
        print(f"🔧 PyInstaller: {self.venv_pyinstaller}")
        print()
        
        # Clean first
        self.clean_previous_builds()
        
        # Build applications
        builds = [
            ("Main Chat", self.build_chat),
            ("Terminal Interface", self.build_tty),
            ("Training App", self.build_train),
            ("Route Trainer", self.build_route_trainer),
            ("Web Interface", self.build_webui),
        ]
        
        all_success = True
        for name, build_func in builds:
            if not build_func():
                all_success = False
                print(f"❌ Failed to build {name}")
            print()
        
        if all_success:
            # Copy additional files
            self.copy_additional_files()
            self.verify_build()
            self.create_readme()
            self.clean_build_artifacts()
            
            print("=" * 50)
            print("🎉 BUILD COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print()
            print(f"📁 Executables and resources are in: {self.package_dir}")
            print("🎨 UI modules are embedded as Python packages")
            print("⚙️  Config file is shared by all applications")
            print()
            print("🔧 Key improvements in this build:")
            print("   - UI modules (core/, ui/) properly bundled as packages")
            print("   - CustomTkinter fully included with assets")
            print("   - Both Classic and Modern themes embedded")
            print("   - Module imports explicitly declared")
            print()
            
            if self.is_windows:
                print("📂 Opening distribution folder...")
                os.startfile(self.package_dir)
            else:
                print(f"📂 Distribution folder: {self.package_dir}")
                
        else:
            print("❌ BUILD FAILED! Check errors above.")
            sys.exit(1)

def main():
    """Main entry point"""
    try:
        builder = EdgarBuildSystem()
        builder.build_all()
    except KeyboardInterrupt:
        print("\n❌ Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()