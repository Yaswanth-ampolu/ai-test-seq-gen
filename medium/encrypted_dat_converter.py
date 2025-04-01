#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Encrypted Settings DAT to JSON Converter

This script specifically handles the encrypted settings.dat files from the Spring Test App,
using the same encryption keys and methods as the application itself.

It converts only the settings.dat file to JSON format for easier viewing and editing.
"""

import os
import json
import base64
import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Same constants as in settings_service.py
APP_SALT = b'SpringTestApp_2025_Salt_Value'
APP_PASSWORD = b'SpringTestApp_Secure_Password_2025'

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return obj.__dict__
        return super().default(obj)

def generate_key():
    """Generate encryption key from app password.
    
    Returns:
        bytes: Encryption key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=APP_SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(APP_PASSWORD))
    return key

def decrypt_settings_dat(file_path):
    """
    Decrypt a settings.dat file using the application's encryption key.
    
    Args:
        file_path (Path): Path to the encrypted .dat file
        
    Returns:
        tuple: (decrypted_data, success_flag)
    """
    try:
        # Read encrypted data
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
        
        # Decrypt data
        fernet = Fernet(generate_key())
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Parse JSON
        settings = json.loads(decrypted_data.decode('utf-8'))
        
        return settings, True
    except Exception as e:
        print(f"Error decrypting settings file: {str(e)}")
        return None, False

def convert_settings_dat_to_json(dat_path, json_path):
    """
    Convert an encrypted settings.dat file to .json format.
    
    Args:
        dat_path (str or Path): Path to the settings.dat file
        json_path (str or Path): Path where the JSON file will be saved
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    dat_path = Path(dat_path)
    json_path = Path(json_path)
    
    try:
        # Try to decrypt the file
        data, success = decrypt_settings_dat(dat_path)
        
        if not success or data is None:
            print(f"Could not decrypt {dat_path}")
            # Fall back to storing binary data
            with open(dat_path, 'rb') as f:
                binary_data = f.read()
                
            # Create a fallback dictionary with metadata and base64 content
            data = {
                "_conversion_error": True,
                "_error_message": "Settings data could not be decrypted properly",
                "_file_name": dat_path.name,
                "_file_size_bytes": len(binary_data),
                "_file_modified": datetime.datetime.fromtimestamp(dat_path.stat().st_mtime).isoformat(),
                "_binary_data_base64": base64.b64encode(binary_data).decode('utf-8'),
                "_encryption_note": "This file appears to be encrypted with a different key or method"
            }
        
        # Save the data to JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DateTimeEncoder, indent=4, ensure_ascii=False)
        
        if success:
            print(f"Successfully decrypted and converted settings.dat to {json_path}")
        else:
            print(f"Created binary representation of settings.dat (decryption failed)")
        
        return True
    
    except Exception as e:
        print(f"Error processing settings.dat: {str(e)}")
        return False

def process_settings_file():
    """
    Process the settings.dat file in the appdata directory and convert it to JSON.
    """
    base_dir = Path(__file__).parent.parent
    appdata_dir = base_dir / 'appdata'
    medium_dir = base_dir / 'medium'
    
    # Ensure medium directory exists
    os.makedirs(medium_dir, exist_ok=True)
    
    # Process settings.dat (known to be encrypted)
    settings_dat = appdata_dir / 'settings.dat'
    if settings_dat.exists():
        settings_json = medium_dir / 'settings.json'
        if convert_settings_dat_to_json(settings_dat, settings_json):
            print(f"Settings conversion complete: {settings_dat} → {settings_json}")
        else:
            print(f"Failed to convert settings.dat")
    else:
        print(f"Settings file not found at {settings_dat}")

if __name__ == "__main__":
    print("Processing encrypted settings.dat file...")
    process_settings_file()
    print("Processing complete.") 