"""
Together.ai API client module for the Spring Test App.
Contains functions for making API requests to Together.ai and handling responses.
"""
import requests
import pandas as pd
import json
import time
import threading
import re
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from utils.constants import API_ENDPOINT, DEFAULT_MODEL, DEFAULT_TEMPERATURE, SYSTEM_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE
# Removed dependency on text_parser
# from utils.text_parser import extract_command_sequence, format_parameter_text, extract_error_message


# Helper functions moved directly to this file to avoid dependency on text_parser
def format_parameter_text(parameters: Dict[str, Any]) -> str:
    """
    Format parameters for display or for use in API prompts.
    
    Args:
        parameters: Dictionary of parameters.
        
    Returns:
        Formatted parameter text.
    """
    lines = []
    
    # Format each parameter as a line
    for key, value in parameters.items():
        # Skip timestamp and metadata
        if key in ["Timestamp", "prompt"]:
            continue
            
        # Simple string conversion
        formatted_value = str(value)
        lines.append(f"{key}: {formatted_value}")
    
    return "\n".join(lines)

def extract_command_sequence(text: str) -> Dict[str, Any]:
    """
    Extract a command sequence from text (usually API response).
    
    Args:
        text: The text containing a command sequence, often from API response.
        
    Returns:
        A dictionary representing the command sequence or empty dict if parsing fails.
    """
    import json
    
    # Try to extract JSON from the response
    json_start_idx = text.find("[")
    json_end_idx = text.rfind("]") + 1
    
    if json_start_idx >= 0 and json_end_idx > json_start_idx:
        # Found JSON-like syntax in brackets
        json_content = text[json_start_idx:json_end_idx]
    else:
        json_content = text
    
    # Clean up any markdown formatting
    if json_content.startswith("```") and json_content.endswith("```"):
        json_content = json_content[3:-3].strip()
    
    # Try to parse the JSON
    try:
        data = json.loads(json_content)
        return data
    except json.JSONDecodeError:
        # If JSON parsing fails, return empty dict
        return {}

def extract_error_message(response_text: str) -> str:
    """
    Extract error message from API response.
    
    Args:
        response_text: The API response text.
        
    Returns:
        The extracted error message, or empty string if none found.
    """
    # Simple extraction - look for common error message patterns
    error_patterns = [
        r"Error:\s*(.+?)(?:\n|$)",
        r"Failed to\s*(.+?)(?:\n|$)",
        r"Unable to\s*(.+?)(?:\n|$)",
        r"I apologize, but I cannot\s*(.+?)(?:\n|$)"
    ]
    
    for pattern in error_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""


