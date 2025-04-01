"""
Chat panel module for the Spring Test App.
Main chat interface with message display and controls.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                           QPushButton, QMessageBox, QProgressBar, QSplitter, QFrame,
                           QSizePolicy, QApplication)
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QTimer, QSize, pyqtProperty, 
                         QPropertyAnimation)
from PyQt5.QtGui import QIcon, QMovie, QTransform, QPixmap
from PyQt5.QtSvg import QSvgWidget
import pandas as pd
from datetime import datetime
import re

from ui.chat_components.chat_display import ChatBubbleDisplay
from ui.chat_components.chat_specification_form import SpecificationFormManager
from models.data_models import TestSequence, SpringSpecification


class ChatPanel(QWidget):
    """Chat panel widget for the Spring Test App."""
    
    # Define signals
    sequence_generated = pyqtSignal(object)  # TestSequence object
    
    def __init__(self, chat_service, sequence_generator):
        """Initialize the chat panel.
        
        Args:
            chat_service: Chat service.
            sequence_generator: Sequence generator service.
        """
        super().__init__()
        
        # Enable transparency for the widget
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Store services
        self.chat_service = chat_service
        self.sequence_generator = sequence_generator
        
        # Get the settings service from chat service
        self.settings_service = self.chat_service.settings_service
        
        # State variables
        self.is_generating = False
        
        # Create and store the specification form manager
        self.spec_form_manager = None  # Will be created when needed
        self.spec_form_active = False  # Track whether form is active
        
        # Set up the UI
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Load chat history
        self.refresh_chat_display()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for full-width content
        layout.setSpacing(0)  # Remove spacing between components
        
        # Create a main content widget with padding
        content_widget = QWidget()
        content_widget.setObjectName("ContentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        
        # Apply transparency to the content widget
        content_widget.setStyleSheet("""
            #ContentWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                      stop:0 rgba(255, 255, 255, 0.7),
                                      stop:1 rgba(240, 240, 255, 0.8));
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.8);
            }
        """)
        
        # Chat panel title
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 8)
        
        # Replace the text title with the Sushma logo
        logo_widget = QSvgWidget("resources/Sushma_logo-722x368.svg")
        logo_widget.setObjectName("LogoWidget")
        logo_widget.setFixedSize(200, 100)
        logo_widget.setStyleSheet("""
            #LogoWidget {
                background-color: transparent;
                margin-bottom: 10px;
            }
        """)
        title_layout.addWidget(logo_widget)
        title_layout.setAlignment(Qt.AlignLeft)
        
        # Add the title layout to the content layout
        content_layout.addLayout(title_layout)
        
        # Create a frame for the chat display
        chat_frame = QFrame()
        chat_frame.setObjectName("ChatDisplayFrame")
        chat_frame.setFrameShape(QFrame.NoFrame)
        chat_frame.setStyleSheet("""
            #ChatDisplayFrame {
                background-color: transparent;
                border-radius: 12px;
                border: none;
            }
        """)
        
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat display with bubble styling
        self.chat_display = ChatBubbleDisplay(self)
        chat_layout.addWidget(self.chat_display)
        
        # Add the chat frame to the content layout with stretch
        content_layout.addWidget(chat_frame, 1)  # Give it stretch factor 1
        
        # Create container for specification forms
        self.form_container = QWidget()
        self.form_container.setObjectName("FormContainer")
        self.form_container.setContentsMargins(8, 8, 8, 8)
        self.form_container.setVisible(False)  # Hidden initially
        
        # Form container layout
        form_container_layout = QVBoxLayout(self.form_container)
        form_container_layout.setContentsMargins(0, 0, 0, 0)
        form_container_layout.setSpacing(0)
        
        # Style the form container
        self.form_container.setStyleSheet("""
            #FormContainer {
                background-color: rgba(240, 240, 255, 0.7);
                border-radius: 12px;
                border: 1px solid rgba(66, 133, 244, 0.3);
            }
        """)
        
        # Add the form container to the content layout
        content_layout.addWidget(self.form_container)
        
        # Create a container for the input area (to manage positioning)
        input_container = QWidget()
        input_container.setObjectName("InputContainer")
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setFixedHeight(60)  # Fixed height for the input container
        
        # Style the input container
        input_container.setStyleSheet("""
            #InputContainer {
                background-color: transparent;
            }
        """)
        
        # Input container layout
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(12)
        
        # Create a frame for the floating input area
        input_frame = QFrame()
        input_frame.setObjectName("InputFrame")
        
        # Style the input frame to look like a floating element
        input_frame.setStyleSheet("""
            #InputFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 rgba(255, 255, 255, 0.7),
                                    stop:1 rgba(255, 255, 255, 0.85));
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 24px;
            }
            #InputFrame:hover {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(66, 133, 244, 0.3);
            }
        """)
        
        # Input frame layout
        input_frame_layout = QHBoxLayout(input_frame)
        input_frame_layout.setContentsMargins(16, 8, 8, 8)
        input_frame_layout.setSpacing(8)
        
        # Modern text input area
        self.user_input = QTextEdit()
        self.user_input.setObjectName("ChatInput")
        self.user_input.setPlaceholderText("Message Sushma Assistant...")
        self.user_input.setFixedHeight(40)
        self.user_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Style the input text area
        self.user_input.setStyleSheet("""
            QTextEdit#ChatInput {
                border: none;
                background-color: transparent;
                padding: 8px 0px;
                font-size: 14px;
                color: #202124;
            }
            QTextEdit#ChatInput:focus {
                outline: none;
            }
        """)
        
        # Add the input text area to the input frame layout
        input_frame_layout.addWidget(self.user_input, 1)  # Give it stretch factor
        
        # Send button with modern icon
        self.generate_btn = QPushButton()
        self.generate_btn.setObjectName("SendButton")
        self.generate_btn.setIcon(QIcon("resources/sendbutton.svg"))
        self.generate_btn.setIconSize(QSize(20, 20))
        self.generate_btn.setFixedSize(40, 40)
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self.on_send_clicked)
        
        # Style the send button
        self.generate_btn.setStyleSheet("""
            QPushButton#SendButton {
                background-color: #4285F4;
                border-radius: 20px;
                border: none;
                margin: 0;
                padding: 0;
            }
            QPushButton#SendButton:hover {
                background-color: #5294FF;
            }
            QPushButton#SendButton:pressed {
                background-color: #3060C0;
            }
            QPushButton#SendButton:disabled {
                background-color: #C0C0C0;
            }
        """)
        
        # Add the send button to the input frame layout
        input_frame_layout.addWidget(self.generate_btn)
        
        # Add the input frame to the input container layout
        input_layout.addWidget(input_frame)
        
        # Add the input container to the content layout
        content_layout.addWidget(input_container, 0)  # No stretch
        
        # Create a container for the progress indicators
        progress_container = QWidget()
        progress_container.setObjectName("ProgressContainer")
        progress_container.setContentsMargins(0, 0, 0, 0)
        progress_container.setFixedHeight(40)
        progress_container.hide()  # Initially hidden
        
        # Progress container layout
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(16, 0, 16, 0)
        progress_layout.setSpacing(12)
        
        # Modern loading indicator
        self.loading_indicator = QFrame()
        self.loading_indicator.setObjectName("LoadingIndicator")
        self.loading_indicator.setFixedSize(20, 20)
        
        # Style the loading indicator
        self.loading_indicator.setStyleSheet("""
            #LoadingIndicator {
                background-color: transparent;
                border: 2px solid rgba(66, 133, 244, 0.2);
                border-top: 2px solid #4285F4;
                border-radius: 10px;
            }
        """)
        
        # Create a simpler animation effect without using rotation property
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.toggle_loading_indicator)
        self.loading_state = 0
        
        # Status label
        self.status_label = QLabel("Processing your request...")
        self.status_label.setObjectName("StatusLabel")
        font = self.status_label.font()
        font.setPointSize(11)
        self.status_label.setFont(font)
        
        # Style the status label
        self.status_label.setStyleSheet("""
            #StatusLabel {
                color: #5F6368;
            }
        """)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        
        # Style the cancel button
        self.cancel_btn.setStyleSheet("""
            #CancelButton {
                background-color: transparent;
                color: #4285F4;
                border: none;
                font-size: 12px;
                padding: 4px 8px;
            }
            #CancelButton:hover {
                text-decoration: underline;
            }
        """)
        
        # Modern progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        
        # Style the progress bar
        self.progress_bar.setStyleSheet("""
            #ProgressBar {
                background-color: rgba(66, 133, 244, 0.1);
                border: none;
                border-radius: 2px;
            }
            #ProgressBar::chunk {
                background-color: #4285F4;
                border-radius: 2px;
            }
        """)
        
        # Add the loading indicator and status label to the progress layout
        progress_layout.addWidget(self.loading_indicator)
        progress_layout.addWidget(self.status_label, 1)  # Give it stretch
        progress_layout.addWidget(self.cancel_btn)
        
        # Create a progress bar container
        progress_bar_container = QWidget()
        progress_bar_layout = QVBoxLayout(progress_bar_container)
        progress_bar_layout.setContentsMargins(0, 4, 0, 0)
        progress_bar_layout.addWidget(self.progress_bar)
        
        # Add the progress bar container to the content layout
        content_layout.addWidget(progress_bar_container)
        
        # Add the progress container to the content layout
        content_layout.addWidget(progress_container)
        
        # Store references to containers for showing/hiding
        self.progress_container = progress_container
        self.progress_bar_container = progress_bar_container
        
        # Add the content widget to the main layout
        layout.addWidget(content_widget, 1)  # Give it stretch
        
        # Set the main layout
        self.setLayout(layout)
        
        # Style the chat display scrollbar
        self.chat_display.setStyleSheet("""
            QWebEngineView {
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 12px 2px 12px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(66, 133, 244, 0.5);
                min-height: 40px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(66, 133, 244, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
    
    def connect_signals(self):
        """Connect signals from the sequence generator."""
        self.sequence_generator.sequence_generated.connect(self.on_sequence_generated_async)
        self.sequence_generator.progress_updated.connect(self.on_progress_updated)
        self.sequence_generator.status_updated.connect(self.on_status_updated)
    
    def refresh_chat_display(self):
        """Refresh the chat display with current history."""
        # Get chat history
        history = self.chat_service.get_history()
        
        # Use the chat display component to refresh
        self.chat_display.refresh_display(history)
    
    def on_send_clicked(self):
        """Handle send button clicks (for both chat and generation)."""
        # Get user input
        user_input = self.user_input.toPlainText()
        
        # Check if input is empty
        if not user_input:
            QMessageBox.warning(self, "Missing Input", "Please enter your request.")
            return
        
        # Check if generation is already in progress
        if self.is_generating:
            QMessageBox.warning(self, "Processing", "Please wait for the current request to complete.")
            return
        
        # Add user message to chat history
        self.chat_service.add_message("user", user_input)
        
        # Clear the input field immediately after sending
        self.user_input.clear()
        
        # Refresh chat display
        self.refresh_chat_display()
        
        # Check if this is a request to update specifications
        if self._is_spec_update_request(user_input):
            self._handle_spec_update_request()
            return
        
        # Check if the message contains sequence data markers
        sequence_data_start = "---SEQUENCE_DATA_START---"
        sequence_data_end = "---SEQUENCE_DATA_END---"
        
        if sequence_data_start in user_input and sequence_data_end in user_input:
            # Direct input contains sequence data - process it directly
            try:
                # Extract parts
                parts = user_input.split(sequence_data_start)
                conversation_text = parts[0].strip()
                
                # Extract the sequence data
                seq_parts = parts[1].split(sequence_data_end)
                sequence_json_text = seq_parts[0].strip()
                
                # If there's additional text after the sequence data, add it to conversation
                if len(seq_parts) > 1 and seq_parts[1].strip():
                    conversation_text += "\n\n" + seq_parts[1].strip()
                
                # Add the conversation text to chat
                self.chat_service.add_message("assistant", conversation_text)
                self.refresh_chat_display()
                
                # Parse the sequence data
                import json
                try:
                    # First try standard JSON parsing
                    data = json.loads(sequence_json_text)
                except json.JSONDecodeError:
                    # If that fails, try to convert the non-standard format to proper JSON
                    # This handles formats like [R00, ZF, Zero Force, , , , ]
                    try:
                        # Convert the input to a format that can be parsed
                        rows = []
                        for line in sequence_json_text.strip().split('\n'):
                            # Remove the brackets and parse cells
                            line = line.strip()
                            if line.startswith('[') and line.endswith(']'):
                                # Remove the brackets
                                line = line[1:-1]
                                
                                # Intelligently parse cells to handle commas within values
                                cells = []
                                current_cell = ""
                                in_parentheses = False
                                in_quotes = False
                                cell_index = 0  # Track which cell position we're in
                                found_scrag_cmd = False  # Flag to track if we've seen "Scrag" in the CMD position
                                
                                for char in line:
                                    if char == '"' and (len(current_cell) == 0 or current_cell[-1] != '\\'):
                                        # Toggle quote state (but not if escaped)
                                        in_quotes = not in_quotes
                                        current_cell += char
                                    elif char == '(' or char == '[':
                                        in_parentheses = True
                                        current_cell += char
                                    elif char == ')' or char == ']':
                                        in_parentheses = False
                                        current_cell += char
                                    elif char == ',' and not (in_parentheses or in_quotes):
                                        # Process the completed cell before deciding what to do with the comma
                                        completed_cell = current_cell.strip()
                                        
                                        # Check if we just processed the CMD cell and it's a Scrag command
                                        if cell_index == 1 and completed_cell == "Scrag":
                                            found_scrag_cmd = True
                                            print(f"DEBUG: Found Scrag command in CMD position")
                                        
                                        # Special case for Scrag command format "Rxx,y" in the Condition field (4th column)
                                        if (found_scrag_cmd and cell_index == 3 and 
                                            completed_cell and 
                                            (re.match(r'^"?R\d+$', completed_cell) or  # Pattern is "R" followed by digits (like R03)
                                             re.match(r'^"?R\d+,\d*"?$', completed_cell))):  # Pattern already has comma (like R03,2)
                                            # This is a reference to another row in Scrag command, keep it intact
                                            current_cell += char
                                            print(f"DEBUG: Keeping comma in Scrag condition: {current_cell}")
                                            # Check if this is the second comma for Scrag
                                            if re.match(r'^"?R\d+,\d+$', current_cell.strip()):
                                                # We've already got the full R03,2 pattern, next comma should be a separator
                                                cells.append(current_cell.strip())
                                                current_cell = ""
                                                cell_index += 1
                                        else:
                                            # This comma is a cell separator
                                            cells.append(completed_cell)
                                            current_cell = ""
                                            cell_index += 1
                                    else:
                                        # This character is part of the current cell
                                        current_cell += char
                                
                                # Add the last cell
                                cells.append(current_cell.strip())
                                
                                # Remove quotes around cells if present
                                for i in range(len(cells)):
                                    if cells[i].startswith('"') and cells[i].endswith('"'):
                                        cells[i] = cells[i][1:-1]
                                    # Also clean up any trailing commas from Scrag commands
                                    if cells[i].endswith(","):
                                        cells[i] = cells[i][:-1]
                                
                                # Make sure we have exactly 7 cells for the expected columns
                                while len(cells) < 7:
                                    cells.append("")
                                
                                # If we have too many cells, combine the extras into the appropriate column
                                if len(cells) > 7:
                                    print(f"WARNING: Found {len(cells)} cells, expected 7. Combining extras.")
                                    # Keep the first 6 cells as-is and combine the remaining cells into the last column
                                    cells = cells[:6] + [", ".join(cells[6:])]
                                
                                # Create a row with the proper column names
                                row = {
                                    "Row": cells[0] if cells[0] else "",
                                    "CMD": cells[1] if cells[1] else "",
                                    "Description": cells[2] if cells[2] else "",
                                    "Condition": cells[3] if cells[3] else "",
                                    "Unit": cells[4] if cells[4] else "",
                                    "Tolerance": cells[5] if cells[5] else "",
                                    "Speed rpm": cells[6] if cells[6] else ""
                                }
                                rows.append(row)
                        
                        # Use the manually parsed data
                        data = rows
                        print(f"DEBUG: Manually parsed {len(data)} rows from custom format")
                        if not data:
                            raise ValueError("No valid sequence data found")
                    except Exception as e:
                        # If manual parsing also fails, report the error
                        self.chat_service.add_message(
                            "assistant", 
                            f"I couldn't parse the sequence data format: {str(e)}\n\n" +
                            "Please ensure the sequence data is properly formatted."
                        )
                        self.refresh_chat_display()
                        return
                
                # Create DataFrame from sequence data
                df = pd.DataFrame(data)
                
                # Ensure all required columns are present
                required_columns = ["Row", "CMD", "Description", "Condition", "Unit", "Tolerance", "Speed rpm"]
                
                # Fix column names - handle both "Cmd" and "CMD" variations
                if "Cmd" in df.columns and "CMD" not in df.columns:
                    df = df.rename(columns={"Cmd": "CMD"})
                
                # Rename any mismatched columns
                if "Speed" in df.columns and "Speed rpm" not in df.columns:
                    df = df.rename(columns={"Speed": "Speed rpm"})
                    
                # Add any missing columns
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = ""
                
                # Reorder columns to match required format
                df = df[required_columns]
                
                # Create parameters dictionary
                parameters = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "prompt": "Generated sequence"
                }
                
                # Create a TestSequence object
                test_sequence = TestSequence(
                    rows=df.to_dict('records'),
                    parameters=parameters
                )
                
                # Emit the sequence to display in sidebar
                print(f"DEBUG: Emitting sequence with {len(test_sequence.rows)} rows to sidebar")
                self.sequence_generated.emit(test_sequence)
                return
                
            except (json.JSONDecodeError, ValueError) as e:
                # If parsing fails, add error message and proceed with normal processing
                self.chat_service.add_message(
                    "assistant", 
                    f"I couldn't parse the sequence data in your message: {str(e)}"
                )
                self.refresh_chat_display()
                # Continue with normal processing
        
        # Create parameters dictionary using timestamp and original prompt
        parameters = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prompt": user_input
        }
        
        # Add a processing message 
        processing_msg = "Processing your message..."
        self.chat_service.add_message(
            "assistant",
            processing_msg
        )
        self.refresh_chat_display()
        
        # Make sure the processing message is visible immediately
        QApplication.processEvents()
        
        # Check if the input contains spring specifications and parse them
        contains_specs = self.parse_spring_specs(user_input)
        
        # If specs were parsed, update the sequence generator
        if contains_specs:
            # Get the updated specification and set it in the sequence generator
            updated_spec = self.settings_service.get_spring_specification()
            self.sequence_generator.set_spring_specification(updated_spec)
            
            # Add a note to the chat about using the parsed specifications
            self.chat_service.add_message(
                "assistant",
                "I've updated the spring specifications based on your message."
            )
            self.refresh_chat_display()
        
        # If this might be a request for a test sequence, include specification status
        # Use a simple keyword detection approach to predict if this is a test sequence request
        test_sequence_keywords = ["sequence", "test", "generate", "spring", "specification", "create test", 
                                  "spring test", "compression test", "tension test", "make a", "scragging", 
                                  "setup", "create a sequence", "coil", "load", "force"]
        
        # Count how many test-related keywords appear in the user input
        keyword_count = sum(1 for keyword in test_sequence_keywords if keyword.lower() in user_input.lower())
        
        # If there are multiple test-related keywords, or the user explicitly mentions test sequence,
        # include the specification status in the parameters
        is_likely_test_request = keyword_count >= 2 or any(phrase in user_input.lower() for phrase in 
                                                          ["test sequence", "spring test", "generate sequence"])
        
        if is_likely_test_request:
            # Get current spring specification to check its status
            spring_spec = self.sequence_generator.get_spring_specification()
            
            # Check if specifications are properly set up
            if not spring_spec or not spring_spec.enabled:
                # Remove the processing message
                self.chat_service.history.pop()
                
                # Show a message asking to set up specifications
                self.chat_service.add_message(
                    "assistant",
                    "Before I can generate a test sequence, you need to set up your spring specifications. "
                    "Would you like to do that now using a form?"
                )
                self.refresh_chat_display()
                
                # Show the specification form
                self.show_specification_form()
                return
            
            # Generate the specification status text for the AI
            specifications_status = self.generate_specification_status(spring_spec)
            
            # Add the status to parameters
            parameters["specifications_status"] = specifications_status
            
            # Include spring specification in the prompt if available
            if spring_spec:
                # Add specification text to the prompt if not already included
                spec_text = spring_spec.to_prompt_text()
                if spec_text not in parameters['prompt']:
                    parameters['prompt'] = f"{spec_text}\n\n{parameters['prompt']}"
        
        # Start generation
        self.start_generation(parameters)
    
    def on_cancel_clicked(self):
        """Handle cancel button clicks."""
        if self.is_generating:
            # Cancel the operation
            self.sequence_generator.cancel_current_operation()
            
            # Update UI
            self.on_status_updated("Operation cancelled")
            self.on_progress_updated(0)
            
            # Add cancellation message to chat
            self.chat_service.add_message(
                "assistant", 
                "I've cancelled the sequence generation as requested."
            )
            self.refresh_chat_display()
            
            # Reset generating state
            self.set_generating_state(False)
    
    def start_generation(self, parameters):
        """Start sequence generation.
        
        Args:
            parameters: Dictionary of spring parameters.
        """
        # Set generating state
        self.set_generating_state(True)
        
        # Reset progress and status
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting generation...")
        
        # Start async generation
        self.sequence_generator.generate_sequence_async(parameters)
    
    def set_generating_state(self, is_generating):
        """Set the generating state and update UI accordingly.
        
        Args:
            is_generating: Whether generation is in progress.
        """
        self.is_generating = is_generating
        
        # Update UI based on state
        self.generate_btn.setEnabled(not is_generating)
        self.user_input.setReadOnly(is_generating)
        
        if is_generating:
            # Show progress indicators
            self.progress_container.show()
            self.progress_bar_container.show()
            self.progress_bar.setValue(0)
            # Start timer-based animation
            self.loading_timer.start(150)  # Update every 150ms for smooth animation
            self.status_label.setText("Processing your request...")
        else:
            # Hide progress indicators
            self.progress_container.hide()
            self.progress_bar_container.hide()
            # Stop timer-based animation
            self.loading_timer.stop()
            self.status_label.setText("Ready")
    
    def on_sequence_generated_async(self, sequence, error):
        """Handle asynchronous sequence generation completion.
        
        Args:
            sequence: The generated sequence or None if error.
            error: Error message if any.
        """
        print(f"DEBUG: ChatPanel.on_sequence_generated_async called with {type(sequence).__name__}")
        
        # Reset generating state
        self.set_generating_state(False)
        
        # Clear the "Processing your message..." text by removing the last assistant message if it's a processing message
        last_message = self.chat_service.get_last_message()
        if last_message and last_message.role == "assistant" and "Processing your message..." in last_message.content:
            # Remove the processing message from history
            self.chat_service.history.pop()
            print("DEBUG: Removed 'Processing your message...' placeholder")
        
        # Check if sequence is None or empty
        if sequence is None or (isinstance(sequence, pd.DataFrame) and sequence.empty):
            # Handle error case
            if error:
                # Show error message
                error_msg = f"Error generating sequence: {error}"
                self.chat_service.add_message(
                    "assistant", 
                    error_msg + "\nPlease try providing more specific spring details."
                )
            else:
                # Generic error
                self.chat_service.add_message(
                    "assistant", 
                    "I'm having trouble processing your request. Please try again with more details."
                )
            self.refresh_chat_display()
            return
        
        # Handle different types of sequence objects properly
        if isinstance(sequence, pd.DataFrame):
            print(f"DEBUG: Processing DataFrame with {len(sequence)} rows")
            # Check if it has a CHAT row (for conversation or hybrid responses)
            chat_rows = sequence[sequence["Row"] == "CHAT"]
            
            # If we have chat content, display it in the chat panel
            if not chat_rows.empty:
                chat_message = chat_rows["Description"].values[0]
                self.chat_service.add_message("assistant", chat_message)
                
                # Force refresh chat display to ensure message appears
                self.refresh_chat_display()
                
                # Make sure the message is visible by forcing a repaint
                QApplication.processEvents()
            
            # Check if we also have actual sequence rows (for hybrid or sequence-only responses)
            sequence_rows = sequence[sequence["Row"] != "CHAT"]
            if not sequence_rows.empty:
                # We have actual sequence data to display in the results panel
                # Only send the sequence part (without the CHAT row)
                sequence_rows = sequence_rows.reset_index(drop=True)
                
                # Convert DataFrame to TestSequence object before emitting
                # Create a simple parameter dictionary for the TestSequence
                parameters = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "prompt": "Generated sequence"
                }
                
                # Create TestSequence with the sequence rows and parameters
                test_sequence = TestSequence(
                    rows=sequence_rows.to_dict('records'),
                    parameters=parameters
                )
                
                # If we had chat content, add it to the parameters for display
                if not chat_rows.empty:
                    test_sequence.parameters["chat_message"] = chat_rows["Description"].values[0]
                
                # Emit the TestSequence object to display in the sidebar
                print(f"DEBUG: Emitting sequence with {len(test_sequence.rows)} rows to sidebar")
                self.sequence_generated.emit(test_sequence)
                
                # If we didn't have chat content already, add a generic message to the chat panel
                if chat_rows.empty:
                    self.chat_service.add_message(
                        "assistant", 
                        "I've generated a test sequence based on your request. "
                        "You can see the results in the right panel."
                    )
                    self.refresh_chat_display()
                    
                    # Make sure the message is visible
                    QApplication.processEvents()
            else:
                # No sequence data was found, this was purely a conversation message
                # Make sure the chat display is refreshed 
                self.refresh_chat_display()
                
                # Make sure the message is visible
                QApplication.processEvents()
        
        elif hasattr(sequence, 'rows') and hasattr(sequence, 'parameters'):
            print(f"DEBUG: Processing TestSequence object with {len(sequence.rows)} rows")
            # It's already a TestSequence object - check if it has a chat message in parameters
            if "chat_message" in sequence.parameters:
                # Display the chat message
                self.chat_service.add_message("assistant", sequence.parameters["chat_message"])
                self.refresh_chat_display()
                
                # Make sure the message is visible
                QApplication.processEvents()
            else:
                # Add a generic notification in the chat panel
                self.chat_service.add_message(
                    "assistant", 
                    "I've generated a test sequence based on your request. "
                    "You can see the results in the right panel."
                )
                self.refresh_chat_display()
                
                # Make sure the message is visible
                QApplication.processEvents()
            
            # Emit the TestSequence object to display in the sidebar
            print(f"DEBUG: Emitting TestSequence with {len(sequence.rows)} rows to sidebar")
            self.sequence_generated.emit(sequence)
        else:
            # Unknown object type - show error
            print(f"DEBUG: Received unknown object type: {type(sequence).__name__}")
            self.chat_service.add_message(
                "assistant", 
                "I received an unexpected response format. Please try again with a different request."
            )
            self.refresh_chat_display()
            
            # Make sure the message is visible
            QApplication.processEvents()
    
    def on_progress_updated(self, progress):
        """Handle progress updates.
        
        Args:
            progress: Progress percentage (0-100).
        """
        if progress > 0 and progress < 100:
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setValue(0)
    
    def on_status_updated(self, status):
        """Handle status updates.
        
        Args:
            status: Status message.
        """
        if status and status.strip():
            self.status_label.setText(status)
    
    def validate_api_key(self):
        """Check if API key is provided, but don't validate it to save credits."""
        # Get the API key from the sequence generator
        api_key = self.sequence_generator.api_client.api_key
        
        # Check if API key is empty
        if not api_key:
            # Add message to chat history
            self.chat_service.add_message(
                "assistant", 
                "Please enter an API key in the Settings tab of the Specifications panel to use the chat."
            )
            self.refresh_chat_display()
            return False
        
        # Simply acknowledge the key is present, don't validate to save credits
        self.chat_service.add_message(
            "assistant", 
            "API key is set. You can start chatting or generating sequences."
        )
        self.refresh_chat_display()
        return True
    
    def parse_spring_specs(self, text):
        """Parse spring specifications from the user input if present.
        
        Args:
            text: User input text
        
        Returns:
            True if specifications were found and parsed, False otherwise
        """
        # Check if the text contains spring specification format
        if not any(pattern in text.lower() for pattern in [
            "part name:", "free length:", "wire dia:", "od:", "set point", "safety limit:"
        ]):
            return False
        
        # Create parsed data dictionary
        parsed_data = {
            "basic_info": {},
            "set_points": []
        }
        
        # Define patterns for basic info
        patterns = {
            "part_name": r"Part Name:\s*(.+?)(?:\n|$)",
            "part_number": r"Part Number:\s*(.+?)(?:\n|$)",
            "part_id": r"ID:\s*([^\n]+)(?:\n|$)",  # Updated to match any characters until newline
            "free_length": r"Free Length:\s*([\d.]+)(?:\s*mm)?(?:\n|$)",
            "coil_count": r"No of Coils:\s*([\d.]+)(?:\n|$)",
            "wire_dia": r"(?:Wire|Wired) Dia(?:meter)?:\s*([\d.]+)(?:\s*mm)?(?:\n|$)",
            "outer_dia": r"OD:\s*([\d.]+)(?:\s*mm)?(?:\n|$)",
            "safety_limit": r"[Ss]afety limit:\s*([\d.]+)(?:\s*N)?(?:\n|$)"
        }
        
        # Extract basic info
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                try:
                    if key in ["free_length", "coil_count", "wire_dia", "outer_dia", "safety_limit"]:
                        parsed_data["basic_info"][key] = float(value)
                    else:
                        # Store part ID and other text fields as they are
                        parsed_data["basic_info"][key] = value
                except (ValueError, TypeError):
                    # Skip if conversion fails
                    continue
        
        # Extract set points
        set_point_indices = []
        
        # Find all set point indices mentioned in the text
        for match in re.finditer(r"Set Po(?:i|n)(?:i|t)-(\d+)", text, re.IGNORECASE):
            try:
                index = int(match.group(1))
                if index not in set_point_indices:
                    set_point_indices.append(index)
            except ValueError:
                continue
        
        # Process each set point
        for index in set_point_indices:
            set_point = {"index": index - 1}  # Convert to 0-based index
            
            # Position pattern
            position_pattern = r"Set Po(?:i|n)(?:i|t)-" + str(index) + r"(?:\s+in mm)?:\s*([\d.]+)(?:\s*mm)?(?:\n|$)"
            position_match = re.search(position_pattern, text, re.IGNORECASE)
            
            # Load pattern (with tolerance)
            load_pattern = r"Set Po(?:i|n)(?:i|t)-" + str(index) + r" Load In N:\s*([\d.]+)(?:±([\d.]+)%)?(?:\s*N)?(?:\n|$)"
            load_match = re.search(load_pattern, text, re.IGNORECASE)
            
            # Extract values
            if position_match:
                try:
                    set_point["position"] = float(position_match.group(1).strip())
                except (ValueError, TypeError):
                    continue
            
            if load_match:
                try:
                    set_point["load"] = float(load_match.group(1).strip())
                    
                    # Extract tolerance if present
                    if load_match.group(2):
                        set_point["tolerance"] = float(load_match.group(2).strip())
                except (ValueError, TypeError):
                    continue
            
            # Add set point if it has both position and load
            if "position" in set_point and "load" in set_point:
                set_point["enabled"] = True
                if "tolerance" not in set_point:
                    set_point["tolerance"] = 10.0  # Default tolerance
                parsed_data["set_points"].append(set_point)
        
        # Update specifications if we found any
        if not parsed_data["basic_info"] and not parsed_data["set_points"]:
            return False
        
        # Use the settings service
        settings_service = self.settings_service
        
        # Update basic info if any was found
        if parsed_data["basic_info"]:
            # Get values from basic info or use current values
            spec = settings_service.get_spring_specification()
            
            part_name = parsed_data["basic_info"].get("part_name", spec.part_name)
            part_number = parsed_data["basic_info"].get("part_number", spec.part_number)
            part_id = parsed_data["basic_info"].get("part_id", spec.part_id)
            free_length = parsed_data["basic_info"].get("free_length", spec.free_length_mm)
            coil_count = parsed_data["basic_info"].get("coil_count", spec.coil_count)
            wire_dia = parsed_data["basic_info"].get("wire_dia", spec.wire_dia_mm)
            outer_dia = parsed_data["basic_info"].get("outer_dia", spec.outer_dia_mm)
            safety_limit = parsed_data["basic_info"].get("safety_limit", spec.safety_limit_n)
            
            # Update basic info
            settings_service.update_spring_basic_info(
                part_name, part_number, part_id, free_length, coil_count,
                wire_dia, outer_dia, safety_limit, "mm", True
            )
        
        # Update set points if any were found
        for sp in parsed_data["set_points"]:
            if sp["index"] < len(settings_service.get_spring_specification().set_points):
                # Update existing set point
                settings_service.update_set_point(
                    sp["index"], sp["position"], sp["load"], sp["tolerance"], sp["enabled"]
                )
            else:
                # Add new set point first
                settings_service.add_set_point()
                settings_service.update_set_point(
                    sp["index"], sp["position"], sp["load"], sp["tolerance"], sp["enabled"]
                )
        
        return len(parsed_data["basic_info"]) > 0 or len(parsed_data["set_points"]) > 0
    
    def toggle_loading_indicator(self):
        """Toggle the loading indicator appearance for animation effect."""
        self.loading_state = (self.loading_state + 1) % 4
        
        # Use different border styles to create a rotation illusion
        if self.loading_state == 0:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-top: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """)
        elif self.loading_state == 1:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-right: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """)
        elif self.loading_state == 2:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-bottom: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """)
        else:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-left: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """)
    
    def generate_specification_status(self, spring_spec):
        """Generate a status message about the spring specifications for the AI.
        
        Args:
            spring_spec: The SpringSpecification object or None.
            
        Returns:
            A string describing the specification status.
        """
        if not spring_spec:
            return "NO SPECIFICATIONS SET: Please ask the user to provide spring specifications before generating a test sequence."
        
        # Check if specification is enabled
        if not spring_spec.enabled:
            return "SPECIFICATIONS NOT ENABLED: Specifications exist but are not enabled. Ask the user to enable them in the Specifications panel."
        
        # Check for missing essential specifications
        missing_specs = []
        
        if spring_spec.free_length_mm <= 0:
            missing_specs.append("Free Length")
        
        if spring_spec.wire_dia_mm <= 0:
            missing_specs.append("Wire Diameter")
        
        if spring_spec.outer_dia_mm <= 0:
            missing_specs.append("Outer Diameter")
        
        if spring_spec.coil_count <= 0:
            missing_specs.append("Coil Count")
        
        # Check set points
        valid_set_points = [sp for sp in spring_spec.set_points if sp.enabled and sp.position_mm > 0 and sp.load_n > 0]
        
        if not valid_set_points:
            missing_specs.append("Set Points (position and load)")
        
        if missing_specs:
            return f"INCOMPLETE SPECIFICATIONS: The following specifications are missing or invalid: {', '.join(missing_specs)}. Please ask the user to provide them before generating a test sequence."
        
        # All specifications are valid
        return f"COMPLETE SPECIFICATIONS: All necessary spring specifications are set and valid. The specification includes {len(valid_set_points)} valid set points."
    
    def _create_spec_form_manager(self):
        """Create the specification form manager if it doesn't exist."""
        if self.spec_form_manager is None:
            # Create the form manager
            self.spec_form_manager = SpecificationFormManager()
            
            # Connect signals
            self.spec_form_manager.form_completed.connect(self._on_spec_form_completed)
            self.spec_form_manager.form_cancelled.connect(self._on_spec_form_cancelled)
            
            # Add to form container
            form_container_layout = self.form_container.layout()
            form_container_layout.addWidget(self.spec_form_manager)
    
    def show_specification_form(self):
        """Show the specification form in the chat panel."""
        # Create form manager if needed
        self._create_spec_form_manager()
        
        # Show the form container
        self.form_container.setVisible(True)
        
        # Start the form workflow
        self.spec_form_manager.start_form_workflow()
        
        # Mark form as active
        self.spec_form_active = True
        
        # Disable input while form is active
        self.user_input.setEnabled(False)
        self.generate_btn.setEnabled(False)
    
    def hide_specification_form(self):
        """Hide the specification form."""
        # Hide the form container
        self.form_container.setVisible(False)
        
        # Mark form as inactive
        self.spec_form_active = False
        
        # Re-enable input
        self.user_input.setEnabled(True)
        self.generate_btn.setEnabled(True)
    
    def _on_spec_form_completed(self, form_data):
        """Handle form completion.
        
        Args:
            form_data: Dictionary of collected form data.
        """
        # Hide the form
        self.hide_specification_form()
        
        # Process the collected data
        self._process_form_data(form_data)
        
        # Add message to chat history
        self.chat_service.add_message(
            "assistant", 
            "I've updated the spring specifications based on your input. Now you can generate a test sequence."
        )
        self.refresh_chat_display()
    
    def _on_spec_form_cancelled(self):
        """Handle form cancellation."""
        # Hide the form
        self.hide_specification_form()
        
        # Add message to chat history
        self.chat_service.add_message(
            "assistant", 
            "Specification update was cancelled. You can try again or continue with the current specifications."
        )
        self.refresh_chat_display()
    
    def _process_form_data(self, form_data):
        """Process the collected form data and update specifications.
        
        Args:
            form_data: Dictionary with basic_info, optional_info, and set_points.
        """
        # Get basic info
        basic_info = form_data.get("basic_info", {})
        
        # Get optional info
        optional_info = form_data.get("optional_info", {})
        
        # Get set points
        set_points = form_data.get("set_points", [])
        
        # Get the settings service
        settings_service = self.settings_service
        
        # Prepare all parameters to update at once
        try:
            # Convert part_id to int if possible
            part_id_str = basic_info.get("part_id", "0")
            # Only attempt to convert to int if the string contains only digits
            if part_id_str.isdigit():
                part_id = int(part_id_str)
            else:
                # If it's not a pure number, keep it as is to ensure it gets passed correctly
                part_id = part_id_str
                print(f"Using part_id as string: {part_id}")
        except Exception as e:
            # If there's any error, log it but don't default to 0
            print(f"Error converting part_id: {str(e)}")
            part_id = basic_info.get("part_id", "0")
        
        # Update all spring information in a single call to avoid partial updates
        settings_service.update_spring_basic_info(
            # Basic info parameters
            part_name=basic_info.get("part_name", ""),
            part_number=basic_info.get("part_number", ""),
            part_id=part_id,
            free_length=basic_info.get("free_length", 0.0),
            unit=basic_info.get("unit", "mm"),
            force_unit=basic_info.get("force_unit", "N"),
            test_mode=basic_info.get("test_mode", "Height Mode"),
            component_type=basic_info.get("component_type", "Compression"),
            first_speed=basic_info.get("first_speed", 0.0),
            second_speed=basic_info.get("second_speed", 0.0),
            # Move safety limit to basic info
            safety_limit=optional_info.get("safety_limit", 0.0),
            
            # Optional info parameters
            coil_count=optional_info.get("coil_count", 0.0),
            wire_dia=optional_info.get("wire_dia", 0.0),
            outer_dia=optional_info.get("outer_dia", 0.0),
            offer_number=optional_info.get("offer_number", ""),
            production_batch_number=optional_info.get("production_batch_number", ""),
            part_rev_no_date=optional_info.get("part_rev_no_date", ""),
            material_description=optional_info.get("material_description", ""),
            surface_treatment=optional_info.get("surface_treatment", ""),
            end_coil_finishing=optional_info.get("end_coil_finishing", ""),
            
            # Always enable specifications
            enabled=True  
        )
        
        print(f"Updated all specification fields - basic info: {basic_info}")
        print(f"Updated all specification fields - optional info: {optional_info}")
        
        # Update set points if any
        if set_points:
            # First clear existing set points
            settings_service.clear_set_points()
            
            # Add each set point
            for sp_data in set_points:
                # Add a new set point
                settings_service.add_set_point()
                
                # Get the index (0-based)
                index = len(settings_service.get_spring_specification().set_points) - 1
                
                # Update the set point
                settings_service.update_set_point(
                    index=index,
                    position=sp_data.get("position", 0.0),
                    load=sp_data.get("load", 0.0),
                    tolerance=sp_data.get("tolerance", 10.0),
                    enabled=True
                )
            
            print(f"Added {len(set_points)} set points")
        
        # Get the updated spring specification
        updated_spec = settings_service.get_spring_specification()
        
        # Update the sequence generator
        self.sequence_generator.set_spring_specification(updated_spec)
        
        # Find parent window to access the specifications panel in the sidebar
        parent = self.parent()
        while parent and not hasattr(parent, 'sidebar'):
            parent = parent.parent()
        
        # If we found a parent with sidebar access, refresh the specifications panel
        if parent and hasattr(parent, 'sidebar'):
            # Get the specifications panel from the sidebar
            # This will refresh the UI to show the updated specifications
            try:
                # Get the specifications tab and reload it
                self._update_sidebar_specifications(parent.sidebar)
                print("Successfully updated specifications in sidebar")
            except Exception as e:
                print(f"Error updating specifications in sidebar: {str(e)}")
    
    def _update_sidebar_specifications(self, sidebar):
        """Update specifications in the sidebar panel.
        
        Args:
            sidebar: The sidebar widget.
        """
        # Get the latest specification first to ensure we're working with current data
        updated_spec = self.settings_service.get_spring_specification()
        if not updated_spec:
            print("No specifications found in settings service")
            return False
            
        print(f"Updating sidebar with specification: {updated_spec.part_name}, {updated_spec.part_number}, ID: {updated_spec.part_id}")
        print(f"Safety limit: {updated_spec.safety_limit_n}")
            
        # First try to activate the specifications tab
        try:
            # Switch to the specifications tab
            sidebar.tab_widget.setCurrentIndex(sidebar.tab_widget.indexOf(sidebar.specs_tab))
            print("Switched to specifications tab")
        except Exception as e:
            print(f"Error switching to specifications tab: {str(e)}")
        
        # Try to find the specifications panel in the sidebar
        specs_panel = None
        for i in range(sidebar.specs_layout.count()):
            widget = sidebar.specs_layout.itemAt(i).widget()
            if widget and widget.__class__.__name__ == 'SpecificationsPanel':
                specs_panel = widget
                break
        
        if specs_panel:
            # If we found the specs panel, update it with our data
            try:
                # First, make sure the panel has the latest specification from the settings service
                specs_panel.specifications = updated_spec
                
                # Now update all UI elements explicitly to match our data
                print(f"Setting part_name: {updated_spec.part_name}")
                specs_panel.part_name_input.setText(updated_spec.part_name)
                
                print(f"Setting part_number: {updated_spec.part_number}")
                specs_panel.part_number_input.setText(updated_spec.part_number)
                
                # Handle part_id more carefully - it could be a string or int
                part_id_str = str(updated_spec.part_id) if updated_spec.part_id is not None else ""
                print(f"Setting part_id: {part_id_str}")
                specs_panel.part_id_input.setText(part_id_str)
                
                print(f"Setting free_length: {updated_spec.free_length_mm}")
                specs_panel.free_length_input.setValue(updated_spec.free_length_mm)
                
                print(f"Setting coil_count: {updated_spec.coil_count}")
                specs_panel.coil_count_input.setValue(updated_spec.coil_count)
                
                print(f"Setting wire_dia: {updated_spec.wire_dia_mm}")
                specs_panel.wire_dia_input.setValue(updated_spec.wire_dia_mm)
                
                print(f"Setting outer_dia: {updated_spec.outer_dia_mm}")
                specs_panel.outer_dia_input.setValue(updated_spec.outer_dia_mm)
                
                print(f"Setting safety_limit: {updated_spec.safety_limit_n}")
                specs_panel.safety_limit_input.setValue(updated_spec.safety_limit_n)
                
                print(f"Setting unit: {updated_spec.unit}")
                specs_panel.unit_input.setCurrentText(updated_spec.unit)
                
                print(f"Setting force_unit: {updated_spec.force_unit}")
                specs_panel.force_unit_input.setCurrentText(updated_spec.force_unit)
                
                print(f"Setting test_mode: {updated_spec.test_mode}")
                specs_panel.test_mode_input.setCurrentText(updated_spec.test_mode)
                
                print(f"Setting component_type: {updated_spec.component_type}")
                specs_panel.component_type_input.setCurrentText(updated_spec.component_type)
                
                print(f"Setting first_speed: {updated_spec.first_speed}")
                specs_panel.first_speed_input.setValue(updated_spec.first_speed)
                
                print(f"Setting second_speed: {updated_spec.second_speed}")
                specs_panel.second_speed_input.setValue(updated_spec.second_speed)
                
                print(f"Setting offer_number: {updated_spec.offer_number}")
                specs_panel.offer_number_input.setText(updated_spec.offer_number)
                
                print(f"Setting production_batch_number: {updated_spec.production_batch_number}")
                specs_panel.production_batch_number_input.setText(updated_spec.production_batch_number)
                
                print(f"Setting part_rev_no_date: {updated_spec.part_rev_no_date}")
                specs_panel.part_rev_no_date_input.setText(updated_spec.part_rev_no_date)
                
                print(f"Setting material_description: {updated_spec.material_description}")
                specs_panel.material_description_input.setText(updated_spec.material_description)
                
                print(f"Setting surface_treatment: {updated_spec.surface_treatment}")
                specs_panel.surface_treatment_input.setText(updated_spec.surface_treatment)
                
                print(f"Setting end_coil_finishing: {updated_spec.end_coil_finishing}")
                specs_panel.end_coil_finishing_input.setText(updated_spec.end_coil_finishing)
                
                # Now call load_specifications to refresh the rest of the UI
                print("Calling load_specifications")
                specs_panel.load_specifications()
                
                # Also explicitly call refresh_set_points to update any set points display
                print("Calling refresh_set_points")
                specs_panel.refresh_set_points()
                print("Refreshed specifications panel with manual field updates")
                
                # Force a UI update
                specs_panel.update()
                QApplication.processEvents()
                
                # Make sure specifications are enabled
                if not specs_panel.enabled_checkbox.isChecked():
                    print("Enabling specifications in the panel")
                    specs_panel.enabled_checkbox.setChecked(True)
                    specs_panel.on_enabled_changed(Qt.Checked)
                
                return True
            except Exception as e:
                print(f"Error refreshing specifications panel: {str(e)}")
        else:
            print("Could not find specifications panel in sidebar")
            
            # As a fallback, try to trigger a refresh on the sidebar object itself
            try:
                # Check if sidebar has the display_specifications method
                if hasattr(sidebar, 'display_specifications'):
                    # Prepare the data for display
                    specs_data = {
                        "Basic Information": {
                            "Part Name": updated_spec.part_name,
                            "Part Number": updated_spec.part_number,
                            "Part ID": updated_spec.part_id,
                            "Free Length": f"{updated_spec.free_length_mm} {updated_spec.unit}",
                            "Component Type": updated_spec.component_type,
                            "Test Mode": updated_spec.test_mode,
                            "Safety Limit": f"{updated_spec.safety_limit_n} {updated_spec.force_unit}",
                            "Status": "Enabled" if updated_spec.enabled else "Disabled"
                        },
                        "Technical Specifications": {
                            "Coil Count": updated_spec.coil_count,
                            "Wire Diameter": f"{updated_spec.wire_dia_mm} {updated_spec.unit}",
                            "Outer Diameter": f"{updated_spec.outer_dia_mm} {updated_spec.unit}",
                            "First Speed": f"{updated_spec.first_speed} {updated_spec.unit}/s",
                            "Second Speed": f"{updated_spec.second_speed} {updated_spec.unit}/s"
                        }
                    }
                    
                    # Call the display method
                    sidebar.display_specifications(specs_data)
                    print("Updated sidebar with specifications data")
                    
                    return True
            except Exception as e:
                print(f"Error updating sidebar specifications display: {str(e)}")
        
        return False
    
    def _is_spec_update_request(self, user_input):
        """Check if the user input is a request to update specifications.
        
        Args:
            user_input: The user's input text
        
        Returns:
            True if it's a request to update specifications, False otherwise
        """
        # First check for direct mentions of the form or updating specifications
        if any(phrase in user_input.lower() for phrase in [
            "edit specification", "update specification", "edit spec", "update spec",
            "change spec", "fill specification", "specification form", "spec form",
            "update spring", "edit spring", "create spring", "define spring",
            "enter specification", "enter spec", "input spec"
        ]):
            return True
            
        # If the user is asking for a test sequence but specifications are not enabled,
        # we'll also offer the form as an option
        if any(phrase in user_input.lower() for phrase in [
            "test sequence", "generate sequence", "create sequence", "make sequence",
            "spring test", "compression test", "tension test"
        ]):
            # Check if specifications are enabled
            spring_spec = self.settings_service.get_spring_specification()
            if not spring_spec or not spring_spec.enabled:
                return True
                
        return False
        
    def _handle_spec_update_request(self):
        """Handle the request to update specifications."""
        # Get the current specification status
        spring_spec = self.settings_service.get_spring_specification()
        
        # Determine the appropriate message based on the specification status
        if not spring_spec or not spring_spec.enabled:
            # No specifications set or not enabled
            message = "I noticed that you don't have any active spring specifications. Would you like to set them up now?"
        else:
            # Specifications exist but user wants to update
            message = "Would you like to update your spring specifications using a form?"
        
        # Add confirmation message to chat history
        self.chat_service.add_message("assistant", message)
        
        # Add option buttons as a special message type (this will be rendered specially in the chat display)
        buttons_html = """
        <div class="option-buttons">
            <button class="option-button yes-button" onclick="showSpecForm()">Yes, update specifications</button>
            <button class="option-button no-button" onclick="continueWithoutSpecForm()">No, continue without updating</button>
        </div>
        """
        
        # Store state for the choice
        self._awaiting_spec_form_choice = True
        
        # Add JavaScript to handle button clicks
        js_code = """
        <script>
        function showSpecForm() {
            // Notify Python code to show the form
            // This will be handled by the bridge object
            if (window.bridge) {
                window.bridge.showSpecificationForm();
            }
        }
        
        function continueWithoutSpecForm() {
            // Notify Python code to continue without showing the form
            if (window.bridge) {
                window.bridge.continueWithoutSpecForm();
            }
        }
        </script>
        """
        
        # Register JavaScript bridge callbacks
        self.chat_display.page().runJavaScript(js_code)
        
        # Add buttons content - for now, let's add a simplified version that shows the form directly
        # In a real implementation, we'd need to set up a proper JavaScript bridge
        self.show_specification_form()
        
        # Refresh the display
        self.refresh_chat_display() 