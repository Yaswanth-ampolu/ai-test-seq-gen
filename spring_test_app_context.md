# Spring Test App Context Documentation

## Project Overview

The Spring Test App is a desktop application designed for generating test sequences for spring testing machines. The app leverages modern large language models to create testing sequences based on spring specifications, making the process more intuitive and accessible to engineers.

## Core Features

- **Natural Language Processing**: Users can provide spring specifications in natural language or structured format
- **AI-Powered Sequence Generation**: Communicates with Together.ai's API to generate spring test sequences
- **Spring Specification Management**: Allows defining, updating, and storing spring specifications
- **Test Sequence Display**: Visualizes sequences in tables with user-friendly formatting
- **Export Functionality**: Exports sequences to multiple formats (CSV, JSON, Excel)
- **Interactive Chat Interface**: Provides a conversational interface for working with the AI
- **Responsive UI**: Modern, efficient interface with dark/light theme support
- **Settings Persistence**: Saves user preferences and specification data between sessions

## Application Architecture

The Spring Test App follows a modular architecture with clear separation of concerns:

### 1. UI Layer
- **Main Window**: Central container that hosts all UI components
- **Chat Panel**: Interface for user input and AI responses
- **Sidebar/Results Panel**: Displays generated test sequences
- **Specifications Panel**: Interface for managing spring specifications

### 2. Service Layer
- **Settings Service**: Manages application settings and spring specifications
- **Sequence Generator**: Handles the business logic for generating test sequences
- **Chat Service**: Manages chat history and message formatting
- **Export Service**: Handles exporting sequences to various formats

### 3. Data Layer
- **Spring Specification**: Represents spring parameters including set points
- **Test Sequence**: Represents a generated test sequence
- **Chat Message**: Represents messages in the chat history

### 4. Utility Layer
- **API Client**: Handles communication with the Together.ai API
- **Constants**: Defines application constants and templates
- **Styles**: Manages application theming

## Key Components

### Spring Specification Model

The `SpringSpecification` class is central to the application, representing all the parameters required for spring testing:

```python
@dataclass
class SpringSpecification:
    """Specifications for a spring to be tested."""
    part_name: str = ""
    part_number: str = ""
    part_id: int = 0
    free_length_mm: float = 0.0
    coil_count: float = 0.0
    wire_dia_mm: float = 0.0
    outer_dia_mm: float = 0.0
    set_points: List[SetPoint] = field(default_factory=list)
    safety_limit_n: float = 0.0
    unit: str = "mm"  # mm or inch
    enabled: bool = False
    create_defaults: bool = False  # Whether to create default set points
```

### Set Points

Set points define specific positions and corresponding loads for spring testing:

```python
@dataclass
class SetPoint:
    """Represents a set point for spring testing."""
    position_mm: float
    load_n: float
    tolerance_percent: float = 10.0
    enabled: bool = True
```

### Sequence Generator

The `SequenceGenerator` service handles the logic of generating test sequences:

- Communicates with the API client to send requests to Together.ai
- Maintains spring specifications for use in generation
- Processes responses into structured sequence data
- Emits signals to update the UI with progress and results

### Together API Client

The `TogetherAPIClient` manages communication with the AI service:

- Formats parameters into prompts for the LLM
- Makes asynchronous API requests in a worker thread
- Processes responses to extract sequence data
- Handles error cases and retries

### Chat Panel

The `ChatPanel` provides the main interface for user interaction:

- Captures user input and displays AI responses
- Parses spring specifications from structured user input
- Manages the state of sequence generation
- Provides visual feedback on operation progress

## Recent Changes and Improvements

### 1. Enhanced AI Prompting

The system prompt has been updated to provide better guidance to the AI:

- Instructs the AI to check for complete specifications
- Includes detailed specification status message
- Guides the AI on how to formulate responses

### 2. Specification Status Generation

Added a new method `generate_specification_status()` that provides detailed information about the current state of specifications:

```python
def generate_specification_status(self, spring_spec):
    """Generate a status message about the spring specifications for the AI."""
    if not spring_spec:
        return "NO SPECIFICATIONS SET: Please ask the user to provide spring specifications..."
    
    # Check if specification is enabled
    if not spring_spec.enabled:
        return "SPECIFICATIONS NOT ENABLED: Specifications exist but are not enabled..."
    
    # Check for missing essential specifications
    missing_specs = []
    # [validation logic]
    
    if missing_specs:
        return f"INCOMPLETE SPECIFICATIONS: The following specifications are missing or invalid: {', '.join(missing_specs)}..."
    
    # All specifications are valid
    return f"COMPLETE SPECIFICATIONS: All necessary spring specifications are set and valid..."
```

### 3. Natural Intent Detection

Removed manual parsing for user intent to allow the AI to determine requests for test sequences naturally:

- No longer uses regex to detect sequence requests
- Allows the AI to interpret user requests based on context
- Provides a more natural conversation flow

