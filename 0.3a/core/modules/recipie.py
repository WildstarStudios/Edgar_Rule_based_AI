# core/modules/recipe.py
from fuzzywuzzy import fuzz

module_mode = True  # Enable multi-turn mode - NEVER set this to False in process function
strict_matching = True  # Enable strict matching for this module

def get_expected_patterns():
    """Define patterns that this module expects to handle"""
    return [
        "recipe", "cook", "food", "meal", "dish", "cooking", "baking",
        "ingredients", "kitchen", "how to cook", "how to make", "recipe for",
        "what can i cook", "dinner idea", "lunch idea", "breakfast idea",
        "breakfast", "dinner", "lunch", "snack", "dessert", "appetizer",
        "vegetarian", "vegan", "gluten free", "healthy", "low carb", "keto",
        "easy recipe", "quick recipe", "simple recipe", "fast meal",
        "what should i eat", "hungry", "meal prep", "cookbook",
        "something else", "other", "different", "another option",
        "more options", "what else", "other choices", "alternatives"
    ]

def process(user_input, api):
    # Get or initialize user's recipe state from module context
    user_context = api.get_module_context()
    if 'recipe_state' not in user_context:
        user_context['recipe_state'] = {
            'step': 0,
            'recipe_type': None,
            'dietary_restrictions': [],
            'ingredients_provided': False,
            'last_recipe': None,
            'current_options': []
        }
        api.set_module_context(user_context)
    
    state = user_context['recipe_state']
    input_lower = user_input.lower()
    
    # Check for completion signals FIRST - these will deactivate the module
    if _fuzzy_match_done(input_lower):
        return _handle_completion_request(state, api)
    
    # Then check for "something else" requests
    if _fuzzy_match_something_else(input_lower):
        return _handle_something_else_request(state, api)
    
    # Enhanced fuzzy matching for common food categories and ingredients
    if state['step'] == 0:
        # First interaction - detect if user is asking for a specific type of recipe
        detected_category = _fuzzy_detect_category(input_lower)
        if detected_category:
            state['step'] = 2
            state['recipe_type'] = detected_category
            api.set_module_context(user_context)
            
            recipe_suggestion = _get_recipe_suggestion(detected_category)
            state['last_recipe'] = detected_category
            state['current_options'] = ["instructions", "dietary", "different", "similar", "something else"]
            
            return [(f"Great! I love {detected_category} recipes! 🎉\n\n"
                    f"{recipe_suggestion}\n\n"
                    "Would you like the full instructions, dietary adjustments, a different recipe, or something else?", 
                    1.0, "Recipe Module")]
        
        # Standard greeting
        state['step'] = 1
        state['current_options'] = ["breakfast", "lunch", "dinner", "dessert", "snacks", "healthy", "ingredients", "something else"]
        api.set_module_context(user_context)
        
        return [("I'd love to help you cook something delicious! 🍳\n\n"
                "What are you in the mood for?\n\n"
                "• **Breakfast** 🥞 - Pancakes, eggs, smoothies\n"
                "• **Lunch** 🥪 - Sandwiches, salads, soups\n" 
                "• **Dinner** 🍝 - Pasta, chicken, stir-fry\n"
                "• **Dessert** 🍪 - Cakes, cookies, pies\n"
                "• **Snacks** 🥑 - Quick bites and appetizers\n"
                "• **Healthy** 🥗 - Low-calorie, nutritious options\n\n"
                "Or tell me what ingredients you have on hand!\n\n"
                "You can always say 'something else' for more options!", 1.0, "Recipe Module")]
    
    elif state['step'] == 1:
        # Process recipe type selection with enhanced fuzzy matching
        detected_category = _fuzzy_detect_category(input_lower)
        
        # Also check for ingredients
        detected_ingredients = _fuzzy_detect_ingredients(input_lower)
        
        if detected_ingredients:
            state['step'] = 2
            state['ingredients_provided'] = True
            state['recipe_type'] = "custom"
            state['current_options'] = ["instructions", "different", "something else"]
            api.set_module_context(user_context)
            
            custom_recipe = _get_recipe_from_ingredients(detected_ingredients)
            state['last_recipe'] = "custom"
            
            return [(f"Perfect! Let me suggest something with {', '.join(detected_ingredients[:3])}...\n\n"
                    f"{custom_recipe}\n\n"
                    "Would you like cooking instructions, a different recipe, or something else?", 
                    1.0, "Recipe Module")]
        
        if detected_category:
            state['step'] = 2
            state['recipe_type'] = detected_category
            state['current_options'] = ["instructions", "dietary", "different", "similar", "something else"]
            api.set_module_context(user_context)
            
            recipe_suggestion = _get_recipe_suggestion(detected_category)
            state['last_recipe'] = detected_category
            
            return [(f"Excellent choice! {detected_category.title()} it is! 🎉\n\n"
                    f"{recipe_suggestion}\n\n"
                    "Would you like cooking instructions, dietary adjustments, a different recipe, or something else?", 
                    1.0, "Recipe Module")]
        else:
            # Didn't understand the recipe type - LOW confidence to pass to next module
            state['current_options'] = ["breakfast", "lunch", "dinner", "dessert", "snacks", "healthy", "ingredients", "something else"]
            return [("I'm not quite sure what you're craving! 🤔\n\n"
                    "Try saying: breakfast, lunch, dinner, dessert, snacks, healthy, or tell me what ingredients you have!\n\n"
                    "Or say 'something else' for more options!",
                    0.3, "Recipe Module")]
    
    elif state['step'] == 2:
        # Handle instructions, dietary restrictions, or new requests
        dietary_restrictions = _fuzzy_detect_dietary(input_lower)
        wants_instructions = _fuzzy_match_instructions(input_lower)
        wants_different = _fuzzy_match_different(input_lower)
        wants_similar = _fuzzy_match_similar(input_lower)
        
        if dietary_restrictions:
            state['dietary_restrictions'].extend(dietary_restrictions)
            state['dietary_restrictions'] = list(set(state['dietary_restrictions']))  # Remove duplicates
            state['step'] = 3
            state['current_options'] = ["instructions", "different", "something else"]
            api.set_module_context(user_context)
            
            dietary_list = ", ".join(dietary_restrictions)
            adapted_recipe = _get_dietary_recipe(state['recipe_type'], dietary_restrictions)
            state['last_recipe'] = f"{state['recipe_type']}_{'_'.join(dietary_restrictions)}"
            
            return [(f"Got it! I've adjusted the recipe for {dietary_list}. 🥗\n\n"
                    f"{adapted_recipe}\n\n"
                    "Would you like the cooking instructions, a different recipe, or something else?", 
                    1.0, "Recipe Module")]
        
        elif wants_instructions:
            instructions = _get_cooking_instructions(state['recipe_type'], state.get('dietary_restrictions', []))
            state['current_options'] = ["different", "similar", "something else"]
            return [(f"Here are the step-by-step instructions:\n\n{instructions}\n\n"
                    "Want to try a different recipe, something similar, or explore other options?", 
                    1.0, "Recipe Module")]
        
        elif wants_different:
            state['step'] = 1
            state['recipe_type'] = None
            state['dietary_restrictions'] = []
            state['current_options'] = ["breakfast", "lunch", "dinner", "dessert", "snacks", "healthy", "ingredients", "something else"]
            api.set_module_context(user_context)
            
            return [("Sure! Let's find something different. What are you in the mood for now?\n\n"
                    "• Breakfast • Lunch • Dinner • Dessert • Snacks • Healthy\n\n"
                    "Or say 'something else' for more options!", 
                    1.0, "Recipe Module")]
        
        elif wants_similar and state['last_recipe']:
            similar_recipe = _get_similar_recipe(state['last_recipe'])
            state['current_options'] = ["instructions", "different", "something else"]
            return [(f"Here's another {state['recipe_type']} recipe you might like:\n\n{similar_recipe}\n\n"
                    "Want instructions for this one, a different recipe, or something else?", 
                    1.0, "Recipe Module")]
        
        else:
            # Check if this might be a new recipe request
            new_category = _fuzzy_detect_category(input_lower)
            if new_category:
                state['step'] = 2
                state['recipe_type'] = new_category
                state['current_options'] = ["instructions", "dietary", "different", "similar", "something else"]
                api.set_module_context(user_context)
                
                recipe_suggestion = _get_recipe_suggestion(new_category)
                state['last_recipe'] = new_category
                
                return [(f"Great! Let's try {new_category} instead! 🎉\n\n"
                        f"{recipe_suggestion}\n\n"
                        "Would you like instructions, dietary adjustments, or something else?", 
                        1.0, "Recipe Module")]
            
            # Unclear response - offer help with LOW confidence
            state['current_options'] = ["instructions", "dietary", "different", "similar", "something else"]
            return [("I'm not sure what you'd like to do next. 🤔\n\n"
                    "You can ask for:\n• Instructions\n• Dietary changes  \n• A different recipe\n• Something similar\n• Or say 'something else' for more options!",
                    0.4, "Recipe Module")]
    
    elif state['step'] == 3:
        # Handle dietary-adjusted recipes
        wants_instructions = _fuzzy_match_instructions(input_lower)
        wants_different = _fuzzy_match_different(input_lower)
        
        if wants_instructions:
            instructions = _get_cooking_instructions(state['recipe_type'], state.get('dietary_restrictions', []))
            state['current_options'] = ["different", "something else"]
            return [(f"Here are the cooking instructions:\n\n{instructions}\n\n"
                    "Want to try a different recipe or explore other options?", 
                    1.0, "Recipe Module")]
        
        elif wants_different:
            state['step'] = 1
            state['recipe_type'] = None
            state['dietary_restrictions'] = []
            state['current_options'] = ["breakfast", "lunch", "dinner", "dessert", "snacks", "healthy", "ingredients", "something else"]
            api.set_module_context(user_context)
            
            return [("Sure! Let's find something different. What are you in the mood for now?\n\n"
                    "• Breakfast • Lunch • Dinner • Dessert • Snacks • Healthy\n\n"
                    "Or say 'something else' for more options!", 
                    1.0, "Recipe Module")]
        
        else:
            # Check for new recipe requests even in step 3
            new_category = _fuzzy_detect_category(input_lower)
            if new_category:
                state['step'] = 2
                state['recipe_type'] = new_category
                state['dietary_restrictions'] = []
                state['current_options'] = ["instructions", "dietary", "different", "similar", "something else"]
                api.set_module_context(user_context)
                
                recipe_suggestion = _get_recipe_suggestion(new_category)
                state['last_recipe'] = new_category
                
                return [(f"Great! Let's explore {new_category} recipes! 🎉\n\n"
                        f"{recipe_suggestion}\n\n"
                        "Would you like instructions, dietary adjustments, or something else?", 
                        1.0, "Recipe Module")]
            
            # Default to offering options with MEDIUM confidence
            state['current_options'] = ["instructions", "different", "something else"]
            return [("What would you like to do next?\n\n"
                    "• **Instructions** - Get cooking steps\n"
                    "• **Different** - Try another recipe\n"
                    "• **Something Else** - More options\n\n"
                    "What sounds good?", 0.6, "Recipe Module")]
    
    # Fallback with fuzzy matching for common queries
    fallback_response = _handle_fallback_query(input_lower)
    if fallback_response:
        return fallback_response
    
    # Final fallback - always offer to continue with LOW confidence
    state['current_options'] = ["continue", "something else"]
    return [("I'm not sure what you'd like to do with recipes. 🤔\n\n"
            "Would you like to continue with recipes or explore other options?\n\n"
            "Say 'continue' for more recipes or 'something else' for other options!", 
            0.2, "Recipe Module")]

