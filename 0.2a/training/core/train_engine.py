import json
import os
import datetime

class ModelManager:
    def __init__(self, parent, on_model_change=None):
        self.parent = parent
        self.on_model_change = on_model_change
        # Save models in the training folder (one level above core)
        self.models_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
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
    
    def save_model(self, name, qa_groups):
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
                'qa_groups': []
            }
        
        model_data['qa_groups'] = qa_groups
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
        self.current_model = name
        return model_data
    
    def save_current_model(self):
        """Save current model with QA groups"""
        if not self.current_model:
            raise ValueError("No model selected")
        return self.model_manager.save_model(self.current_model, self.qa_groups)
    
    def update_model_info(self, description="", author="", version=""):
        """Update current model information"""
        if not self.current_model:
            raise ValueError("No model selected")
        return self.model_manager.update_model_info(self.current_model, description, author, version)
    
    def add_qa_group(self, group_data):
        """Add a new QA group"""
        self.qa_groups.append(group_data)
    
    def update_qa_group(self, index, group_data):
        """Update existing QA group"""
        if 0 <= index < len(self.qa_groups):
            self.qa_groups[index] = group_data
    
    def delete_qa_group(self, index):
        """Delete QA group by index"""
        if 0 <= index < len(self.qa_groups):
            self.qa_groups.pop(index)
    
    def get_qa_groups(self):
        """Get all QA groups"""
        return self.qa_groups
    
    def search_qa_groups(self, search_term, search_mode="both"):
        """Enhanced search QA groups based on criteria including questions and answers"""
        if not search_term:
            return self.qa_groups
        
        filtered_groups = []
        search_term_lower = search_term.lower()
        
        for group in self.qa_groups:
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
        """Import QA groups from JSON file"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_groups = []
        if isinstance(data, list):
            imported_groups = data
        else:
            imported_groups = [data]
        
        for i, qa in enumerate(imported_groups):
            self.qa_groups.append({
                'group_name': qa.get('group_name', f"Imported {i+1}"),
                'group_description': qa.get('group_description', "Imported from JSON"),
                'questions': qa.get('questions', []),
                'answers': qa.get('answers', []),
                'topic': qa.get('topic', 'general'),
                'priority': qa.get('priority', 'medium'),
                'follow_ups': qa.get('follow_ups', [])
            })
        
        return len(imported_groups)
    
    def export_to_json(self, filename):
        """Export QA groups to JSON file"""
        export_data = []
        for group in self.qa_groups:
            export_data.append({
                'group_name': group['group_name'],
                'group_description': group.get('group_description', ''),
                'questions': group['questions'],
                'answers': group['answers'],
                'topic': group['topic'],
                'priority': group['priority'],
                'follow_ups': group.get('follow_ups', [])
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
    
    @property
    def available_models(self):
        """Get available models from model manager"""
        return self.model_manager.available_models if self.model_manager else []
