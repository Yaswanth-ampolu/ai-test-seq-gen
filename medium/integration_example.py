#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Integration Example

This script demonstrates how to integrate the DAT/JSON utility with
the existing application flow without disrupting it.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from the application
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import utility module
from medium.dat_json_utility import convert_dat_to_json, watch_dat_files
from medium.encrypted_dat_converter import convert_encrypted_dat_to_json

# Try to import application modules
try:
    from services.settings_service import SettingsService
    from services.chat_service import ChatService
    HAS_APP_MODULES = True
except ImportError:
    HAS_APP_MODULES = False

def setup_automatic_conversion():
    """
    Set up automatic conversion of .dat files whenever they are saved.
    This function hooks into the existing application flow without disrupting it.
    """
    base_dir = Path(__file__).parent.parent
    appdata_dir = base_dir / 'appdata'
    
    # Initial conversion of existing files
    print("Setting up automatic .dat to .json conversion...")
    file_times = watch_dat_files(appdata_dir)
    print(f"Watching {len(file_times)} .dat files for changes")
    
    # Return the file times dictionary for later comparison
    return file_times

def integrate_with_settings_service():
    """
    Demonstrates how to integrate with the SettingsService
    to automatically convert settings when they are saved.
    """
    if not HAS_APP_MODULES:
        print("Application modules not available. Skipping integration demo.")
        return
    
    # Get reference to the original save_settings method
    original_save_settings = SettingsService.save_settings
    
    # Create a wrapper function that calls the original and then converts to JSON
    def save_settings_wrapper(self, *args, **kwargs):
        # Call the original method
        result = original_save_settings(self, *args, **kwargs)
        
        # After saving, convert to JSON using the encrypted converter
        settings_path = Path(self.settings_file)
        json_path = Path(__file__).parent / f"{settings_path.stem}.json"
        convert_encrypted_dat_to_json(settings_path, json_path)
        
        return result
    
    # Replace the original method with our wrapper
    SettingsService.save_settings = save_settings_wrapper
    print("Integrated with SettingsService - .dat files will be automatically converted to JSON")

def integrate_with_chat_service():
    """
    Demonstrates how to integrate with the ChatService
    to automatically convert chat history when it's saved.
    """
    if not HAS_APP_MODULES:
        print("Application modules not available. Skipping integration demo.")
        return
    
    # Get reference to the original save_history method
    original_save_history = ChatService.save_history
    
    # Create a wrapper function that calls the original and then converts to JSON
    def save_history_wrapper(self, *args, **kwargs):
        # Call the original method
        result = original_save_history(self, *args, **kwargs)
        
        # After saving, convert to JSON
        # Try encrypted first, fall back to regular conversion
        history_path = Path(self.history_file)
        json_path = Path(__file__).parent / f"{history_path.stem}.json"
        
        try:
            convert_encrypted_dat_to_json(history_path, json_path)
        except Exception:
            # Fall back to standard conversion
            convert_dat_to_json(history_path, json_path, background=False)
        
        return result
    
    # Replace the original method with our wrapper
    ChatService.save_history = save_history_wrapper
    print("Integrated with ChatService - .dat files will be automatically converted to JSON")

def manual_conversion():
    """
    Manually convert all .dat files to JSON.
    """
    base_dir = Path(__file__).parent.parent
    appdata_dir = base_dir / 'appdata'
    medium_dir = Path(__file__).parent
    
    print("Converting existing .dat files to JSON format...")
    
    # Handle settings.dat with encrypted converter
    settings_dat = appdata_dir / 'settings.dat'
    if settings_dat.exists():
        settings_json = medium_dir / 'settings.json'
        success = convert_encrypted_dat_to_json(settings_dat, settings_json)
        if success:
            print(f"Successfully converted encrypted {settings_dat.name} to {settings_json.name}")
        else:
            print(f"Failed to convert encrypted {settings_dat.name}")
    
    # Try to handle other .dat files with both methods
    for dat_file in appdata_dir.glob('*.dat'):
        if dat_file.name == 'settings.dat':
            continue  # Already processed
            
        json_file = medium_dir / f"{dat_file.stem}.json"
        
        # Try encrypted first, then regular conversion
        try:
            success = convert_encrypted_dat_to_json(dat_file, json_file)
            if success:
                print(f"Successfully converted {dat_file.name} using encrypted converter")
                continue
        except Exception:
            pass
            
        # Fall back to regular conversion
        json_path = convert_dat_to_json(dat_file, json_file, background=False)
        if json_path:
            print(f"Successfully converted {dat_file.name} using standard converter")
        else:
            print(f"Failed to convert {dat_file.name}")

if __name__ == "__main__":
    print("DAT to JSON Integration Example")
    print("-" * 50)
    
    # Choose integration method based on availability of modules
    if HAS_APP_MODULES:
        print("Application modules detected - demonstrating integration...")
        integrate_with_settings_service()
        integrate_with_chat_service()
    else:
        print("Application modules not found - using standalone conversion...")
        manual_conversion()
    
    # Set up automatic conversion for future changes
    file_times = setup_automatic_conversion()
    
    print("-" * 50)
    print("Integration complete!")
    print("All .dat files will now be automatically converted to JSON format")
    print("JSON files are saved in the 'medium' directory")
    
    # If run as standalone script, exit here
    if not HAS_APP_MODULES:
        sys.exit(0)
    
    # If integrated with the application, we can continue normal execution
    print("Continuing with normal application flow...") 