# ===== ENHANCED FUZZY MATCHING FUNCTIONS =====

def _fuzzy_match_done(user_input):
    """Fuzzy matching for completion requests - THESE DEACTIVATE THE MODULE"""
    done_keywords = [
        "thank you", "thanks", "that's all", "that is all", "im done", 
        "i'm done", "all done", "finished", "no more", "that'll be all",
        "im good", "i'm good", "no thanks", "not now", "maybe later",
        "that's it", "that is it", "im finished", "i'm finished"
    ]
    # STRICT MATCHING: Require 80% similarity for done signals
    return any(fuzz.token_set_ratio(user_input, keyword) >= 80 for keyword in done_keywords)

def _fuzzy_match_something_else(user_input):
    """Fuzzy matching for 'something else' requests - THESE DON'T DEACTIVATE"""
    something_else_keywords = [
        "something else", "other", "different", "another option", 
        "more options", "what else", "other choices", "alternatives",
        "other options", "different options", "more choices", "else",
        "what other", "show me other", "give me other"
    ]
    # STRICT MATCHING: Require 75% similarity for something else
    return any(fuzz.token_set_ratio(user_input, keyword) >= 75 for keyword in something_else_keywords)

def _handle_completion_request(state, api):
    """Handle completion requests - DEACTIVATES the module"""
    # Clear the context
    api.set_module_context({})
    
    # Set module_mode to False to deactivate - this is the ONLY place we do this
    global module_mode
    module_mode = False
    
    return [("You're welcome! Happy cooking! 🧑‍🍳\n\n"
            "I'm switching back to normal mode. What would you like to talk about now?", 
            1.0, "Recipe Module")]

