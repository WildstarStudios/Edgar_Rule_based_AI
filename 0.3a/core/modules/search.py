"""
Wikipedia Search Module for Edgar AI Assistant

This module provides Wikipedia search and summary functionality by directly scraping Wikipedia.
It can search for topics and generate concise summaries.
Single-turn module - processes one request and exits.
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from typing import List, Tuple, Optional

# Module configuration
module_name = "search"
module_version = "1.0"

def process(user_input: str, api) -> List[Tuple[str, float, str]]:
    """
    Process user input to search Wikipedia and generate summaries by scraping.
    
    Args:
        user_input: The user's input text
        api: StreamingAPI instance for communication
        
    Returns:
        List of responses in format (answer, confidence, source)
    """
    try:
        # Extract search query from user input
        search_query = _extract_search_query(user_input)
        
        if not search_query:
            return [("I'm ready to search Wikipedia. What would you like me to look up?", 0.8, "Wikipedia Searcher")]
        
        api.stream_status(f"Searching Wikipedia for: {search_query}")
        api.stream_thinking("🔍 Searching Wikipedia...")
        
        # Step 1: Search Wikipedia using the search page
        search_url = f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if no results were found
        no_results = soup.find('div', class_='mw-search-nonefound') or soup.find('p', class_='mw-search-nonefound')
        if no_results:
            return [(
                f"I couldn't find any Wikipedia articles matching '{search_query}'. "
                "Please try a different search term or check your spelling.", 
                0.9, 
                "Wikipedia Searcher"
            )]
        
        # NEW FIX: Better method to find the first search result
        article_url = _find_first_search_result(soup, search_query)
        
        if not article_url:
            return [(
                f"I couldn't find any Wikipedia articles matching '{search_query}'. "
                "Please try a different search term.", 
                0.9, 
                "Wikipedia Searcher"
            )]
        
        api.stream_status(f"Found article, extracting summary...")
        api.stream_thinking("📖 Reading article...")
        
        # Step 2: Scrape the actual article
        article_response = requests.get(article_url, headers=headers, timeout=10)
        article_response.raise_for_status()
        
        # Check if we got a 404 or other error
        if article_response.status_code != 200:
            return [(
                f"I found a potential match for '{search_query}' but the article doesn't seem to exist. "
                "Please try a different search term.",
                0.8,
                "Wikipedia Searcher"
            )]
        
        article_soup = BeautifulSoup(article_response.content, 'html.parser')
        
        # Check if this is a disambiguation page
        if _is_disambiguation_page(article_soup):
            options = _get_disambiguation_options(article_soup)
            disambiguation_response = _format_disambiguation_response(search_query, options)
            return [(
                disambiguation_response,
                0.9,
                "Wikipedia Disambiguation"
            )]
        
        # Extract article title
        title = _extract_article_title(article_soup)
        
        # Extract summary (first few paragraphs)
        summary = _extract_article_summary(article_soup)
        
        if not summary:
            # Try alternative extraction method
            summary = _extract_article_summary_alt(article_soup)
            
        if not summary:
            return [(
                f"I found the Wikipedia page for '{title}' but couldn't extract a readable summary. "
                f"You can read it here: {article_url}",
                0.8,
                "Wikipedia Searcher"
            )]
        
        formatted_response = _format_wikipedia_response(title, summary, article_url)
        
        return [(
            formatted_response,
            1.0,  # High confidence for successful searches
            f"Wikipedia: {title}"
        )]
            
    except requests.RequestException as e:
        error_msg = f"Network error while accessing Wikipedia: {str(e)}"
        api.stream_error(error_msg)
        return [(
            "I couldn't connect to Wikipedia. Please check your internet connection and try again.",
            0.5,
            "Network Error"
        )]
        
    except Exception as e:
        error_msg = f"Unexpected error in Wikipedia module: {str(e)}"
        api.stream_error(error_msg)
        return [(
            "An unexpected error occurred while searching Wikipedia.",
            0.3,
            "Module Error"
        )]

def _find_first_search_result(soup: BeautifulSoup, search_query: str) -> Optional[str]:
    """
    NEW: Better method to find the first valid search result from Wikipedia search page.
    """
    # Method 1: Look for search result containers
    search_results = soup.find_all('div', class_='mw-search-result')
    if search_results:
        first_result = search_results[0]
        link = first_result.find('a', href=True)
        if link:
            href = link.get('href', '')
            if href.startswith('/wiki/'):
                return "https://en.wikipedia.org" + href
    
    # Method 2: Look for search result links in the content area
    content_div = soup.find('div', class_='mw-search-results')
    if content_div:
        links = content_div.find_all('a', href=re.compile('^/wiki/'))
        for link in links:
            href = link.get('href', '')
            # Avoid special pages and disambiguation pages for the first result
            if (href.startswith('/wiki/') and 
                not ':' in href and  # Avoid Wikipedia special pages
                not '(disambiguation)' in href.lower()):
                return "https://en.wikipedia.org" + href
    
    # Method 3: Look for any wiki links in the main content
    main_content = soup.find('div', id='mw-content-text')
    if main_content:
        links = main_content.find_all('a', href=re.compile('^/wiki/'))
        for link in links:
            href = link.get('href', '')
            if (href.startswith('/wiki/') and 
                not ':' in href and
                not '(disambiguation)' in href.lower()):
                return "https://en.wikipedia.org" + href
    
    # Method 4: Check if we were redirected to an article directly
    # This handles cases where the search immediately goes to an article
    title_element = soup.find('h1', id='firstHeading')
    if title_element:
        # We're already on an article page
        current_url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(search_query.replace(' ', '_'))
        return current_url
    
    return None

def _is_disambiguation_page(soup: BeautifulSoup) -> bool:
    """Check if the page is a disambiguation page"""
    disambig_indicator = soup.find('div', id='disambig')
    if disambig_indicator:
        return True
    
    # Also check for disambiguation in the title or headings
    page_title = soup.find('h1', class_='firstHeading')
    if page_title and 'disambiguation' in page_title.get_text().lower():
        return True
    
    return False

def _get_disambiguation_options(soup: BeautifulSoup) -> List[str]:
    """Extract disambiguation options from the page"""
    options = []
    
    # Look for list items in disambiguation pages
    list_items = soup.find_all('li')
    for item in list_items:
        link = item.find('a', href=re.compile('^/wiki/'))
        if link and not link.get('class'):  # Avoid navigation links
            text = link.get_text().strip()
            if text and len(text) < 100:  # Reasonable length for a topic
                options.append(text)
    
    return options[:8]  # Return top 8 options

def _extract_article_title(soup: BeautifulSoup) -> str:
    """Extract the article title"""
    title_element = soup.find('h1', class_='firstHeading')
    if title_element:
        return title_element.get_text().strip()
    return "Unknown Title"

def _extract_article_summary(soup: BeautifulSoup, num_paragraphs: int = 3) -> str:
    """
    Extract the summary from a Wikipedia article.
    Gets the first few paragraphs from the main content.
    """
    # Find the main content div
    content_div = soup.find('div', id='mw-content-text')
    if not content_div:
        return None
    
    # Get paragraphs from the main content
    paragraphs = []
    all_paragraphs = content_div.find_all('p')
    
    for p in all_paragraphs:
        text = p.get_text().strip()
        
        # Remove Wikipedia annotations
        text = re.sub(r'\[edit\]', '', text)  # Remove [edit] markers
        text = re.sub(r'\[\d+\]', '', text)  # Remove citation markers [1], [2], etc.
        text = re.sub(r'\[citation needed\]', '', text)  # Remove [citation needed]
        text = re.sub(r'\[who\]', '', text)  # Remove [who?] markers
        text = re.sub(r'\[when\]', '', text)  # Remove [when?] markers
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        # Skip empty paragraphs, navigation, and very short paragraphs
        if (text and 
            len(text) > 30 and 
            not text.startswith('This article') and
            not 'may refer to:' in text.lower() and
            not text.startswith('For other uses') and
            not text.startswith('In music')):
            paragraphs.append(text)
        
        if len(paragraphs) >= num_paragraphs:
            break
    
    # Join paragraphs with proper spacing
    if paragraphs:
        return '\n\n'.join(paragraphs)
    return None

def _extract_article_summary_alt(soup: BeautifulSoup) -> str:
    """
    Alternative method to extract summary - more aggressive but preserves formatting
    """
    # Try to find the main content area
    content = soup.find('div', {'id': 'mw-content-text'})
    if not content:
        return None
    
    # Get all text and find the first substantial block
    all_text = content.get_text()
    
    # Remove Wikipedia-specific annotations before processing
    all_text = re.sub(r'\[edit\]', '', all_text)  # Remove [edit] markers
    all_text = re.sub(r'\[\d+\]', '', all_text)  # Remove citation markers
    all_text = re.sub(r'\[citation needed\]', '', all_text)  # Remove [citation needed]
    all_text = re.sub(r'\[who\]', '', all_text)  # Remove [who?]
    all_text = re.sub(r'\[when\]', '', all_text)  # Remove [when?]
    
    # Split into paragraphs by double newlines or periods followed by space
    paragraphs = re.split(r'\n\s*\n|\.\s+(?=[A-Z])', all_text)
    
    # Take first 3-5 meaningful paragraphs
    summary_paragraphs = []
    for paragraph in paragraphs:
        clean_paragraph = paragraph.strip()
        clean_paragraph = re.sub(r'\s+', ' ', clean_paragraph)  # Normalize internal whitespace
        
        if (len(clean_paragraph) > 50 and 
            len(summary_paragraphs) < 4 and
            not clean_paragraph.startswith('This article') and
            not 'may refer to:' in clean_paragraph.lower() and
            not clean_paragraph.startswith('For other uses')):
            # Add period if it doesn't end with punctuation
            if clean_paragraph and clean_paragraph[-1] not in '.!?':
                clean_paragraph += '.'
            summary_paragraphs.append(clean_paragraph)
    
    # Join with proper spacing
    if summary_paragraphs:
        return '\n\n'.join(summary_paragraphs)
    return None

def _extract_search_query(user_input: str) -> Optional[str]:
    """
    Extract the search query from user input by removing common trigger phrases.
    
    Args:
        user_input: Raw user input
        
    Returns:
        Extracted search query or None if no meaningful query found
    """
    # Common trigger phrases to remove
    trigger_phrases = [
        "search", "search for", "search up", "look up", "find",
        "wikipedia", "wiki", "what is", "who is", "tell me about",
        "find information about", "can you search for"
    ]
    
    query = user_input.lower().strip()
    
    # Remove trigger phrases
    for phrase in trigger_phrases:
        if query.startswith(phrase):
            query = query[len(phrase):].strip()
            # Also try with the phrase + "for" if it doesn't end with "for"
            if not phrase.endswith("for") and query.startswith("for "):
                query = query[4:].strip()
            break
    
    # Remove punctuation and clean up
    query = re.sub(r'[^\w\s]', '', query)
    query = query.strip()
    
    # Return None if query is empty or too short
    if not query or len(query) < 2:
        return None
    
    return query

def _format_wikipedia_response(topic: str, summary: str, url: str) -> str:
    """
    Format Wikipedia response in a user-friendly way.
    
    Args:
        topic: Main topic
        summary: Article summary
        url: Wikipedia URL
        
    Returns:
        Formatted response string
    """
    response = f"📚 **Wikipedia Search Results**\n\n"
    response += f"**{topic}**\n\n"
    response += f"{summary}\n\n"
    response += f"🔗 Read more: {url}"
    
    return response

def _format_disambiguation_response(query: str, options: List[str]) -> str:
    """
    Format disambiguation response when multiple matches are found.
    
    Args:
        query: Original search query
        options: List of disambiguation options
        
    Returns:
        Formatted disambiguation response
    """
    response = f"🔍 **Wikipedia Search - Multiple Matches**\n\n"
    response += f"Multiple Wikipedia articles match '{query}':\n\n"
    
    for i, option in enumerate(options, 1):
        response += f"{i}. {option}\n"
    
    response += "\nPlease specify which one you meant, for example: "
    response += f"'search for {options[0]}' or 'tell me about {options[1]}'"
    
    return response

# Test function for module development
def test_module():
    """Test the Wikipedia module functionality"""
    print("Testing Wikipedia Search Module...")
    
    # Mock API for testing
    class MockAPI:
        def stream_text(self, text, prefix="", wpm=None):
            print(f"STREAM: {prefix}{text}")
        
        def stream_thinking(self, text):
            print(f"THINKING: {text}")
        
        def stream_status(self, status):
            print(f"STATUS: {status}")
        
        def stream_error(self, error):
            print(f"ERROR: {error}")
        
        def get_config(self):
            return {'streaming_speed': 10000, 'additional_info_speed': 10000}
    
    api = MockAPI()
    
    # Test cases
    test_inputs = [
        "search godot",
        "search godot more ing",
        "what is python programming", 
        "who is Albert Einstein",
        "search asdfghjkl12345"  # Test non-existent article
    ]
    
    for test_input in test_inputs:
        print(f"\n{'='*50}")
        print(f"Testing: '{test_input}'")
        print(f"{'=' * 50}")
        
        results = process(test_input, api)
        
        for answer, confidence, source in results:
            print(f"Confidence: {confidence}, Source: {source}")
            print(f"Answer: {answer}")

if __name__ == "__main__":
    test_module()