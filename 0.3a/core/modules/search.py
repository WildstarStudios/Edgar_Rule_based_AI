# core/modules/search.py
from fuzzywuzzy import fuzz
import re
import requests
import urllib.parse

def get_expected_patterns():
    """Define patterns that this module expects to handle"""
    return [
        "search", "look up", "find", "web search", "search for",
        "search about", "look up about", "find about", 
        "search info", "look up info", "find info",
        "search the web", "search online", "web lookup",
        "what is", "what are", "who is", "tell me about",
        "explain", "define", "summary of", "information about"
    ]

def process(user_input, api):
    """Handle search requests in single-turn mode"""
    search_query = _extract_search_query(user_input)
    
    if not search_query:
        return [("To search Wikipedia, please start with a search phrase like 'search about [topic]', 'look up [thing]', or 'what is [subject]'.", 0.8, "Search Module")]
    
    # Perform search
    api.stream_thinking(f"🔍 Searching Wikipedia for '{search_query}'...")
    results = perform_wikipedia_search(search_query)
    
    if not results or 'error' in results[0]:
        error_msg = results[0]['error'] if results and 'error' in results[0] else "No results found"
        return [(f"❌ Wikipedia search failed: {error_msg}. Try a different query?", 1.0, "Search Module")]
    
    # Generate and display summary
    api.stream_thinking("📝 Generating comprehensive summary...")
    all_sections = generate_comprehensive_summary(search_query, results)
    
    if not all_sections:
        return [(f"❌ Couldn't generate a good summary for '{search_query}'. Try a different query?", 1.0, "Search Module")]
    
    # Combine all sections into one response
    full_response = "\n\n".join(all_sections)
    full_response += "\n\n🔍 *Source: Wikipedia*"
    
    return [(full_response, 1.0, "Search Module")]

def _extract_search_query(user_input):
    """Extract search query from user input"""
    input_lower = user_input.lower().strip()
    
    # List of valid trigger phrases with their patterns
    trigger_patterns = [
        (r'^search\s+(?:up|about|for)?\s+(.+)', 'search'),
        (r'^look up\s+(.+)', 'look up'),
        (r'^find\s+(?:about|info on)?\s+(.+)', 'find'),
        (r'^web search\s+(.+)', 'web search'),
        (r'^search the web for\s+(.+)', 'search the web for'),
        (r'^tell me about\s+(.+)', 'tell me about'),
        (r'^what is\s+(.+)', 'what is'),
        (r'^what are\s+(.+)', 'what are'),
        (r'^who is\s+(.+)', 'who is'),
        (r'^explain\s+(.+)', 'explain'),
        (r'^define\s+(.+)', 'define'),
        (r'^summary of\s+(.+)', 'summary of'),
        (r'^information about\s+(.+)', 'information about')
    ]
    
    # Try regex patterns first
    for pattern, trigger in trigger_patterns:
        try:
            match = re.search(pattern, input_lower, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                # Clean up the query
                query = re.sub(r'^\s*(up|about|for|the|a|an)\s+', '', query).strip()
                if len(query) > 2:
                    return query
        except Exception:
            continue
    
    # Fallback: check for trigger phrases at the beginning
    trigger_starts = [
        'search', 'look up', 'find', 'web search', 
        'what is', 'what are', 'who is', 'tell me about',
        'explain', 'define', 'summary of', 'information about'
    ]
    
    for trigger in trigger_starts:
        if input_lower.startswith(trigger):
            query = input_lower[len(trigger):].strip()
            # Clean up the query
            query = re.sub(r'^\s*(up|about|for|the|a|an)\s+', '', query).strip()
            if len(query) > 2:
                return query
    
    # Additional fallback: check for any trigger word presence
    for trigger in ['search', 'look up', 'find', 'what is', 'who is']:
        if trigger in input_lower:
            # Extract everything after the trigger
            parts = input_lower.split(trigger, 1)
            if len(parts) > 1:
                query = parts[1].strip()
                # Clean up the query
                query = re.sub(r'^\s*(up|about|for|the|a|an)\s+', '', query).strip()
                if len(query) > 2:
                    return query
    
    return None

def perform_wikipedia_search(query):
    """Search Wikipedia and return structured results"""
    try:
        # Clean and format the query for Wikipedia
        clean_query = _clean_wikipedia_query(query)
        
        # First, try to get the exact page
        exact_page = _get_wikipedia_page(clean_query)
        if exact_page and not exact_page.get('error'):
            return [exact_page]
        
        # If exact page not found, try search
        search_results = _search_wikipedia(clean_query)
        if search_results:
            return search_results[:3]  # Return top 3 results
        
        return [{'error': 'No Wikipedia page found for this topic'}]
            
    except Exception as e:
        return [{'error': f'Wikipedia search failed: {str(e)}'}]

def _clean_wikipedia_query(query):
    """Clean query for Wikipedia search"""
    # Remove common prefixes and clean up
    query = re.sub(r'^\s*(the|a|an)\s+', '', query, flags=re.IGNORECASE)
    query = query.strip()
    
    # For "what is" queries, remove the prefix and focus on the main topic
    if query.lower().startswith('what is '):
        query = query[8:].strip()
    elif query.lower().startswith('what are '):
        query = query[9:].strip()
    elif query.lower().startswith('who is '):
        query = query[7:].strip()
    
    # Capitalize first letter of each word for better Wikipedia matching
    words = query.split()
    if len(words) > 1:
        query = ' '.join(word.capitalize() for word in words)
    else:
        query = query.capitalize()
    
    return query

def _get_wikipedia_page(query):
    """Get a specific Wikipedia page by title"""
    try:
        # Try to get the page directly
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Edgar AI Assistant/1.0'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', query),
                'link': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'description': data.get('extract', ''),
                'image': data.get('thumbnail', {}).get('source', ''),
                'type': 'wikipedia'
            }
        else:
            return {'error': f'Wikipedia page not found: {query}'}
            
    except Exception as e:
        return {'error': f'Failed to fetch Wikipedia page: {str(e)}'}