def _handle_something_else_request(state, api):
    """Handle 'something else' requests - DOES NOT DEACTIVATE"""
    current_step = state['step']
    
    if current_step == 0 or current_step == 1:
        # Initial steps - offer advanced options
        state['current_options'] = ["cooking tips", "meal planning", "kitchen tools", "back to recipes"]
        return [("Sure! Here are some other ways I can help: 🧑‍🍳\n\n"
                "• **Cooking Tips** - General kitchen advice and techniques\n"
                "• **Meal Planning** - Weekly meal ideas and planning\n"
                "• **Kitchen Tools** - Recommended equipment and tools\n"
                "• **Back to Recipes** - Return to recipe search\n\n"
                "What would you like help with?", 0.9, "Recipe Module")]
    
    elif current_step == 2:
        # Recipe selected - offer related options
        state['current_options'] = ["cooking tips", "meal planning", "ingredient substitutes", "back to recipe"]
        return [(f"Looking for something different with your {state['recipe_type']} recipe? 🧐\n\n"
                "• **Cooking Tips** - Techniques for this type of dish\n"
                "• **Meal Planning** - How to incorporate this into weekly meals\n"
                "• **Ingredient Substitutes** - Alternatives for dietary needs\n"
                "• **Back to Recipe** - Return to your current recipe\n\n"
                "What would you like?", 0.9, "Recipe Module")]
    
    elif current_step == 3:
        # Final steps - wrap-up options
        state['current_options'] = ["cooking techniques", "meal prep", "back to recipes"]
        return [("More ways I can assist: 📚\n\n"
                "• **Cooking Techniques** - Learn specific cooking methods\n"
                "• **Meal Prep** - Batch cooking and storage tips\n"
                "• **Back to Recipes** - Return to recipe search\n\n"
                "What would you like?", 0.9, "Recipe Module")]
    
    # Default something else response
    state['current_options'] = ["cooking tips", "meal planning", "back to recipes"]
    return [("Here are some other options: 🔧\n\n"
            "• **Cooking Tips** - General kitchen advice\n"
            "• **Meal Planning** - Weekly meal organization\n"
            "• **Back to Recipes** - Return to what we were discussing\n\n"
            "What sounds helpful?", 0.8, "Recipe Module")]

