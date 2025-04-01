"""
Chat display module for rendering and styling chat messages using WebEngine.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWebChannel import QWebChannel
from datetime import datetime
import os
import json
import re

from ui.chat_components.message_formatter import MessageFormatter


class ChatBubbleDisplay(QWebEngineView):
    
    
    def __init__(self, parent=None):
        """Initialize the chat bubble display.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.page().setBackgroundColor(Qt.transparent)
        self.setStyleSheet("background: transparent;")
        
        
        self.load_html_template()
        
    def load_html_template(self):
        
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 16px;
                    background-color: transparent;
                    color: 
                    overflow-y: auto;
                    overflow-x: hidden;
                }
                
                .chat-container {
                    max-width: 100%;
                    margin: 0 auto;
                    display: flex;
                    flex-direction: column;
                }
                
                .message-group {
                    margin-bottom: 16px;
                    display: flex;
                    flex-direction: column;
                }
                
                .message-bubble {
                    padding: 12px 16px;
                    border-radius: 18px;
                    max-width: 80%;
                    margin: 2px 0;
                    position: relative;
                    line-height: 1.5;
                    overflow-wrap: break-word;
                    word-wrap: break-word;
                }
                
                .user-group {
                    align-items: flex-end;
                }
                
                .assistant-group {
                    align-items: flex-start;
                }
                
                .user-bubble {
                    background-color: rgba(66, 133, 244, 0.9);
                    color: white;
                    align-self: flex-end;
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }
                
                .assistant-bubble {
                    background-color: rgba(241, 243, 244, 0.75);
                    color: 
                    align-self: flex-start;
                    backdrop-filter: blur(8px);
                    -webkit-backdrop-filter: blur(8px);
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
                
                .user-bubble-first {
                    border-radius: 18px 18px 4px 18px;
                }
                
                .user-bubble-middle {
                    border-radius: 18px 4px 4px 18px;
                }
                
                .user-bubble-last {
                    border-radius: 18px 4px 18px 18px;
                }
                
                .assistant-bubble-first {
                    border-radius: 18px 18px 18px 4px;
                }
                
                .assistant-bubble-middle {
                    border-radius: 4px 18px 18px 4px;
                }
                
                .assistant-bubble-last {
                    border-radius: 4px 18px 18px 18px;
                }
                
                .timestamp {
                    font-size: 0.7rem;
                    color: rgba(255, 255, 255, 0.7);
                    margin-top: 4px;
                    text-align: right;
                }
                
                .assistant-timestamp {
                    color: 
                    margin-left: 8px;
                }
                
                code {
                    font-family: 'Consolas', 'Courier New', monospace;
                    background-color: rgba(0, 0, 0, 0.1);
                    padding: 2px 4px;
                    border-radius: 4px;
                }
                
                pre {
                    background-color: rgba(0, 0, 0, 0.8);
                    color: 
                    padding: 12px;
                    border-radius: 8px;
                    overflow-x: auto;
                    font-family: 'Consolas', 'Courier New', monospace;
                    margin: 8px 0;
                }
                
                pre code {
                    background-color: transparent;
                    padding: 0;
                    color: inherit;
                }
                
                .code-header {
                    background-color: rgba(0, 0, 0, 0.5);
                    padding: 6px 12px;
                    border-radius: 8px 8px 0 0;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 0.8rem;
                    color: 
                    display: flex;
                    justify-content: space-between;
                }
                
                .code-block {
                    margin: 8px 0;
                }
                
                .code-content {
                    margin-top: 0;
                    border-top-left-radius: 0;
                    border-top-right-radius: 0;
                }
                
                .hljs-keyword, .hljs-selector-tag, .hljs-literal, .hljs-section, .hljs-link {
                    color: 
                }
                
                .hljs-function .hljs-keyword {
                    color: 
                }
                
                .hljs-string, .hljs-title, .hljs-name, .hljs-type, .hljs-attribute, .hljs-symbol, .hljs-bullet, .hljs-addition, .hljs, .hljs-code, .hljs-regexp, .hljs-selector-class, .hljs-selector-attr, .hljs-selector-pseudo, .hljs-template-tag, .hljs-template-variable {
                    color: 
                }
                
                .hljs-comment, .hljs-quote, .hljs-deletion, .hljs-meta {
                    color: 
                }
                
                .hljs-keyword, .hljs-selector-tag, .hljs-literal, .hljs-title, .hljs-section, .hljs-doctag, .hljs-type, .hljs-name, .hljs-strong {
                    font-weight: bold;
                }
                
                .hljs-emphasis {
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <div class="chat-container" id="chat-container">
                <!-- Chat messages will be inserted here -->
            </div>
        </body>
        </html>
        """
        
        
        self.setHtml(html_content)
    
    def refresh_display(self, chat_history):
        """Refresh the chat display with the current chat history.
        
        Args:
            chat_history: List of ChatMessage objects with role, content, and timestamp.
        """
        if not chat_history:
            return
        
        
        grouped_messages = []
        current_group = []
        current_role = None
        
        for message in chat_history:
            
            if hasattr(message, 'role'):
                
                role = message.role
                content = message.content
                timestamp = message.timestamp.isoformat() if hasattr(message.timestamp, 'isoformat') else str(message.timestamp)
            else:
                
                role = message.get('role', '')
                content = message.get('content', '')
                timestamp = message.get('timestamp', '')
            
            if role != current_role and current_group:
                grouped_messages.append((current_role, current_group))
                current_group = []
            
            current_role = role
            current_group.append({'content': content, 'timestamp': timestamp})
        
        
        if current_group:
            grouped_messages.append((current_role, current_group))
        
        
        html_parts = []
        
        for role, messages in grouped_messages:
            if role == 'user':
                html_parts.append('<div class="message-group user-group">')
            else:
                html_parts.append('<div class="message-group assistant-group">')
            
            for i, message in enumerate(messages):
                content = message['content']
                timestamp = message['timestamp']
                
                
                formatted_time = ""
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        formatted_time = dt.strftime("%I:%M %p")
                    except (ValueError, TypeError):
                        formatted_time = timestamp
                
                
                position_class = ""
                if len(messages) == 1:
                    position_class = ""  
                elif i == 0:
                    position_class = f"{role}-bubble-first"
                elif i == len(messages) - 1:
                    position_class = f"{role}-bubble-last"
                else:
                    position_class = f"{role}-bubble-middle"
                
                
                content = self.format_code_blocks(content)
                
                if role == 'user':
                    bubble_class = f"message-bubble user-bubble {position_class}"
                    html_parts.append(f'<div class="{bubble_class}">{content}</div>')
                    
                    
                    if i == len(messages) - 1 and formatted_time:
                        html_parts.append(f'<div class="timestamp">{formatted_time}</div>')
                else:
                    bubble_class = f"message-bubble assistant-bubble {position_class}"
                    html_parts.append(f'<div class="{bubble_class}">{content}</div>')
                    
                    
                    if i == len(messages) - 1 and formatted_time:
                        html_parts.append(f'<div class="timestamp assistant-timestamp">{formatted_time}</div>')
            
            html_parts.append('</div>')
        
        
        html = "\n".join(html_parts)
        
        
        safe_html = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
        js = f"""
        try {{
            let container = document.getElementById('chat-container');
            if (container) {{
                container.innerHTML = `{safe_html}`;
                
                // Scroll to the bottom
                window.scrollTo(0, document.body.scrollHeight);
                
                // Also try alternative scroll method
                container.scrollTop = container.scrollHeight;
                
                console.log("Chat display updated with new messages");
            }} else {{
                console.error("Chat container element not found");
            }}
        }} catch (error) {{
            console.error("Error updating chat display:", error);
        }}
        """
        
        print(f"DEBUG: Updating chat display with {len(html_parts)} HTML parts")
        self.page().runJavaScript(js)
    
    def format_code_blocks(self, content):
        """Format code blocks in the content.
        
        Args:
            content: Message content.
        
        Returns:
            Formatted content with syntax highlighted code blocks.
        """
        
        code_block_pattern = r'```([a-zA-Z0-9]*)\n([\s\S]*?)\n```'
        
        def code_replacer(match):
            language = match.group(1) or 'text'
            code_content = match.group(2)
            
            
            code_content = (code_content
                            .replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace('"', '&quot;'))
            
            return f"""
            <div class="code-block">
                <div class="code-header">{language}</div>
                <pre class="code-content"><code class="{language}">{code_content}</code></pre>
            </div>
            """
        
        
        content = re.sub(code_block_pattern, code_replacer, content)
        
        
        inline_code_pattern = r'`([^`]+)`'
        content = re.sub(
            inline_code_pattern,
            r'<code>\1</code>',
            content
        )
        
        
        content = content.replace('\n', '<br>')
        
        return content
    
    def add_message(self, message):
        """Add a single message to the display.
        
        Args:
            message: ChatMessage object.
        """
        
        self.chat_history.append(message)
        
        
        self.refresh_display() 
