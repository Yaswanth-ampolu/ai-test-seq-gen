"""
Sample spring test sequence generator for testing.
"""
import pandas as pd
import json
import re
from datetime import datetime

class TestSequence:
    """Simple TestSequence class for testing purposes."""
    def __init__(self, rows, parameters):
        self.rows = rows
        self.parameters = parameters
        self.created_at = datetime.now()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "rows": self.rows,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat()
        }

def create_sample_sequence():
    """Create a sample test sequence for a compression spring."""
    # Sample rows
    rows = [
        {"Row": "R00", "CMD": "ZF", "Description": "Zero Force", "Condition": "", "Unit": "", "Tolerance": "", "Speed rpm": ""},
        {"Row": "R01", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": "", "Speed rpm": "10"},
        {"Row": "R02", "CMD": "FL(P)", "Description": "Measure Free Length-Position", "Condition": "", "Unit": "mm", "Tolerance": "58.0(57.9,58.1)", "Speed rpm": ""},
        {"Row": "R03", "CMD": "Mv(P)", "Description": "L1", "Condition": "40", "Unit": "mm", "Tolerance": "", "Speed rpm": "50"},
        {"Row": "R04", "CMD": "Fr(P)", "Description": "Force @ Position", "Condition": "", "Unit": "N", "Tolerance": "23.6(21.24,25.96)", "Speed rpm": ""},
        {"Row": "R05", "CMD": "Mv(P)", "Description": "L2", "Condition": "33", "Unit": "mm", "Tolerance": "", "Speed rpm": "50"},
        {"Row": "R06", "CMD": "Fr(P)", "Description": "Force @ Position", "Condition": "", "Unit": "N", "Tolerance": "34.14(30.73,37.55)", "Speed rpm": ""},
        {"Row": "R07", "CMD": "Mv(P)", "Description": "Move to Position", "Condition": "28", "Unit": "mm", "Tolerance": "", "Speed rpm": "50"},
        {"Row": "R08", "CMD": "Fr(P)", "Description": "Force @ Position", "Condition": "", "Unit": "N", "Tolerance": "42.36(38.12,46.6)", "Speed rpm": ""},
        {"Row": "R09", "CMD": "Scrag", "Description": "Scragging", "Condition": "R03,2", "Unit": "", "Tolerance": "", "Speed rpm": ""},
        {"Row": "R10", "CMD": "Mv(P)", "Description": "Move to Position", "Condition": "40", "Unit": "mm", "Tolerance": "", "Speed rpm": "50"},
        {"Row": "R11", "CMD": "Fr(P)", "Description": "Force @ Position", "Condition": "", "Unit": "N", "Tolerance": "23.6(21.24,25.96)", "Speed rpm": ""},
        {"Row": "R12", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": "", "Speed rpm": "10"},
        {"Row": "R13", "CMD": "FL(P)", "Description": "Measure Free Length-Position", "Condition": "", "Unit": "mm", "Tolerance": "58.0(57.9,58.1)", "Speed rpm": ""},
        {"Row": "R14", "CMD": "PMsg", "Description": "User Message", "Condition": "Test Complete", "Unit": "", "Tolerance": "", "Speed rpm": ""}
    ]
    
    # Sample parameters
    parameters = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": "Generate a test sequence for a compression spring",
        "Free Length": 58.0,
        "Wire Diameter": 3.0,
        "Outer Diameter": 32.0,
        "Test Type": "Compression",
        "chat_message": "Here's a standard compression test sequence for the spring with the specifications you provided. This sequence includes:\n\n1. Initial zeroing and contact detection\n2. Free length measurement with tolerance\n3. Compression to three different positions (L1, L2, and additional position)\n4. Force measurements at each position\n5. Scragging cycle to stabilize the spring\n6. Repeat measurements to verify performance after scragging\n7. Final free length verification\n\nThe tolerances are set to approximately ±10% for force measurements and ±0.1mm for length measurements."
    }
    
    # Create TestSequence
    sequence = TestSequence(
        rows=rows,
        parameters=parameters
    )
    
    return sequence

def print_sequence_as_chat_message():
    """Print the sample sequence in a format that can be pasted into the chat."""
    sequence = create_sample_sequence()
    
    # Generate the chat message format
    chat_message = sequence.parameters["chat_message"]
    
    # Format the sequence rows
    sequence_rows = []
    for row in sequence.rows:
        # Format each row as [R00, ZF, Zero Force, , , , ]
        row_values = []
        for field in ["Row", "CMD", "Description", "Condition", "Unit", "Tolerance", "Speed rpm"]:
            value = row[field]
            
            # Add double quotes around values containing commas to ensure proper parsing
            is_scrag_condition = (field == "Condition" and row["CMD"] == "Scrag" and 
                                  re.match(r'^R\d+,\d+$', str(value)) if value else False)
            
            if value and ("," in str(value) or is_scrag_condition):
                # Make sure we don't double-quote
                if not (str(value).startswith('"') and str(value).endswith('"')):
                    value = f'"{value}"'
            
            row_values.append(value)
        
        # Join the values with commas
        row_str = "[" + ", ".join([str(v) for v in row_values]) + "]"
        sequence_rows.append(row_str)
    
    # Join the rows
    sequence_text = "\n".join(sequence_rows)
    
    # Create the final message
    final_message = f"""{chat_message}

---SEQUENCE_DATA_START---
{sequence_text}
---SEQUENCE_DATA_END---

You can use this sequence directly with your spring testing machine. Let me know if you need any adjustments!"""
    
    print(final_message)

if __name__ == "__main__":
    print_sequence_as_chat_message() 