class TogetherAPIClientWorker(QObject):
    """Worker class for making API requests to Together.ai in a separate thread."""
    
    # Define signals
    finished = pyqtSignal(object, str)  # (DataFrame, error_message)
    progress = pyqtSignal(int)  # Progress percentage (0-100)
    status = pyqtSignal(str)    # Status message
    
    def __init__(self, api_client, parameters, model, temperature, max_retries):
        """Initialize the worker.
        
        Args:
            api_client: The API client to use for requests.
            parameters: Dictionary of spring parameters.
            model: The model to use for generation.
            temperature: The temperature to use for generation.
            max_retries: Maximum number of retry attempts.
        """
        super().__init__()
        self.api_client = api_client
        self.parameters = parameters
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.is_cancelled = False
    
    def cancel(self):
        """Cancel the current operation."""
        self.is_cancelled = True
    
    def run(self):
        """Run the API request in a separate thread."""
        # Format parameter text for prompt
        parameter_text = format_parameter_text(self.parameters)
        
        # Get the original user prompt
        original_prompt = self.parameters.get('prompt', '')
        
        # Get specifications status if provided
        specifications_status = self.parameters.get('specifications_status', 'No specification status provided')
        
        # Check if test_type is provided in parameters
        test_type_text = ""
        if "Test Type" in self.parameters:
            test_type = self.parameters["Test Type"]
            test_type_text = f"This should be a {test_type} test sequence."
        
        # Create a simplified user prompt that instructs the AI about the format
        # Let the AI determine response format rather than trying to predict intent ourselves
        user_prompt = USER_PROMPT_TEMPLATE.format(
            parameter_text=parameter_text,
            test_type_text=test_type_text,
            prompt=original_prompt
        )
        
        # Include previous context if available
        if self.api_client.chat_memory:
            user_prompt += "\n\nPrevious context:\n" + "\n".join(self.api_client.chat_memory[-3:])
        
        # Format the system prompt with specifications status
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            specifications_status=specifications_status
        )
        
        # Create payload for Together.ai API
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature
        }
        
        # Save the request for debugging
        self.api_client.request_history.append({
            "timestamp": time.time(),
            "payload": payload
        })
        
        # Make the request with retries
        response_text = ""
        error_message = ""
        
        self.status.emit("Preparing request...")
        self.progress.emit(10)
        
        for attempt in range(self.max_retries):
            if self.is_cancelled:
                self.finished.emit(pd.DataFrame(), "Operation cancelled")
                return
                
            try:
                self.status.emit(f"Sending request to Together.ai (attempt {attempt+1}/{self.max_retries})...")
                self.progress.emit(20 + (attempt * 15))
                
                response = self.api_client.session.post(
                    API_ENDPOINT,
                    headers=self.api_client.get_headers(),
                    json=payload,
                    timeout=60  # 60 second timeout
                )
                response.raise_for_status()
                response_json = response.json()
                
                self.status.emit("Processing response...")
                self.progress.emit(80)
                
                # Parse response from Together.ai
                message = response_json['choices'][0].get('message', {})
                response_text = message.get('content', '')
                
                # Save context for continuity
                self.api_client.chat_memory.append(parameter_text)
                if len(self.api_client.chat_memory) > 10:  # Keep memory limited
                    self.api_client.chat_memory = self.api_client.chat_memory[-10:]
                
                # Save raw response for debugging
                self.api_client.last_raw_response = response_text
                
                # Process the response
                self.status.emit("Processing response...")
                self.progress.emit(80)
                
                # Clean up response text - remove markdown backticks if present
                response_text = response_text.replace("```json", "").replace("```", "").strip()
                
                # Print the raw response for debugging
                print(f"DEBUG: Raw response received: {response_text[:200]}...")
                
                # Check for hybrid response format with both text and sequence data
                sequence_data_start = "---SEQUENCE_DATA_START---"
                sequence_data_end = "---SEQUENCE_DATA_END---"
                
                if sequence_data_start in response_text and sequence_data_end in response_text:
                    # This is a hybrid response with both text and sequence data
                    # Extract the parts
                    parts = response_text.split(sequence_data_start)
                    conversation_text = parts[0].strip()
                    
                    # Extract the sequence data
                    seq_parts = parts[1].split(sequence_data_end)
                    sequence_json_text = seq_parts[0].strip()
                    
                    # If there's additional text after the sequence data, add it to conversation
                    if len(seq_parts) > 1 and seq_parts[1].strip():
                        conversation_text += "\n\n" + seq_parts[1].strip()
                    
                    try:
                        print(f"DEBUG: Attempting to parse sequence data: {sequence_json_text[:200]}...")
                        # First try standard JSON parsing
                        data = json.loads(sequence_json_text)
                        print(f"DEBUG: Successfully parsed sequence data as JSON with {len(data)} rows")
                        
                        # Create a DataFrame with the sequence data
                        df = pd.DataFrame(data)
                        
                    except json.JSONDecodeError:
                        print("DEBUG: JSON parsing failed, trying custom format parsing")
                        # If JSON parsing fails, try to parse the custom format [R00, ZF, Zero Force, , , , ]
                        try:
                            rows = []
                            for line in sequence_json_text.strip().split('\n'):
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
                                    
                                    # Make sure we have exactly 7 cells
                                    while len(cells) < 7:
                                        cells.append("")
                                    
                                    # If we have too many cells, combine the extras into the appropriate column
                                    if len(cells) > 7:
                                        print(f"WARNING: Found {len(cells)} cells, expected 7. Combining extras.")
                                        # Keep the first 6 cells as-is and combine the remaining cells into the last column
                                        cells = cells[:6] + [", ".join(cells[6:])]
                                    
                                    row = {
                                        "Row": cells[0],
                                        "CMD": cells[1],
                                        "Description": cells[2],
                                        "Condition": cells[3],
                                        "Unit": cells[4],
                                        "Tolerance": cells[5],
                                        "Speed rpm": cells[6]
                                    }
                                    rows.append(row)
                            
                            if rows:
                                print(f"DEBUG: Successfully parsed {len(rows)} rows from custom format")
                                data = rows
                                df = pd.DataFrame(data)
                            else:
                                raise ValueError("No valid rows found in custom format")
                                
                        except Exception as e:
                            print(f"DEBUG: Custom format parsing failed: {str(e)}")
                            # If that also fails, create a conversation-only response
                            message_df = pd.DataFrame([{"Row": "CHAT", "CMD": "CHAT", "Description": response_text}])
                            df = message_df
                    
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
                    
                    # Add the conversation text to a special "CHAT" row
                    chat_row = pd.DataFrame({
                        "Row": ["CHAT"], 
                        "CMD": ["CHAT"], 
                        "Description": [conversation_text]
                    })
                    
                    # Add empty values for other columns
                    for col in required_columns:
                        if col not in chat_row.columns:
                            chat_row[col] = ""
                    
                    # Combine the chat row with the sequence data
                    df = pd.concat([chat_row, df], ignore_index=True)
                    
                # Handle JSON-only responses (sequence data without conversation)
                elif response_text.strip().startswith("[") and response_text.strip().endswith("]"):
                    try:
                        print("DEBUG: Attempting to parse JSON-only response")
                        # First try parsing as standard JSON
                        data = json.loads(response_text)
                        print(f"DEBUG: Successfully parsed JSON-only data with {len(data)} rows")
                        df = pd.DataFrame(data)
                        
                    except json.JSONDecodeError:
                        print("DEBUG: JSON-only parsing failed, trying custom format")
                        # Try parsing custom format [R00, ZF, Zero Force, , , , ]
                        try:
                            rows = []
                            for line in response_text.strip().split('\n'):
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
                                    
                                    # Make sure we have exactly 7 cells
                                    while len(cells) < 7:
                                        cells.append("")
                                    
                                    # If we have too many cells, combine the extras into the appropriate column
                                    if len(cells) > 7:
                                        print(f"WARNING: Found {len(cells)} cells, expected 7. Combining extras.")
                                        # Keep the first 6 cells as-is and combine the remaining cells into the last column
                                        cells = cells[:6] + [", ".join(cells[6:])]
                                    
                                    row = {
                                        "Row": cells[0],
                                        "CMD": cells[1],
                                        "Description": cells[2],
                                        "Condition": cells[3],
                                        "Unit": cells[4],
                                        "Tolerance": cells[5],
                                        "Speed rpm": cells[6]
                                    }
                                    rows.append(row)
                            
                            if rows:
                                print(f"DEBUG: Successfully parsed {len(rows)} rows from JSON-only custom format")
                                data = rows
                                df = pd.DataFrame(data)
                            else:
                                raise ValueError("No valid rows found in custom format")
                                
                        except Exception as e:
                            print(f"DEBUG: Custom format parsing failed: {str(e)}")
                            # If all parsing fails, create a conversation-only response
                            message_df = pd.DataFrame([{"Row": "CHAT", "CMD": "CHAT", "Description": response_text}])
                            df = message_df
                        
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
                else:
                    print("DEBUG: Response doesn't contain sequence data, creating conversation-only response")
                    # No sequence data found - this was a conversational response
                    # Create a custom message-only DataFrame
                    message_df = pd.DataFrame([{"Row": "CHAT", "CMD": "CHAT", "Description": response_text}])
                    df = message_df
                
                print(f"DEBUG: Final DataFrame has {len(df)} rows, emitting result")
                # Always return df - if it's empty or contains a CHAT row, will be handled correctly by the receiver
                self.finished.emit(df, error_message)
                return
            
            except requests.exceptions.HTTPError as e:
                error_message = f"HTTP Error: {str(e)}"
                status_code = e.response.status_code if hasattr(e, 'response') and hasattr(e.response, 'status_code') else "unknown"
                self.status.emit(f"HTTP Error (status code: {status_code})")
                
                # Try to parse error response
                try:
                    error_json = e.response.json()
                    error_message = extract_error_message(error_json) or error_message
                except:
                    pass
                
            except requests.exceptions.ConnectionError:
                error_message = "Connection Error: Failed to connect to the API server. Please check your internet connection."
                self.status.emit("Connection Error")
                
            except requests.exceptions.Timeout:
                error_message = "Timeout Error: The request timed out. Please try again."
                self.status.emit("Timeout Error")
                
            except requests.exceptions.RequestException as e:
                error_message = f"Request Error: {str(e)}"
                self.status.emit("Request Error")
                
            except json.JSONDecodeError:
                error_message = "JSON Error: Could not parse the API response."
                self.status.emit("JSON Parsing Error")
                
            except Exception as e:
                error_message = f"Unexpected Error: {str(e)}"
                self.status.emit("Unexpected Error")
            
            # Wait before retrying
            if attempt < self.max_retries - 1:
                self.status.emit(f"Retrying in 3 seconds... (attempt {attempt+1}/{self.max_retries})")
                time.sleep(3)
        
        # If we get here, all retries failed
        self.status.emit("Failed after maximum retry attempts")
        
        # Create an empty DataFrame to return
        df = pd.DataFrame()
        self.finished.emit(df, error_message)


