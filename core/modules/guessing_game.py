"""
Guessing Game module for Edgar AI
A simple number guessing game that requires multiple interactions
"""
import random

module_mode = True  # This module requires multiple messages

def process(input_text: str, context: dict) -> dict:
    """Process guessing game - supports multiple interactions"""
    game_state = context.get('module_state', {})
    
    if not game_state:
        # Start new game
        game_state = {
            'number': random.randint(1, 100),
            'attempts': 0,
            'max_attempts': 7,
            'game_active': True
        }
        
        return {
            'result': "I'm thinking of a number between 1 and 100. Can you guess what it is?",
            'needs_followup': True,
            'module_state': game_state,
            'prompt': "Take a guess!"
        }
    
    if game_state.get('game_active', False):
        # Game is active, process guess
        try:
            guess = int(input_text.strip())
            game_state['attempts'] += 1
            
            if guess == game_state['number']:
                game_state['game_active'] = False
                return {
                    'result': f"🎉 Congratulations! You guessed the number {game_state['number']} in {game_state['attempts']} attempts!",
                    'needs_followup': False,
                    'module_state': game_state
                }
            elif guess < game_state['number']:
                hint = "📈 Try a higher number!"
            else:
                hint = "📉 Try a lower number!"
            
            remaining = game_state['max_attempts'] - game_state['attempts']
            
            if remaining <= 0:
                game_state['game_active'] = False
                return {
                    'result': f"❌ Game over! The number was {game_state['number']}. Better luck next time!",
                    'needs_followup': False,
                    'module_state': game_state
                }
            else:
                return {
                    'result': f"{hint} You have {remaining} attempts remaining.",
                    'needs_followup': True,
                    'module_state': game_state,
                    'prompt': "Guess again!"
                }
                
        except ValueError:
            return {
                'result': "Please enter a valid number between 1 and 100.",
                'needs_followup': True,
                'module_state': game_state,
                'prompt': "Try again with a number!"
            }
    
    else:
        # Game is over
        return {
            'result': "The game has ended. Say 'play again' to start a new game!",
            'needs_followup': False,
            'module_state': {}
        }