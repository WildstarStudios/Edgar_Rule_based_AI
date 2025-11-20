# core/modules/search.py
from fuzzywuzzy import fuzz
from ddgs import DDGS
import Levenshtein
import time
import re

module_mode = True
strict_matching = False

def get_expected_patterns():
    """Define patterns that this module expects to handle"""
    return [
        # Search trigger phrases (required for new searches)
        "search", "look up", "find", "web search", "search for",
        "search about", "look up about", "find about", 
        "search info", "look up info", "find info",
        "search the web", "search online", "web lookup",
        "what is", "what are", "who is", "tell me about",
        "explain", "define", "summary of", "information about",
        
        # Navigation patterns (no trigger required)
        "more results", "next", "more", "show more",
        "different search", "new search", "search again",
        "tell me more about", "details for", "result",
        
        # Source patterns (no trigger required)
        "sources", "references", "source", "citations",
        
        # Completion patterns (no trigger required)
        "yes", "no", "done", "stop", "exit search"
    ]

def process(user_input, api):
    user_context = api.get_module_context()
    state = user_context.get('search_state', _initialize_search_state())
    
    input_lower = user_input.lower().strip()
    
    # Handle completion requests
    if _is_completion_request(input_lower):
        return _handle_completion_request(state, api)
    
    # Handle sources request (no trigger required)
    if _is_sources_request(input_lower) and state['step'] == 1 and state['showing_results']:
        return _handle_sources_request(state, api)
    
    # Main search flow
    if state['step'] == 0:
        # Initial state - require search trigger phrase
        return _handle_initial_search(input_lower, state, api)
    elif state['step'] == 1:
        # In search session - handle follow-ups and new searches with trigger
        return _handle_follow_up(input_lower, state, api)
    
    return _fallback_response()

def _handle_initial_search(user_input, state, api):
    """Handle initial search request - requires trigger phrase"""
    search_query = _extract_search_query(user_input)
    
    if not search_query:
        return [("To search the web, please start with a search phrase like 'search about [topic]', 'look up [thing]', or 'what is [subject]'.", 0.8, "Search Module")]
    
    # Update state for new search
    state.update({
        'step': 1,
        'last_query': search_query,
        'current_page': 0,
        'showing_results': False,
        'summary_provided': False,
        'summary_sections_shown': 0,
        'all_summary_sections': []
    })
    _save_state(state, api)
    
    # Perform search
    api.stream_thinking(f"🔍 Searching for '{search_query}'...")
    results = perform_search(search_query)
    state['last_results'] = results
    
    if not results or 'error' in results[0]:
        error_msg = results[0]['error'] if results and 'error' in results[0] else "No results found"
        return [(f"❌ Search failed: {error_msg}. Try a different query?", 1.0, "Search Module")]
    
    state['showing_results'] = True
    _save_state(state, api)
    
    # Generate and display summary
    api.stream_thinking("📝 Generating comprehensive summary...")
    all_sections = generate_comprehensive_summary(search_query, results)
    state['all_summary_sections'] = all_sections
    
    if not all_sections:
        return [(f"❌ Couldn't generate a good summary for '{search_query}'. Try a different query?", 1.0, "Search Module")]
    
    state['summary_sections_shown'] = 1
    _save_state(state, api)
    
    formatted_response = format_initial_response(all_sections[0], state)
    return [(formatted_response, 1.0, "Search Module")]

def _handle_follow_up(user_input, state, api):
    """Handle follow-up interactions after initial search"""
    if not state['showing_results']:
        return _fallback_response()
    
    # Handle more content requests (no trigger required)
    if _is_more_request(user_input):
        return _handle_more_content(state, api)
    
    # Handle specific result requests (no trigger required)
    detail_match = _extract_result_number(user_input)
    if detail_match and detail_match <= len(state['last_results']):
        return _handle_result_detail(detail_match, state)
    
    # Handle summary requests (no trigger required)
    if _is_summary_request(user_input) and state['summary_sections_shown'] == 0:
        return _handle_summary_request(state, api)
    
    # Handle new search - REQUIRES TRIGGER PHRASE even in follow-up
    new_query = _extract_search_query(user_input)
    if new_query:
        return _handle_new_search(new_query, state, api)
    
    # If no recognized command and no trigger phrase, show help
    return [("I'm not sure what you'd like to do. You can say 'more' for additional information, 'sources' to see references, or start a new search with 'search about [topic]'.", 0.7, "Search Module")]

