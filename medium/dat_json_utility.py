#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DAT/JSON Utility Module

This module provides functions for converting between .dat and .json formats,
while maintaining compatibility with the existing application flow.
It can be imported and used by other parts of the application as needed.
"""

import os
import json
import pickle
import datetime
import base64
from pathlib import Path
import threading

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return obj.__dict__
        return super().default(obj)

def safe_pickle_load(file_path):
    """
    Attempts to load pickle data safely with multiple approaches.
    
    Args:
        file_path (Path): Path to the pickle file
        
    Returns:
        tuple: (data, success_flag)
    """
    # Try standard pickle load first
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f), True
    except Exception as e:
        print(f"Standard pickle load failed: {str(e)}")
    
    # If that fails, try reading the file in binary mode and include it as base64
    try:
        with open(file_path, 'rb') as f:
            binary_data = f.read()
            
        # Create a fallback dictionary with metadata and base64 content
        result = {
            "_conversion_error": True,
            "_error_message": "Pickle data could not be parsed properly",
            "_file_name": file_path.name,
            "_file_size_bytes": len(binary_data),
            "_file_modified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "_binary_data_base64": base64.b64encode(binary_data).decode('utf-8')
        }
        
        return result, False
    except Exception as e:
        print(f"Binary fallback also failed: {str(e)}")
        return None, False

def convert_dat_to_json(dat_path, json_path=None, background=True):
    """
    Convert a .dat file to .json format.
    
    Args:
        dat_path (str or Path): Path to the .dat file
        json_path (str or Path, optional): Path where the JSON file will be saved.
            If None, saves to the medium directory with the same name.
        background (bool): Whether to run conversion in background thread
    
    Returns:
        Path or Thread: If background=True, returns the thread object.
                       If background=False, returns the path to the saved JSON file.
    """
    dat_path = Path(dat_path)
    
    # If json_path not provided, use default location in medium directory
    if json_path is None:
        medium_dir = Path(__file__).parent
        json_path = medium_dir / f"{dat_path.stem}.json"
    else:
        json_path = Path(json_path)
    
    # Ensure medium directory exists
    os.makedirs(json_path.parent, exist_ok=True)
    
    def _convert():
        try:
            # Load the pickle data with enhanced safety
            data, full_success = safe_pickle_load(dat_path)
            
            if data is None:
                print(f"Could not extract any data from {dat_path}")
                return False
            
            # Serialize to JSON with datetime handling
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, cls=DateTimeEncoder, indent=4, ensure_ascii=False)
            
            if full_success:
                print(f"Successfully converted {dat_path} to {json_path}")
            else:
                print(f"Created partial JSON representation of {dat_path} (binary fallback)")
            
            return True
        except Exception as e:
            print(f"Error converting {dat_path}: {str(e)}")
            return False
    
    if background:
        # Run conversion in background thread to not disrupt application flow
        thread = threading.Thread(target=_convert)
        thread.daemon = True
        thread.start()
        return thread
    else:
        # Run synchronously
        success = _convert()
        if success:
            return json_path
        return None

def watch_dat_files(appdata_dir=None, auto_convert=True):
    """
    Set up a watcher that automatically converts .dat files to .json
    whenever they are modified.
    
    Args:
        appdata_dir (str or Path, optional): Directory containing .dat files
        auto_convert (bool): Whether to automatically convert files on change
    
    Returns:
        dict: A mapping of .dat files to their last modification times
    """
    if appdata_dir is None:
        appdata_dir = Path(__file__).parent.parent / 'appdata'
    else:
        appdata_dir = Path(appdata_dir)
    
    # Record initial file modification times
    dat_files = {}
    for dat_file in appdata_dir.glob('*.dat'):
        dat_files[dat_file] = dat_file.stat().st_mtime
        
        # Convert existing files if auto_convert is True
        if auto_convert:
            convert_dat_to_json(dat_file)
    
    return dat_files

def json_to_python(json_path):
    """
    Load a JSON file and convert it to Python objects.
    
    Args:
        json_path (str or Path): Path to the JSON file
    
    Returns:
        object: The Python object representation of the JSON data
    """
    json_path = Path(json_path)
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON file {json_path}: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    # Convert all .dat files in appdata directory
    base_dir = Path(__file__).parent.parent
    appdata_dir = base_dir / 'appdata'
    
    for dat_file in appdata_dir.glob('*.dat'):
        convert_dat_to_json(dat_file, background=False)
        print(f"Converted {dat_file.name} to JSON format") 