def _fuzzy_detect_category(user_input):
    """Enhanced fuzzy matching for recipe categories"""
    categories = {
        "breakfast": ["breakfast", "morning", "pancake", "waffle", "egg", "cereal", "oatmeal", "smoothie", "brunch", "coffee", "toast"],
        "lunch": ["lunch", "midday", "sandwich", "salad", "soup", "wrap", "burger", "noon", "midday meal", "soup", "salad"],
        "dinner": ["dinner", "evening", "pasta", "chicken", "beef", "fish", "rice", "supper", "night meal", "main course", "entree"],
        "dessert": ["dessert", "sweet", "cake", "cookie", "pie", "brownie", "ice cream", "chocolate", "pudding", "custard", "treat"],
        "snack": ["snack", "appetizer", "quick", "bite", "finger food", "chips", "dip", "munchies", "small bite", "appetiser"],
        "healthy": ["healthy", "low calorie", "light", "diet", "nutritious", "wholesome", "clean eating", "fit", "wellness", "low fat"]
    }
    
    best_match = None
    best_score = 0
    
    for category, keywords in categories.items():
        for keyword in keywords:
            similarity = fuzz.token_set_ratio(user_input, keyword)
            if similarity > best_score and similarity >= 70:  # Increased from 50% to 70%
                best_score = similarity
                best_match = category
    
    return best_match

