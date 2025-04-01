"""
Chat specification form module for handling spring specification forms in chat.
This module provides interactive forms for users to input specification data directly in the chat.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
                           QPushButton, QCheckBox, QFrame, QScrollArea,
                           QSizePolicy, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFont

class SpecificationFormSection(QGroupBox):
    """Base class for a section in the specification form."""
    
    # Define signals
    section_completed = pyqtSignal(dict)  # Data collected in this section
    section_cancelled = pyqtSignal()
    
    def __init__(self, title, parent=None):
        """Initialize the section widget.
        
        Args:
            title: Section title
            parent: Parent widget
        """
        super().__init__(title, parent)
        
        # Initialize UI
        self._init_ui()
        
        # Store collected data
        self.collected_data = {}
    
    def _init_ui(self):
        """Initialize the UI (to be implemented by subclasses)."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(15, 20, 15, 15)
        
        # Form layout
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.main_layout.addLayout(self.form_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(32)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        buttons_layout.addWidget(self.cancel_button)
        
        # Spacer
        buttons_layout.addStretch()
        
        # Continue button
        self.continue_button = QPushButton("Continue")
        self.continue_button.setMinimumHeight(32)
        self.continue_button.setCursor(Qt.PointingHandCursor)
        self.continue_button.clicked.connect(self.on_continue_clicked)
        buttons_layout.addWidget(self.continue_button)
        
        # Add buttons layout
        self.main_layout.addLayout(buttons_layout)
        
        # Set a fixed width for the form to make it more compact and centered
        self.setFixedWidth(400)
        
        # Apply styling to make it visually distinct in the chat
        self.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 8px;
                margin-top: 20px;
                font-weight: bold;
                color: #202124;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #1a73e8;
                font-size: 14px;
            }
            QPushButton {
                background-color: #f1f3f4;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 6px 16px;
                color: #202124;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e8eaed;
                border-color: #d2d5d9;
            }
            QPushButton:pressed {
                background-color: #dadce0;
            }
            QPushButton:disabled {
                color: #9aa0a6;
                background-color: #f1f3f4;
                border-color: #dadce0;
            }
            QDoubleSpinBox, QLineEdit {
                padding: 6px 8px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                background-color: white;
                min-height: 24px;
                selection-background-color: #e8f0fe;
            }
            QDoubleSpinBox:focus, QLineEdit:focus {
                border-color: #1a73e8;
                outline: none;
            }
            QComboBox {
                padding: 6px 8px;
                border: 1px solid #dadce0;
                border-radius: 4px;
                background-color: white;
                min-height: 24px;
                selection-background-color: #e8f0fe;
            }
            QComboBox:focus {
                border-color: #1a73e8;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border-left: none;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBkPSJNNyAxMGw1IDUgNS01eiIgZmlsbD0iIzVGNjM2OCIvPjwvc3ZnPg==);
            }
            QLabel {
                color: #202124;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        
        # Set continue button style to be more prominent
        self.continue_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1967d2;
            }
            QPushButton:pressed {
                background-color: #185abc;
            }
        """)
    
    def collect_data(self):
        """Collect data from the form (to be implemented by subclasses)."""
        pass
    
    def on_continue_clicked(self):
        """Handle continue button click."""
        # Collect data
        self.collect_data()
        
        # Emit signal with collected data
        self.section_completed.emit(self.collected_data)
    
    def on_cancel_clicked(self):
        """Handle cancel button click."""
        # Emit cancel signal
        self.section_cancelled.emit()

class BasicInfoSection(SpecificationFormSection):
    """Section for collecting basic spring information."""
    
    def __init__(self, parent=None):
        """Initialize the basic info section."""
        super().__init__("Basic Spring Information", parent)
        
        # Create form inputs
        self._create_form_inputs()
    
    def _create_form_inputs(self):
        """Create form inputs for basic info."""
        # Part number input
        self.part_number_input = QLineEdit()
        self.part_number_input.setMinimumWidth(120)
        self.part_number_input.setPlaceholderText("Enter part number")
        self.form_layout.addRow("Part Number:", self.part_number_input)
        
        # Part name input
        self.part_name_input = QLineEdit()
        self.part_name_input.setMinimumWidth(120)
        self.part_name_input.setPlaceholderText("Enter part name")
        self.form_layout.addRow("Part Name:", self.part_name_input)
        
        # Part ID input
        self.part_id_input = QLineEdit()
        self.part_id_input.setMinimumWidth(120)
        self.part_id_input.setPlaceholderText("Enter part ID")
        self.form_layout.addRow("Part ID:", self.part_id_input)
        
        # Free length input
        self.free_length_input = QDoubleSpinBox()
        self.free_length_input.setRange(0, 1000)
        self.free_length_input.setSuffix(" mm")
        self.free_length_input.setDecimals(2)
        self.free_length_input.setMinimumWidth(120)
        self.form_layout.addRow("Free Length:", self.free_length_input)
        
        # Component Type input
        self.component_type_input = QComboBox()
        self.component_type_input.addItems(["Compression", "Tension"])
        self.component_type_input.setMinimumWidth(120)
        self.form_layout.addRow("Component Type:", self.component_type_input)
        
        # Test Mode input
        self.test_mode_input = QComboBox()
        self.test_mode_input.addItems(["Height Mode", "Deflection Mode", "Tension Mode"])
        self.test_mode_input.setCurrentText("Height Mode")
        self.test_mode_input.setMinimumWidth(120)
        self.form_layout.addRow("Test Mode:", self.test_mode_input)
        
        # Displacement Unit input
        self.unit_input = QComboBox()
        self.unit_input.addItems(["mm", "inch"])
        self.unit_input.setCurrentText("mm")
        self.unit_input.setMinimumWidth(120)
        self.form_layout.addRow("Displacement Unit:", self.unit_input)
        
        # Force Unit input
        self.force_unit_input = QComboBox()
        self.force_unit_input.addItems(["N", "lbf", "kgf"])
        self.force_unit_input.setCurrentText("N")
        self.force_unit_input.setMinimumWidth(120)
        self.form_layout.addRow("Force Unit:", self.force_unit_input)
        
        # First Speed input
        self.first_speed_input = QDoubleSpinBox()
        self.first_speed_input.setRange(0, 1000)
        self.first_speed_input.setSuffix(" mm/s")
        self.first_speed_input.setDecimals(1)
        self.first_speed_input.setMinimumWidth(120)
        self.form_layout.addRow("First Speed:", self.first_speed_input)
        
        # Second Speed input
        self.second_speed_input = QDoubleSpinBox()
        self.second_speed_input.setRange(0, 1000)
        self.second_speed_input.setSuffix(" mm/s")
        self.second_speed_input.setDecimals(1)
        self.second_speed_input.setMinimumWidth(120)
        self.form_layout.addRow("Second Speed:", self.second_speed_input)
        
        # Safety limit input moved from optional to basic info
        self.safety_limit_input = QDoubleSpinBox()
        self.safety_limit_input.setRange(0, 10000)
        self.safety_limit_input.setDecimals(2)
        self.safety_limit_input.setSuffix(" N")
        self.safety_limit_input.setMinimumWidth(120)
        self.form_layout.addRow("Safety Limit:", self.safety_limit_input)
        
        # Add descriptive text
        description = QLabel("Enter the basic information about your spring that will be used for testing.")
        description.setStyleSheet("color: #5f6368; font-size: 12px; margin-top: 5px;")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        self.main_layout.insertWidget(0, description)
    
    def collect_data(self):
        """Collect data from the form."""
        self.collected_data = {
            "part_name": self.part_name_input.text(),
            "part_number": self.part_number_input.text(),
            "part_id": self.part_id_input.text(),
            "free_length": self.free_length_input.value(),
            "component_type": self.component_type_input.currentText(),
            "test_mode": self.test_mode_input.currentText(),
            "unit": self.unit_input.currentText(),
            "force_unit": self.force_unit_input.currentText(),
            "first_speed": self.first_speed_input.value(),
            "second_speed": self.second_speed_input.value(),
            "safety_limit": self.safety_limit_input.value(),
        }
        return self.collected_data

class OptionalInfoSection(SpecificationFormSection):
    """Section for collecting optional spring information."""
    
    def __init__(self, parent=None):
        """Initialize the optional info section."""
        super().__init__("Optional Information", parent)
        
        # Create form inputs
        self._create_form_inputs()
    
    def _create_form_inputs(self):
        """Create form inputs for optional info."""
        # Add descriptive text
        description = QLabel("These fields are optional and provide additional details about your spring.")
        description.setStyleSheet("color: #5f6368; font-size: 12px;")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        self.main_layout.insertWidget(0, description)
        
        # Coil count input
        self.coil_count_input = QDoubleSpinBox()
        self.coil_count_input.setRange(0, 100)
        self.coil_count_input.setDecimals(1)
        self.coil_count_input.setMinimumWidth(120)
        self.form_layout.addRow("Number of Coils:", self.coil_count_input)
        
        # Wire diameter input
        self.wire_dia_input = QDoubleSpinBox()
        self.wire_dia_input.setRange(0, 100)
        self.wire_dia_input.setSuffix(" mm")
        self.wire_dia_input.setDecimals(2)
        self.wire_dia_input.setMinimumWidth(120)
        self.form_layout.addRow("Wire Diameter:", self.wire_dia_input)
        
        # Outer diameter input
        self.outer_dia_input = QDoubleSpinBox()
        self.outer_dia_input.setRange(0, 500)
        self.outer_dia_input.setDecimals(2)
        self.outer_dia_input.setSuffix(" mm")
        self.outer_dia_input.setMinimumWidth(120)
        self.form_layout.addRow("Outer Diameter:", self.outer_dia_input)
        
        # Safety limit removed from here as it's now in basic info section
        
        # Additional fields
        self.offer_number_input = QLineEdit()
        self.offer_number_input.setMinimumWidth(120)
        self.offer_number_input.setPlaceholderText("Enter offer number")
        self.form_layout.addRow("Offer Number:", self.offer_number_input)
        
        self.production_batch_input = QLineEdit()
        self.production_batch_input.setMinimumWidth(120)
        self.production_batch_input.setPlaceholderText("Enter batch number")
        self.form_layout.addRow("Production Batch:", self.production_batch_input)
        
        self.part_rev_input = QLineEdit()
        self.part_rev_input.setMinimumWidth(120)
        self.part_rev_input.setPlaceholderText("Enter revision info")
        self.form_layout.addRow("Part Revision:", self.part_rev_input)
        
        self.material_input = QLineEdit()
        self.material_input.setMinimumWidth(120)
        self.material_input.setPlaceholderText("Enter material")
        self.form_layout.addRow("Material:", self.material_input)
        
        self.surface_treatment_input = QLineEdit()
        self.surface_treatment_input.setMinimumWidth(120)
        self.surface_treatment_input.setPlaceholderText("Enter treatment")
        self.form_layout.addRow("Surface Treatment:", self.surface_treatment_input)
        
        self.end_coil_input = QLineEdit()
        self.end_coil_input.setMinimumWidth(120)
        self.end_coil_input.setPlaceholderText("Enter finishing")
        self.form_layout.addRow("End Coil Finishing:", self.end_coil_input)
    
    def collect_data(self):
        """Collect data from the form."""
        self.collected_data = {
            "coil_count": self.coil_count_input.value(),
            "wire_dia": self.wire_dia_input.value(),
            "outer_dia": self.outer_dia_input.value(),
            # Safety limit removed from here
            "offer_number": self.offer_number_input.text(),
            "production_batch_number": self.production_batch_input.text(),
            "part_rev_no_date": self.part_rev_input.text(),
            "material_description": self.material_input.text(),
            "surface_treatment": self.surface_treatment_input.text(),
            "end_coil_finishing": self.end_coil_input.text(),
        }
        return self.collected_data

class SetPointSection(SpecificationFormSection):
    """Section for collecting set point information."""
    
    def __init__(self, parent=None, index=0):
        """Initialize the set point section."""
        super().__init__(f"Set Point {index+1}", parent)
        
        # Store index
        self.index = index
        
        # Create form inputs
        self._create_form_inputs()
    
    def _create_form_inputs(self):
        """Create form inputs for set point."""
        # Position input
        self.position_input = QDoubleSpinBox()
        self.position_input.setRange(0, 500)
        self.position_input.setDecimals(2)
        self.position_input.setSuffix(" mm")
        self.position_input.setMinimumWidth(120)
        self.form_layout.addRow("Position:", self.position_input)
        
        # Load input
        self.load_input = QDoubleSpinBox()
        self.load_input.setRange(0, 1000)
        self.load_input.setDecimals(2)
        self.load_input.setSuffix(" N")
        self.load_input.setMinimumWidth(120)
        self.form_layout.addRow("Load:", self.load_input)
        
        # Tolerance input
        self.tolerance_input = QDoubleSpinBox()
        self.tolerance_input.setRange(0, 100)
        self.tolerance_input.setValue(10.0)
        self.tolerance_input.setSuffix(" %")
        self.tolerance_input.setDecimals(1)
        self.tolerance_input.setMinimumWidth(120)
        self.form_layout.addRow("Tolerance:", self.tolerance_input)
        
        # Explanatory text
        explanation = QLabel("Position = height in mm, Load = force in N")
        explanation.setStyleSheet("color: #5f6368; font-size: 12px; margin-top: 5px;")
        explanation.setWordWrap(True)
        explanation.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(explanation)
        
        # Add another set point checkbox with improved layout
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 8, 0, 0)
        
        self.add_another_checkbox = QCheckBox("Add another set point after this one")
        self.add_another_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #202124;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        checkbox_layout.addWidget(self.add_another_checkbox)
        
        self.main_layout.addWidget(checkbox_container)
    
    def collect_data(self):
        """Collect data from the form."""
        self.collected_data = {
            "index": self.index,
            "position": self.position_input.value(),
            "load": self.load_input.value(),
            "tolerance": self.tolerance_input.value(),
            "add_another": self.add_another_checkbox.isChecked(),
        }
        return self.collected_data

class SpecificationFormManager(QWidget):
    """Manager for the specification form workflow."""
    
    # Define signals
    form_completed = pyqtSignal(dict)  # Completed form data
    form_cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the form manager."""
        super().__init__(parent)
        
        # Set up UI
        self._init_ui()
        
        # Track form data
        self.form_data = {
            "basic_info": {},
            "optional_info": {},
            "set_points": []
        }
        
        # Track current state
        self.current_section = None
        self.set_point_index = 0
        self.form_state = "init"  # init, basic, optional, set_point, complete
    
    def _init_ui(self):
        """Initialize the UI."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # Set initial size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setFixedWidth(420) # Container slightly wider than sections
        
        # Apply styling
        self.setStyleSheet("""
            SpecificationFormManager {
                background-color: transparent;
            }
        """)
    
    def start_form_workflow(self):
        """Start the form workflow."""
        # Reset form data
        self.form_data = {
            "basic_info": {},
            "optional_info": {},
            "set_points": []
        }
        
        # Reset state
        self.set_point_index = 0
        self.form_state = "basic"
        
        # Start with basic info
        self._show_basic_info_section()
    
    def _show_basic_info_section(self):
        """Show the basic info section."""
        # Clear current section if any
        self._clear_current_section()
        
        # Create and set up basic info section
        self.current_section = BasicInfoSection(self)
        self.current_section.section_completed.connect(self._on_basic_info_completed)
        self.current_section.section_cancelled.connect(self._on_form_cancelled)
        
        # Add to layout
        self.layout.addWidget(self.current_section, 0, Qt.AlignCenter)
        
        # Update state
        self.form_state = "basic"
    
    def _on_basic_info_completed(self, data):
        """Handle basic info section completion."""
        # Store data
        self.form_data["basic_info"] = data
        
        # Ask if they want to add optional info
        self._show_optional_confirmation()
    
    def _show_optional_confirmation(self):
        """Show confirmation for optional info section."""
        # Clear current section
        self._clear_current_section()
        
        # Create custom confirmation widget
        confirmation = QGroupBox("Optional Information")
        confirmation_layout = QVBoxLayout(confirmation)
        confirmation_layout.setContentsMargins(15, 20, 15, 15)
        confirmation_layout.setSpacing(15)
        
        # Add message
        message = QLabel("Would you like to add optional spring information?")
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 13px;")
        confirmation_layout.addWidget(message)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Skip button
        skip_button = QPushButton("Skip")
        skip_button.setMinimumHeight(32)
        skip_button.setCursor(Qt.PointingHandCursor)
        skip_button.clicked.connect(self._skip_optional_info)
        buttons_layout.addWidget(skip_button)
        
        # Spacer
        buttons_layout.addStretch()
        
        # Continue button
        continue_button = QPushButton("Add Optional Info")
        continue_button.setMinimumHeight(32)
        continue_button.setCursor(Qt.PointingHandCursor)
        continue_button.clicked.connect(self._show_optional_info_section)
        buttons_layout.addWidget(continue_button)
        
        # Style continue button
        continue_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                font-weight: bold;
                padding: 6px 16px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #1967d2;
            }
            QPushButton:pressed {
                background-color: #185abc;
            }
        """)
        
        confirmation_layout.addLayout(buttons_layout)
        
        # Apply styling to match other sections
        confirmation.setFixedWidth(400)
        confirmation.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 8px;
                margin-top: 20px;
                font-weight: bold;
                color: #202124;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #1a73e8;
                font-size: 14px;
            }
            QPushButton {
                background-color: #f1f3f4;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 6px 16px;
                color: #202124;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e8eaed;
                border-color: #d2d5d9;
            }
            QPushButton:pressed {
                background-color: #dadce0;
            }
        """)
        
        # Add to layout
        self.layout.addWidget(confirmation, 0, Qt.AlignCenter)
        self.current_section = confirmation
        
        # Update state
        self.form_state = "optional_confirm"
    
    def _skip_optional_info(self):
        """Skip optional info section."""
        # Proceed to set point confirmation
        self._show_set_point_confirmation()
    
    def _show_optional_info_section(self):
        """Show the optional info section."""
        # Clear current section
        self._clear_current_section()
        
        # Create and set up optional info section
        self.current_section = OptionalInfoSection(self)
        self.current_section.section_completed.connect(self._on_optional_info_completed)
        self.current_section.section_cancelled.connect(self._on_form_cancelled)
        
        # Add to layout
        self.layout.addWidget(self.current_section, 0, Qt.AlignCenter)
        
        # Update state
        self.form_state = "optional"
    
    def _on_optional_info_completed(self, data):
        """Handle optional info section completion."""
        # Store data
        self.form_data["optional_info"] = data
        
        # Proceed to set point confirmation
        self._show_set_point_confirmation()
    
    def _show_set_point_confirmation(self):
        """Show confirmation for set point section."""
        # Clear current section
        self._clear_current_section()
        
        # Create custom confirmation widget
        confirmation = QGroupBox("Set Points")
        confirmation_layout = QVBoxLayout(confirmation)
        confirmation_layout.setContentsMargins(15, 20, 15, 15)
        confirmation_layout.setSpacing(15)
        
        # Add message
        message = QLabel("Would you like to add set points for testing?")
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 13px;")
        confirmation_layout.addWidget(message)
        
        # Add explanation
        explanation = QLabel("Set points define specific positions and expected loads for your spring test sequence.")
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #5f6368; font-size: 12px; margin-top: -5px;")
        confirmation_layout.addWidget(explanation)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Skip button
        skip_button = QPushButton("Skip")
        skip_button.setMinimumHeight(32)
        skip_button.setCursor(Qt.PointingHandCursor)
        skip_button.clicked.connect(self._skip_set_points)
        buttons_layout.addWidget(skip_button)
        
        # Spacer
        buttons_layout.addStretch()
        
        # Continue button
        continue_button = QPushButton("Add Set Points")
        continue_button.setMinimumHeight(32)
        continue_button.setCursor(Qt.PointingHandCursor)
        continue_button.clicked.connect(self._show_set_point_section)
        buttons_layout.addWidget(continue_button)
        
        # Style continue button
        continue_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                font-weight: bold;
                padding: 6px 16px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1967d2;
            }
            QPushButton:pressed {
                background-color: #185abc;
            }
        """)
        
        confirmation_layout.addLayout(buttons_layout)
        
        # Apply styling to match other sections
        confirmation.setFixedWidth(400)
        confirmation.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 8px;
                margin-top: 20px;
                font-weight: bold;
                color: #202124;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #1a73e8;
                font-size: 14px;
            }
            QPushButton {
                background-color: #f1f3f4;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 6px 16px;
                color: #202124;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e8eaed;
                border-color: #d2d5d9;
            }
            QPushButton:pressed {
                background-color: #dadce0;
            }
        """)
        
        # Add to layout
        self.layout.addWidget(confirmation, 0, Qt.AlignCenter)
        self.current_section = confirmation
        
        # Update state
        self.form_state = "set_point_confirm"
    
    def _skip_set_points(self):
        """Skip set points."""
        # Finish the form
        self._complete_form()
    
    def _show_set_point_section(self):
        """Show the set point section."""
        # Clear current section
        self._clear_current_section()
        
        # Create and set up set point section
        self.current_section = SetPointSection(self, self.set_point_index)
        self.current_section.section_completed.connect(self._on_set_point_completed)
        self.current_section.section_cancelled.connect(self._on_form_cancelled)
        
        # Add to layout
        self.layout.addWidget(self.current_section, 0, Qt.AlignCenter)
        
        # Update state
        self.form_state = "set_point"
    
    def _on_set_point_completed(self, data):
        """Handle set point section completion."""
        # Store data
        self.form_data["set_points"].append(data)
        
        # Check if we should add another set point
        if data["add_another"]:
            # Increment index and show another set point section
            self.set_point_index += 1
            self._show_set_point_section()
        else:
            # Finish the form
            self._complete_form()
    
    def _complete_form(self):
        """Complete the form workflow."""
        # Clear current section
        self._clear_current_section()
        
        # Get summary data
        basic_info = self.form_data.get("basic_info", {})
        set_points = self.form_data.get("set_points", [])
        
        # Create completion message as HTML for better formatting
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #202124;
                    padding: 0;
                    margin: 0;
                    background-color: transparent;
                }}
                .container {{
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border: 1px solid #dadce0;
                }}
                h2 {{
                    color: #1a73e8;
                    margin-top: 0;
                    font-size: 16px;
                    font-weight: 600;
                }}
                .summary {{
                    background-color: white;
                    border-radius: 6px;
                    padding: 12px;
                    margin-bottom: 15px;
                    border: 1px solid #e8eaed;
                    font-size: 13px;
                }}
                .label {{
                    color: #5f6368;
                    font-weight: 500;
                }}
                .spacer {{
                    height: 15px;
                }}
                .btn {{
                    background-color: #1a73e8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 24px;
                    font-weight: bold;
                    cursor: pointer;
                    text-align: center;
                    display: block;
                    margin: 10px auto 0;
                    font-size: 14px;
                }}
                .btn:hover {{
                    background-color: #1967d2;
                }}
                .btn:active {{
                    background-color: #185abc;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Specifications Complete</h2>
                <div class="summary">
                    <div class="label">Part:</div> {basic_info.get('part_name', 'Not specified')}
                    <br>
                    <div class="label">Number:</div> {basic_info.get('part_number', 'Not specified')}
                    <br>
                    <div class="label">Free Length:</div> {basic_info.get('free_length', '0')} {basic_info.get('unit', 'mm')}
                    <br>
                    <div class="label">Set Points:</div> {len(set_points)}
                </div>
                <p style="margin: 0; font-size: 13px;">
                    All spring specifications have been collected. Click Done to update specifications and continue.
                </p>
                <button id="done-btn" class="btn" onclick="completeForm()">Done</button>
                <script>
                    function completeForm() {{
                        window.formComplete = true;
                    }}
                </script>
            </div>
        </body>
        </html>
        """
        
        try:
            # Try to use QWebEngineView if available
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            from PyQt5.QtCore import QUrl
            
            # Create web view
            web_view = QWebEngineView()
            web_view.setFixedSize(400, 300)
            web_view.setHtml(html_content)
            
            # Connect JavaScript bridge
            web_view.page().runJavaScript(
                "window.formComplete = false;", 
                lambda result: None
            )
            
            # Check for button click periodically
            self.check_timer = QTimer()
            self.check_timer.setInterval(100)  # 100ms
            self.check_timer.timeout.connect(lambda: self._check_form_completion(web_view))
            self.check_timer.start()
            
            # Add to layout
            self.layout.addWidget(web_view, 0, Qt.AlignCenter)
            self.current_section = web_view
            
        except ImportError:
            # Fallback to standard widgets if QWebEngineView is not available
            completion = QGroupBox("Specifications Complete")
            completion_layout = QVBoxLayout(completion)
            completion_layout.setContentsMargins(15, 20, 15, 15)
            completion_layout.setSpacing(15)
            
            # Add summary
            summary_frame = QFrame()
            summary_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 6px;
                    border: 1px solid #e8eaed;
                }
            """)
            summary_layout = QVBoxLayout(summary_frame)
            summary_layout.setSpacing(5)
            
            # Add summary content
            part_label = QLabel(f"<b>Part:</b> {basic_info.get('part_name', 'Not specified')}")
            part_num_label = QLabel(f"<b>Number:</b> {basic_info.get('part_number', 'Not specified')}")
            free_length_label = QLabel(f"<b>Free Length:</b> {basic_info.get('free_length', '0')} {basic_info.get('unit', 'mm')}")
            set_points_label = QLabel(f"<b>Set Points:</b> {len(set_points)}")
            
            summary_layout.addWidget(part_label)
            summary_layout.addWidget(part_num_label)
            summary_layout.addWidget(free_length_label)
            summary_layout.addWidget(set_points_label)
            
            completion_layout.addWidget(summary_frame)
            
            # Add message
            message = QLabel("All spring specifications have been collected. Click Done to update specifications and continue.")
            message.setWordWrap(True)
            message.setStyleSheet("font-size: 13px;")
            completion_layout.addWidget(message)
            
            # Done button
            done_button = QPushButton("Done")
            done_button.setMinimumHeight(36)
            done_button.setCursor(Qt.PointingHandCursor)
            done_button.clicked.connect(self._on_form_done)
            
            # Style done button
            done_button.setStyleSheet("""
                QPushButton {
                    background-color: #1a73e8;
                    color: white;
                    border: none;
                    font-weight: bold;
                    padding: 8px 24px;
                    min-width: 120px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1967d2;
                }
                QPushButton:pressed {
                    background-color: #185abc;
                }
            """)
            
            # Center the button
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(done_button)
            button_layout.addStretch()
            
            completion_layout.addLayout(button_layout)
            
            # Apply styling to match other sections
            completion.setFixedWidth(400)
            completion.setStyleSheet("""
                QGroupBox {
                    background-color: #f8f9fa;
                    border: 1px solid #dadce0;
                    border-radius: 8px;
                    margin-top: 20px;
                    font-weight: bold;
                    color: #202124;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px;
                    color: #1a73e8;
                    font-size: 14px;
                }
            """)
            
            # Add to layout
            self.layout.addWidget(completion, 0, Qt.AlignCenter)
            self.current_section = completion
        
        # Update state
        self.form_state = "complete"
    
    def _check_form_completion(self, web_view):
        """Check if the form completion button was clicked in the web view."""
        web_view.page().runJavaScript(
            "window.formComplete;", 
            lambda result: self._handle_web_form_completion(result)
        )
    
    def _handle_web_form_completion(self, is_complete):
        """Handle completion from web view."""
        if is_complete:
            self.check_timer.stop()
            self._on_form_done()
    
    def _on_form_done(self):
        """Handle form completion."""
        # Emit signal with collected data
        self.form_completed.emit(self.form_data)
        
        # Clear current section
        self._clear_current_section()
    
    def _on_form_cancelled(self):
        """Handle form cancellation."""
        # Emit cancel signal
        self.form_cancelled.emit()
        
        # Clear current section
        self._clear_current_section()
    
    def _clear_current_section(self):
        """Clear the current section."""
        if self.current_section:
            # Remove from layout
            self.layout.removeWidget(self.current_section)
            
            # Delete widget
            self.current_section.deleteLater()
            self.current_section = None 