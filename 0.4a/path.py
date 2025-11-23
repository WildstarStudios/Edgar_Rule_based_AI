#!/usr/bin/env python3
"""
File List Generator
Generates a complete list of all files in the current directory and subdirectories.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
import json
import datetime

class FileListGenerator:
    """Generates comprehensive file listings for a directory"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.file_count = 0
        self.total_size = 0
        
    def generate_file_list(self, 
                         include_hidden: bool = False,
                         include_size: bool = False,
                         include_date: bool = False,
                         max_depth: int = None,
                         output_format: str = "text") -> Dict:
        """
        Generate a comprehensive file listing.
        
        Args:
            include_hidden: Whether to include hidden files/folders
            include_size: Whether to include file sizes
            include_date: Whether to include modification dates
            max_depth: Maximum directory depth to traverse (None for unlimited)
            output_format: Output format - "text", "json", or "csv"
            
        Returns:
            Dictionary containing file listing and metadata
        """
        print(f"📁 Scanning directory: {self.root_dir}")
        
        files_data = []
        self.file_count = 0
        self.total_size = 0
        
        for file_path in self.root_dir.rglob('*'):
            # Skip directories, we only want files
            if not file_path.is_file():
                continue
                
            # Skip hidden files if not included
            if not include_hidden and self._is_hidden(file_path):
                continue
                
            # Check depth limit
            if max_depth is not None:
                depth = len(file_path.relative_to(self.root_dir).parts)
                if depth > max_depth:
                    continue
            
            # Get file info
            file_info = self._get_file_info(file_path, include_size, include_date)
            files_data.append(file_info)
            
            self.file_count += 1
            self.total_size += file_info.get('size_bytes', 0)
        
        # Sort files by path for consistent output
        files_data.sort(key=lambda x: x['relative_path'])
        
        result = {
            'metadata': {
                'directory': str(self.root_dir),
                'scan_date': datetime.datetime.now().isoformat(),
                'total_files': self.file_count,
                'total_size_bytes': self.total_size,
                'total_size_human': self._format_size(self.total_size),
                'include_hidden': include_hidden,
                'include_size': include_size,
                'include_date': include_date,
                'max_depth': max_depth
            },
            'files': files_data
        }
        
        return result
    
    def _get_file_info(self, file_path: Path, include_size: bool, include_date: bool) -> Dict:
        """Get detailed information about a file"""
        relative_path = file_path.relative_to(self.root_dir)
        
        file_info = {
            'relative_path': str(relative_path),
            'name': file_path.name,
            'extension': file_path.suffix.lower() if file_path.suffix else '',
            'depth': len(relative_path.parts) - 1
        }
        
        if include_size:
            size = file_path.stat().st_size
            file_info.update({
                'size_bytes': size,
                'size_human': self._format_size(size)
            })
        
        if include_date:
            mtime = file_path.stat().st_mtime
            file_info['modified'] = datetime.datetime.fromtimestamp(mtime).isoformat()
        
        return file_info
    
    def _is_hidden(self, file_path: Path) -> bool:
        """Check if a file or directory is hidden"""
        # Check for dot files (Unix hidden files)
        if file_path.name.startswith('.'):
            return True
        
        # On Windows, check file attributes
        if os.name == 'nt':
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
                return attrs != -1 and (attrs & 2)  # FILE_ATTRIBUTE_HIDDEN
            except:
                pass
        
        return False
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.2f} {size_names[i]}"
    
    def save_to_file(self, data: Dict, output_file: str, output_format: str = "text"):
        """Save the file listing to a file"""
        
        output_path = Path(output_file)
        
        if output_format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 JSON output saved to: {output_path}")
            
        elif output_format == "csv":
            self._save_as_csv(data, output_path)
            print(f"💾 CSV output saved to: {output_path}")
            
        else:  # text format
            self._save_as_text(data, output_path)
            print(f"💾 Text output saved to: {output_path}")
    
    def _save_as_text(self, data: Dict, output_path: Path):
        """Save file listing as formatted text"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 60 + "\n")
            f.write(f"FILE LISTING: {data['metadata']['directory']}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Scan Date: {data['metadata']['scan_date']}\n")
            f.write(f"Total Files: {data['metadata']['total_files']}\n")
            f.write(f"Total Size: {data['metadata']['total_size_human']}\n")
            f.write(f"Include Hidden: {data['metadata']['include_hidden']}\n")
            f.write("=" * 60 + "\n\n")
            
            # Write files
            for file_info in data['files']:
                line = file_info['relative_path']
                
                if 'size_human' in file_info:
                    line = f"{line} ({file_info['size_human']})"
                
                if 'modified' in file_info:
                    mod_date = datetime.datetime.fromisoformat(file_info['modified']).strftime('%Y-%m-%d %H:%M')
                    line = f"{line} - {mod_date}"
                
                f.write(line + "\n")
    
    def _save_as_csv(self, data: Dict, output_path: Path):
        """Save file listing as CSV"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            headers = ['Relative Path', 'Filename', 'Extension', 'Depth']
            if data['metadata']['include_size']:
                headers.extend(['Size (Bytes)', 'Size (Human)'])
            if data['metadata']['include_date']:
                headers.append('Last Modified')
            
            writer.writerow(headers)
            
            # Write data
            for file_info in data['files']:
                row = [
                    file_info['relative_path'],
                    file_info['name'],
                    file_info['extension'],
                    file_info['depth']
                ]
                
                if data['metadata']['include_size']:
                    row.extend([
                        file_info.get('size_bytes', ''),
                        file_info.get('size_human', '')
                    ])
                
                if data['metadata']['include_date']:
                    if 'modified' in file_info:
                        mod_date = datetime.datetime.fromisoformat(file_info['modified']).strftime('%Y-%m-%d %H:%M:%S')
                        row.append(mod_date)
                    else:
                        row.append('')
                
                writer.writerow(row)


