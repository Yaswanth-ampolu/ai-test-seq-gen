"""
Web Engine Sidebar module for the Spring Test App.
Contains a modern sidebar widget using PyQtWebEngine for enhanced styling and animations.
"""
import sys
import os
import json
import datetime
import pandas as pd
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolButton, 
                           QFrame, QSizePolicy, QApplication, QFileDialog, QMessageBox,
                           QPushButton, QLabel, QTabWidget, QTextEdit, QHeaderView, QTableView,
                           QGroupBox, QComboBox, QMenu, QAction, QGraphicsOpacityEffect)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import (Qt, QUrl, pyqtSignal, pyqtSlot, QSize, QPropertyAnimation,
                        QEasingCurve, QObject, pyqtProperty, QTimer)
from PyQt5.QtGui import QFont, QIcon, QColor

from models.data_models import TestSequence
from models.table_models import PandasModel
from utils.constants import FILE_FORMATS

# Set up logging
logger = logging.getLogger(__name__)


class WebEngineSidebar(QWidget):
    """Modern sidebar widget using PyQtWebEngine for enhanced styling."""
    
    # Define signals
    collapsed_changed = pyqtSignal(bool)
    
    def __init__(self, export_service=None):
        """Initialize the web engine sidebar.
        
        Args:
            export_service: Export service for exporting sequences.
        """
        super().__init__()
        
        # Store services
        self.export_service = export_service
        
        # Current sequence
        self.current_sequence = None
        
        # Store current state
        self.is_collapsed = False
        self.default_width = 500
        self.collapsed_width = 40
        self.animation_duration = 250  # ms - slightly longer for smoother animation
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Set object name for styling
        self.setObjectName("WebEngineSidebar")
        
        # Set up the UI
        self.init_ui()
        
        # Set up animations
        self.setup_animations()
        
        # Apply initial stylesheet
        self.setStyleSheet("""
            QWidget#WebEngineSidebar {
                background-color: #ffffff;
                border-left: 1px solid #ddd;
            }
            
            QFrame#SidebarToggleContainer {
                background-color: #f8f9fa;
                border-right: 1px solid #ddd;
            }
            
            QToolButton#SidebarToggleButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            
            QToolButton#SidebarToggleButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            
            QToolButton#SidebarToggleButton:pressed {
                background-color: rgba(0, 0, 0, 0.1);
            }
            
            QFrame#SidebarContentContainer {
                background-color: white;
                border: none;
            }
            
            QGroupBox {
                font-weight: 500;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 0.5ex;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 5px;
                color: #666;
            }
        """)
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout (horizontal)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create toggle button container (always visible)
        toggle_container = QFrame()
        toggle_container.setFrameShape(QFrame.NoFrame)
        toggle_container.setFixedWidth(40)
        toggle_container.setObjectName("SidebarToggleContainer")
        toggle_layout = QVBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 10, 0, 0)
        toggle_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        
        # Toggle/Menu button using menubutton.svg
        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(QIcon("resources/menubutton.svg"))
        self.toggle_btn.setIconSize(QSize(24, 24))
        self.toggle_btn.setToolTip("Menu (Right-click) & Toggle Sidebar (Left-click)")
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setObjectName("SidebarToggleButton")
        # Click will toggle sidebar or show menu on right-click
        self.toggle_btn.clicked.connect(self.on_toggle_btn_clicked)
        toggle_layout.addWidget(self.toggle_btn)
        
        # Add toggle container to main layout
        self.main_layout.addWidget(toggle_container)
        
        # Create content container
        self.content_container = QFrame()
        self.content_container.setFrameShape(QFrame.StyledPanel)
        self.content_container.setObjectName("SidebarContentContainer")
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        content_layout.setSpacing(5)  # Reduced spacing
        
        # Create tab widget for different views with custom styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)  # More modern look
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setObjectName("SidebarTabWidget")
        
        # SEQUENCE TAB - Streamlined
        sequence_tab = QWidget()
        sequence_layout = QVBoxLayout(sequence_tab)
        sequence_layout.setContentsMargins(3, 3, 3, 3)  # Compact margins
        sequence_layout.setSpacing(2)  # Minimal spacing
        
        # Table header - smaller and less prominent
        sequence_title = QLabel("Generated Test Sequence")
        sequence_title.setFont(QFont("Arial", 10))  # Reduced size, no bold
        sequence_title.setAlignment(Qt.AlignCenter)
        sequence_title.setStyleSheet("color: #666; margin-bottom: 2px;")  # Subtle styling
        sequence_title.setMaximumHeight(20)  # Limit height
        sequence_layout.addWidget(sequence_title)
        
        # Add webview for results
        self.sequences_web_view = QWebEngineView()
        self.sequences_web_view.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars, True)
        self.sequences_web_view.page().setBackgroundColor(QColor(245, 245, 247))
        sequence_layout.addWidget(self.sequences_web_view)
        
        # Also add a standard table view (initially hidden) as fallback
        self.results_table = QTableView()
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSortingEnabled(True)
        self.results_table.hide()  # Hidden by default
        sequence_layout.addWidget(self.results_table)
        
        self.tab_widget.addTab(sequence_tab, "Sequence")
        
        # PARAMETERS TAB - Streamlined
        params_tab = QWidget()
        params_layout = QVBoxLayout(params_tab)
        params_layout.setContentsMargins(3, 3, 3, 3)
        params_layout.setSpacing(2)
        
        # Parameters display (rich text)
        self.parameters_display = QTextEdit()
        self.parameters_display.setReadOnly(True)
        self.parameters_display.setStyleSheet("QTextEdit { border: 1px solid #ddd; border-radius: 4px; }")
        params_layout.addWidget(self.parameters_display)
        
        self.tab_widget.addTab(params_tab, "Parameters")
        
        # JSON TAB - Streamlined
        json_tab = QWidget()
        json_layout = QVBoxLayout(json_tab)
        json_layout.setContentsMargins(3, 3, 3, 3)
        json_layout.setSpacing(2)
        
        # JSON display
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setFont(QFont("Courier New", 10))
        self.json_display.setStyleSheet("QTextEdit { background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; }")
        json_layout.addWidget(self.json_display)
        
        self.tab_widget.addTab(json_tab, "JSON")
        
        # SPECIFICATIONS TAB - Streamlined
        self.specs_tab = QWidget()
        self.specs_layout = QVBoxLayout(self.specs_tab)
        self.specs_layout.setContentsMargins(3, 3, 3, 3)
        self.specs_layout.setSpacing(2)
        
        # Create a WebEngineView for specifications as well for consistent styling
        self.specs_web_view = QWebEngineView()
        self.specs_web_view.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars, True)
        self.specs_web_view.page().setBackgroundColor(QColor(245, 245, 247))
        self.specs_layout.addWidget(self.specs_web_view)
        
        # Load empty specifications view
        self.load_empty_specs_view()
        
        self.tab_widget.addTab(self.specs_tab, "Specifications")
        
        # Style the tab widget
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #fff;
            }
            QTabBar::tab {
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #ddd;
                border-bottom: none;
                background-color: #f8f8f8;
            }
            QTabBar::tab:selected {
                background-color: #fff;
                border-bottom-color: #fff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e6e6e6;
            }
        """)
        
        # Add tab widget to content layout
        content_layout.addWidget(self.tab_widget)
        
        # Add export controls
        if self.export_service:
            # Export group
            export_group = QGroupBox("Export Options")
            export_group.setMaximumHeight(90)  # Limit height
            export_layout = QVBoxLayout()
            export_layout.setContentsMargins(5, 5, 5, 5)
            export_layout.setSpacing(5)
            
            # Export format selection - horizontal and compact
            format_layout = QHBoxLayout()
            format_layout.setSpacing(5)
            format_label = QLabel("Format:")
            format_label.setFixedWidth(50)
            format_layout.addWidget(format_label)
            
            self.format_combo = QComboBox()
            self.format_combo.setStyleSheet("QComboBox { height: 24px; }")
            for format_name in self.export_service.get_supported_formats():
                self.format_combo.addItem(format_name)
            format_layout.addWidget(self.format_combo)
            
            export_layout.addLayout(format_layout)
            
            # Export buttons - improved styling
            export_btn_layout = QHBoxLayout()
            export_btn_layout.setSpacing(5)
            
            self.export_btn = QPushButton("Export Sequence")
            self.export_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    height: 24px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #ccc;
                }
            """)
            self.export_btn.clicked.connect(self.on_export_clicked)
            self.export_btn.setEnabled(False)  # Disabled until a sequence is available
            export_btn_layout.addWidget(self.export_btn)
            
            self.save_template_btn = QPushButton("Save as Template")
            self.save_template_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px 10px;
                    height: 24px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:disabled {
                    color: #aaa;
                    border: 1px solid #eee;
                }
            """)
            self.save_template_btn.clicked.connect(self.on_save_template_clicked)
            self.save_template_btn.setEnabled(False)  # Disabled until a sequence is available
            export_btn_layout.addWidget(self.save_template_btn)
            
            export_layout.addLayout(export_btn_layout)
            
            export_group.setLayout(export_layout)
            content_layout.addWidget(export_group)
        
        # Add content container to main layout
        self.main_layout.addWidget(self.content_container)
        
        # Set default sizes
        self.setFixedWidth(self.default_width)
        
        # Initialize with empty content
        self.load_empty_sequence_view()
    
    def setup_animations(self):
        """Set up animations for collapsing/expanding."""
        # Width animation with smoother transition
        self.width_animation = QPropertyAnimation(self, b"sidebar_width")
        self.width_animation.setEasingCurve(QEasingCurve.OutCubic)  # Smoother curve
        self.width_animation.setDuration(250)  # Slightly longer for smoother effect
        self.width_animation.finished.connect(self.on_animation_finished)
        
        # Add opacity animation for content fading
        self.content_container.setGraphicsEffect(None)  # Clear any existing effects
        self.opacity_effect = QGraphicsOpacityEffect(self.content_container)
        self.opacity_effect.setOpacity(1.0)
        self.content_container.setGraphicsEffect(self.opacity_effect)
        
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
    
    def load_empty_sequence_view(self):
        """Load empty sequence view HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Spring Test Results</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                    margin: 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    color: #333;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: calc(100vh - 20px);
                }
                .empty-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    width: 100%;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 6px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    transition: all 0.2s ease-in-out;
                }
                .empty-container:hover {
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .icon {
                    font-size: 36px;
                    margin-bottom: 15px;
                    color: #3498db;
                    opacity: 0.8;
                }
                h2 {
                    margin-bottom: 8px;
                    color: #2c3e50;
                    font-size: 16px;
                    font-weight: 500;
                }
                p {
                    color: #7f8c8d;
                    max-width: 300px;
                    line-height: 1.4;
                    font-size: 13px;
                    margin-top: 0;
                }
            </style>
        </head>
        <body>
            <div class="empty-container">
                <div class="icon">📊</div>
                <h2>No Test Sequence Available</h2>
                <p>Generate a new test sequence using the chat input to see results displayed here.</p>
            </div>
        </body>
        </html>
        """
        
        # Set the HTML content
        self.sequences_web_view.setHtml(html)
    
    def toggle_collapsed(self):
        """Toggle collapsed state with enhanced animations."""
        if self.width_animation.state() == QPropertyAnimation.Running:
            return  # Don't toggle if animation is running
        
        self.is_collapsed = not self.is_collapsed
        
        # First handle opacity animation if collapsing
        if self.is_collapsed:
            # Start fading out content
            self.opacity_animation.setDirection(QPropertyAnimation.Forward)
            self.opacity_animation.start()
            
            # Connect to opacity animation finish to start width animation after fade
            self.opacity_animation.finished.connect(self._start_width_animation)
        else:
            # Just start width animation when expanding
            self._start_width_animation()
            
        # Emit signal
        self.collapsed_changed.emit(self.is_collapsed)
    
    def _start_width_animation(self):
        """Start width animation after opacity effect if needed."""
        # Disconnect the signal to avoid multiple connections
        try:
            self.opacity_animation.finished.disconnect(self._start_width_animation)
        except:
            pass
            
        # Hide content immediately when collapsing
        if self.is_collapsed:
            self.content_container.hide()
        
        # Start width animation
        target_width = self.collapsed_width if self.is_collapsed else self.default_width
        self.width_animation.setStartValue(self.width())
        self.width_animation.setEndValue(target_width)
        self.width_animation.start()
    
    def on_animation_finished(self):
        """Handle animation finished event with fade-in effect."""
        # Show content when expansion is complete
        if not self.is_collapsed:
            self.content_container.show()
            # Fade in content
            self.opacity_animation.setDirection(QPropertyAnimation.Backward)
            self.opacity_animation.start()
    
    # Property for animation
    def get_sidebar_width(self):
        """Get sidebar width for animation property."""
        return self.width()
    
    def set_sidebar_width(self, width):
        """Set sidebar width for animation property."""
        self.setFixedWidth(width)
    
    sidebar_width = pyqtProperty(int, get_sidebar_width, set_sidebar_width)
    
    def on_toggle_btn_clicked(self):
        """Handle toggle button clicks by toggling sidebar and showing context menu on right-click."""
        # Get mouse button from event
        modifiers = QApplication.keyboardModifiers()
        
        # If right-click or holding Ctrl key (for context menu)
        if QApplication.mouseButtons() & Qt.RightButton or modifiers & Qt.ControlModifier:
            # Create context menu
            menu = QMenu(self)
            
            # Add toggle sidebar action
            if self.is_collapsed:
                toggle_action = QAction("Expand Sidebar", self)
            else:
                toggle_action = QAction("Collapse Sidebar", self)
            toggle_action.triggered.connect(self.toggle_collapsed)
            menu.addAction(toggle_action)
            
            menu.addSeparator()
            
            # Add clear display action
            clear_action = QAction("Clear Display", self)
            clear_action.triggered.connect(self.clear_display)
            menu.addAction(clear_action)
            
            # Add export actions if export service exists and there's a sequence
            if self.export_service and self.current_sequence:
                menu.addSeparator()
                
                export_action = QAction("Quick Export (CSV)", self)
                export_action.triggered.connect(self.quick_export)
                menu.addAction(export_action)
                
                export_dialog_action = QAction("Export with Options...", self)
                export_dialog_action.triggered.connect(self.on_export_clicked)
                menu.addAction(export_dialog_action)
            
            # Show menu at button position
            pos = self.toggle_btn.mapToGlobal(self.toggle_btn.rect().bottomRight())
            menu.exec_(pos)
        else:
            # Direct toggle on left-click
            self.toggle_collapsed()
    
    def display_sequence(self, sequence):
        """Display a sequence in the sidebar.
        
        Args:
            sequence: TestSequence object.
        """
        if not sequence:
            logger.warning("Attempted to display None sequence")
            return
            
        logger.debug("Displaying sequence with %d rows", len(sequence.rows))
        
        # Store current sequence
        self.current_sequence = sequence
        
        # If the sidebar is collapsed, expand it
        if self.is_collapsed:
            self.toggle_collapsed()
        
        # Display in table (for backward compatibility)
        try:
            df = pd.DataFrame(sequence.rows)
            logger.debug("Created DataFrame with %d rows and columns: %s", len(df), df.columns.tolist())
            model = PandasModel(df)
            self.results_table.setModel(model)
            logger.debug("Set model to results_table")
        except Exception as e:
            logger.error("Failed to display sequence in table: %s", str(e))
        
        # Update webview with sequence data
        try:
            html = self.generate_sequence_html(sequence)
            self.sequences_web_view.setHtml(html)
            logger.debug("Updated sequence web view")
        except Exception as e:
            logger.error("Failed to update sequence web view: %s", str(e))
            # Fall back to showing the table if webview fails
            self.results_table.show()
            self.sequences_web_view.hide()
        
        # Update parameters display with enhanced styling
        try:
            params_html = """
            <html>
            <head>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                        margin: 0;
                        padding: 10px;
                        color: #333;
                        font-size: 13px;
                    }
                    
                    .param-container {
                        display: flex;
                        flex-direction: column;
                        gap: 8px;
                    }
                    
                    .param-item {
                        display: flex;
                        padding: 6px 8px;
                        background-color: #f8f9fa;
                        border-radius: 4px;
                        border-left: 3px solid #3498db;
                    }
                    
                    .param-label {
                        font-weight: 500;
                        color: #2c3e50;
                        width: 160px;
                        min-width: 120px;
                    }
                    
                    .param-value {
                        flex: 1;
                        color: #333;
                    }
                    
                    .chat-message {
                        background-color: #edf6ff;
                        padding: 12px;
                        border-radius: 8px;
                        margin-bottom: 15px;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                        border-left: 3px solid #3498db;
                    }
                    
                    .chat-label {
                        font-weight: 600;
                        color: #2980b9;
                        margin-bottom: 5px;
                    }
                    
                    .chat-content {
                        color: #333;
                        line-height: 1.4;
                    }
                </style>
            </head>
            <body>
            """
            
            # If there's a chat message, show it first with enhanced formatting
            if "chat_message" in sequence.parameters:
                chat_message = sequence.parameters["chat_message"]
                params_html += f"""
                <div class="chat-message">
                    <div class="chat-label">Assistant message:</div>
                    <div class="chat-content">{chat_message}</div>
                </div>
                """
            
            # Start parameter container for all other parameters
            params_html += '<div class="param-container">'
            
            # Add parameters (excluding metadata)
            for key, value in sequence.parameters.items():
                # Skip timestamp, chat message, and other metadata
                if key in ["Timestamp", "chat_message"]:
                    continue
                
                params_html += f"""
                <div class="param-item">
                    <div class="param-label">{key}:</div>
                    <div class="param-value">{value}</div>
                </div>
                """
            
            params_html += "</div></body></html>"
            
            self.parameters_display.setHtml(params_html)
            logger.debug("Updated parameters display")
        except Exception as e:
            logger.error("Failed to update parameters display: %s", str(e))
        
        # Update JSON display with syntax highlighting
        try:
            # Create a copy of the sequence data without the chat message to avoid clutter
            json_data = sequence.to_dict()
            if "chat_message" in json_data.get("parameters", {}):
                # Truncate long chat messages for JSON display
                chat_message = json_data["parameters"]["chat_message"]
                if len(chat_message) > 100:
                    json_data["parameters"]["chat_message"] = chat_message[:100] + "... (truncated)"
                
            json_text = json.dumps(json_data, indent=2)
            
            # Create HTML with syntax highlighting
            json_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                        line-height: 1.4;
                        padding: 10px;
                        margin: 0;
                        background-color: #f8f8f8;
                    }}
                    pre {{
                        margin: 0;
                        white-space: pre-wrap;
                    }}
                    .string {{ color: #d14; }}
                    .number {{ color: #099; }}
                    .boolean {{ color: #905; }}
                    .null {{ color: #999; }}
                    .key {{ color: #0086b3; }}
                </style>
            </head>
            <body>
                <pre id="json">{json_text}</pre>
                <script>
                    // Simple JSON syntax highlighting
                    document.addEventListener('DOMContentLoaded', function() {{
                        const jsonElement = document.getElementById('json');
                        const jsonText = jsonElement.textContent;
                        
                        // Replace JSON with syntax-highlighted version
                        const highlighted = jsonText
                            .replace(/("(\\\\u[a-zA-Z0-9]{{4}}|\\\\[^u]|[^\\\\"])*"(\\s*:)?|\\b(true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)/g, 
                            function(match) {{
                                let cls = 'number';
                                if (/^"/.test(match)) {{
                                    if (/:$/.test(match)) {{
                                        cls = 'key';
                                        // Remove the colon from the match for styling
                                        match = match.replace(/:$/, '') + ':';
                                    }} else {{
                                        cls = 'string';
                                    }}
                                }} else if (/true|false/.test(match)) {{
                                    cls = 'boolean';
                                }} else if (/null/.test(match)) {{
                                    cls = 'null';
                                }}
                                
                                // Add appropriate styling
                                if (cls === 'key') {{
                                    return '<span class="' + cls + '">' + match.replace(/:$/, '') + '</span>:';
                                }} else {{
                                    return '<span class="' + cls + '">' + match + '</span>';
                                }}
                            }});
                        
                        jsonElement.innerHTML = highlighted;
                    }});
                </script>
            </body>
            </html>
            """
            
            self.json_display.setHtml(json_html)
            logger.debug("Updated JSON display with syntax highlighting")
        except Exception as e:
            logger.error("Failed to update JSON display: %s", str(e))
        
        # Enable export buttons if they exist
        if hasattr(self, 'export_btn'):
            self.export_btn.setEnabled(True)
        if hasattr(self, 'save_template_btn'):
            self.save_template_btn.setEnabled(True)
        
        # Switch to sequence tab
        self.tab_widget.setCurrentIndex(0)
        logger.debug("Switched to sequence tab")
    
    def generate_sequence_html(self, sequence):
        """Generate HTML for sequence display.
        
        Args:
            sequence: TestSequence object.
            
        Returns:
            str: HTML content.
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Spring Test Results</title>
            <style>
                :root {
                    --primary-color: #3498db;
                    --secondary-color: #2980b9;
                    --background-color: #f8f9fa;
                    --card-background: #ffffff;
                    --text-color: #333333;
                    --border-color: #e0e0e0;
                    --highlight-color: #e8f4fc;
                    --success-color: #28a745;
                    --info-color: #17a2b8;
                    --warning-color: #ffc107;
                }
                
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                }
                
                body {
                    background-color: var(--background-color);
                    color: var(--text-color);
                    padding: 0;
                    margin: 0;
                    overflow-x: hidden;
                    font-size: 13px;
                }
                
                .container {
                    padding: 0;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                }
                
                .results-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 0;
                    background-color: white;
                    border-radius: 3px;
                    overflow: hidden;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                }
                
                .results-table th {
                    background-color: var(--highlight-color);
                    color: var(--text-color);
                    font-weight: 600;
                    text-align: left;
                    padding: 8px 6px;
                    border-bottom: 1px solid var(--border-color);
                    position: sticky;
                    top: 0;
                    font-size: 12px;
                    white-space: nowrap;
                }
                
                .results-table td {
                    padding: 6px;
                    border-bottom: 1px solid var(--border-color);
                    vertical-align: middle;
                }
                
                .results-table tr:nth-child(even) {
                    background-color: rgba(0, 0, 0, 0.01);
                }
                
                .results-table tr:hover {
                    background-color: rgba(52, 152, 219, 0.05);
                }
                
                .command-cell {
                    font-weight: 500;
                    color: var(--primary-color);
                    white-space: nowrap;
                }
                
                .row-cell {
                    font-family: monospace;
                    color: #7f8c8d;
                    font-size: 11px;
                    text-align: center;
                }

                /* Value cells */
                .position-cell {
                    text-align: right;
                    font-weight: 500;
                }
                
                .desc-cell {
                    color: #666;
                    font-style: italic;
                }
                
                .unit-cell {
                    color: #888;
                    font-size: 11px;
                    text-align: center;
                }
                
                /* Animation for hover effect */
                .results-table tr {
                    transition: background-color 0.15s ease-in-out;
                }
                
                /* Mobile responsiveness */
                @media (max-width: 600px) {
                    .results-table th, .results-table td {
                        padding: 4px;
                        font-size: 11px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <table class="results-table">
                    <thead>
                        <tr>
        """
        
        # Add table headers
        if sequence.rows:
            for key in sequence.rows[0].keys():
                html += f"<th>{key}</th>"
        
        html += """
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add table rows
        for row in sequence.rows:
            html += "<tr>"
            for key, value in row.items():
                # Special styling for specific columns
                class_name = ""
                
                if key == "CMD":
                    class_name = "command-cell"
                elif key == "Row":
                    class_name = "row-cell"
                elif key == "Description":
                    class_name = "desc-cell"
                elif key in ["Position", "Value"]:
                    class_name = "position-cell"
                elif key == "Unit":
                    class_name = "unit-cell"
                
                html += f'<td class="{class_name}">{value or ""}</td>'
            html += "</tr>"
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <script>
                // Add any JavaScript enhancements here
                document.addEventListener('DOMContentLoaded', function() {
                    // Highlight the active row on hover
                    const rows = document.querySelectorAll('.results-table tbody tr');
                    rows.forEach(row => {
                        row.addEventListener('mouseenter', function() {
                            this.style.backgroundColor = 'rgba(52, 152, 219, 0.08)';
                        });
                        row.addEventListener('mouseleave', function() {
                            this.style.backgroundColor = '';
                        });
                    });
                });
            </script>
        </body>
        </html>
        """
        
        return html
    
    def clear_display(self):
        """Clear the display."""
        # Clear table
        self.results_table.setModel(None)
        
        # Clear webview
        self.load_empty_sequence_view()
        
        # Clear parameters display
        self.parameters_display.clear()
        
        # Clear JSON display
        self.json_display.clear()
        
        # Clear specifications display
        if hasattr(self, 'specs_web_view'):
            self.load_empty_specs_view()
        
        # Clear current sequence
        self.current_sequence = None
        
        # Disable export buttons if they exist
        if hasattr(self, 'export_btn'):
            self.export_btn.setEnabled(False)
        if hasattr(self, 'save_template_btn'):
            self.save_template_btn.setEnabled(False)
    
    def on_export_clicked(self):
        """Handle export button clicks."""
        # Check if a sequence is available
        if not self.current_sequence or not self.export_service:
            QMessageBox.warning(self, "No Sequence", "No test sequence available to export.")
            return
        
        # Get selected format
        format_name = self.format_combo.currentText()
        file_extension = FILE_FORMATS.get(format_name, ".csv")
        
        # Get file name from user
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Sequence", "", f"{format_name} Files (*{file_extension})"
        )
        
        if not file_name:
            return  # User cancelled
        
        # Add extension if not present
        if not file_name.endswith(file_extension):
            file_name += file_extension
        
        # Export the sequence
        success, error_msg = self.export_service.export_sequence(
            self.current_sequence, file_name, format_name
        )
        
        if success:
            QMessageBox.information(self, "Export Successful", f"Sequence exported to {file_name}")
        else:
            QMessageBox.critical(self, "Export Failed", f"Failed to export sequence: {error_msg}")
    
    def on_save_template_clicked(self):
        """Handle save template button clicks."""
        # Check if a sequence is available
        if not self.current_sequence:
            QMessageBox.warning(self, "No Sequence", "No test sequence available to save as a template.")
            return
        
        # Not implemented yet
        QMessageBox.information(self, "Not Implemented", "This feature is not yet implemented.")
    
    def quick_export(self):
        """Quickly export the current sequence to CSV without dialog."""
        if not self.current_sequence or not self.export_service:
            return
        
        try:
            # Get a default filename based on timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"spring_sequence_{timestamp}.csv"
            
            # Use the documents folder as default location
            import os
            documents_path = os.path.expanduser("~/Documents")
            if not os.path.exists(documents_path):
                documents_path = os.path.expanduser("~")
            
            file_path = os.path.join(documents_path, default_filename)
            
            # Export the sequence
            success, error_msg = self.export_service.export_sequence(
                self.current_sequence, file_path, "CSV"
            )
            
            if success:
                QMessageBox.information(self, "Quick Export Successful", 
                                       f"Sequence exported to {file_path}")
            else:
                QMessageBox.critical(self, "Export Failed", 
                                    f"Failed to export sequence: {error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error during export: {str(e)}")
    
    def load_empty_specs_view(self):
        """Load empty specifications view HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Spring Test Results</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                    margin: 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    color: #333;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: calc(100vh - 20px);
                }
                .empty-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    width: 100%;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 6px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    transition: all 0.2s ease-in-out;
                }
                .empty-container:hover {
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .icon {
                    font-size: 36px;
                    margin-bottom: 15px;
                    color: #3498db;
                    opacity: 0.8;
                }
                h2 {
                    margin-bottom: 8px;
                    color: #2c3e50;
                    font-size: 16px;
                    font-weight: 500;
                }
                p {
                    color: #7f8c8d;
                    max-width: 300px;
                    line-height: 1.4;
                    font-size: 13px;
                    margin-top: 0;
                }
            </style>
        </head>
        <body>
            <div class="empty-container">
                <div class="icon">📊</div>
                <h2>No Specifications Available</h2>
                <p>Add specifications to see them displayed here.</p>
            </div>
        </body>
        </html>
        """
        
        # Set the HTML content
        self.specs_web_view.setHtml(html)
    
    def add_specifications_panel(self, specs_panel):
        """Add the specifications panel to the sidebar.
        
        Args:
            specs_panel: Specifications panel to add, or None to display specifications data in HTML format.
        """
        # Clear any existing widgets
        while self.specs_layout.count():
            item = self.specs_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        if specs_panel:
            # Hide our web view and add the custom panel
            self.specs_web_view.hide()
            self.specs_layout.addWidget(specs_panel)
        else:
            # Add back our web view if it was removed
            self.specs_web_view.show()
            self.specs_layout.addWidget(self.specs_web_view)
            self.load_empty_specs_view()
        
        # Switch to the specifications tab
        self.tab_widget.setCurrentWidget(self.specs_tab)
    
    def display_specifications(self, specs_data):
        """Display specifications data in HTML format.
        
        Args:
            specs_data: Dictionary of specification data to display.
        """
        if not specs_data:
            self.load_empty_specs_view()
            return
            
        # Generate HTML for specifications display
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Spring Specifications</title>
            <style>
                :root {
                    --primary-color: #3498db;
                    --secondary-color: #2980b9;
                    --background-color: #f8f9fa;
                    --card-background: #ffffff;
                    --text-color: #333333;
                    --border-color: #e0e0e0;
                    --highlight-color: #e8f4fc;
                }
                
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                }
                
                body {
                    background-color: var(--background-color);
                    color: var(--text-color);
                    padding: 15px;
                    margin: 0;
                    font-size: 13px;
                    line-height: 1.4;
                }
                
                .specs-container {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                
                .spec-section {
                    background-color: white;
                    border-radius: 6px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    overflow: hidden;
                }
                
                .section-header {
                    background-color: var(--highlight-color);
                    padding: 10px 15px;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .section-header h2 {
                    font-size: 14px;
                    font-weight: 600;
                    color: var(--secondary-color);
                    margin: 0;
                }
                
                .section-content {
                    padding: 10px 15px;
                }
                
                .spec-items {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                
                .spec-item {
                    display: flex;
                    padding: 6px 8px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    border-left: 3px solid var(--primary-color);
                }
                
                .spec-label {
                    font-weight: 500;
                    color: #2c3e50;
                    width: 160px;
                    min-width: 120px;
                }
                
                .spec-value {
                    flex: 1;
                    color: #333;
                }
                
                /* Visual variations based on spec type */
                .spec-item.critical {
                    border-left-color: #e74c3c;
                }
                
                .spec-item.warning {
                    border-left-color: #f39c12;
                }
                
                .spec-item.success {
                    border-left-color: #2ecc71;
                }
                
                .spec-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }
                
                .spec-table th {
                    background-color: var(--highlight-color);
                    text-align: left;
                    padding: 8px;
                    font-weight: 500;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .spec-table td {
                    padding: 6px 8px;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .spec-table tr:nth-child(even) {
                    background-color: rgba(0, 0, 0, 0.01);
                }
            </style>
        </head>
        <body>
            <div class="specs-container">
        """
        
        # Process specifications sections
        for section, items in specs_data.items():
            html += f"""
                <div class="spec-section">
                    <div class="section-header">
                        <h2>{section}</h2>
                    </div>
                    <div class="section-content">
                        <div class="spec-items">
            """
            
            # Add items for this section
            if isinstance(items, dict):
                for key, value in items.items():
                    # Determine if this spec has a special category
                    spec_class = ""
                    if key.lower().startswith("critical") or key.lower().startswith("error"):
                        spec_class = "critical"
                    elif key.lower().startswith("warn"):
                        spec_class = "warning"
                    elif key.lower().startswith("pass") or key.lower().startswith("success"):
                        spec_class = "success"
                    
                    html += f"""
                            <div class="spec-item {spec_class}">
                                <div class="spec-label">{key}:</div>
                                <div class="spec-value">{value}</div>
                            </div>
                    """
            elif isinstance(items, list):
                # Display list items as a table
                html += """
                        <table class="spec-table">
                            <thead>
                                <tr>
                """
                
                # Add headers if list items are dictionaries
                if items and isinstance(items[0], dict):
                    for key in items[0].keys():
                        html += f"<th>{key}</th>"
                
                html += """
                                </tr>
                            </thead>
                            <tbody>
                """
                
                # Add rows
                for item in items:
                    html += "<tr>"
                    if isinstance(item, dict):
                        for value in item.values():
                            html += f"<td>{value}</td>"
                    else:
                        html += f"<td>{item}</td>"
                    html += "</tr>"
                
                html += """
                            </tbody>
                        </table>
                """
            
            html += """
                        </div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        # Set the HTML content and switch to specs tab
        self.specs_web_view.setHtml(html)
        self.specs_web_view.show()
        self.tab_widget.setCurrentWidget(self.specs_tab) 