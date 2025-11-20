import json
import os
import datetime

class ModelManager:
    def __init__(self, parent, on_model_change=None):
        self.parent = parent
        self.on_model_change = on_model_change
        self.models_folder = "models"
        self.current_model = None
        self.available_models = []
        
        os.makedirs(self.models_folder, exist_ok=True)
        self.load_available_models()
    
    def load_available_models(self):
        """Load all available models from the models folder"""
        self.available_models = []
        if os.path.exists(self.models_folder):
            for file in os.listdir(self.models_folder):
                if file.endswith('.json'):
                    model_name = file[:-5]
                    self.available_models.append(model_name)
        self.available_models.sort()
    
    def get_model_path(self, model_name):
        return os.path.join(self.models_folder, f"{model_name}.json")
    
    def create_model(self, name, description="", author="", version="1.0.0"):
        if not name.strip():
            raise ValueError("Model name cannot be empty")
        
        if name in self.available_models:
            raise ValueError(f"Model '{name}' already exists")
        
        model_data = {
            'name': name,
            'description': description,
            'author': author,
            'version': version,
            'created_at': datetime.datetime.now().isoformat(),
            'sections': ["General", "Technical", "Creative"],  # Default sections
            'qa_groups': []
        }
        
        model_path = self.get_model_path(name)
        with open(model_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
        
        self.load_available_models()
        self.current_model = name
        return model_data
    
    def load_model(self, name):
        if name not in self.available_models:
            raise ValueError(f"Model '{name}' not found")
        
        model_path = self.get_model_path(name)
        with open(model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        # Ensure sections exist for backward compatibility
        if 'sections' not in model_data:
            model_data['sections'] = ["General", "Technical", "Creative"]
        
        self.current_model = name
        return model_data
    
    def update_model_info(self, name, description="", author="", version=""):
        if name not in self.available_models:
            raise ValueError(f"Model '{name}' not found")
        
        model_path = self.get_model_path(name)
        with open(model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        if description is not None:
            model_data['description'] = description
        if author is not None:
            model_data['author'] = author
        if version is not None:
            model_data['version'] = version
        
        model_data['updated_at'] = datetime.datetime.now().isoformat()
        
        with open(model_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
        
        return model_data
    
    def save_model(self, name, qa_groups, sections=None):
        model_path = self.get_model_path(name)
        
        if os.path.exists(model_path):
            with open(model_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
        else:
            model_data = {
                'name': name,
                'description': f"Model {name}",
                'author': "",
                'version': "1.0.0",
                'created_at': datetime.datetime.now().isoformat(),
                'sections': ["General", "Technical", "Creative"],
                'qa_groups': []
            }
        
        model_data['qa_groups'] = qa_groups
        if sections is not None:
            model_data['sections'] = sections
        model_data['updated_at'] = datetime.datetime.now().isoformat()
        
        with open(model_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
        
        return model_data
    
    def delete_model(self, name):
        if name not in self.available_models:
            raise ValueError(f"Model '{name}' not found")
        
        model_path = self.get_model_path(name)
        os.remove(model_path)
        self.load_available_models()
        
        if self.current_model == name:
            self.current_model = None

class TrainingEngine:
    """Backend engine for training data management"""
    
    def __init__(self):
        self.model_manager = None
        self.current_model = None
        self.qa_groups = []
        self.sections = []
    
    def initialize_model_manager(self, parent):
        """Initialize model manager with parent reference"""
        self.model_manager = ModelManager(parent)
    
    def create_model(self, name, description="", author="", version="1.0.0"):
        """Create a new model"""
        return self.model_manager.create_model(name, description, author, version)
    
    def load_model(self, name):
        """Load a model"""
        model_data = self.model_manager.load_model(name)
        self.qa_groups = model_data.get('qa_groups', [])
        self.sections = model_data.get('sections', ["General", "Technical", "Creative"])
        self.current_model = name
        return model_data
    
    def save_current_model(self):
        """Save current model with QA groups and sections"""
        if not self.current_model:
            raise ValueError("No model selected")
        
        return self.model_manager.save_model(self.current_model, self.qa_groups, self.sections)
    
    def update_model_info(self, description="", author="", version=""):
        """Update current model information"""
        if not self.current_model:
            raise ValueError("No model selected")
        return self.model_manager.update_model_info(self.current_model, description, author, version)
    
    def update_sections(self, new_sections):
        """Update the sections list"""
        self.sections = new_sections
    
    def get_sections(self):
        """Get available sections"""
        return self.sections
    
    def move_group_to_section(self, group_index, section_name):
        """Move a group to a different section"""
        if 0 <= group_index < len(self.qa_groups):
            self.qa_groups[group_index]['section'] = section_name
    
    def get_groups_in_section(self, section_name):
        """Get all groups in a specific section"""
        return [group for group in self.qa_groups if group.get('section') == section_name]
    
    def handle_section_deletion(self, deleted_section, action, target_section=None):
        """Handle deletion of a section with various options for groups in that section"""
        groups_in_section = self.get_groups_in_section(deleted_section)
        
        if action == "move_to_uncategorized":
            for group in groups_in_section:
                group['section'] = ""
        elif action == "delete_groups":
            # Remove groups that are in the deleted section
            self.qa_groups = [group for group in self.qa_groups if group.get('section') != deleted_section]
        elif action == "move_to_section" and target_section:
            for group in groups_in_section:
                group['section'] = target_section
    
    def get_groups_by_section(self, section_filter):
        """Get groups filtered by section"""
        if section_filter == "All Sections":
            return self.qa_groups
        elif section_filter == "Uncategorized":
            return [group for group in self.qa_groups if not group.get('section')]
        else:
            return [group for group in self.qa_groups if group.get('section') == section_filter]
    
    def add_qa_group(self, group_data):
        """Add a new QA group"""
        # Ensure section is set, default to first section if not specified
        if 'section' not in group_data and self.sections:
            group_data['section'] = self.sections[0]
        self.qa_groups.append(group_data)
    
    def update_qa_group(self, index, group_data):
        """Update existing QA group"""
        if 0 <= index < len(self.qa_groups):
            # Preserve section if not specified in update
            if 'section' not in group_data:
                group_data['section'] = self.qa_groups[index].get('section', self.sections[0] if self.sections else "")
            self.qa_groups[index] = group_data
    
    def delete_qa_group(self, index):
        """Delete QA group by index"""
        if 0 <= index < len(self.qa_groups):
            self.qa_groups.pop(index)
    
    def get_qa_groups(self):
        """Get all QA groups"""
        return self.qa_groups
    
    def search_qa_groups(self, search_term, search_mode="both", section_filter="All Sections"):
        """Enhanced search QA groups based on criteria including questions, answers, and section"""
        # First filter by section
        if section_filter == "All Sections":
            groups_to_search = self.qa_groups
        elif section_filter == "Uncategorized":
            groups_to_search = [g for g in self.qa_groups if not g.get('section')]
        else:
            groups_to_search = [g for g in self.qa_groups if g.get('section') == section_filter]
        
        if not search_term:
            return groups_to_search
        
        filtered_groups = []
        search_term_lower = search_term.lower()
        
        for group in groups_to_search:
            match = False
            
            if search_mode == "both":
                # Search in name, description, questions, and answers
                match = (search_term_lower in group['group_name'].lower() or 
                        search_term_lower in group.get('group_description', '').lower() or
                        any(search_term_lower in q.lower() for q in group.get('questions', [])) or
                        any(search_term_lower in a.lower() for a in group.get('answers', [])))
            
            elif search_mode == "name":
                match = search_term_lower in group['group_name'].lower()
            
            elif search_mode == "description":
                match = search_term_lower in group.get('group_description', '').lower()
            
            elif search_mode == "questions":
                # Search only in questions
                match = any(search_term_lower in q.lower() for q in group.get('questions', []))
            
            elif search_mode == "answers":
                # Search only in answers
                match = any(search_term_lower in a.lower() for a in group.get('answers', []))
            
            if match:
                filtered_groups.append(group)
        
        return filtered_groups
    
    def get_stats(self):
        """Get training statistics"""
        total_questions = sum(len(g['questions']) for g in self.qa_groups)
        total_answers = sum(len(g['answers']) for g in self.qa_groups)
        total_followups = sum(self.count_followup_nodes(g.get('follow_ups', [])) for g in self.qa_groups)
        
        return {
            'groups': len(self.qa_groups),
            'questions': total_questions,
            'answers': total_answers,
            'followups': total_followups
        }
    
    def count_followup_nodes(self, data):
        """Count total nodes in follow-up tree"""
        count = 0
        for item in data:
            count += 1
            count += self.count_followup_nodes(item.get('children', []))
        return count
    
    def import_from_json(self, filename):
        """Import QA groups from JSON file - supports both full model format and QA groups only"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_groups = []
        
        # Check if it's a full model JSON or just QA groups
        if isinstance(data, dict) and 'qa_groups' in data:
            # Full model format - extract QA groups
            imported_groups = data['qa_groups']
            print(f"Imported {len(imported_groups)} QA groups from full model JSON")
        elif isinstance(data, list):
            # Direct QA groups format
            imported_groups = data
            print(f"Imported {len(imported_groups)} QA groups from QA groups JSON")
        else:
            # Single QA group or unexpected format
            imported_groups = [data]
            print(f"Imported 1 QA group from JSON")
        
        for i, qa in enumerate(imported_groups):
            group_data = {
                'group_name': qa.get('group_name', f"Imported {i+1}"),
                'group_description': qa.get('group_description', "Imported from JSON"),
                'questions': qa.get('questions', []),
                'answers': qa.get('answers', []),
                'topic': qa.get('topic', 'general'),
                'priority': qa.get('priority', 'medium'),
                'follow_ups': qa.get('follow_ups', []),
                'section': qa.get('section', self.sections[0] if self.sections else "")  # Add section with default
            }
            self.qa_groups.append(group_data)
        
        return len(imported_groups)
    
    def export_to_json(self, filename=None):
        """Export full model to JSON file with automatic filename generation"""
        if not self.current_model:
            raise ValueError("No model loaded for export")
        
        # Generate automatic filename if not provided
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.current_model}_{timestamp}.json"
        # Ensure .json extension if not present
        elif not filename.endswith('.json'):
            filename += '.json'
        
        # Get the full model data
        model_data = self.model_manager.load_model(self.current_model)
        
        # Update with current QA groups and sections (in case there are unsaved changes)
        model_data['qa_groups'] = self.qa_groups
        model_data['sections'] = self.sections
        model_data['exported_at'] = datetime.datetime.now().isoformat()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported full model '{self.current_model}' to {filename}")
        return filename
    
    def export_qa_groups_only(self, filename=None):
        """Export only QA groups to JSON (for backward compatibility)"""
        if not self.current_model:
            raise ValueError("No model loaded for export")
        
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.current_model}_qa_groups_{timestamp}.json"
        elif not filename.endswith('.json'):
            filename += '.json'
        
        export_data = []
        for group in self.qa_groups:
            export_data.append({
                'group_name': group['group_name'],
                'group_description': group.get('group_description', ''),
                'questions': group['questions'],
                'answers': group['answers'],
                'topic': group['topic'],
                'priority': group['priority'],
                'follow_ups': group.get('follow_ups', []),
                'section': group.get('section', '')  # Include section in export
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported QA groups from '{self.current_model}' to {filename}")
        return filename
    
    @property
    def available_models(self):
        """Get available models from model manager"""
        return self.model_manager.available_models if self.model_manager else []
