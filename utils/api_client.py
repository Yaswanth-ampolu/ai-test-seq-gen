"""
API client module for the Spring Test App.
Contains functions for making API requests to Together.ai and handling responses.
"""

# This file now serves as a wrapper to maintain compatibility
# while ensuring Together.ai is the only API integration used

from utils.together_api_client import TogetherAPIClient as APIClient
from utils.together_api_client import TogetherAPIClientWorker as APIClientWorker

# Re-export the Together.ai client as the main API client
__all__ = ['APIClient', 'APIClientWorker'] 