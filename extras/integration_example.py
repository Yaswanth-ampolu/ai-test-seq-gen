#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Together.ai API Integration Example

This script demonstrates how to use the Together.ai API in the Spring Test App.
This is the primary API integration for the application.
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add parent directory to path so we can import from the application
sys.path.insert(0, str(Path(__file__).parent))

# Import utilities and services
from utils.together_api_client import TogetherAPIClient as APIClient
from utils.constants import API_ENDPOINT, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from services.settings_service import SettingsService

def demonstrate_together_api():
    """
    Demonstrate how to use the Together.ai API client.
    """
    # Create settings service to store API key
    settings_service = SettingsService()
    
    # Create Together.ai API client
    api_client = APIClient()
    
    # Get API key from environment or prompt user
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        api_key = input("Enter your Together.ai API key: ")
    
    # Set API key
    api_client.set_api_key(api_key)
    settings_service.set_api_key(api_key)
    
    # Validate API key
    is_valid, message = api_client.validate_api_key()
    print(f"API key validation: {message}")
    
    if not is_valid:
        print("Exiting due to invalid API key")
        return
    
    # Example query
    print("\nGenerating a simple test sequence...")
    parameters = {
        "prompt": "Generate a test sequence for a compression spring with free length 50mm and wire diameter 2mm",
        "Test Type": "Compression"
    }
    
    # Call the API and get the response
    df, error = api_client.generate_sequence(parameters)
    
    if error:
        print(f"Error: {error}")
        return
    
    # Display the response
    chat_rows = df[df["Row"] == "CHAT"]
    if not chat_rows.empty:
        print("\nChat response:")
        print(chat_rows["Description"].values[0])
    
    # Display sequence (excluding chat rows)
    sequence_rows = df[df["Row"] != "CHAT"]
    if not sequence_rows.empty:
        print("\nGenerated sequence:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(sequence_rows)

def main():
    """Main function."""
    print("Together.ai API Integration Example")
    print("-" * 50)
    
    demonstrate_together_api()
    
    print("-" * 50)
    print("Integration example complete!")

if __name__ == "__main__":
    main() 