def _fuzzy_detect_ingredients(user_input):
    """Fuzzy matching for common ingredients"""
    ingredient_keywords = [
        "chicken", "beef", "pork", "fish", "salmon", "tuna", "shrimp",
        "egg", "eggs", "milk", "cheese", "butter", "yogurt",
        "flour", "sugar", "salt", "pepper", "oil", "vinegar",
        "tomato", "onion", "garlic", "potato", "carrot", "broccoli",
        "rice", "pasta", "bread", "noodle", "quinoa", "oat",
        "chocolate", "vanilla", "cinnamon", "herb", "spice"
    ]
    
    detected = []
    for ingredient in ingredient_keywords:
        similarity = fuzz.token_set_ratio(user_input, ingredient)
        if similarity >= 70:  # Increased from 60% to 70%
            detected.append(ingredient)
    
    return detected[:4]

def _fuzzy_detect_dietary(user_input):
    """Fuzzy matching for dietary restrictions"""
    dietary_restrictions = {
        "vegetarian": ["vegetarian", "veggie", "meatless", "no meat", "plant based"],
        "vegan": ["vegan", "dairy free", "egg free", "no dairy", "plant only"],
        "gluten_free": ["gluten", "gluten free", "wheat free", "celiac", "no gluten"],
        "low_carb": ["low carb", "keto", "ketogenic", "no carb", "low sugar"],
        "healthy": ["healthy", "low calorie", "light", "diet", "low fat", "nutritious"]
    }
    
    detected = []
    for restriction, keywords in dietary_restrictions.items():
        for keyword in keywords:
            similarity = fuzz.token_set_ratio(user_input, keyword)
            if similarity >= 75:  # Increased from 65% to 75%
                if restriction not in detected:
                    detected.append(restriction)
    
    return detected

def _fuzzy_match_instructions(user_input):
    """Fuzzy matching for instruction requests"""
    instruction_keywords = ["instruction", "how to", "steps", "directions", "cook", "make", "prepare", "method"]
    # STRICT MATCHING: Require 70% similarity
    return any(fuzz.token_set_ratio(user_input, keyword) >= 70 for keyword in instruction_keywords)

def _fuzzy_match_different(user_input):
    """Fuzzy matching for different recipe requests"""
    different_keywords = ["different", "another", "new", "other", "else", "change", "not this"]
    # STRICT MATCHING: Require 70% similarity
    return any(fuzz.token_set_ratio(user_input, keyword) >= 70 for keyword in different_keywords)

def _fuzzy_match_similar(user_input):
    """Fuzzy matching for similar recipe requests"""
    similar_keywords = ["similar", "like this", "same", "more like", "another like"]
    # STRICT MATCHING: Require 70% similarity
    return any(fuzz.token_set_ratio(user_input, keyword) >= 70 for keyword in similar_keywords)

def _fuzzy_match_affirmative(user_input):
    """Fuzzy matching for affirmative responses"""
    affirmative_keywords = ["yes", "yeah", "sure", "ok", "okay", "please", "yep", "alright"]
    return any(fuzz.token_set_ratio(user_input, keyword) >= 70 for keyword in affirmative_keywords)

def _handle_fallback_query(user_input):
    """Handle common recipe-related queries with fuzzy matching"""
    common_queries = {
        "easy": ("Looking for something easy? Try these quick recipes:\n\n"
                "• **5-Minute Omelette** - 2 eggs, salt, pepper, 1 minute prep!\n"
                "• **Avocado Toast** - Bread + avocado + salt = delicious!\n"
                "• **Microwave Mug Cake** - Mix flour, sugar, cocoa, milk - 90 seconds!\n\n"
                "Which one sounds good? Or say 'something else' for more options!", 0.8),
        "quick": ("Need something fast? 🏃‍♂️\n\n"
                 "**Quick Options:**\n"
                 "• Stir-fry (10 mins)\n• Pasta (12 mins)  \n• Salad (5 mins)\n• Sandwich (3 mins)\n\n"
                 "Which appeals to you? Or say 'something else' for more!", 0.8),
        "healthy": ("Healthy choices! 🥗\n\n"
                   "**Nutritious Options:**\n"
                   "• Grilled chicken salad\n• Vegetable stir-fry\n• Quinoa bowl\n• Baked fish\n\n"
                   "Want details on any of these? Or say 'something else'!", 0.8),
        "cheap": ("Budget-friendly meals! 💰\n\n"
                 "**Economical Choices:**\n"
                 "• Bean chili\n• Pasta with marinara\n• Egg fried rice\n• Potato soup\n\n"
                 "Which sounds good? Or say 'something else' for more options!", 0.7),
        "fancy": ("Feeling fancy! 🎩\n\n"
                 "**Special Occasion Recipes:**\n"
                 "• Garlic butter steak\n• Shrimp scampi\n• Chocolate lava cake\n• Stuffed mushrooms\n\n"
                 "Want to impress someone? Or say 'something else' for other ideas!", 0.7),
        "cooking tips": ("**Essential Cooking Tips** 🎯\n\n"
                        "• **Mise en place** - Prep all ingredients before starting\n"
                        "• **Taste as you go** - Season gradually\n"
                        "• **Don't overcrowd pans** - Food steams instead of browns\n"
                        "• **Let meat rest** - Juices redistribute for tenderness\n"
                        "• **Sharp knives** - Safer and more efficient\n\n"
                        "Need tips for something specific?", 0.8),
        "meal planning": ("**Meal Planning Made Easy** 📅\n\n"
                         "1. **Plan weekly** - Create a menu for the week\n"
                         "2. **Check inventory** - See what you already have\n"
                         "3. **Batch cook** - Make larger portions for leftovers\n"
                         "4. **Theme nights** - Taco Tuesday, Pizza Friday, etc.\n"
                         "5. **Prep ahead** - Chop veggies, marinate proteins\n\n"
                         "Want specific meal plans?", 0.8)
    }
    
    for query, (response, confidence) in common_queries.items():
        if fuzz.token_set_ratio(user_input, query) >= 60:
            return [(response, confidence, "Recipe Module")]
    
    return None

