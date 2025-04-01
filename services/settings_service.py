"""
Settings service for the Spring Test App.
Contains functions for saving and loading application settings.
"""
import os
import json
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from models.data_models import SpringSpecification, SetPoint
import pickle

# Default settings
DEFAULT_SETTINGS = {
    "api_key": "",
    "default_export_format": "CSV",
    "recent_sequences": [],
    "max_chat_history": 100,
    "spring_specification": None
}

# App salt for encryption (do not change)
APP_SALT = b'SpringTestApp_2025_Salt_Value'
# App encryption key derivation password
APP_PASSWORD = b'SpringTestApp_Secure_Password_2025'

class SettingsService:
    """Service for managing application settings."""
    
    def __init__(self):
        """Initialize the settings service."""
        # Set up default settings
        self.settings = {
            "api_key": "",
            "theme": "light",
            "spring_specification": None
        }
        
        # Path to settings file
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appdata")
        self.settings_file = os.path.join(data_dir, "settings.dat")
        
        # Create the appdata directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load settings from file
        self.load_settings()
        
        # Initialize spring specification if it doesn't exist
        if "spring_specification" not in self.settings or self.settings["spring_specification"] is None:
            self.settings["spring_specification"] = SpringSpecification().to_dict()
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists.
        
        Returns:
            Path to the data directory.
        """
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appdata")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            # Create .gitignore to prevent accidental commit of sensitive data
            with open(os.path.join(data_dir, ".gitignore"), "w") as f:
                f.write("# Ignore all files in this directory\n*\n!.gitignore\n")
        return data_dir
    
    def _generate_key(self):
        """Generate encryption key from app password.
        
        Returns:
            Encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=APP_SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(APP_PASSWORD))
        return key
    
    def load_settings(self):
        """Load settings from file."""
        if not os.path.exists(self.settings_file):
            logging.info("Settings file not found, using defaults")
            return
        
        try:
            # Read encrypted data
            with open(self.settings_file, "rb") as f:
                encrypted_data = f.read()
            
            # Decrypt data
            fernet = Fernet(self._generate_key())
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse JSON
            loaded_settings = json.loads(decrypted_data.decode('utf-8'))
            
            # Update settings with loaded values
            self.settings.update(loaded_settings)
            
            # Log loaded settings details
            spec_info = ""
            if "spring_specification" in loaded_settings:
                spec_dict = loaded_settings["spring_specification"]
                set_points = spec_dict.get("set_points", [])
                spec_info = f" with {len(set_points)} set points"
            
            logging.info(f"Settings loaded successfully{spec_info}")
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Save settings to disk.
        
        Returns:
            True if settings were saved successfully, False otherwise.
        """
        try:
            # Ensure the settings directory exists
            data_dir = os.path.dirname(self.settings_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Log what's being saved
            spec_info = ""
            if "spring_specification" in self.settings:
                spec_dict = self.settings["spring_specification"]
                set_points = spec_dict.get("set_points", [])
                spec_info = f" with {len(set_points)} set points"
            
            # Convert settings to JSON
            settings_json = json.dumps(self.settings, indent=2)
            
            # Encrypt data
            fernet = Fernet(self._generate_key())
            encrypted_data = fernet.encrypt(settings_json.encode('utf-8'))
            
            # Write encrypted data
            with open(self.settings_file, "wb") as f:
                f.write(encrypted_data)
            
            logging.info(f"Settings saved successfully{spec_info}")
            return True
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            return False
    
    def get_api_key(self):
        """Get the API key.
        
        Returns:
            The API key.
        """
        return self.settings.get("api_key", "")
    
    def set_api_key(self, api_key):
        """Set the API key.
        
        Args:
            api_key: The API key to set.
        """
        self.settings["api_key"] = api_key
        self.save_settings()
    
    def get_default_export_format(self):
        """Get the default export format.
        
        Returns:
            The default export format.
        """
        return self.settings.get("default_export_format", "CSV")
    
    def set_default_export_format(self, format):
        """Set the default export format.
        
        Args:
            format: The format to use.
        """
        self.settings["default_export_format"] = format
        self.save_settings()
    
    def add_recent_sequence(self, sequence_id):
        """Add a sequence to the recent sequences list.
        
        Args:
            sequence_id: The ID of the sequence to add.
        """
        recent = self.settings.get("recent_sequences", [])
        
        # Remove the sequence if it already exists
        if sequence_id in recent:
            recent.remove(sequence_id)
        
        # Add to the beginning of the list
        recent.insert(0, sequence_id)
        
        # Limit the list to 10 items
        self.settings["recent_sequences"] = recent[:10]
        self.save_settings()
    
    def get_recent_sequences(self):
        """Get the list of recent sequences.
        
        Returns:
            List of recent sequence IDs.
        """
        return self.settings.get("recent_sequences", [])
    
    def get_spring_specification(self):
        """Get the spring specification.
        
        Returns:
            The SpringSpecification object.
        """
        spec_dict = self.settings.get("spring_specification")
        
        if spec_dict:
            spec = SpringSpecification.from_dict(spec_dict)
            logging.info(f"Loaded spring specification with {len(spec.set_points)} set points")
            return spec
        else:
            # Return default specification with no default set points
            logging.info("No spring specification found in settings, returning empty default")
            return SpringSpecification(create_defaults=False)
    
    def set_spring_specification(self, specification):
        """Set the spring specification.
        
        Args:
            specification: The SpringSpecification object.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        # Ensure the specification has an 'enabled' attribute
        if not hasattr(specification, 'enabled'):
            logging.warning("Specification missing 'enabled' attribute, setting to True")
            specification.enabled = True
        
        # Save the specification to the settings
        self.settings["spring_specification"] = specification.to_dict()
        
        # Log the operation
        logging.info(f"Saving spring specification with {len(specification.set_points)} set points")
        
        # Save the settings to disk
        return self.save_settings()
    
    def update_spring_basic_info(self, part_name=None, part_number=None, part_id=None, 
                               free_length=None, coil_count=None, wire_dia=None, 
                               outer_dia=None, safety_limit=None, unit=None, enabled=None,
                               force_unit=None, test_mode=None, component_type=None, 
                               first_speed=None, second_speed=None, offer_number=None,
                               production_batch_number=None, part_rev_no_date=None,
                               material_description=None, surface_treatment=None,
                               end_coil_finishing=None):
        """Update the basic info of the spring specification.
        
        Args:
            part_name: Part name.
            part_number: Part number.
            part_id: Part ID.
            free_length: Free length.
            coil_count: Coil count.
            wire_dia: Wire diameter.
            outer_dia: Outer diameter.
            safety_limit: Safety limit.
            unit: Unit (mm or in).
            enabled: Whether spring specifications are enabled.
            force_unit: Force unit (N, lbf, kgf).
            test_mode: Test mode (Height, Force, Tension).
            component_type: Component type (Compression, Tension).
            first_speed: First speed value.
            second_speed: Second speed value.
            offer_number: Offer number.
            production_batch_number: Production batch number.
            part_rev_no_date: Part revision number or date.
            material_description: Material description.
            surface_treatment: Surface treatment.
            end_coil_finishing: End coil finishing.
            
        Returns:
            True if updated successfully, False otherwise.
        """
        # Get current specification
        specification = self.get_spring_specification()
        
        # Update fields that are provided
        if part_name is not None:
            specification.part_name = part_name
            print(f"Set part name: {part_name}")
        
        if part_number is not None:
            specification.part_number = part_number
            print(f"Set part number: {part_number}")
        
        if part_id is not None:
            specification.part_id = part_id
            print(f"Set part ID: {part_id}")
        
        if free_length is not None:
            specification.free_length_mm = free_length
            print(f"Set free length: {free_length}")
        
        if coil_count is not None:
            specification.coil_count = coil_count
            print(f"Set coil count: {coil_count}")
        
        if wire_dia is not None:
            specification.wire_dia_mm = wire_dia
            print(f"Set wire diameter: {wire_dia}")
        
        if outer_dia is not None:
            specification.outer_dia_mm = outer_dia
            print(f"Set outer diameter: {outer_dia}")
        
        if safety_limit is not None:
            specification.safety_limit_n = safety_limit
            print(f"Set safety limit: {safety_limit}")
        
        if unit is not None:
            specification.unit = unit
            print(f"Set unit: {unit}")
        
        if enabled is not None:
            specification.enabled = enabled
            print(f"Set enabled: {enabled}")
        
        # Update new fields that are provided
        if force_unit is not None:
            specification.force_unit = force_unit
            print(f"Set force unit: {force_unit}")
        
        if test_mode is not None:
            specification.test_mode = test_mode
            print(f"Set test mode: {test_mode}")
        
        if component_type is not None:
            specification.component_type = component_type
            print(f"Set component type: {component_type}")
        
        if first_speed is not None:
            specification.first_speed = first_speed
            print(f"Set first speed: {first_speed}")
        
        if second_speed is not None:
            specification.second_speed = second_speed
            print(f"Set second speed: {second_speed}")
        
        if offer_number is not None:
            specification.offer_number = offer_number
            print(f"Set offer number: {offer_number}")
        
        if production_batch_number is not None:
            specification.production_batch_number = production_batch_number
            print(f"Set production batch number: {production_batch_number}")
        
        if part_rev_no_date is not None:
            specification.part_rev_no_date = part_rev_no_date
            print(f"Set part revision: {part_rev_no_date}")
        
        if material_description is not None:
            specification.material_description = material_description
            print(f"Set material description: {material_description}")
        
        if surface_treatment is not None:
            specification.surface_treatment = surface_treatment
            print(f"Set surface treatment: {surface_treatment}")
        
        if end_coil_finishing is not None:
            specification.end_coil_finishing = end_coil_finishing
            print(f"Set end coil finishing: {end_coil_finishing}")
        
        # Save the updated specification
        return self.set_spring_specification(specification)
    
    def update_set_point(self, index, position, load, tolerance=10.0, enabled=True):
        """Update a set point in the spring specification.
        
        Args:
            index: Index of the set point to update.
            position: New position value (mm).
            load: New load value (N).
            tolerance: New tolerance value (%).
            enabled: Whether the set point is enabled.
            
        Returns:
            True if updated successfully, False otherwise.
        """
        print(f"Updating set point at index {index}: position={position}, load={load}, tolerance={tolerance}, enabled={enabled}")
        
        # Get current specification
        specification = self.get_spring_specification()
        
        # Print current set points count for debugging
        print(f"Current set points count: {len(specification.set_points)}")
        
        # Validate index
        if index < 0 or index >= len(specification.set_points):
            logging.error(f"Invalid set point index: {index}, max: {len(specification.set_points)-1}")
            return False
            
        # Convert inputs to appropriate types
        try:
            position = float(position)
            load = float(load)
            tolerance = float(tolerance)
        except (ValueError, TypeError) as e:
            logging.error(f"Error converting values for set point update: {e}")
            return False
            
        # Update the set point
        specification.set_points[index].position_mm = position
        specification.set_points[index].load_n = load
        specification.set_points[index].tolerance_pct = tolerance
        specification.set_points[index].enabled = enabled
        
        print(f"Updated set point {index}: {position}, {load}, {tolerance}")
        
        # Save the updated specification
        return self.set_spring_specification(specification)
    
    def clear_set_points(self):
        """Clear all set points from the current spring specification.
        
        Returns:
            True if cleared successfully, False otherwise.
        """
        # Get current specification
        specification = self.get_spring_specification()
        
        # Clear set points
        specification.set_points = []
        
        # Save the updated specification
        return self.set_spring_specification(specification)
    
    def delete_set_point(self, index):
        """Delete a set point from the spring specification.
        
        Args:
            index: Set point index (0-based)
        """
        spec = self.get_spring_specification()
        
        if 0 <= index < len(spec.set_points):
            spec.set_points.pop(index)
            self.set_spring_specification(spec)
        
        return spec
    
    def add_set_point(self):
        """Add a new set point to the spring specification."""
        spec = self.get_spring_specification()
        
        # Add a new set point with default values
        new_point = SetPoint(0.0, 0.0, 10.0, True)
        spec.set_points.append(new_point)
        
        print(f"Added new set point, total now: {len(spec.set_points)}")
        
        # Save the updated specification
        self.set_spring_specification(spec)
        
        # Return the updated specification
        return spec 