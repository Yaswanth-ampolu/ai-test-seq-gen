# Settings Conversion Utilities

This directory contains utilities for working with the Spring Test App's settings files, allowing you to convert between the application's encrypted `.dat` format and human-readable JSON.

## Utilities

1. **encrypted_dat_converter.py** - Converts `settings.dat` to `settings.json`
2. **json_to_settings_dat.py** - Converts `settings.json` back to `settings.dat`

## Why Use These Utilities?

- **Editing Settings**: The application stores settings in an encrypted binary format. These utilities let you convert to human-readable JSON to inspect or modify settings.
- **Backup and Transfer**: Export settings to JSON for backup or to transfer to another installation.
- **Troubleshooting**: Debug application settings issues by viewing the actual settings data.
- **Set Points Configuration**: Easily edit spring set points by modifying the JSON file and converting back.

## How to Use

### Converting settings.dat to JSON

To convert the application's settings to JSON format:

```bash
python encrypted_dat_converter.py
```

This will:
1. Read the `settings.dat` file from the `appdata` directory
2. Decrypt it using the application's encryption key
3. Save it as `settings.json` in the `medium` directory

### Converting JSON back to settings.dat

To convert your edited `settings.json` back to the application's format:

```bash
python json_to_settings_dat.py
```

This will:
1. Read the `settings.json` file from the `medium` directory
2. Encrypt it using the application's encryption key
3. Save it as `settings.dat` in the `appdata` directory
4. Create a backup of any existing `settings.dat` file as `settings.dat.bak`

## Editing Spring Specifications

The `settings.json` file contains all the spring specifications used by the application, including set points. 

### Set Points Structure

Set points are stored in the JSON structure like this:

```json
"set_points": [
    {
        "position_mm": 40.0,
        "load_n": 23.6,
        "tolerance_percent": 10.0,
        "enabled": true
    },
    {
        "position_mm": 33.0,
        "load_n": 34.14,
        "tolerance_percent": 10.0,
        "enabled": true
    }
]
```

### Editing Steps

1. Run `encrypted_dat_converter.py` to extract settings to JSON
2. Edit `medium/settings.json` with any text editor
3. Run `json_to_settings_dat.py` to convert back to the application format
4. Restart the Spring Test App to load the new settings

## Safety Features

- **Backup Creation**: The JSON-to-DAT converter automatically creates a backup of the existing settings
- **Validation**: Basic validation checks for required fields before writing the settings.dat file
- **Error Handling**: Detailed error messages if something goes wrong during conversion

## Example Workflow

1. **Extract**: `python encrypted_dat_converter.py`
2. **Edit**: Modify `medium/settings.json` to add or change set points
3. **Convert**: `python json_to_settings_dat.py`
4. **Use**: Restart the Spring Test App to use your modified settings

## Troubleshooting

- If conversion fails, check that the JSON file is valid (no syntax errors)
- Make sure the root of the JSON contains required fields like `api_key` and `spring_specification`
- Ensure permissions allow writing to the `appdata` directory
- If all else fails, the application will revert to default settings 