# ===== RECIPE CONTENT FUNCTIONS =====

def _get_recipe_suggestion(category):
    """Get detailed recipe suggestion based on category"""
    recipes = {
        "breakfast": 
            "**Fluffy Buttermilk Pancakes** 🥞\n\n"
            "**Ingredients:**\n"
            "• 1 cup all-purpose flour\n• 2 tbsp sugar\n• 2 tsp baking powder\n• 1/2 tsp baking soda\n• 1/4 tsp salt\n"
            "• 1 cup buttermilk\n• 1 large egg\n• 2 tbsp melted butter\n• 1 tsp vanilla extract\n\n"
            "**Quick Overview:** Mix dry ingredients. Whisk wet ingredients. Combine gently. Cook on buttered griddle until golden!",
        
        "lunch":
            "**Mediterranean Quinoa Bowl** 🥗\n\n"
            "**Ingredients:**\n"
            "• 1 cup cooked quinoa\n• 1/2 cucumber, diced\n• 1 cup cherry tomatoes, halved\n• 1/4 red onion, sliced\n"
            "• 1/4 cup feta cheese\n• 2 tbsp kalamata olives\n• 2 tbsp olive oil\n• 1 tbsp lemon juice\n• Fresh herbs\n\n"
            "**Quick Overview:** Combine all ingredients in a bowl. Drizzle with olive oil and lemon juice. Top with feta!",
        
        "dinner":
            "**Creamy Garlic Parmesan Chicken** 🍗\n\n"
            "**Ingredients:**\n"
            "• 2 chicken breasts\n• 3 cloves garlic, minced\n• 1 cup heavy cream\n• 1/2 cup grated Parmesan\n"
            "• 1 cup spinach\n• 2 tbsp butter\n• Salt, pepper, Italian seasoning\n\n"
            "**Quick Overview:** Sear chicken. Sauté garlic in butter. Add cream and Parmesan. Return chicken, add spinach. Simmer!",
        
        "dessert":
            "**Classic Chocolate Chip Cookies** 🍪\n\n"
            "**Ingredients:**\n"
            "• 2 1/4 cups flour\n• 1 tsp baking soda\n• 1 cup butter, softened\n• 3/4 cup brown sugar\n• 3/4 cup white sugar\n"
            "• 2 large eggs\n• 2 tsp vanilla\n• 2 cups chocolate chips\n• 1 tsp salt\n\n"
            "**Quick Overview:** Cream butter and sugars. Add eggs and vanilla. Mix in dry ingredients. Fold in chips. Bake at 375°F!",
        
        "snack":
            "**Fresh Guacamole** 🥑\n\n"
            "**Ingredients:**\n"
            "• 3 ripe avocados\n• 1 lime, juiced\n• 1/2 red onion, diced\n• 1 tomato, diced\n"
            "• 2 tbsp cilantro, chopped\n• 1 jalapeño, minced (optional)\n• Salt to taste\n\n"
            "**Quick Overview:** Mash avocados. Mix with all ingredients. Adjust seasoning. Serve immediately with chips!",
        
        "healthy":
            "**Power Green Smoothie** 🥤\n\n"
            "**Ingredients:**\n"
            "• 1 cup spinach\n• 1/2 banana\n• 1/2 cup Greek yogurt\n• 1/2 cup almond milk\n"
            "• 1 tbsp chia seeds\n• 1 tbsp honey\n• 1/2 cup frozen mango\n• Ice cubes\n\n"
            "**Quick Overview:** Blend all ingredients until smooth. Add more liquid if needed. Enjoy immediately!"
    }
    
    return recipes.get(category, 
        "**Simple Pasta Aglio e Olio** 🍝\n\n"
        "**Ingredients:**\n• 8 oz spaghetti\n• 4 cloves garlic, sliced\n• 1/2 cup olive oil\n• Red pepper flakes\n• Parsley, salt, pepper\n\n"
        "**Quick Overview:** Cook pasta. Sauté garlic in oil until golden. Toss with pasta, pepper flakes, and parsley!")

