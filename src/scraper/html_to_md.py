"""Convert HTML content to clean Markdown."""

import re
import logging
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class HTMLToMarkdownConverter(HTMLParser):
    """Convert HTML to Markdown format."""
    
    def __init__(self, base_url: str = ""):
        super().__init__()
        self.reset()
        self.base_url = base_url
        self.markdown = []
        self.current_list = []
        self.list_stack = []
        self.in_code = False
        self.in_pre = False
        self.code_buffer = []
    
    def handle_starttag(self, tag, attrs):
        """Handle opening tags."""
        attrs_dict = dict(attrs)
        
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag[1])
            self.markdown.append('\n' + '#' * level + ' ')
        
        elif tag == 'p':
            self.markdown.append('\n')
        
        elif tag == 'br':
            self.markdown.append('\n')
        
        elif tag in ['ul', 'ol']:
            self.list_stack.append(tag)
        
        elif tag == 'li':
            if self.list_stack:
                indent = '  ' * (len(self.list_stack) - 1)
                if self.list_stack[-1] == 'ul':
                    self.markdown.append(f'\n{indent}• ')
                else:
                    self.markdown.append(f'\n{indent}1. ')
        
        elif tag == 'strong' or tag == 'b':
            self.markdown.append('**')
        
        elif tag == 'em' or tag == 'i':
            self.markdown.append('*')
        
        elif tag == 'code':
            self.in_code = True
            self.markdown.append('`')
        
        elif tag == 'pre':
            self.in_pre = True
            self.code_buffer = []
            self.markdown.append('\n```\n')
        
        elif tag == 'a':
            href = attrs_dict.get('href', '#')
            # Convert relative URLs to absolute
            if href and href.startswith('/'):
                href = urljoin(self.base_url, href)
            self.markdown.append('[')
            self._temp_href = href
        
        elif tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', 'image')
            if src and src.startswith('/'):
                src = urljoin(self.base_url, src)
            self.markdown.append(f'![{alt}]({src})')
        
        elif tag == 'blockquote':
            self.markdown.append('\n> ')
        
        elif tag in ['div', 'section', 'article']:
            # Skip wrapper divs
            pass
    
    def handle_endtag(self, tag):
        """Handle closing tags."""
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']:
            self.markdown.append('\n')
        
        elif tag in ['ul', 'ol']:
            if self.list_stack:
                self.list_stack.pop()
            self.markdown.append('\n')
        
        elif tag in ['strong', 'b']:
            self.markdown.append('**')
        
        elif tag in ['em', 'i']:
            self.markdown.append('*')
        
        elif tag == 'code':
            self.in_code = False
            self.markdown.append('`')
        
        elif tag == 'pre':
            self.in_pre = False
            self.markdown.append('\n```\n')
        
        elif tag == 'a':
            self.markdown.append(f']({self._temp_href})')
            self._temp_href = None
        
        elif tag == 'blockquote':
            self.markdown.append('\n')
    
    def handle_data(self, data):
        """Handle text content."""
        if not data.strip():
            # Preserve single spaces between words
            if self.markdown and not self.markdown[-1].endswith(' '):
                if not self.in_pre:
                    data = ' ' if data else ''
            else:
                data = ''
        
        if self.in_pre:
            # In code blocks, preserve whitespace
            self.markdown.append(data)
        else:
            # Normal text - clean up whitespace
            text = ' '.join(data.split())
            self.markdown.append(text)
    
    def get_markdown(self):
        """Get the final markdown text."""
        text = ''.join(self.markdown)
        # Clean up excessive newlines
        text = re.sub(r'\n\n\n+', '\n\n', text)
        text = text.strip()
        return text


def html_to_markdown(html_content: str, base_url: str = "") -> str:
    """
    Convert HTML to Markdown.
    
    Args:
        html_content: HTML string to convert
        base_url: Base URL for relative link conversion
        
    Returns:
        Markdown formatted string
    """
    try:
        converter = HTMLToMarkdownConverter(base_url=base_url)
        converter.feed(html_content)
        return converter.get_markdown()
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {e}")
        # Return raw text if conversion fails
        return html_content


def clean_markdown(markdown_text: str) -> str:
    """
    Clean up Markdown text.
    
    Args:
        markdown_text: Raw markdown text
        
    Returns:
        Cleaned markdown text
    """
    # Remove HTML comments
    markdown_text = re.sub(r'<!--.*?-->', '', markdown_text, flags=re.DOTALL)
    
    # Remove multiple blank lines
    markdown_text = re.sub(r'\n\n\n+', '\n\n', markdown_text)
    
    # Remove trailing whitespace
    markdown_text = '\n'.join(line.rstrip() for line in markdown_text.split('\n'))
    
    # Remove nav/ad patterns (common in Zendesk)
    patterns = [
        r'Was this article helpful\?.*?(?=\n\n|$)',
        r'Related articles.*?(?=\n\n|$)',
        r'Did you find it helpful\?.*?(?=\n\n|$)',
    ]
    for pattern in patterns:
        markdown_text = re.sub(pattern, '', markdown_text, flags=re.IGNORECASE | re.DOTALL)
    
    return markdown_text.strip()