def _extract_search_query(user_input):
    """Extract search query from user input - requires trigger phrases"""
    # List of valid trigger phrases that must be at the beginning
    trigger_phrases = [
        r'^search (?:up|about|for)?\s+(.+)',
        r'^look up\s+(.+)',
        r'^find (?:about|info on)?\s+(.+)',
        r'^search\s+(.+)',
        r'^find\s+(.+)',
        r'^web search\s+(.+)',
        r'^search the web for\s+(.+)',
        r'^tell me about\s+(.+)',
        r'^what is\s+(.+)',
        r'^what are\s+(.+)',
        r'^who is\s+(.+)',
        r'^explain\s+(.+)',
        r'^define\s+(.+)',
        r'^summary of\s+(.+)',
        r'^information about\s+(.+)'
    ]
    
    for pattern in trigger_phrases:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Clean up common prefixes but keep the natural query
            query = re.sub(r'^\s*(up|about|for|the)\s+', '', query).strip()
            if len(query) > 2:
                return query
    
    # Check for trigger phrases at the beginning (without regex)
    trigger_starts = [
        'search', 'look up', 'find', 'web search', 
        'what is', 'what are', 'who is', 'tell me about',
        'explain', 'define', 'summary of', 'information about'
    ]
    
    for trigger in trigger_starts:
        if user_input.lower().startswith(trigger):
            query = user_input[len(trigger):].strip()
            if len(query) > 2:
                return query
    
    return None

# ... (rest of the functions remain the same as the previous optimized version)

def _initialize_search_state():
    return {
        'step': 0,
        'last_query': None,
        'last_results': [],
        'current_page': 0,
        'showing_results': False,
        'search_type': 'general',
        'summary_provided': False,
        'summary_sections_shown': 0,
        'all_summary_sections': []
    }

def _handle_more_content(state, api):
    """Handle request for more summary content"""
    if not state['all_summary_sections']:
        api.stream_thinking("📝 Generating comprehensive summary...")
        all_sections = generate_comprehensive_summary(state['last_query'], state['last_results'])
        state['all_summary_sections'] = all_sections
        state['summary_sections_shown'] = 0
    
    if state['summary_sections_shown'] < len(state['all_summary_sections']):
        next_section = state['all_summary_sections'][state['summary_sections_shown']]
        state['summary_sections_shown'] += 1
        _save_state(state, api)
        
        response = next_section + "\n\n"
        if state['summary_sections_shown'] < len(state['all_summary_sections']):
            response += "💡 Say **'more'** to continue learning about this topic."
        else:
            response += "✅ **That's all the key information!**\n"
            response += "• Say **'sources'** to see references\n"
            response += "• Say **'search about [new topic]'** for a new search\n"
            response += "• Say **'done'** to finish this search session\n"
        
        return [(response, 1.0, "Search Module")]
    
    return _handle_additional_search(state, api)

def _handle_additional_search(state, api):
    """Get additional search results when all sections are shown"""
    state['current_page'] += 1
    _save_state(state, api)
    
    api.stream_thinking(f"🔍 Getting more information about '{state['last_query']}'...")
    more_results = perform_search(state['last_query'], page=state['current_page'])
    
    if not more_results or 'error' in more_results[0]:
        return [("I've found all the key information available. Would you like to see the sources or search for something else?", 0.9, "Search Module")]
    
    state['last_results'].extend(more_results)
    api.stream_thinking("📝 Generating additional information...")
    additional_sections = generate_additional_summary(state['last_query'], state['last_results'])
    
    if additional_sections:
        state['all_summary_sections'].extend(additional_sections)
        next_section = state['all_summary_sections'][state['summary_sections_shown']]
        state['summary_sections_shown'] += 1
        _save_state(state, api)
        
        response = next_section + "\n\n"
        response += "💡 Say **'more'** for even more information or **'sources'** to see references."
        return [(response, 1.0, "Search Module")]
    
    return [("I've gathered comprehensive information on this topic. Would you like to see the sources or search for something else?", 0.9, "Search Module")]

