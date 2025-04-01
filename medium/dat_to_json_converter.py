#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DAT to JSON Converter

This script converts .dat files from the appdata directory to JSON format and saves them
in the medium directory. It preserves the original data structure and does not
interfere with the application's regular operation.
"""

import os
import json
import pickle
import datetime
import struct
from pathlib import Path
import base64

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
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

def dat_to_json(dat_path, json_path):
    """
    Convert a .dat file to .json format.
    
    Args:
        dat_path (str): Path to the .dat file
        json_path (str): Path where the JSON file will be saved
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
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

def convert_all_dat_files():
    """
    Convert all .dat files in the appdata directory to JSON and save them
    in the medium directory.
    """
    # Define paths
    base_dir = Path(__file__).parent.parent
    appdata_dir = base_dir / 'appdata'
    medium_dir = base_dir / 'medium'
    
    # Ensure medium directory exists
    os.makedirs(medium_dir, exist_ok=True)
    
    # Process all .dat files
    dat_files = list(appdata_dir.glob('*.dat'))
    if not dat_files:
        print("No .dat files found in appdata directory.")
        return
    
    success_count = 0
    for dat_file in dat_files:
        # Create corresponding JSON filename
        json_file = medium_dir / f"{dat_file.stem}.json"
        
        # Convert the file
        if dat_to_json(dat_file, json_file):
            success_count += 1
    
    print(f"Conversion completed: {success_count}/{len(dat_files)} files converted successfully.")

if __name__ == "__main__":
    convert_all_dat_files() 