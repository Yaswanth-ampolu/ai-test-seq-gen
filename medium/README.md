# DAT to JSON Conversion Utility

This folder contains utility scripts for converting `.dat` files from the Spring Test App's `appdata` directory to JSON format. These tools allow for better data inspection, interoperability, and debugging without disrupting the normal application flow.

## Files

1. **dat_to_json_converter.py**
   - Standalone script for converting all `.dat` files to JSON
   - Preserves original data structure
   - Handles datetime objects and custom classes

2. **dat_json_utility.py**
   - Importable module with functions for programmatic conversion
   - Supports background conversion to avoid disrupting application flow
   - Includes file watching capability for automatic conversion

3. **encrypted_dat_converter.py**
   - Specialized converter for encrypted `.dat` files (like `settings.dat`)
   - Uses the same encryption keys and methods as the application
   - Properly decrypts the data before converting to JSON

4. **integration_example.py**
   - Demonstrates how to integrate conversion with existing application services
   - Shows method monkey-patching to add conversion to save operations
   - Works standalone or integrated with the application

## Usage

### Standalone Conversion

To convert all `.dat` files in the `appdata` directory to JSON:

```bash
python dat_to_json_converter.py
```

For encrypted `.dat` files (like settings.dat):

```bash
python encrypted_dat_converter.py
```

### Programmatic Usage

```python
from medium.dat_json_utility import convert_dat_to_json

# Convert a specific .dat file
convert_dat_to_json('appdata/chat_history.dat')

# Convert and specify output location
convert_dat_to_json('appdata/chat_history.dat', 'path/to/output.json')

# Convert synchronously and get result path
json_path = convert_dat_to_json('appdata/chat_history.dat', background=False)
```

For encrypted files:

```python
from medium.encrypted_dat_converter import convert_encrypted_dat_to_json

# Convert an encrypted .dat file
convert_encrypted_dat_to_json('appdata/settings.dat', 'medium/settings.json')
```

### Automatic Integration

To set up automatic conversion whenever `.dat` files are modified:

```bash
python integration_example.py
```

This will:
1. Convert all existing `.dat` files to JSON (including encrypted ones)
2. Set up hooks to automatically convert files when saved
3. Continue with normal application flow

## Benefits

- **Non-disruptive**: These utilities work alongside the existing application without modifying its core functionality
- **Background Processing**: Conversions can run in background threads to avoid UI freezes
- **Human-Readable Data**: JSON files are easier to inspect and edit than binary `.dat` files
- **Encryption Handling**: Properly decrypts encrypted files to make them human-readable
- **Interoperability**: JSON format enables integration with other tools and systems

## Note

The original `.dat` files remain untouched - this utility only creates JSON copies in the `medium` folder. 