def _handle_sources_request(state, api):
    """Handle request to show sources"""
    sources_info = format_sources_list(state['last_results'], state)
    return [(sources_info, 1.0, "Search Module")]

def _handle_summary_request(state, api):
    """Handle request for summary"""
    api.stream_thinking("📝 Generating summary...")
    all_sections = generate_comprehensive_summary(state['last_query'], state['last_results'])
    state['all_summary_sections'] = all_sections
    
    if not all_sections:
        return [("❌ Couldn't generate a summary from the available information.", 0.9, "Search Module")]
    
    state['summary_sections_shown'] = 1
    _save_state(state, api)
    return [(all_sections[0], 1.0, "Search Module")]

def _handle_result_detail(result_number, state):
    """Handle request for specific result details"""
    result = state['last_results'][result_number - 1]
    detailed_info = get_detailed_result(result)
    return [(detailed_info, 1.0, "Search Module")]

def _handle_new_search(new_query, state, api):
    """Handle starting a new search"""
    state.update({
        'last_query': new_query,
        'current_page': 0,
        'summary_provided': False,
        'summary_sections_shown': 0,
        'all_summary_sections': []
    })
    _save_state(state, api)
    
    api.stream_thinking(f"🔍 Searching for '{new_query}'...")
    results = perform_search(new_query)
    state['last_results'] = results
    
    if not results or 'error' in results[0]:
        error_msg = results[0]['error'] if results and 'error' in results[0] else "No results found"
        return [(f"❌ Search failed: {error_msg}. Try a different query?", 1.0, "Search Module")]
    
    api.stream_thinking("📝 Generating comprehensive summary...")
    all_sections = generate_comprehensive_summary(new_query, results)
    state['all_summary_sections'] = all_sections
    
    if not all_sections:
        return [(f"❌ Couldn't generate a good summary for '{new_query}'.", 1.0, "Search Module")]
    
    state['summary_sections_shown'] = 1
    _save_state(state, api)
    formatted_response = format_initial_response(all_sections[0], state)
    return [(formatted_response, 1.0, "Search Module")]

def _save_state(state, api):
    """Save state to module context"""
    user_context = api.get_module_context()
    user_context['search_state'] = state
    api.set_module_context(user_context)

def perform_search(query, page=0):
    """Perform search with better query optimization"""
    try:
        with DDGS() as ddgs:
            time.sleep(0.5)
            
            # Enhanced query for better results
            enhanced_query = _enhance_search_query(query)
            
            results = list(ddgs.text(
                query=enhanced_query,
                region='wt-wt',
                safesearch='moderate',
                max_results=15,
                backend='html'
            ))
            
            if not results:
                return [{'error': 'No results found from search engine'}]
            
            filtered_results = _filter_search_results(results, query)
            return filtered_results[:8] if filtered_results else [{'error': 'No high-quality results found after filtering'}]
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return [{'error': f'Search failed: {str(e)}'}]

def _enhance_search_query(query):
    """Enhance search query for better results"""
    query_lower = query.lower()
    
    if any(term in query_lower for term in ['godot', 'unity', 'unreal', 'game engine']):
        return f"{query} game engine features capabilities documentation"
    elif any(term in query_lower for term in ['python', 'javascript', 'java', 'programming']):
        return f"{query} programming language tutorial documentation"
    elif any(term in query_lower for term in ['what is', 'who is', 'explain']):
        return f"{query} definition overview introduction"
    else:
        return f"{query} overview features uses documentation"