class TogetherAPIClient:
    """Client for interacting with the Together.ai API."""
    
    def __init__(self, api_key: str = ""):
        """Initialize the API client.
        
        Args:
            api_key: API key for Together.ai.
        """
        self.api_key = api_key
        self.last_raw_response = ""
        self.chat_memory = []
        self.request_history = []
        self.session = requests.Session()
        self.current_worker = None
        self.current_thread = None
    
    def set_api_key(self, api_key: str) -> None:
        """Set the API key.
        
        Args:
            api_key: API key for Together.ai.
        """
        self.api_key = api_key
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests.
        
        Returns:
            Dictionary of headers.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_sequence_async(self, parameters: Dict[str, Any], 
                             callback: Callable[[pd.DataFrame, str], None],
                             progress_callback: Optional[Callable[[int], None]] = None,
                             status_callback: Optional[Callable[[str], None]] = None,
                             model: str = DEFAULT_MODEL, 
                             temperature: float = DEFAULT_TEMPERATURE,
                             max_retries: int = 3) -> None:
        """Generate a sequence asynchronously.
        
        Args:
            parameters: Parameters for sequence generation.
            callback: Function to call with the result.
            progress_callback: Function to call with progress updates.
            status_callback: Function to call with status updates.
            model: Model to use.
            temperature: Temperature to use.
            max_retries: Maximum number of retries.
        """
        # Cancel any existing operation
        self.cancel_current_operation()
        
        # Create a worker
        self.current_worker = TogetherAPIClientWorker(
            self, parameters, model, temperature, max_retries
        )
        
        # Connect signals
        self.current_worker.finished.connect(callback)
        if progress_callback:
            self.current_worker.progress.connect(progress_callback)
        if status_callback:
            self.current_worker.status.connect(status_callback)
        
        # Create a thread for the worker
        self.current_thread = threading.Thread(target=self.current_worker.run)
        self.current_thread.daemon = True
        
        # Start the thread
        self.current_thread.start()
    
    def cancel_current_operation(self) -> None:
        """Cancel the current operation."""
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker = None
        
        self.current_thread = None
    
    def generate_sequence(self, parameters: Dict[str, Any], 
                         model: str = DEFAULT_MODEL, 
                         temperature: float = DEFAULT_TEMPERATURE,
                         max_retries: int = 3) -> Tuple[pd.DataFrame, str]:
        """Generate a sequence synchronously.
        
        Args:
            parameters: Parameters for sequence generation.
            model: Model to use.
            temperature: Temperature to use.
            max_retries: Maximum number of retries.
            
        Returns:
            Tuple of (DataFrame, error_message).
        """
        result_df = None
        error_message = ""
        
        # Define a callback to get the result
        def callback(df, error_msg):
            nonlocal result_df, error_message
            result_df = df
            error_message = error_msg
        
        # Generate the sequence asynchronously
        self.generate_sequence_async(
            parameters, callback, None, None, model, temperature, max_retries
        )
        
        # Wait for the thread to complete
        if self.current_thread:
            self.current_thread.join()
        
        # Reset the worker and thread
        self.current_worker = None
        self.current_thread = None
        
        # Return the result
        return result_df, error_message
    
    def validate_api_key(self) -> Tuple[bool, str]:
        """Validate the API key.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check if API key is set
        if not self.api_key:
            return False, "API key is not set"
        
        try:
            # Simple echo request to validate the API key
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "user", "content": "Echo test"}
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }
            
            response = self.session.post(
                API_ENDPOINT,
                headers=self.get_headers(),
                json=payload,
                timeout=15  # shorter timeout for validation
            )
            
            response.raise_for_status()
            return True, "API key is valid"
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') and hasattr(e.response, 'status_code') else "unknown"
            if status_code == 401:
                return False, "Invalid API key"
            else:
                return False, f"HTTP Error (status code: {status_code})"
                
        except requests.exceptions.ConnectionError:
            return False, "Failed to connect to the API server. Please check your internet connection."
            
        except requests.exceptions.Timeout:
            return False, "Request timed out. Please try again."
            
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
            
        except Exception as e:
            return False, f"Unexpected error: {str(e)}" 