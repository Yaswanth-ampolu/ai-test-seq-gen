"""
Data models module for the Spring Test App.
Contains classes for chat messages and other data structures.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class ChatMessage:
    """Represents a single chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the chat message to a dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create a ChatMessage instance from a dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        )


@dataclass
class TestSequence:
    """Represents a generated test sequence with metadata."""
    rows: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the test sequence to a dictionary."""
        return {
            "rows": self.rows,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSequence':
        """Create a TestSequence instance from a dictionary."""
        return cls(
            rows=data["rows"],
            parameters=data["parameters"],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            name=data.get("name")
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the test sequence to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestSequence':
        """Create a TestSequence instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class SetPoint:
    """Represents a set point for spring testing."""
    position_mm: float
    load_n: float
    tolerance_percent: float = 10.0
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the set point to a dictionary."""
        return {
            "position_mm": self.position_mm,
            "load_n": self.load_n,
            "tolerance_percent": self.tolerance_percent,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SetPoint':
        """Create a SetPoint instance from a dictionary."""
        return cls(
            position_mm=data.get("position_mm", 0.0),
            load_n=data.get("load_n", 0.0),
            tolerance_percent=data.get("tolerance_percent", 10.0),
            enabled=data.get("enabled", True)
        )


@dataclass
class SpringSpecification:
    """Specifications for a spring to be tested."""
    part_name: str = ""
    part_number: str = ""
    part_id: int = 0
    free_length_mm: float = 0.0
    coil_count: float = 0.0
    wire_dia_mm: float = 0.0
    outer_dia_mm: float = 0.0
    set_points: List[SetPoint] = field(default_factory=list)
    safety_limit_n: float = 0.0
    unit: str = "mm"  # Displacement unit: mm or inch
    enabled: bool = False
    create_defaults: bool = False  # Whether to create default set points

    # New fields
    force_unit: str = "N" # N, lbf, kgf
    test_mode: str = "Height Mode" # Height Mode, Deflection Mode, Tension Mode
    component_type: str = "Compression" # Compression, Tension
    first_speed: float = 0.0
    second_speed: float = 0.0
    offer_number: str = ""
    production_batch_number: str = ""
    part_rev_no_date: str = ""
    material_description: str = ""
    surface_treatment: str = ""
    end_coil_finishing: str = ""

    def __post_init__(self):
        """Initialize default set points if none are provided and create_defaults is True."""
        if not self.set_points and self.create_defaults:
            self.set_points = [
                SetPoint(40.0, 23.6),
                SetPoint(33.0, 34.14),
                SetPoint(28.0, 42.36)
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the spring specification to a dictionary."""
        result = {
            "part_name": self.part_name,
            "part_number": self.part_number,
            "part_id": self.part_id,
            "free_length_mm": self.free_length_mm,
            "coil_count": self.coil_count,
            "wire_dia_mm": self.wire_dia_mm,
            "outer_dia_mm": self.outer_dia_mm,
            "set_points": [sp.to_dict() for sp in self.set_points],
            "safety_limit_n": self.safety_limit_n,
            "unit": self.unit,
            "enabled": self.enabled,
            "create_defaults": self.create_defaults,
            # New fields
            "force_unit": self.force_unit,
            "test_mode": self.test_mode,
            "component_type": self.component_type,
            "first_speed": self.first_speed,
            "second_speed": self.second_speed,
            "offer_number": self.offer_number,
            "production_batch_number": self.production_batch_number,
            "part_rev_no_date": self.part_rev_no_date,
            "material_description": self.material_description,
            "surface_treatment": self.surface_treatment,
            "end_coil_finishing": self.end_coil_finishing
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpringSpecification':
        """Create a SpringSpecification instance from a dictionary."""
        try:
            # Extract create_defaults to control whether default set points will be created
            create_defaults = data.get("create_defaults", False)
            
            spec = cls(
                part_name=data.get("part_name", ""),
                part_number=data.get("part_number", ""),
                part_id=data.get("part_id", 0),
                free_length_mm=data.get("free_length_mm", 0.0),
                coil_count=data.get("coil_count", 0.0),
                wire_dia_mm=data.get("wire_dia_mm", 0.0),
                outer_dia_mm=data.get("outer_dia_mm", 0.0),
                set_points=[],  # Will be set below
                safety_limit_n=data.get("safety_limit_n", 0.0),
                unit=data.get("unit", "mm"),
                enabled=data.get("enabled", False),
                create_defaults=create_defaults,  # Pass the extracted value
                # New fields - use .get() for backward compatibility
                force_unit=data.get("force_unit", "N"),
                test_mode=data.get("test_mode", "Height Mode"),
                component_type=data.get("component_type", "Compression"),
                first_speed=data.get("first_speed", 0.0),
                second_speed=data.get("second_speed", 0.0),
                offer_number=data.get("offer_number", ""),
                production_batch_number=data.get("production_batch_number", ""),
                part_rev_no_date=data.get("part_rev_no_date", ""),
                material_description=data.get("material_description", ""),
                surface_treatment=data.get("surface_treatment", ""),
                end_coil_finishing=data.get("end_coil_finishing", "")
            )
            
            # Log what we're loading
            print(f"Loading SpringSpecification from dict: {data.get('part_name', '')}")
            
            # Set the set points if they exist in the data
            if "set_points" in data and isinstance(data["set_points"], list):
                # Count how many set points we have
                num_set_points = len(data["set_points"])
                print(f"Loading {num_set_points} set points from data")
                
                spec.set_points = [SetPoint.from_dict(sp) for sp in data["set_points"]]
                print(f"Successfully loaded {len(spec.set_points)} set points into specification")
            else:
                print("No set points found in data, keeping empty set")
            
            return spec
        except Exception as e:
            print(f"Error creating SpringSpecification from dict: {str(e)}")
            # Return a basic specification if parsing fails
            return cls(create_defaults=False)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the spring specification to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SpringSpecification':
        """Create a SpringSpecification instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def to_prompt_text(self) -> str:
        """Convert the spring specification to text for use in AI prompts."""
        text = f"Spring Specifications:\n"
        text += f"Part Name: {self.part_name}\n"
        text += f"Part Number: {self.part_number}\n"
        text += f"ID: {self.part_id}\n"
        text += f"Free Length: {self.free_length_mm} {self.unit}\n"
        text += f"No of Coils: {self.coil_count}\n"
        text += f"Wire Dia: {self.wire_dia_mm} {self.unit}\n"
        text += f"OD: {self.outer_dia_mm} {self.unit}\n"
        
        for i, sp in enumerate(self.set_points, 1):
            if sp.enabled:
                text += f"Set Point-{i} Position: {sp.position_mm} {self.unit}\n"
                text += f"Set Point-{i} Load: {sp.load_n}±{sp.tolerance_percent}% {self.force_unit}\n"
        
        text += f"Safety Limit: {self.safety_limit_n} {self.force_unit}\n"
        text += f"Displacement Unit: {self.unit}\n"
        text += f"Force Unit: {self.force_unit}\n"
        text += f"Test Mode: {self.test_mode}\n"
        text += f"Component Type: {self.component_type}\n"
        text += f"First Speed: {self.first_speed}\n"
        text += f"Second Speed: {self.second_speed}\n"
        text += f"Offer Number: {self.offer_number}\n"
        text += f"Production Batch Number: {self.production_batch_number}\n"
        text += f"Part Revision: {self.part_rev_no_date}\n"
        text += f"Material: {self.material_description}\n"
        text += f"Surface Treatment: {self.surface_treatment}\n"
        text += f"End Coil Finishing: {self.end_coil_finishing}\n"
        
        return text


@dataclass
class AppSettings:
    """Application settings that can be saved and loaded."""
    api_key: str = ""
    default_export_format: str = "CSV"
    recent_sequences: List[str] = field(default_factory=list)
    max_chat_history: int = 100
    spring_specification: Optional[SpringSpecification] = None
    
    def __post_init__(self):
        """Initialize default spring specification if none is provided."""
        if self.spring_specification is None:
            self.spring_specification = SpringSpecification()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the settings to a dictionary."""
        return {
            "api_key": self.api_key,
            "default_export_format": self.default_export_format,
            "recent_sequences": self.recent_sequences,
            "max_chat_history": self.max_chat_history,
            "spring_specification": self.spring_specification.to_dict() if self.spring_specification else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create an AppSettings instance from a dictionary."""
        spring_spec_data = data.get("spring_specification")
        spring_spec = SpringSpecification.from_dict(spring_spec_data) if spring_spec_data else None
        
        return cls(
            api_key=data.get("api_key", ""),
            default_export_format=data.get("default_export_format", "CSV"),
            recent_sequences=data.get("recent_sequences", []),
            max_chat_history=data.get("max_chat_history", 100),
            spring_specification=spring_spec
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the settings to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AppSettings':
        """Create an AppSettings instance from a JSON string."""
        return cls.from_dict(json.loads(json_str)) 