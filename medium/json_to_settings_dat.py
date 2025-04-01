#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JSON to Settings DAT Converter

This script converts a settings.json file back to an encrypted settings.dat file
that can be used by the Spring Test App. It uses the same encryption keys and methods
as the application itself.

This allows users to edit settings in JSON format and then convert back to the
application's native format.
"""

import os
import json
import base64
import logging
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Same constants as in settings_service.py
APP_SALT = b'SpringTestApp_2025_Salt_Value'
APP_PASSWORD = b'SpringTestApp_Secure_Password_2025'

def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

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

def encrypt_settings_json(json_path, dat_path):
    """
    Encrypt a settings.json file to a settings.dat file.
    
    Args:
        json_path (str or Path): Path to the settings.json file
        dat_path (str or Path): Path where the encrypted .dat file will be saved
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    json_path = Path(json_path)
    dat_path = Path(dat_path)
    
    # Ensure the target directory exists
    os.makedirs(dat_path.parent, exist_ok=True)
    
    try:
        # Read JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            settings_data = json.load(f)
        
        # Check if this is a valid settings file
        if not isinstance(settings_data, dict):
            logging.error("Invalid settings.json format: root must be a dictionary/object")
            return False
        
        # Check for required keys
        required_keys = ["api_key", "spring_specification"]
        missing_keys = [key for key in required_keys if key not in settings_data]
        if missing_keys:
            logging.warning(f"Settings file is missing required keys: {', '.join(missing_keys)}")
            logging.warning("The application may not work correctly with these settings")
        
        # Convert to JSON string
        settings_json = json.dumps(settings_data)
        
        # Encrypt data
        fernet = Fernet(generate_key())
        encrypted_data = fernet.encrypt(settings_json.encode('utf-8'))
        
        # Write encrypted data to file
        with open(dat_path, 'wb') as f:
            f.write(encrypted_data)
        
        logging.info(f"Successfully encrypted and converted {json_path} to {dat_path}")
        
        # Check if there are set points to log
        if "spring_specification" in settings_data and "set_points" in settings_data["spring_specification"]:
            set_points = settings_data["spring_specification"]["set_points"]
            logging.info(f"Settings contain {len(set_points)} set points")
        
        return True
    
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error converting settings.json to settings.dat: {str(e)}")
        return False

def main():
    """Main entry point for the script."""
    setup_logging()
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    appdata_dir = base_dir / 'appdata'
    medium_dir = base_dir / 'medium'
    
    settings_json = medium_dir / 'settings.json'
    settings_dat = appdata_dir / 'settings.dat'
    
    if not settings_json.exists():
        logging.error(f"Settings JSON file not found at {settings_json}")
        return 1
    
    # Check if settings.dat already exists and create a backup if it does
    if settings_dat.exists():
        backup_path = settings_dat.with_suffix('.dat.bak')
        logging.info(f"Creating backup of existing settings.dat at {backup_path}")
        try:
            with open(settings_dat, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
        except Exception as e:
            logging.error(f"Failed to create backup: {str(e)}")
            return 1
    
    # Convert JSON to DAT
    success = encrypt_settings_json(settings_json, settings_dat)
    
    if success:
        logging.info("Conversion complete. The application can now use the updated settings.dat file.")
        return 0
    else:
        logging.error("Conversion failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 