### 4. Complete AI-Driven Flow

The AI now manages the entire conversation flow:

- Checks specifications when detecting a sequence request
- Informs the user of any missing specifications
- Generates appropriate sequences when specifications are complete

### 5. Scrag Command Parsing Enhancement

Improved parsing of test sequences containing Scrag commands with references:

- Added cell position tracking to recognize column position
- Implemented command type detection for Scrag commands
- Added pattern-based condition detection for references
- Improved handling of special format "Rxx,y" (e.g., "R03,2")

### 6. Reset Functionality

Added multiple ways to reset spring specifications:

- Added a "Reset Specifications" button in the specifications panel
- Created a command-line option `--reset-specs` for resetting on startup
- Implemented a standalone `reset_specs.py` script
- Created a convenience `reset_specs.bat` batch file for Windows users

### 7. Spring Specification Persistence

Improved how spring specifications are saved and loaded:

- Enhanced the `from_dict` method to properly handle the `create_defaults` parameter
- Added the `create_defaults` parameter to the `to_dict` method output
- Added logging to track specification loading and saving
- Fixed issues with set points not saving properly

### 8. UI Responsiveness

Enhanced UI update handling for better responsiveness:

- Added explicit scroll handling for chat display
- Improved JavaScript for updating the chat container
- Added calls to `QApplication.processEvents()` for immediate UI updates
- Enhanced debug logging for message tracking

## Message Processing Flow

The application follows a well-defined flow for processing user messages:

1. **Input Capture**: The chat panel captures user input from the text field
2. **Spring Specification Detection**: Analyzes input for structured spring specifications
3. **Parameter Preparation**: Prepares parameters for the AI, including current specifications
4. **AI Request**: Sends the request to the Together.ai API asynchronously
5. **Response Processing**: Processes the AI response to extract sequence data
6. **UI Update**: Updates the chat display and sequence panel with results

## Plans for Future Enhancements

### 1. Embedding Implementation

Plans to add semantic search capabilities using Together.ai's embedding models:

- Store and retrieve relevant context from previous conversations
- Keep track of spring specifications mentioned in conversations
- Relate new requests to similar past interactions
- Understand various ways users might express the same concepts

### 2. Enhanced UI Feedback

Plans to improve visual feedback for specification updates:

- Highlight updated specifications in the UI
- Provide visual cues when specifications are incomplete
- Add animation for better user feedback

### 3. Intelligent Conversation Management

Plans to implement a more sophisticated conversation manager:

- Extract specifications from natural conversation
- Understand corrections to previously provided specifications
- Ask targeted questions to complete missing specifications
- Handle specifications over multiple messages

## Installation and Usage

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

### Building Executable

The application includes a build script for creating a standalone executable:

```
python build_exe.py --clean
```

Options:
- `--onefile`: Build a single executable file
- `--console`: Show console window 
- `--clean`: Clean build files before building

### Reset Specifications

To reset specifications to default values:

1. Use the "Reset Specifications" button in the UI
2. Start the application with `python main.py --reset-specs`
3. Run the standalone script `python reset_specs.py`
4. Or on Windows, double-click the `reset_specs.bat` file

## Technical Implementation Details

### API Communication

The application communicates with the Together.ai API using the following pattern:

```python
payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": temperature
}

response = session.post(
    API_ENDPOINT,
    headers=headers,
    json=payload,
    timeout=60
)
```

### Asynchronous Operations

To keep the UI responsive, all API calls are performed asynchronously:

```python
def generate_sequence_async(self, parameters):
    """Generate a test sequence asynchronously."""
    # Create a worker thread
    self.current_worker = TogetherAPIClientWorker(
        self, parameters, model, temperature, max_retries
    )
    
    # Connect signals
    self.current_worker.finished.connect(callback)
    self.current_worker.progress.connect(progress_callback)
    
    # Start the thread
    self.current_thread = threading.Thread(target=self.current_worker.run)
    self.current_thread.daemon = True
    self.current_thread.start()
```

### Settings Persistence

The application saves settings and specifications between sessions using encrypted storage:

```python
def save_settings(self):
    """Save settings to disk."""
    # Serialize settings to JSON
    serialized = json.dumps(self.settings)
    
    # Encrypt the data
    fernet = Fernet(self._generate_key())
    encrypted_data = fernet.encrypt(serialized.encode('utf-8'))
    
    # Write to file
    with open(self.settings_file, "wb") as f:
        f.write(encrypted_data)
```

## Conclusion

The Spring Test App demonstrates a sophisticated approach to integrating AI capabilities into a desktop application. Through continuous improvements to the codebase, the application has evolved to provide a more intuitive and reliable experience for engineers working with spring testing machines.

The modular architecture with clear separation of concerns allows for flexibility and maintainability, while the focus on user experience ensures that the application remains accessible and efficient for its intended users. 