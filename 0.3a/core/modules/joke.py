# core/modules/joke.py
from fuzzywuzzy import fuzz

module_mode = True  # Enable multi-turn mode
strict_matching = True  # Enable strict matching for this module

def get_expected_patterns():
    """Define patterns that this module expects to handle"""
    return [
        "joke", "funny", "humor", "laugh", "punchline",
        "animal joke", "programming joke", "random joke",
        "tell me a joke", "make me laugh", "another joke",
        "yes", "no", "done", "stop", "more", "again",
        "funny", "animal", "programming", "random",
        "punchline", "tell me", "what kind", "which type"
    ]

def process(user_input, api):
    # Get or initialize user's joke state from module context
    user_context = api.get_module_context()
    if 'joke_state' not in user_context:
        user_context['joke_state'] = {
            'step': 0,
            'joke_type': None,
            'setup_delivered': False,
            'punchline_delivered': False
        }
        api.set_module_context(user_context)
    
    state = user_context['joke_state']
    input_lower = user_input.lower()
    
    # Check for completion signals FIRST
    if _fuzzy_match_done(input_lower):
        return _handle_completion_request(state, api)
    
    # Joke interaction flow with fuzzy matching - REORDERED: Check step-specific logic FIRST
    if state['step'] == 0:
        # First interaction - ask for joke type
        state['step'] = 1
        api.set_module_context(user_context)
        
        return [("I'd love to tell you a joke! What kind of joke would you like?\n\n"
                "• **Funny** - General humor\n"
                "• **Animal** - Animal jokes\n" 
                "• **Programming** - Tech humor\n"
                "• **Random** - Surprise me!\n\n"
                "Just say which type you'd like!", 1.0, "Joke Module")]
    
    elif state['step'] == 1:
        # Process joke type selection with fuzzy matching
        joke_type_keywords = {
            "funny": ["funny", "humor", "laugh", "comedy", "hilarious"],
            "animal": ["animal", "pet", "dog", "cat", "bird", "fish", "zoo"],
            "programming": ["programming", "tech", "code", "computer", "software", "developer"],
            "random": ["random", "surprise", "any", "whatever", "don't care"]
        }
        
        best_match = None
        best_score = 0
        
        for joke_type, keywords in joke_type_keywords.items():
            for keyword in keywords:
                similarity = fuzz.token_set_ratio(input_lower, keyword)
                if similarity > best_score:
                    best_score = similarity
                    best_match = joke_type
        
        # STRICT MATCHING: Require 85% similarity for joke type selection
        if best_score >= 85:
            # Valid joke type selected
            state['step'] = 2
            state['joke_type'] = best_match
            state['setup_delivered'] = False
            api.set_module_context(user_context)
            
            # Get joke setup based on type
            setup = _get_joke_setup(best_match)
            
            return [(f"Great choice! Here's a {best_match} joke:\n\n"
                    f"**{setup}**\n\n"
                    "Ready for the punchline? Just say 'yes', 'tell me', or 'punchline'!", 
                    1.0, "Joke Module")]
        else:
            # Invalid input for joke type - signal to move to next module with LOW confidence
            return [("I'm not sure what kind of joke you want. Please choose from: funny, animal, programming, or random.", 0.3, "Joke Module")]
    
    elif state['step'] == 2:
        # DELIVER PUNCHLINE - Check affirmative responses FIRST before other module detection
        affirmative_keywords = ["yes", "punchline", "tell me", "sure", "go ahead", "ok", "okay", "please", "continue", "yeah", "yep"]
        
        best_affirmative_score = 0
        for keyword in affirmative_keywords:
            similarity = fuzz.token_set_ratio(input_lower, keyword)
            if similarity > best_affirmative_score:
                best_affirmative_score = similarity
        
        # STRICT MATCHING: Require 80% similarity for affirmative responses
        if best_affirmative_score >= 80:
            # User wants the punchline - DELIVER AND DEACTIVATE
            state['punchline_delivered'] = True
            api.set_module_context(user_context)
            
            # Get punchline based on joke type
            punchline = _get_joke_punchline(state['joke_type'])
            
            # DEACTIVATE MODULE after punchline
            return _handle_punchline_completion(punchline, api)
        
        # ONLY AFTER checking for punchline requests, check for other module keywords
        other_module_keywords = ['time', 'weather', 'news', 'calculate', 'remind', 'timer', 'alarm', 'what is', 'how is', 'tell me about', 'recipe', 'cook', 'food']
        
        # Use fuzzy matching to detect if this is for another module
        max_similarity = 0
        for keyword in other_module_keywords:
            similarity = fuzz.token_set_ratio(input_lower, keyword)
            if similarity > max_similarity:
                max_similarity = similarity
        
        # If high similarity to other module keywords and we're in the middle of a joke, pass with 0.95 confidence
        if max_similarity >= 75:
            return [("I think you're trying to use another feature. If you want to continue with jokes, say 'another' or 'done'. Otherwise, I'll let another module handle your request.", 0.95, "Joke Module")]
        else:
            # User said something else - this might not be joke-related
            return [("Should I tell you the punchline? Just say 'yes' or 'punchline'!", 0.4, "Joke Module")]
    
    # Fallback for unexpected state
    return [("Hmm, I lost my place in the joke! Let's start over.\n\n"
            "Would you like to hear a joke? Just say what type you'd like!", 
            0.2, "Joke Module")]

def _fuzzy_match_done(user_input):
    """Fuzzy matching for completion requests"""
    done_keywords = [
        "thank you", "thanks", "that's all", "that is all", "im done", 
        "i'm done", "all done", "finished", "no more", "that'll be all",
        "im good", "i'm good", "no thanks", "not now", "maybe later",
        "that's it", "that is it", "im finished", "i'm finished"
    ]
    return any(fuzz.token_set_ratio(user_input, keyword) >= 75 for keyword in done_keywords)

def _handle_completion_request(state, api):
    """Handle completion requests - DEACTIVATES the module"""
    # Clear the context
    api.set_module_context({})
    
    # Set module_mode to False to deactivate
    global module_mode
    module_mode = False
    
    return [("Thanks for the laughs! 😄\n\n"
            "I'm switching back to normal mode. What would you like to talk about now?", 
            1.0, "Joke Module")]

def _handle_punchline_completion(punchline, api):
    """Handle punchline delivery and deactivate module"""
    # Clear the context
    api.set_module_context({})
    
    # Set module_mode to False to deactivate
    global module_mode
    module_mode = False
    
    return [(f"**{punchline}**\n\n"
            "😂 Hope that made you smile!\n\n"
            "I'm switching back to normal mode. What would you like to do next?", 
            1.0, "Joke Module")]

def _get_joke_setup(joke_type):
    """Get joke setup based on type"""
    jokes = {
        "funny": "Why don't scientists trust atoms?",
        "animal": "What do you call a fish wearing a crown?",
        "programming": "Why do programmers prefer dark mode?",
        "random": "Why did the scarecrow win an award?"
    }
    return jokes.get(joke_type, "Why was the math book sad?")

def _get_joke_punchline(joke_type):
    """Get joke punchline based on type"""
    punchlines = {
        "funny": "Because they make up everything!",
        "animal": "A kingfish! 👑🐟", 
        "programming": "Because light attracts bugs! 🐛",
        "random": "Because he was outstanding in his field! 🌾"
    }
    return punchlines.get(joke_type, "Because it had too many problems!")