def display_summary(data: Dict):
    """Display a summary of the file listing"""
    meta = data['metadata']
    
    print("\n" + "=" * 50)
    print("📊 SCAN SUMMARY")
    print("=" * 50)
    print(f"📁 Directory: {meta['directory']}")
    print(f"📅 Scan Date: {meta['scan_date']}")
    print(f"📄 Total Files: {meta['total_files']:,}")
    print(f"💾 Total Size: {meta['total_size_human']}")
    print(f"👁️  Include Hidden: {meta['include_hidden']}")
    print(f"📏 Include Sizes: {meta['include_size']}")
    print(f"📅 Include Dates: {meta['include_date']}")
    print(f"📈 Max Depth: {meta['max_depth'] or 'Unlimited'}")
    print("=" * 50)


def display_file_tree(data: Dict, max_files: int = 50):
    """Display files in a tree-like format"""
    files = data['files']
    meta = data['metadata']
    
    print(f"\n🌳 FILE TREE (showing first {min(max_files, len(files))} files):")
    print("─" * 60)
    
    for i, file_info in enumerate(files[:max_files]):
        indent = "  " * file_info['depth']
        file_display = f"{indent}📄 {file_info['relative_path']}"
        
        if meta['include_size']:
            file_display += f" ({file_info.get('size_human', '')})"
        
        print(file_display)
    
    if len(files) > max_files:
        print(f"  ... and {len(files) - max_files} more files")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Generate a complete list of all files in a directory and its subdirectories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # List all files in current directory
  %(prog)s /path/to/directory       # List files in specific directory
  %(prog)s --hidden                 # Include hidden files
  %(prog)s --size --date            # Include file sizes and dates
  %(prog)s --max-depth 2            # Limit to 2 directory levels deep
  %(prog)s --output files.json      # Save as JSON file
  %(prog)s --format csv             # Output in CSV format
  %(prog)s --tree                   # Display as tree structure
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    
    parser.add_argument(
        '--hidden', '-H',
        action='store_true',
        help='Include hidden files and directories'
    )
    
    parser.add_argument(
        '--size', '-s',
        action='store_true',
        help='Include file sizes'
    )
    
    parser.add_argument(
        '--date', '-d',
        action='store_true',
        help='Include modification dates'
    )
    
    parser.add_argument(
        '--max-depth', '-m',
        type=int,
        help='Maximum directory depth to traverse'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file name (default: print to console)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json', 'csv'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--tree', '-t',
        action='store_true',
        help='Display files in tree format'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress summary output'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = FileListGenerator(args.directory)
        
        # Generate file list
        data = generator.generate_file_list(
            include_hidden=args.hidden,
            include_size=args.size,
            include_date=args.date,
            max_depth=args.max_depth,
            output_format=args.format
        )
        
        # Display summary unless quiet
        if not args.quiet:
            display_summary(data)
        
        # Display tree view if requested
        if args.tree and not args.quiet:
            display_file_tree(data)
        
        # Save to file or print to console
        if args.output:
            generator.save_to_file(data, args.output, args.format)
        else:
            # Print to console
            if args.format == "json":
                print(json.dumps(data, indent=2, ensure_ascii=False))
            elif args.format == "csv":
                # For CSV output to console, we'll just show a preview
                print("CSV format requires --output parameter to save to file.")
                print("Here's a text preview:")
                print("\n".join([f['relative_path'] for f in data['files'][:20]]))
                if len(data['files']) > 20:
                    print(f"... and {len(data['files']) - 20} more files")
            else:
                # Text format to console
                for file_info in data['files']:
                    line = file_info['relative_path']
                    if args.size:
                        line += f" ({file_info.get('size_human', '')})"
                    if args.date and 'modified' in file_info:
                        mod_date = datetime.datetime.fromisoformat(file_info['modified']).strftime('%Y-%m-%d')
                        line += f" - {mod_date}"
                    print(line)
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()