def _filter_search_results(results, original_query):
    """Better filtering of search results"""
    filtered = []
    skip_domains = ['reddit.com', 'quora.com', 'forum.', 'youtube.com', 'tiktok.com', 'pinterest.com']
    skip_titles = ['login', 'sign up', 'download', 'buy', 'price', 'shop', 'wikipedia waiting for godot']
    
    for result in results:
        title = result.get('title', '').lower()
        link = result.get('href', '')
        body = result.get('body', '')
        
        if any(domain in link.lower() for domain in skip_domains):
            continue
        if len(body) < 50:
            continue
        if any(skip in title for skip in skip_titles):
            continue
        
        if not _is_result_relevant(title, body, original_query):
            continue
        
        filtered.append({
            'title': result.get('title', 'No title'),
            'link': link,
            'description': body
        })
    
    return filtered

def _is_result_relevant(title, body, query):
    """Check if search result is relevant to the query"""
    query_terms = query.lower().split()
    title_lower = title.lower()
    body_lower = body.lower()
    
    title_matches = sum(1 for term in query_terms if term in title_lower)
    body_matches = sum(1 for term in query_terms if term in body_lower)
    
    return title_matches >= 1 or body_matches >= len(query_terms) * 0.5

def generate_comprehensive_summary(query, search_results):
    """Generate comprehensive summary with better content extraction"""
    if not search_results or 'error' in search_results[0]:
        return []
    
    all_text = _extract_clean_text(search_results[:6])
    paragraphs = _extract_meaningful_paragraphs(all_text, query)
    
    sections = _build_summary_sections(query, paragraphs)
    
    return sections

def _extract_meaningful_paragraphs(all_text, query):
    """Extract meaningful paragraphs instead of just sentences"""
    paragraphs = re.split(r'\n\s*\n|\.\s+[A-Z]', all_text)
    
    meaningful_paragraphs = []
    query_terms = query.lower().split()
    
    for para in paragraphs:
        para = para.strip()
        if len(para) < 60 or len(para) > 400:
            continue
        
        para_lower = para.lower()
        
        if not any(term in para_lower for term in query_terms):
            continue
        
        if any(unwanted in para_lower for unwanted in ['hours ago', 'just now', 'upvote', 'downvote']):
            continue
        
        cleaned = _clean_paragraph(para)
        if cleaned:
            meaningful_paragraphs.append(cleaned)
    
    return meaningful_paragraphs

def _clean_paragraph(paragraph):
    """Clean and format a paragraph"""
    paragraph = re.sub(r'\b\d{1,2} hours? ago\s*[-–]\s*', '', paragraph)
    paragraph = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\s*[-–]\s*', '', paragraph)
    paragraph = re.sub(r'\d{1,2}:\d{2}\s*(AM|PM)?\s*', '', paragraph)
    paragraph = re.sub(r'\s+', ' ', paragraph).strip()
    
    paragraph = re.sub(r'^(so|but|and|or|however|although)\s+', '', paragraph, flags=re.IGNORECASE)
    paragraph = re.sub(r'\/.*?\ⓘ\s*', '', paragraph)
    
    if paragraph:
        paragraph = paragraph[0].upper() + paragraph[1:]
        if not paragraph.endswith(('.', '!', '?')):
            paragraph += '.'
    
    return paragraph if len(paragraph) > 40 else None

def _build_summary_sections(query, paragraphs):
    """Build summary sections from meaningful paragraphs"""
    sections = []
    
    categorized = _categorize_paragraphs(paragraphs, query)
    
    section_builders = [
        (_build_definition_section, "📚 **What is {query}?**"),
        (_build_features_section, "🌟 **Key Features and Capabilities**"),
        (_build_usage_section, "🚀 **Common Uses and Applications**"),
        (_build_history_section, "📅 **History and Background**"),
        (_build_technical_section, "⚙️ **Technical Details**")
    ]
    
    for builder, title_template in section_builders:
        section = builder(query, categorized)
        if section:
            sections.append(title_template.format(query=query.title()) + "\n\n" + section)
            if len(sections) >= 4:
                break
    
    return sections