def _search_wikipedia(query):
    """Search Wikipedia for a query"""
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': 5,
            'utf8': 1
        }
        headers = {
            'User-Agent': 'Edgar AI Assistant/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            search_results = []
            
            for result in data.get('query', {}).get('search', []):
                # Get more details for each result
                page_result = _get_wikipedia_page(result['title'])
                if page_result and not page_result.get('error'):
                    search_results.append(page_result)
            
            return search_results
        else:
            return []
            
    except Exception as e:
        return []

def generate_comprehensive_summary(query, search_results):
    """Generate comprehensive summary from Wikipedia results"""
    if not search_results or 'error' in search_results[0]:
        return []
    
    # Use the first (most relevant) result
    main_result = search_results[0]
    description = main_result.get('description', '')
    
    if not description:
        return []
    
    # Split the description into meaningful sections
    sections = _parse_wikipedia_content(description, query)
    
    return sections

def _parse_wikipedia_content(content, query):
    """Parse Wikipedia content into organized sections"""
    sections = []
    
    # Clean and split the content
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    
    if not paragraphs:
        return []
    
    # Create main summary section
    if len(paragraphs[0]) > 50:
        main_summary = f"📚 **{query.title()}**\n\n{paragraphs[0]}"
        sections.append(main_summary)
    
    # Create additional sections from remaining paragraphs
    if len(paragraphs) > 1:
        additional_info = "🌟 **Key Information**\n\n"
        for para in paragraphs[1:4]:
            if len(para) > 30:
                additional_info += f"• {para}\n"
        
        if additional_info.count('•') > 0:
            sections.append(additional_info.strip())
    
    # Create features section if we have relevant content
    if len(paragraphs) > 2:
        features = "🚀 **Features**\n\n"
        feature_keywords = ['feature', 'support', 'include', 'provide', 'capability', 'function']
        feature_sentences = []
        
        for para in paragraphs:
            sentences = re.split(r'[.!?]+', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if (any(keyword in sentence.lower() for keyword in feature_keywords) 
                    and len(sentence) > 20):
                    feature_sentences.append(sentence)
        
        for sentence in feature_sentences[:4]:
            features += f"• {sentence}.\n"
        
        if features.count('•') > 0:
            sections.append(features.strip())
    
    return sections

# Helper functions
def _clean_paragraph(paragraph):
    """Clean and format a paragraph"""
    if not paragraph:
        return ""
    
    paragraph = re.sub(r'\s+', ' ', paragraph).strip()
    
    if paragraph:
        paragraph = paragraph[0].upper() + paragraph[1:]
        if not paragraph.endswith(('.', '!', '?')):
            paragraph += '.'
    
    return paragraph
