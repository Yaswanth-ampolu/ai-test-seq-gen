"""
Reset Spring Specifications Tool.
Use this script to completely reset all spring specifications and remove all set points.
"""
import os
import sys
import logging
from services.settings_service import SettingsService
from models.data_models import SpringSpecification

def main():
    """Reset spring specifications to default values and clear all set points."""
    try:
        # Set up basic logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        logging.info("Completely resetting spring specifications and clearing all set points...")
        
        # Create settings service
        settings_service = SettingsService()
        
        # Create default spring specification with no default set points
        default_spec = SpringSpecification(create_defaults=False)
        
        # Log confirmation
        logging.info("Created new specification with no set points")
        
        # Set it in the settings service
        settings_service.set_spring_specification(default_spec)
        
        logging.info("Reset complete. All specifications have been reset to default values.")
        logging.info("All set points have been removed.")
        logging.info("You can now restart the application to see the changes.")
        
        return 0
    except Exception as e:
        logging.error(f"Error resetting specifications: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 