def _get_recipe_from_ingredients(ingredients):
    """Generate recipe based on available ingredients"""
    ingredient_recipes = {
        "chicken": "**Lemon Herb Chicken** 🍋\n\nSear chicken breasts with garlic, thyme, and lemon juice. Serve with roasted vegetables!",
        "pasta": "**Quick Garlic Pasta** 🍝\n\nCook pasta. Sauté garlic in olive oil, toss with pasta, Parmesan, and fresh herbs!",
        "egg": "**French Omelette** 🍳\n\nWhisk 2-3 eggs, cook in butter, fill with cheese and herbs. Simple and elegant!",
        "rice": "**Vegetable Fried Rice** 🍚\n\nSauté vegetables, add cooked rice, soy sauce, and scrambled egg. Quick and satisfying!",
        "tomato": "**Fresh Tomato Salad** 🍅\n\nSlice tomatoes, add basil, mozzarella, olive oil, and balsamic glaze. Refreshing!",
        "chocolate": "**Microwave Mug Cake** 🍫\n\nMix flour, sugar, cocoa, milk, oil in mug. Microwave 90 seconds. Instant dessert!"
    }
    
    # Find the best matching ingredient
    for ingredient in ingredients:
        for key_ingredient, recipe in ingredient_recipes.items():
            if fuzz.token_set_ratio(ingredient, key_ingredient) >= 70:
                return recipe
    
    return ("**Quick Stir-Fry** 🍲\n\n"
           "Sauté your ingredients with garlic and soy sauce. Serve over rice or noodles for a fast, delicious meal!")

def _get_dietary_recipe(category, dietary_restrictions):
    """Get recipe adjusted for dietary restrictions"""
    dietary_recipes = {
        "vegetarian": "**Vegetable Curry** 🍛\n\nSauté onions, garlic, ginger. Add vegetables, coconut milk, curry powder. Simmer until tender!",
        "vegan": "**Buddha Bowl** 🥬\n\nBase: quinoa or rice. Toppings: roasted veggies, beans, avocado, tahini dressing!",
        "gluten_free": "**Gluten-Free Pasta** 🌾\n\nUse gluten-free pasta with olive oil, garlic, cherry tomatoes, and fresh basil!",
        "low_carb": "**Zucchini Noodles** 🥒\n\nSpiralize zucchini. Sauté with garlic, olive oil, cherry tomatoes, and Parmesan!",
        "healthy": "**Grilled Salmon** 🐟\n\nSeason salmon with lemon, herbs. Grill or bake. Serve with steamed vegetables!"
    }
    
    for restriction in dietary_restrictions:
        if restriction in dietary_recipes:
            return dietary_recipes[restriction]
    
    return "**Roasted Vegetable Medley** 🥦\n\nChop assorted vegetables, toss with olive oil and herbs, roast at 400°F until caramelized!"

