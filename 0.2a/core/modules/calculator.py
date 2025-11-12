"""
Calculator module for Edgar AI
Performs basic calculations
"""
import re

module_mode = False  # Single response module

def process(input_text: str, context: dict) -> str:
    """Process calculation request"""
    try:
        # Extract numbers and operators
        text_lower = input_text.lower()
        
        # Look for basic math operations
        if "plus" in text_lower or "+" in text_lower:
            numbers = re.findall(r'\d+', input_text)
            if len(numbers) >= 2:
                result = sum(int(n) for n in numbers)
                return f"{' + '.join(numbers)} = {result}"
        
        elif "minus" in text_lower or "-" in text_lower:
            numbers = re.findall(r'\d+', input_text)
            if len(numbers) >= 2:
                result = int(numbers[0]) - int(numbers[1])
                return f"{numbers[0]} - {numbers[1]} = {result}"
        
        elif "times" in text_lower or "multiplied" in text_lower or "*" in text_lower or "x" in text_lower:
            numbers = re.findall(r'\d+', input_text)
            if len(numbers) >= 2:
                result = int(numbers[0]) * int(numbers[1])
                return f"{numbers[0]} × {numbers[1]} = {result}"
        
        elif "divided" in text_lower or "/" in text_lower:
            numbers = re.findall(r'\d+', input_text)
            if len(numbers) >= 2:
                if int(numbers[1]) == 0:
                    return "I can't divide by zero!"
                result = int(numbers[0]) / int(numbers[1])
                return f"{numbers[0]} ÷ {numbers[1]} = {result:.2f}"
        
        # Try to evaluate simple math expressions
        math_match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', input_text)
        if math_match:
            num1, op, num2 = math_match.groups()
            num1, num2 = int(num1), int(num2)
            
            if op == '+':
                result = num1 + num2
            elif op == '-':
                result = num1 - num2
            elif op == '*':
                result = num1 * num2
            elif op == '/':
                if num2 == 0:
                    return "I can't divide by zero!"
                result = num1 / num2
            else:
                return "I don't understand that operation."
            
            return f"{num1} {op} {num2} = {result}"
        
        return "I can help with basic math! Try asking something like 'what is 5 + 3' or 'calculate 10 times 2'"
        
    except Exception as e:
        return f"Sorry, I couldn't calculate that: {str(e)}"