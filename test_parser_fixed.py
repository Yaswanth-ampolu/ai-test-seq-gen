"""
Test script for verifying CSV parsing improvements, particularly for Scrag commands.
"""
import re
import json

def test_parse_row(row_text):
    """
    Test the parsing of a row with the improved pattern matching.
    
    Args:
        row_text: A string representing a row (without brackets)
    
    Returns:
        List of parsed cells
    """
    print(f"Testing row: [{row_text}]")
    
    # Intelligently parse cells to handle commas within values
    cells = []
    current_cell = ""
    in_parentheses = False
    in_quotes = False
    cell_index = 0  # Track which cell position we're in
    found_scrag_cmd = False  # Flag to track if we've seen "Scrag" in the CMD position
    
    for char in row_text:
        if char == '"' and (len(current_cell) == 0 or current_cell[-1] != '\\'):
            # Toggle quote state (but not if escaped)
            in_quotes = not in_quotes
            current_cell += char
        elif char == '(' or char == '[':
            in_parentheses = True
            current_cell += char
        elif char == ')' or char == ']':
            in_parentheses = False
            current_cell += char
        elif char == ',' and not (in_parentheses or in_quotes):
            # Process the completed cell before deciding what to do with the comma
            completed_cell = current_cell.strip()
            
            # Check if we just processed the CMD cell and it's a Scrag command
            if cell_index == 1 and completed_cell == "Scrag":
                found_scrag_cmd = True
                print(f"DEBUG: Found Scrag command in CMD position")
            
            # Special case for Scrag command format "Rxx,y" in the Condition field (4th column)
            if (found_scrag_cmd and cell_index == 3 and 
                completed_cell and 
                (re.match(r'^"?R\d+$', completed_cell) or  # Pattern is "R" followed by digits (like R03)
                 re.match(r'^"?R\d+,\d*"?$', completed_cell))):  # Pattern already has comma (like R03,2)
                # This is a reference to another row in Scrag command, keep it intact
                current_cell += char
                print(f"DEBUG: Keeping comma in Scrag condition: {current_cell}")
                # Check if this is the second comma for Scrag
                if re.match(r'^"?R\d+,\d+$', current_cell.strip()):
                    # We've already got the full R03,2 pattern, next comma should be a separator
                    cells.append(current_cell.strip())
                    current_cell = ""
                    cell_index += 1
            else:
                # This comma is a cell separator
                cells.append(completed_cell)
                current_cell = ""
                cell_index += 1
        else:
            # This character is part of the current cell
            current_cell += char
    
    # Add the last cell
    cells.append(current_cell.strip())
    
    # Remove quotes around cells if present
    for i in range(len(cells)):
        if cells[i].startswith('"') and cells[i].endswith('"'):
            cells[i] = cells[i][1:-1]
        # Also clean up any trailing commas from Scrag commands
        if cells[i].endswith(","):
            cells[i] = cells[i][:-1]
    
    return cells

def run_tests():
    """Run tests for various row formats."""
    print("Starting test script for Scrag command parsing\n")
    
    # Test cases
    test_cases = [
        # Standard row without commas
        "R00, ZF, Zero Force, , , , ",
        
        # Row with quoted tolerance value containing commas
        'R02, FL(P), Measure Free Length-Position, , mm, "58.0(57.9,58.1)", ',
        
        # Row with Scrag condition with comma
        'R09, Scrag, Scragging, R03,2, , , ',
        
        # Row with quoted Scrag condition with comma
        'R09, Scrag, Scragging, "R03,2", , , ',
        
        # Row with tolerance with comma and Scrag with comma
        'R15, Scrag, Scragging with Tolerance, R03,2, N, "23.6(21.24,25.96)", '
    ]
    
    # Run the tests
    for test_case in test_cases:
        cells = test_parse_row(test_case)
        print(f"Parsed cells: {cells}")
        print(f"Number of cells: {len(cells)}")
        print()
    
    # Test creating a row dictionary for a Scrag command
    print("Creating Scrag row dictionary:")
    cells = test_parse_row("R09, Scrag, Scragging, R03,2, , , ")
    
    # Make sure we have exactly 7 cells
    while len(cells) < 7:
        cells.append("")
    
    # If we have too many cells, combine the extras
    if len(cells) > 7:
        cells = cells[:6] + [", ".join(cells[6:])]
    
    # Clean up the cells (remove trailing commas etc)
    for i in range(len(cells)):
        if cells[i].endswith(","):
            cells[i] = cells[i][:-1]
    
    # Create a row with the proper column names
    row = {
        "Row": cells[0],
        "CMD": cells[1],
        "Description": cells[2],
        "Condition": cells[3],
        "Unit": cells[4],
        "Tolerance": cells[5],
        "Speed rpm": cells[6]
    }
    
    print(f"Row dictionary: {json.dumps(row, indent=2)}")
    print("\nTest complete!")

if __name__ == "__main__":
    run_tests() 