def _get_similar_recipe(last_recipe):
    """Get a similar recipe to the last one"""
    similar_recipes = {
        "breakfast": "**French Toast** 🍞\n\nDip bread in egg-milk mixture. Cook on buttered griddle until golden. Serve with syrup!",
        "lunch": "**Caprese Sandwich** 🥪\n\nFresh mozzarella, tomato, basil, balsamic glaze on crusty bread. Simple perfection!",
        "dinner": "**Beef Stir-Fry** 🥩\n\nSlice beef thin, stir-fry with vegetables and soy sauce. Serve over rice!",
        "dessert": "**Brownies** 🍫\n\nMix butter, sugar, cocoa, eggs, flour. Bake at 350°F for 25 mins. Rich and fudgy!",
        "snack": "**Hummus** 🫘\n\nBlend chickpeas, tahini, lemon juice, garlic, olive oil. Serve with pita or veggies!",
        "healthy": "**Greek Salad** 🥗\n\nCucumber, tomato, red onion, olives, feta, olive oil, oregano. Fresh and light!"
    }
    
    base_category = last_recipe.split('_')[0] if '_' in last_recipe else last_recipe
    return similar_recipes.get(base_category, 
        "**Pasta Pomodoro** 🍅\n\nFresh tomatoes, garlic, basil, olive oil. Simple, classic, and always delicious!")

def _get_cooking_instructions(category, dietary_restrictions=[]):
    """Get detailed cooking instructions"""
    instructions = {
        "breakfast": 
            "**Pancake Instructions:**\n\n"
            "1. Whisk flour, sugar, baking powder, baking soda, and salt in bowl\n"
            "2. In another bowl, whisk buttermilk, egg, melted butter, and vanilla\n"
            "3. Pour wet ingredients into dry, mix gently (lumps are okay!)\n"
            "4. Heat griddle or pan over medium, butter lightly\n"
            "5. Pour 1/4 cup batter, cook until bubbles form (2-3 mins)\n"
            "6. Flip, cook until golden (1-2 mins)\n"
            "7. Serve warm with maple syrup and butter! 🥞",
        
        "lunch":
            "**Quinoa Bowl Instructions:**\n\n"
            "1. Cook quinoa according to package instructions, let cool\n"
            "2. Dice cucumber, halve tomatoes, slice red onion\n"
            "3. Make dressing: whisk olive oil, lemon juice, salt, pepper\n"
            "4. Combine quinoa with vegetables in large bowl\n"
            "5. Drizzle with dressing, toss gently\n"
            "6. Top with feta cheese and olives\n"
            "7. Garnish with fresh herbs and serve! 🥗",
        
        "dinner":
            "**Chicken Instructions:**\n\n"
            "1. Season chicken breasts with salt, pepper, Italian seasoning\n"
            "2. Heat oil in skillet, sear chicken 5-6 mins per side, remove\n"
            "3. In same skillet, melt butter, sauté garlic 1 minute\n"
            "4. Pour in cream, bring to simmer, whisk in Parmesan\n"
            "5. Return chicken to skillet, add spinach\n"
            "6. Simmer 5-7 mins until chicken cooked through\n"
            "7. Serve over pasta or with crusty bread! 🍗",
        
        "dessert":
            "**Cookie Instructions:**\n\n"
            "1. Preheat oven to 375°F, line baking sheets\n"
            "2. Whisk flour, baking soda, salt in bowl\n"
            "3. Cream butter and sugars until light and fluffy\n"
            "4. Beat in eggs one at a time, then vanilla\n"
            "5. Gradually mix in dry ingredients\n"
            "6. Fold in chocolate chips\n"
            "7. Drop tablespoon-sized balls, bake 9-11 mins\n"
            "8. Cool on wire rack, enjoy! 🍪"
    }
    
    base_instructions = instructions.get(category, 
        "**General Cooking Tips:**\n\n"
        "1. Read the entire recipe first\n2. Prepare all ingredients (mise en place)\n"
        "3. Use the right tools and equipment\n4. Taste as you cook\n"
        "5. Don't overcrowd the pan\n6. Let meat rest before slicing\n"
        "7. Season generously but taste first!\n\nHappy cooking! 🧑‍🍳")
    
    if dietary_restrictions:
        dietary_tips = "\n\n**Dietary Notes:** "
        if "vegetarian" in dietary_restrictions:
            dietary_tips += "• Use vegetable broth instead of chicken broth\n"
        if "vegan" in dietary_restrictions:
            dietary_tips += "• Substitute dairy with plant-based alternatives\n"
        if "gluten_free" in dietary_restrictions:
            dietary_tips += "• Check all sauces for hidden gluten\n"
        return base_instructions + dietary_tips
    
    return base_instructions