def _categorize_paragraphs(paragraphs, query):
    """Categorize paragraphs by content type"""
    categories = {
        'definition': [],
        'features': [],
        'usage': [],
        'history': [],
        'technical': [],
        'general': []
    }
    
    definition_keywords = ['is a', 'is an', 'are a', 'are an', 'refers to', 'means', 'defined as', 'known as', 'called']
    feature_keywords = ['features', 'supports', 'includes', 'provides', 'offers', 'capabilities', 'functionality', 'can']
    usage_keywords = ['used for', 'used to', 'usage', 'purpose', 'applications', 'use cases', 'commonly used']
    history_keywords = ['created', 'developed', 'founded', 'released', 'introduced', 'version', 'history', 'originally']
    technical_keywords = ['language', 'framework', 'library', 'tool', 'software', 'platform', 'system', 'technology']
    
    for para in paragraphs:
        para_lower = para.lower()
        
        if any(keyword in para_lower for keyword in definition_keywords):
            categories['definition'].append(para)
        elif any(keyword in para_lower for keyword in feature_keywords):
            categories['features'].append(para)
        elif any(keyword in para_lower for keyword in usage_keywords):
            categories['usage'].append(para)
        elif any(keyword in para_lower for keyword in history_keywords):
            categories['history'].append(para)
        elif any(keyword in para_lower for keyword in technical_keywords):
            categories['technical'].append(para)
        else:
            categories['general'].append(para)
    
    for category in categories:
        categories[category] = _remove_duplicate_paragraphs(categories[category])
    
    return categories

def _build_definition_section(query, categorized):
    paragraphs = categorized['definition'][:3]
    if not paragraphs and categorized['general']:
        paragraphs = categorized['general'][:2]
    
    return _format_paragraphs_as_bullets(paragraphs)

def _build_features_section(query, categorized):
    paragraphs = categorized['features'][:4]
    if not paragraphs and categorized['general']:
        paragraphs = categorized['general'][:3]
    
    return _format_paragraphs_as_bullets(paragraphs)

def _build_usage_section(query, categorized):
    paragraphs = categorized['usage'][:3]
    if not paragraphs and categorized['general']:
        paragraphs = categorized['general'][:2]
    
    return _format_paragraphs_as_bullets(paragraphs)

def _build_history_section(query, categorized):
    paragraphs = categorized['history'][:3]
    return _format_paragraphs_as_bullets(paragraphs)

def _build_technical_section(query, categorized):
    paragraphs = categorized['technical'][:3]
    return _format_paragraphs_as_bullets(paragraphs)

def _format_paragraphs_as_bullets(paragraphs):
    if not paragraphs:
        return ""
    
    formatted = ""
    for para in paragraphs:
        formatted += f"• {para}\n"
    return formatted

def _remove_duplicate_paragraphs(paragraphs):
    unique = []
    seen = set()
    
    for para in paragraphs:
        signature = re.sub(r'\s+', ' ', para.lower().strip())[:50]
        if signature not in seen:
            seen.add(signature)
            unique.append(para)
    
    return unique

def _extract_clean_text(search_results):
    all_text = ""
    for result in search_results:
        description = result.get('description', '')
        description = re.sub(r'\b\d{1,2} hours? ago\s*[-–]\s*', '', description)
        description = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\s*[-–]\s*', '', description)
        description = re.sub(r'\d{1,2}:\d{2}\s*(AM|PM)?\s*', '', description)
        description = re.sub(r'\s+', ' ', description).strip()
        all_text += description + " \n\n"
    return all_text

