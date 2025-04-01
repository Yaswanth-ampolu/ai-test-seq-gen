"""
Check Set Points Utility.
This script checks and displays the current spring specifications and set points.
"""
import os
import sys
import logging
from services.settings_service import SettingsService

def main():
    """Check and display current spring specifications and set points."""
    try:
        # Set up basic logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        logging.info("Checking current spring specifications...")
        
        # Create settings service
        settings_service = SettingsService()
        
        # Get current specification
        spec = settings_service.get_spring_specification()
        
        # Display basic info
        logging.info(f"Spring Specification:")
        logging.info(f"  Part Name: {spec.part_name}")
        logging.info(f"  Part Number: {spec.part_number}")
        logging.info(f"  Part ID: {spec.part_id}")
        logging.info(f"  Free Length: {spec.free_length_mm} mm")
        logging.info(f"  Coil Count: {spec.coil_count}")
        logging.info(f"  Wire Diameter: {spec.wire_dia_mm} mm")
        logging.info(f"  Outer Diameter: {spec.outer_dia_mm} mm")
        logging.info(f"  Safety Limit: {spec.safety_limit_n} N")
        logging.info(f"  Unit: {spec.unit}")
        logging.info(f"  Enabled: {spec.enabled}")
        
        # Display set points
        logging.info(f"Set Points: {len(spec.set_points)}")
        if spec.set_points:
            for i, sp in enumerate(spec.set_points):
                logging.info(f"  Set Point {i+1}:")
                logging.info(f"    Position: {sp.position_mm} mm")
                logging.info(f"    Load: {sp.load_n} N")
                logging.info(f"    Tolerance: {sp.tolerance_percent}%")
                logging.info(f"    Enabled: {sp.enabled}")
        else:
            logging.warning("  No set points found!")
            
        logging.info("Check complete!")
        
        return 0
    except Exception as e:
        logging.error(f"Error checking specifications: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 