def generate_additional_summary(query, search_results):
    if not search_results or 'error' in search_results[0]:
        return []
    
    new_results = search_results[-4:] if len(search_results) > 6 else search_results
    all_text = _extract_clean_text(new_results)
    paragraphs = _extract_meaningful_paragraphs(all_text, query)
    
    if paragraphs:
        section = f"🔍 **Additional Insights: {query.title()}**\n\n"
        for para in paragraphs[:4]:
            section += f"• {para}\n"
        return [section]
    
    return []

def format_initial_response(summary_section, state):
    response = summary_section + "\n\n"
    response += "💡 **Next steps:**\n"
    response += "• Say **'more'** to continue learning about this topic\n"
    response += "• Say **'sources'** to see the full search results with references\n"
    response += "• Say **'search about [new topic]'** for a new search\n"
    response += "• Say **'done'** to finish this search session\n"
    return response

def format_sources_list(results, state):
    if not results or 'error' in results[0]:
        return f"❌ I couldn't find any results for '{state['last_query']}'. Try a different search query?"
    
    response = f"🔍 **Sources and Results for '{state['last_query']}':**\n\n"
    
    for i, result in enumerate(results, 1):
        clean_description = _clean_paragraph(result['description'])
        response += f"**{i}. {result['title']}**\n"
        response += f"   {_truncate_text(clean_description, 120)}\n"
        response += f"   📎 {result['link']}\n\n"
    
    response += "💡 **Next steps:**\n"
    response += "• Say **'tell me about result 2'** for detailed information about a specific result\n" 
    response += "• Say **'more'** for additional information about the topic\n"
    response += "• Say **'search about [new topic]'** for a new search\n"
    response += "• Say **'done'** to finish this search session\n"
    
    return response

def get_detailed_result(result):
    clean_description = _clean_paragraph(result['description'])
    detailed = f"📖 **Detailed Information:**\n\n"
    detailed += f"**Title:** {result['title']}\n\n"
    detailed += f"**Description:** {clean_description}\n\n"
    detailed += f"**Link:** {result['link']}\n\n"
    detailed += "💡 You can say 'more' for additional information, 'sources' for references, or search for something new."
    return detailed

# Command detection functions
def _is_completion_request(user_input):
    done_keywords = ["done", "stop", "exit", "no", "thanks", "thank you", "finished", "that's all", "all done"]
    return user_input in done_keywords or any(fuzz.token_set_ratio(user_input, keyword) >= 80 for keyword in done_keywords)

def _is_sources_request(user_input):
    source_keywords = ["sources", "references", "source", "citations", "where did you get this"]
    return user_input in source_keywords or any(fuzz.token_set_ratio(user_input, keyword) >= 80 for keyword in source_keywords)

def _is_more_request(user_input):
    more_keywords = ["more", "next", "continue", "show more", "what else", "tell me more"]
    return user_input in more_keywords or any(fuzz.token_set_ratio(user_input, keyword) >= 80 for keyword in more_keywords)

def _is_summary_request(user_input):
    summary_keywords = ["summary", "summarize", "overview", "brief", "explain", "what is", "tell me about"]
    return any(fuzz.token_set_ratio(user_input, keyword) >= 70 for keyword in summary_keywords)

def _extract_result_number(user_input):
    patterns = [r'result (\d+)', r'number (\d+)', r'about (\d+)', r'details? (\d+)', r'option (\d+)']
    
    for pattern in patterns:
        match = re.search(pattern, user_input)
        if match:
            return int(match.group(1))
    
    ordinal_patterns = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
        '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5
    }
    
    for word, number in ordinal_patterns.items():
        if word in user_input:
            return number
    
    return None

def _truncate_text(text, max_length):
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def _handle_completion_request(state, api):
    user_context = api.get_module_context()
    user_context['search_state'] = _initialize_search_state()
    api.set_module_context(user_context)
    return [("Search session completed. What would you like to search for next? You can say 'search about [topic]' or 'look up [thing]'", 1.0, "Search Module")]

def _fallback_response():
    return [("To search the web, please start with a search phrase like 'search about [topic]', 'look up [thing]', or 'what is [subject]'.", 0.5, "Search Module")]