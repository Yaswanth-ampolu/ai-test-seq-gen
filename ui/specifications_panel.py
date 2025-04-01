"""
Specifications panel module for the Spring Test App.
Contains the specifications panel for entering and editing spring specifications.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QFormLayout, QGroupBox, QPushButton, QScrollArea, 
                           QTabWidget, QComboBox, QDoubleSpinBox, QCheckBox,
                           QFrame, QSpacerItem, QSizePolicy, QMessageBox, QTextEdit,
                           QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import re
import os
import logging

# Import PyPDF2 for PDF parsing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("PyPDF2 not installed. PDF import feature will be disabled.")

from models.data_models import SpringSpecification, SetPoint


class SetPointWidget(QGroupBox):
    """Widget for editing a single set point."""
    
    # Define signals
    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)  # self
    
    def __init__(self, set_point, index):
        """Initialize the set point widget.
        
        Args:
            set_point: Set point to edit.
            index: Index of the set point.
        """
        super().__init__(f"Set Point {index + 1}")
        
        self.set_point = set_point
        self.index = index
        
        # Set up the UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        # Use a more compact layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(5)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Position input
        self.position_input = QDoubleSpinBox()
        self.position_input.setRange(0, 500)
        self.position_input.setValue(self.set_point.position_mm)
        self.position_input.setDecimals(2)
        self.position_input.valueChanged.connect(self.on_position_changed)
        form_layout.addRow("Position:", self.position_input)
        
        # Load input
        self.load_input = QDoubleSpinBox()
        self.load_input.setRange(0, 1000)
        self.load_input.setValue(self.set_point.load_n)
        self.load_input.setDecimals(2)
        self.load_input.valueChanged.connect(self.on_load_changed)
        form_layout.addRow("Load:", self.load_input)
        
        # Tolerance input
        self.tolerance_input = QDoubleSpinBox()
        self.tolerance_input.setRange(0, 100)
        self.tolerance_input.setValue(self.set_point.tolerance_percent)
        self.tolerance_input.setSuffix(" %")
        self.tolerance_input.setDecimals(1)
        self.tolerance_input.valueChanged.connect(self.on_tolerance_changed)
        form_layout.addRow("Tolerance:", self.tolerance_input)
        
        layout.addLayout(form_layout)
        
        # Controls in a horizontal layout
        controls_layout = QHBoxLayout()
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(self.set_point.enabled)
        self.enabled_checkbox.stateChanged.connect(self.on_enabled_changed)
        controls_layout.addWidget(self.enabled_checkbox)
        
        # Add spacer
        controls_layout.addStretch()
        
        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setMaximumWidth(80)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        controls_layout.addWidget(self.delete_button)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def on_position_changed(self, value):
        """Handle position changes.
        
        Args:
            value: New position value.
        """
        self.set_point.position_mm = value
        self.changed.emit()
    
    def on_load_changed(self, value):
        """Handle load changes.
        
        Args:
            value: New load value.
        """
        self.set_point.load_n = value
        self.changed.emit()
    
    def on_tolerance_changed(self, value):
        """Handle tolerance changes.
        
        Args:
            value: New tolerance value.
        """
        self.set_point.tolerance_percent = value
        self.changed.emit()
    
    def on_enabled_changed(self, state):
        """Handle enabled state changes.
        
        Args:
            state: New enabled state.
        """
        self.set_point.enabled = (state == Qt.Checked)
        self.changed.emit()
    
    def on_delete_clicked(self):
        """Handle delete button clicks."""
        self.delete_requested.emit(self)
    
    def update_index(self, new_index):
        """Update the set point index.
        
        Args:
            new_index: New index.
        """
        self.index = new_index
        self.setTitle(f"Set Point {new_index + 1}")


class SpecificationsPanel(QWidget):
    """Panel for entering and editing spring specifications."""
    
    # Define signals
    specifications_changed = pyqtSignal(object)  # SpringSpecification
    api_key_changed = pyqtSignal(str)  # API Key
    clear_chat_clicked = pyqtSignal()  # Clear chat
    
    def __init__(self, settings_service, sequence_generator, chat_service=None):
        """Initialize the specifications panel.
        
        Args:
            settings_service: Settings service.
            sequence_generator: Sequence generator service.
            chat_service: Chat service (optional).
        """
        super().__init__()
        
        # Store services
        self.settings_service = settings_service
        self.sequence_generator = sequence_generator
        self.chat_service = chat_service
        
        # Store specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Store set point widgets
        self.set_point_widgets = []
        
        # Auto-update flag
        self.auto_update_enabled = False
        
        # Set up the UI
        self.init_ui()
        
        # Load specifications
        self.load_specifications()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Spring Specifications")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Tabs
        tabs = QTabWidget()
        
        # Combined Info & Set Points tab
        combined_tab = QWidget()
        combined_layout = QVBoxLayout()
        
        # Create scroll area for the combined tab
        combined_scroll = QScrollArea()
        combined_scroll.setWidgetResizable(True)
        combined_scroll_content = QWidget()
        combined_scroll_layout = QVBoxLayout(combined_scroll_content)
        
        # Basic info section - Only essential fields
        basic_info_group = QGroupBox("Basic Info")
        basic_info_layout = QFormLayout()
        
        # Part number input
        self.part_number_input = QLineEdit()
        self.part_number_input.textChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Part Number:", self.part_number_input)
        
        # Part name input
        self.part_name_input = QLineEdit()
        self.part_name_input.textChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Part Name:", self.part_name_input)
        
        # Part ID input
        self.part_id_input = QLineEdit()
        self.part_id_input.textChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Part ID:", self.part_id_input)
        
        # Free length input
        self.free_length_input = QDoubleSpinBox()
        self.free_length_input.setRange(0, 1000)
        self.free_length_input.setSuffix(" mm")
        self.free_length_input.setDecimals(2)
        self.free_length_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Free Length:", self.free_length_input)
        
        # Component Type input
        self.component_type_input = QComboBox()
        self.component_type_input.addItems(["Compression", "Tension"])
        self.component_type_input.currentTextChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Component Type:", self.component_type_input)
        
        # Test Mode input
        self.test_mode_input = QComboBox()
        self.test_mode_input.addItems(["Height Mode", "Deflection Mode", "Tension Mode"])
        self.test_mode_input.currentTextChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Test Mode:", self.test_mode_input)
        
        # Displacement Unit input
        self.unit_input = QComboBox()
        self.unit_input.addItems(["mm", "inch"])
        self.unit_input.currentTextChanged.connect(self.on_basic_info_changed)
        self.unit_input.currentTextChanged.connect(self._update_unit_suffixes)
        basic_info_layout.addRow("Displacement Unit:", self.unit_input)
        
        # Force Unit input
        self.force_unit_input = QComboBox()
        self.force_unit_input.addItems(["N", "lbf", "kgf"])
        self.force_unit_input.currentTextChanged.connect(self.on_basic_info_changed)
        self.force_unit_input.currentTextChanged.connect(self._update_unit_suffixes)
        basic_info_layout.addRow("Force Unit:", self.force_unit_input)
        
        # First Speed input
        self.first_speed_input = QDoubleSpinBox()
        self.first_speed_input.setRange(0, 1000) # Adjust range as needed
        self.first_speed_input.setDecimals(1)
        self.first_speed_input.setSuffix(" mm/s")
        self.first_speed_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("First Speed:", self.first_speed_input)
        
        # Second Speed input
        self.second_speed_input = QDoubleSpinBox()
        self.second_speed_input.setRange(0, 1000) # Adjust range as needed
        self.second_speed_input.setDecimals(1)
        self.second_speed_input.setSuffix(" mm/s")
        self.second_speed_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Second Speed:", self.second_speed_input)
        
        # Safety limit input moved to basic info
        self.safety_limit_input = QDoubleSpinBox()
        self.safety_limit_input.setRange(0, 10000)
        self.safety_limit_input.setDecimals(2)
        self.safety_limit_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Safety Limit:", self.safety_limit_input)
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enable Specifications")
        self.enabled_checkbox.stateChanged.connect(self.on_enabled_changed)
        basic_info_layout.addRow("", self.enabled_checkbox)
        
        basic_info_group.setLayout(basic_info_layout)
        combined_scroll_layout.addWidget(basic_info_group)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        combined_scroll_layout.addWidget(separator)
        
        # Optional fields section
        optional_group = QGroupBox("Optional Fields")
        optional_layout = QFormLayout()
        
        # Coil count input
        self.coil_count_input = QDoubleSpinBox()
        self.coil_count_input.setRange(0, 100)
        self.coil_count_input.setDecimals(1)
        self.coil_count_input.valueChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Number of Coils:", self.coil_count_input)
        
        # Wire diameter input
        self.wire_dia_input = QDoubleSpinBox()
        self.wire_dia_input.setRange(0, 100)
        self.wire_dia_input.setSuffix(" mm")
        self.wire_dia_input.setDecimals(2)
        self.wire_dia_input.valueChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Wire Diameter:", self.wire_dia_input)
        
        # Outer diameter input
        self.outer_dia_input = QDoubleSpinBox()
        self.outer_dia_input.setRange(0, 500)
        self.outer_dia_input.setDecimals(2)
        self.outer_dia_input.valueChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Outer Diameter:", self.outer_dia_input)
        
        # Offer Number input
        self.offer_number_input = QLineEdit()
        self.offer_number_input.textChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Offer Number:", self.offer_number_input)
        
        # Production Batch Number input
        self.production_batch_number_input = QLineEdit()
        self.production_batch_number_input.textChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Production Batch:", self.production_batch_number_input)
        
        # Part Revision input
        self.part_rev_no_date_input = QLineEdit()
        self.part_rev_no_date_input.textChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Part Revision:", self.part_rev_no_date_input)
        
        # Material Description input
        self.material_description_input = QLineEdit()
        self.material_description_input.textChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Material:", self.material_description_input)
        
        # Surface Treatment input
        self.surface_treatment_input = QLineEdit()
        self.surface_treatment_input.textChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("Surface Treatment:", self.surface_treatment_input)
        
        # End Coil Finishing input
        self.end_coil_finishing_input = QLineEdit()
        self.end_coil_finishing_input.textChanged.connect(self.on_basic_info_changed)
        optional_layout.addRow("End Coil Finishing:", self.end_coil_finishing_input)
        
        optional_group.setLayout(optional_layout)
        combined_scroll_layout.addWidget(optional_group)
        
        # Set Points section also as part of Optional
        set_points_group = QGroupBox("Set Points (Optional)")
        set_points_layout = QVBoxLayout()
        
        # Container for set points
        set_points_container = QWidget()
        self.set_points_layout = QVBoxLayout(set_points_container)
        set_points_layout.addWidget(set_points_container)
        
        # Add set point button
        add_button = QPushButton("Add Set Point")
        add_button.clicked.connect(self.on_add_set_point)
        set_points_layout.addWidget(add_button)
        
        set_points_group.setLayout(set_points_layout)
        combined_scroll_layout.addWidget(set_points_group)
        
        # Finalize combined tab
        combined_scroll.setWidget(combined_scroll_content)
        combined_layout.addWidget(combined_scroll)
        combined_tab.setLayout(combined_layout)
        
        # Settings tab - new
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        
        # API Key group
        api_key_group = QGroupBox("API Settings")
        api_key_group.setObjectName("SettingsGroup")
        api_key_layout = QFormLayout()
        api_key_layout.setContentsMargins(15, 20, 15, 20)
        api_key_layout.setSpacing(10)
        
        # API key input with icon
        api_key_container = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API Key")
        self.api_key_input.setMinimumHeight(30)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        api_key_container.addWidget(self.api_key_input)
        
        # Show/hide password toggle button could be added here
        
        api_key_layout.addRow("API Key:", api_key_container)
        
        # Key description
        key_description = QLabel("Enter your API key from OpenAI or another LLM provider.")
        key_description.setStyleSheet("color: gray; font-style: italic;")
        key_description.setWordWrap(True)
        api_key_layout.addRow("", key_description)
        
        api_key_group.setLayout(api_key_layout)
        settings_layout.addWidget(api_key_group)
        
        # Chat controls group
        chat_controls_group = QGroupBox("Chat Controls")
        chat_controls_group.setObjectName("SettingsGroup")
        chat_controls_layout = QVBoxLayout()
        chat_controls_layout.setContentsMargins(15, 20, 15, 20)
        chat_controls_layout.setSpacing(10)
        
        # Clear chat description
        clear_chat_description = QLabel("Clear the chat history to start a fresh conversation.")
        clear_chat_description.setStyleSheet("color: gray; font-style: italic;")
        clear_chat_description.setWordWrap(True)
        chat_controls_layout.addWidget(clear_chat_description)
        
        # Clear chat button
        self.clear_chat_btn = QPushButton("Clear Chat History")
        self.clear_chat_btn.setObjectName("ClearChatBtn")
        self.clear_chat_btn.setMinimumHeight(40)
        self.clear_chat_btn.clicked.connect(self.on_clear_chat_clicked)
        chat_controls_layout.addWidget(self.clear_chat_btn)
        
        chat_controls_group.setLayout(chat_controls_layout)
        settings_layout.addWidget(chat_controls_group)
        
        # Reset specifications group
        reset_specs_group = QGroupBox("Reset Specifications")
        reset_specs_group.setObjectName("ResetSpecsGroup")
        reset_specs_layout = QVBoxLayout()
        reset_specs_layout.setContentsMargins(15, 20, 15, 20)
        reset_specs_layout.setSpacing(10)
        
        # Reset specifications description
        reset_specs_description = QLabel("Reset ALL specifications including set points? This action cannot be undone.")
        reset_specs_description.setStyleSheet("color: gray; font-style: italic;")
        reset_specs_description.setWordWrap(True)
        reset_specs_layout.addWidget(reset_specs_description)
        
        # Reset specifications button
        self.reset_specs_btn = QPushButton("Reset All Specifications")
        self.reset_specs_btn.setObjectName("ResetSpecsBtn")
        self.reset_specs_btn.setMinimumHeight(40)
        self.reset_specs_btn.setStyleSheet("QPushButton#ResetSpecsBtn { background-color: #f44336; color: white; }")
        self.reset_specs_btn.clicked.connect(self.on_reset_specifications_clicked)
        reset_specs_layout.addWidget(self.reset_specs_btn)
        
        reset_specs_group.setLayout(reset_specs_layout)
        settings_layout.addWidget(reset_specs_group)
        
        # Add spacer at the bottom of settings tab
        settings_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        settings_tab.setLayout(settings_layout)
        
        # Add tabs to tab widget
        tabs.addTab(combined_tab, "Specifications")
        tabs.addTab(self.create_text_input_tab(), "Paste Specifications")
        tabs.addTab(settings_tab, "Settings")
        
        main_layout.addWidget(tabs)
        
        # Save button
        save_button = QPushButton("Save Specifications")
        save_button.clicked.connect(self.on_save_specifications)
        main_layout.addWidget(save_button)
        
        # Spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(main_layout)
    
    def _normalize_test_mode(self, mode):
        """Normalize test mode to ensure it uses the proper format.
        
        Args:
            mode: Test mode value to normalize
            
        Returns:
            Normalized test mode value
        """
        mode = mode.strip()
        
        # Map old values to new values
        mode_mapping = {
            "Height": "Height Mode",
            "Force": "Deflection Mode",
            "Tension": "Tension Mode"
        }
        
        # Return the mapped value if it exists, otherwise return the original value
        return mode_mapping.get(mode, mode)
        
    def load_specifications(self):
        """Load specifications from the settings service."""
        # Get specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Set basic info values
        self.part_name_input.setText(self.specifications.part_name)
        self.part_number_input.setText(self.specifications.part_number)
        self.part_id_input.setText(str(self.specifications.part_id))
        self.free_length_input.setValue(self.specifications.free_length_mm)
        self.coil_count_input.setValue(self.specifications.coil_count)
        self.wire_dia_input.setValue(self.specifications.wire_dia_mm)
        self.outer_dia_input.setValue(self.specifications.outer_dia_mm)
        self.safety_limit_input.setValue(self.specifications.safety_limit_n)
        self.unit_input.setCurrentText(self.specifications.unit)
        self.force_unit_input.setCurrentText(self.specifications.force_unit)
        
        # Normalize test mode value
        normalized_test_mode = self._normalize_test_mode(self.specifications.test_mode)
        self.test_mode_input.setCurrentText(normalized_test_mode)
        # Update the specification if the value was normalized
        if normalized_test_mode != self.specifications.test_mode:
            self.specifications.test_mode = normalized_test_mode
            self.settings_service.update_spring_basic_info(test_mode=normalized_test_mode)
        
        self.component_type_input.setCurrentText(self.specifications.component_type)
        self.first_speed_input.setValue(self.specifications.first_speed)
        self.second_speed_input.setValue(self.specifications.second_speed)
        self.offer_number_input.setText(self.specifications.offer_number)
        self.production_batch_number_input.setText(self.specifications.production_batch_number)
        self.part_rev_no_date_input.setText(self.specifications.part_rev_no_date)
        self.material_description_input.setText(self.specifications.material_description)
        self.surface_treatment_input.setText(self.specifications.surface_treatment)
        self.end_coil_finishing_input.setText(self.specifications.end_coil_finishing)
        self.enabled_checkbox.setChecked(self.specifications.enabled)
        
        # Load API key
        api_key = self.settings_service.get_api_key()
        if api_key:
            self.api_key_input.setText(api_key)
        
        # Set set points
        self.refresh_set_points()
        
        # Update unit suffixes
        self._update_unit_suffixes()
    
    def refresh_set_points(self):
        """Refresh the set points display."""
        # Clear existing set point widgets
        for widget in self.set_point_widgets:
            self.set_points_layout.removeWidget(widget)
            widget.deleteLater()
        
        self.set_point_widgets = []
        
        # Add set point widgets
        for i, set_point in enumerate(self.specifications.set_points):
            widget = SetPointWidget(set_point, i)
            widget.changed.connect(self.on_specifications_changed)
            widget.delete_requested.connect(self.on_delete_set_point)
            self.set_points_layout.addWidget(widget)
            self.set_point_widgets.append(widget)
        
        # Add a spacer at the end
        self.set_points_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def on_basic_info_changed(self):
        """Handle changes to basic info."""
        # Update specifications
        try:
            part_id_str = self.part_id_input.text()
            # Only convert to int if it's purely digits
            if part_id_str.isdigit():
                part_id = int(part_id_str)
            else:
                # Keep it as a string if it contains non-numeric characters
                part_id = part_id_str
                print(f"Using part_id as string: {part_id}")
        except Exception as e:
            # If there's any error, use the text as is instead of defaulting to 0
            print(f"Error processing part_id: {str(e)}")
            part_id = self.part_id_input.text()
        
        self.settings_service.update_spring_basic_info(
            part_name=self.part_name_input.text(),
            part_number=self.part_number_input.text(),
            part_id=part_id,
            free_length=self.free_length_input.value(),
            coil_count=self.coil_count_input.value(),
            wire_dia=self.wire_dia_input.value(),
            outer_dia=self.outer_dia_input.value(),
            safety_limit=self.safety_limit_input.value(),
            unit=self.unit_input.currentText(),
            force_unit=self.force_unit_input.currentText(),
            test_mode=self.test_mode_input.currentText(),
            component_type=self.component_type_input.currentText(),
            first_speed=self.first_speed_input.value(),
            second_speed=self.second_speed_input.value(),
            offer_number=self.offer_number_input.text(),
            production_batch_number=self.production_batch_number_input.text(),
            part_rev_no_date=self.part_rev_no_date_input.text(),
            material_description=self.material_description_input.text(),
            surface_treatment=self.surface_treatment_input.text(),
            end_coil_finishing=self.end_coil_finishing_input.text(),
            enabled=self.enabled_checkbox.isChecked()
        )
        
        # Refresh specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_enabled_changed(self, state):
        """Handle enabled state changes.
        
        Args:
            state: New enabled state.
        """
        # Update specifications
        self.specifications.enabled = (state == Qt.Checked)
        
        # Update settings
        self.settings_service.set_spring_specification(self.specifications)
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_add_set_point(self):
        """Handle add set point button clicks."""
        # Add new set point
        self.settings_service.add_set_point()
        
        # Refresh specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Refresh set points
        self.refresh_set_points()
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_delete_set_point(self, widget):
        """Handle delete set point requests.
        
        Args:
            widget: Set point widget to delete.
        """
        # Delete set point
        self.settings_service.delete_set_point(widget.index)
        
        # Refresh specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Refresh set points
        self.refresh_set_points()
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_specifications_changed(self):
        """Handle specifications changes."""
        # Update sequence generator
        self.sequence_generator.set_spring_specification(self.specifications)
        
        # Emit signal
        self.specifications_changed.emit(self.specifications)
    
    def on_auto_update_changed(self, state):
        """Handle auto-update checkbox state changes.
        
        Args:
            state: New state (Qt.Checked or Qt.Unchecked).
        """
        self.auto_update_enabled = (state == Qt.Checked)
        
        # Connect/disconnect the textChanged signal based on auto-update state
        if self.auto_update_enabled:
            self.specs_text_input.textChanged.connect(self.on_parse_specifications)
        else:
            try:
                self.specs_text_input.textChanged.disconnect(self.on_parse_specifications)
            except TypeError:
                # Signal was not connected
                pass
    
    def on_parse_specifications(self):
        """Parse specifications from text input and update form fields."""
        # Get text from input
        specs_text = self.specs_text_input.toPlainText()
        
        if not specs_text.strip():
            print("No text to parse - input is empty")
            return
        
        print(f"Parsing specifications text: {len(specs_text)} characters")
        
        # Parse specifications
        parsed_data = self.parse_specifications_text(specs_text)
        
        # Update form fields with parsed data
        if parsed_data:
            print(f"Successfully parsed data: {parsed_data.get('basic_info', {})} and {len(parsed_data.get('set_points', []))} set points")
            
            self.populate_form_from_parsed_data(parsed_data)
            
            # Explicitly save specifications after parsing
            print("Saving specifications to settings after parsing")
            self.settings_service.set_spring_specification(self.specifications)
            
            # Show success message if not auto-updating
            if not self.auto_update_enabled:
                QMessageBox.information(self, "Specifications Parsed", 
                                       "Spring specifications were successfully parsed and updated.")
        else:
            print("Failed to parse specifications - no valid data extracted")
    
    def parse_specifications_text(self, text):
        """Parse specifications from text.
        
        Args:
            text: Text containing specifications.
            
        Returns:
            Dictionary of parsed values or None if parsing failed.
        """
        parsed_data = {
            "basic_info": {},
            "set_points": []
        }
        
        # Preprocess text to improve parsing
        # Replace common typos and normalize spacing
        preprocessed_text = text
        # Insert newlines before key patterns to help with parsing
        for pattern in ["Part Name:", "Part Number:", "ID:", "Free Length:", "No of ", "Wire ", "Wired ", "OD:", "Set Po", "Safety"]:
            preprocessed_text = re.sub(f"\\s+({pattern})", f"\n\\1", preprocessed_text, flags=re.IGNORECASE)
        
        # Print the preprocessed text for debugging
        print(f"Preprocessed text for parsing:\n{preprocessed_text}")
        
        # Basic info patterns
        patterns = {
            "part_name": r"(?:^|\s+)(?:Part|Spring)\s+Name:?\s*(.+?)(?:\s+(?:Part|ID|Free|No|Wire|OD|Set|Safety)|$)",
            "part_number": r"(?:^|\s+)Part\s+Number:?\s*(.+?)(?:\s+(?:Part|ID|Free|No|Wire|OD|Set|Safety)|$)",
            "part_id": r"(?:^|\s+)ID:?\s*(\d+)",
            "free_length": r"(?:^|\s+)Free\s+Length:?\s*([\d.]+)",
            "coil_count": r"(?:^|\s+)No\s+of\s+(?:Coils|Colis):?\s*([\d.]+)",
            "wire_dia": r"(?:^|\s+)(?:Wire|Wired)\s+Dia(?:meter)?:?\s*([\d.]+)",
            "outer_dia": r"(?:^|\s+)OD:?\s*([\d.]+)",
            "safety_limit": r"(?:^|\s+)[Ss]afety\s+[Ll]imit:?\s*([\d.]+)",
            "force_unit": r"(?:^|\s+)Force\s+Unit:?\s*(\w+)",
            "test_mode": r"(?:^|\s+)Test\s+Mode:?\s*(Height Mode|Deflection Mode|Tension Mode|Height|Deflection|Tension)",
            "component_type": r"(?:^|\s+)Component\s+Type:?\s*(\w+)",
            "first_speed": r"(?:^|\s+)First\s+Speed:?\s*([\d.]+)",
            "second_speed": r"(?:^|\s+)Second\s+Speed:?\s*([\d.]+)",
            "offer_number": r"(?:^|\s+)Offer\s+Number:?\s*(.+?)(?:\s+(?:Production|Part|Material|Surface|End)|$)",
            "production_batch_number": r"(?:^|\s+)Production\s+Batch(?:\s+Number)?:?\s*(.+?)(?:\s+(?:Part|Material|Surface|End)|$)",
            "part_rev_no_date": r"(?:^|\s+)Part\s+Rev(?:ision|\.)?:?\s*(.+?)(?:\s+(?:Material|Surface|End)|$)",
            "material_description": r"(?:^|\s+)Material(?:\s+Description)?:?\s*(.+?)(?:\s+(?:Surface|End)|$)",
            "surface_treatment": r"(?:^|\s+)Surface\s+Treatment:?\s*(.+?)(?:\s+(?:End)|$)",
            "end_coil_finishing": r"(?:^|\s+)End\s+Coil(?:\s+Finishing)?:?\s*(.+?)(?:\s+Set|Safety|$)"
        }
        
        # Extract basic info
        for key, pattern in patterns.items():
            match = re.search(pattern, preprocessed_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove trailing text that might have been captured incorrectly
                value = re.sub(r'\s+(?:Part|ID|Free|No|Wire|OD|Set|Safety).*$', '', value, flags=re.IGNORECASE)
                try:
                    if key in ["part_id"]:
                        parsed_data["basic_info"][key] = int(value)
                    elif key in ["free_length", "coil_count", "wire_dia", "outer_dia", "safety_limit"]:
                        # Extract numeric value
                        num_match = re.search(r"([\d.]+)", value)
                        if num_match:
                            parsed_data["basic_info"][key] = float(num_match.group(1))
                    else:
                        # Handle text fields
                        if key in ["part_name", "part_number", "offer_number", "production_batch_number", 
                                    "part_rev_no_date", "material_description", "surface_treatment", "end_coil_finishing",
                                    "force_unit", "test_mode", "component_type"]:
                            parsed_data["basic_info"][key] = value
                        else:
                            # Assume string for others, though should be specific types mostly
                            parsed_data["basic_info"][key] = value
                except (ValueError, TypeError):
                    print(f"Error converting {key} value: {value}")
        
        # New improved set point extraction
        # First find all set point data in the preprocessed text
        set_point_pattern = r"Set\s+Point\-(\d+)\s+in\s+mm:\s*([\d.]+).*?Set\s+Point\-\1\s+Load\s+In\s+N:\s*([\d.]+)(?:±([\d.]+)%)?.*?N"
        
        # Try direct line-by-line search for set points if pattern doesn't work
        if not re.search(set_point_pattern, preprocessed_text, re.IGNORECASE | re.DOTALL):
            lines = preprocessed_text.split('\n')
            lines_text = '\n'.join(lines)
            print(f"Searching line by line for set points in:\n{lines_text}")
            
            # Find position lines
            position_matches = []
            for i, line in enumerate(lines):
                pos_match = re.search(r"Set\s+Point\-(\d+)\s+in\s+mm:\s*([\d.]+)", line, re.IGNORECASE)
                if pos_match:
                    position_matches.append((i, int(pos_match.group(1)), float(pos_match.group(2))))
            
            # Find load lines
            load_matches = []
            for i, line in enumerate(lines):
                load_match = re.search(r"Set\s+Point\-(\d+)\s+Load\s+In\s+N:\s*([\d.]+)(?:±([\d.]+)%)?", line, re.IGNORECASE)
                if load_match:
                    tolerance = 10.0
                    if load_match.group(3):
                        tolerance = float(load_match.group(3))
                    load_matches.append((i, int(load_match.group(1)), float(load_match.group(2)), tolerance))
            
            print(f"Found {len(position_matches)} position matches: {position_matches}")
            print(f"Found {len(load_matches)} load matches: {load_matches}")
            
            # Match positions with loads by index
            for pos_line, pos_index, position in position_matches:
                for load_line, load_index, load, tolerance in load_matches:
                    if pos_index == load_index:
                        parsed_data["set_points"].append({
                            "index": pos_index - 1,  # Convert to 0-based
                            "position": position,
                            "load": load,
                            "tolerance": tolerance,
                            "enabled": True
                        })
                        break
        else:
            # Use the full pattern if it works
            for match in re.finditer(set_point_pattern, preprocessed_text, re.IGNORECASE | re.DOTALL):
                index = int(match.group(1))
                position = float(match.group(2))
                load = float(match.group(3))
                tolerance = 10.0
                if match.group(4):
                    tolerance = float(match.group(4))
                
                parsed_data["set_points"].append({
                    "index": index - 1,  # Convert to 0-based
                    "position": position,
                    "load": load,
                    "tolerance": tolerance,
                    "enabled": True
                })
        
        print(f"Set points found in text: {parsed_data['set_points']}")
        
        # Return None if no basic info was found
        if not parsed_data["basic_info"]:
            return None
        
        return parsed_data
    
    def populate_form_from_parsed_data(self, parsed_data):
        """Populate form fields from parsed data.
        
        Args:
            parsed_data: Dictionary of parsed values.
        """
        basic_info = parsed_data.get("basic_info", {})
        set_points = parsed_data.get("set_points", [])
        
        # Update basic info fields
        if "part_name" in basic_info:
            self.part_name_input.setText(basic_info["part_name"])
            print(f"Set part name: {basic_info['part_name']}")
        
        if "part_number" in basic_info:
            self.part_number_input.setText(basic_info["part_number"])
            print(f"Set part number: {basic_info['part_number']}")
        
        if "part_id" in basic_info:
            self.part_id_input.setText(str(basic_info["part_id"]))
            print(f"Set part ID: {basic_info['part_id']}")
        
        if "free_length" in basic_info:
            self.free_length_input.setValue(basic_info["free_length"])
            print(f"Set free length: {basic_info['free_length']}")
        
        if "coil_count" in basic_info:
            self.coil_count_input.setValue(basic_info["coil_count"])
            print(f"Set coil count: {basic_info['coil_count']}")
        
        if "wire_dia" in basic_info:
            self.wire_dia_input.setValue(basic_info["wire_dia"])
            print(f"Set wire diameter: {basic_info['wire_dia']}")
        
        if "outer_dia" in basic_info:
            self.outer_dia_input.setValue(basic_info["outer_dia"])
            print(f"Set outer diameter: {basic_info['outer_dia']}")
        
        if "safety_limit" in basic_info:
            self.safety_limit_input.setValue(basic_info["safety_limit"])
            print(f"Set safety limit: {basic_info['safety_limit']}")
        
        if "force_unit" in basic_info:
            self.force_unit_input.setCurrentText(basic_info["force_unit"])
            print(f"Set force unit: {basic_info['force_unit']}")
        
        if "test_mode" in basic_info:
            normalized_test_mode = self._normalize_test_mode(basic_info["test_mode"])
            self.test_mode_input.setCurrentText(normalized_test_mode)
            print(f"Set test mode: {normalized_test_mode} (original: {basic_info['test_mode']})")
        
        if "component_type" in basic_info:
            self.component_type_input.setCurrentText(basic_info["component_type"])
            print(f"Set component type: {basic_info['component_type']}")
        
        if "first_speed" in basic_info:
            self.first_speed_input.setValue(basic_info["first_speed"])
            print(f"Set first speed: {basic_info['first_speed']}")
        
        if "second_speed" in basic_info:
            self.second_speed_input.setValue(basic_info["second_speed"])
            print(f"Set second speed: {basic_info['second_speed']}")
        
        if "offer_number" in basic_info:
            self.offer_number_input.setText(basic_info["offer_number"])
            print(f"Set offer number: {basic_info['offer_number']}")
        
        if "production_batch_number" in basic_info:
            self.production_batch_number_input.setText(basic_info["production_batch_number"])
            print(f"Set production batch: {basic_info['production_batch_number']}")
        
        if "part_rev_no_date" in basic_info:
            self.part_rev_no_date_input.setText(basic_info["part_rev_no_date"])
            print(f"Set part revision: {basic_info['part_rev_no_date']}")
        
        if "material_description" in basic_info:
            self.material_description_input.setText(basic_info["material_description"])
            print(f"Set material: {basic_info['material_description']}")
        
        if "surface_treatment" in basic_info:
            self.surface_treatment_input.setText(basic_info["surface_treatment"])
            print(f"Set surface treatment: {basic_info['surface_treatment']}")
        
        if "end_coil_finishing" in basic_info:
            self.end_coil_finishing_input.setText(basic_info["end_coil_finishing"])
            print(f"Set end coil finishing: {basic_info['end_coil_finishing']}")
        
        # Enable specifications checkbox
        self.enabled_checkbox.setChecked(True)
        print("Enabled specifications checkbox")
        
        # Update specifications
        self.on_basic_info_changed()
        
        # Process set points
        if set_points:
            print(f"Processing {len(set_points)} set points from parsed data")
            
            # Get current specification for updating
            self.specifications = self.settings_service.get_spring_specification()
            
            # Clear existing set points to avoid duplicates
            self.settings_service.clear_set_points()
            print("Cleared existing set points")
            
            # Add each set point
            for sp_data in set_points:
                index = sp_data["index"]
                print(f"Adding set point with index {index}, position {sp_data['position']}, load {sp_data['load']}")
                
                # First add a new set point
                self.settings_service.add_set_point()
                
                # Update the set point data
                self.settings_service.update_set_point(
                    index=index,
                    position=sp_data["position"],
                    load=sp_data["load"],
                    tolerance=sp_data.get("tolerance", 10.0),
                    enabled=sp_data.get("enabled", True)
                )
            
            # Refresh specifications
            self.specifications = self.settings_service.get_spring_specification()
            
            # Print the number of set points loaded
            print(f"Updated specification now has {len(self.specifications.set_points)} set points")
            
            # Refresh set points display
            self.refresh_set_points()
            
            # Emit signal for specifications changed
            self.on_specifications_changed()
        else:
            print("No set points found to update")

    def on_save_specifications(self):
        """Handle save specifications button clicks."""
        print(f"Saving specifications with {len(self.specifications.set_points)} set points")
        
        # Ensure specifications are enabled
        if not self.specifications.enabled:
            print("Automatically enabling specifications before saving")
            self.specifications.enabled = True
            self.enabled_checkbox.setChecked(True)
        
        # Double-check that basic info changes are committed
        self.on_basic_info_changed()
        
        # Save specifications
        saved = self.settings_service.set_spring_specification(self.specifications)
        
        if saved:
            print("Successfully saved specifications to settings file")
            
            # Show success message
            QMessageBox.information(self, "Specifications Saved", 
                                  "Spring specifications saved successfully. These will be used for future sequence generations.")
            
            # Update the sequence generator with the saved specs
            self.sequence_generator.set_spring_specification(self.specifications)
        else:
            print("Failed to save specifications to settings file")
            
            # Show error message
            QMessageBox.warning(self, "Save Failed", 
                               "Failed to save specifications. Please check the log for more information.")

    def on_upload_pdf(self):
        """Handle upload PDF button clicks."""
        if not PDF_SUPPORT:
            QMessageBox.warning(
                self, 
                "Feature Not Available", 
                "PDF support requires the PyPDF2 package. Please install it and restart the application."
            )
            return
        
        # Open file dialog to select PDF
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select PDF File",
            "",
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            # User cancelled
            print("PDF upload cancelled by user")
            return
        
        try:
            # Update status
            self.upload_status.setText(f"Processing {os.path.basename(file_path)}...")
            print(f"Processing PDF file: {file_path}")
            
            # Extract text from PDF
            extracted_text = self.extract_text_from_pdf(file_path)
            
            if not extracted_text:
                self.upload_status.setText("No text extracted from PDF.")
                print("No text was extracted from the PDF")
                return
            
            print(f"Extracted {len(extracted_text)} characters from PDF")
            
            # Set text in input field
            self.specs_text_input.setPlainText(extracted_text)
            
            # Parse the specifications
            print("Parsing specifications from extracted PDF text")
            self.on_parse_specifications()
            
            # Explicitly save specifications again to ensure they persist
            print("Explicitly saving specifications after PDF parsing")
            self.settings_service.set_spring_specification(self.specifications)
            
            # Update status
            self.upload_status.setText(f"Processed {os.path.basename(file_path)}")
            
            # Show success message with instructions
            QMessageBox.information(
                self,
                "PDF Processed",
                "The PDF has been processed and specifications have been extracted. Please review them and click 'Save Specifications' to confirm."
            )
            
        except Exception as e:
            error_msg = str(e)
            self.upload_status.setText(f"Error: {error_msg}")
            logging.error(f"Error processing PDF: {error_msg}")
            print(f"Error processing PDF: {error_msg}")
            QMessageBox.critical(
                self, 
                "PDF Processing Error", 
                f"An error occurred while processing the PDF file: {error_msg}"
            )
    
    def extract_text_from_pdf(self, file_path):
        """Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text.
        """
        extracted_text = ""
        
        # Open the PDF file
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text:
                    extracted_text += page_text + "\n"
        
        # Process extracted text to clean it up
        # This is important as PDF extraction can include various formatting characters
        cleaned_text = self.clean_pdf_text(extracted_text)
        
        return cleaned_text
    
    def clean_pdf_text(self, text):
        """Clean up text extracted from PDF.
        
        Args:
            text: Raw text extracted from PDF.
            
        Returns:
            Cleaned text.
        """
        # Create a new string to build our formatted output
        formatted_output = ""
        
        # Preprocess: insert newlines before key patterns to help with parsing
        preprocessed_text = text
        for pattern in ["Part Name", "Part Number", "ID:", "Free Length", "No of ", "Wire ", "Wired ", "OD:", "Set Po", "Safety"]:
            preprocessed_text = re.sub(f"([^\\n])\\s+({pattern})", f"\\1\n\\2", preprocessed_text, flags=re.IGNORECASE)
        
        # Replace multiple spaces with a single space within lines
        cleaned_lines = []
        for line in preprocessed_text.split('\n'):
            cleaned_lines.append(re.sub(r'\s+', ' ', line).strip())
        cleaned = '\n'.join(cleaned_lines)
        
        # Dictionary to store extracted values
        extracted = {}
        
        # More flexible patterns to match various PDF formats
        patterns = {
            "part_name": [
                r'(?:part|spring)[\s:]+name[\s:]*([^,;\n\d]+)',
                r'(?:^|\n)[\s:]*part[\s:]*name[\s:]*([^,;\n\d]+)'
            ],
            "part_number": [
                r'(?:part|spring)[\s:]+(?:number|no\.?|#)[\s:]*([^,;\n]+)',
                r'(?:^|\n)[\s:]*part[\s:]*number[\s:]*([^,;\n]+)'
            ],
            "part_id": [
                r'(?:part|spring)?[\s:]*id[\s:]*(\d+)',
                r'(?:^|\n)[\s:]*id[\s:]*(\d+)'
            ],
            "free_length": [
                r'free[\s:]+length[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*free[\s:]*length[\s:]*(\d+\.?\d*)'
            ],
            "coil_count": [
                r'(?:number[\s:]+of[\s:]+(?:coils|colis)|no[\s:]+of[\s:]+(?:coils|colis))[\s:]*(\d+\.?\d*)',
                r'(?:^|\n)[\s:]*(?:no\.?|number)[\s:]*of[\s:]*(?:coils|colis)[\s:]*(\d+\.?\d*)'
            ],
            "wire_dia": [
                r'(?:wire|wired)[\s:]+dia(?:meter)?[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*(?:wire|wired)[\s:]*dia(?:meter)?[\s:]*(\d+\.?\d*)'
            ],
            "outer_dia": [
                r'(?:outer[\s:]+dia(?:meter)?|od)[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*(?:outer[\s:]*diameter|od)[\s:]*(\d+\.?\d*)'
            ],
            "safety_limit": [
                r'safety[\s:]+limit[\s:]*(\d+\.?\d*)[\s]*(?:n)?',
                r'(?:^|\n)[\s:]*safety[\s:]*limit[\s:]*(\d+\.?\d*)'
            ],
            "force_unit": [
                r'force[\s:]+unit[\s:]*(\w+)',
                r'(?:^|\n)[\s:]*force[\s:]*unit[\s:]*(\w+)'
            ],
            "test_mode": [
                r'test[\s:]+mode[\s:]*(Height Mode|Deflection Mode|Tension Mode|Height|Deflection|Tension)',
                r'(?:^|\n)[\s:]*test[\s:]*mode[\s:]*(Height Mode|Deflection Mode|Tension Mode|Height|Deflection|Tension)'
            ],
            "component_type": [
                r'component[\s:]+type[\s:]*(\w+)',
                r'(?:^|\n)[\s:]*component[\s:]*type[\s:]*(\w+)'
            ],
            "first_speed": [
                r'first[\s:]+speed[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*first[\s:]*speed[\s:]*(\d+\.?\d*)'
            ],
            "second_speed": [
                r'second[\s:]+speed[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*second[\s:]*speed[\s:]*(\d+\.?\d*)'
            ],
            "offer_number": [
                r'offer[\s:]+number[\s:]*(\d+)',
                r'(?:^|\n)[\s:]*offer[\s:]*number[\s:]*(\d+)'
            ],
            "production_batch_number": [
                r'production[\s:]+batch[\s:]*(\d+)',
                r'(?:^|\n)[\s:]*production[\s:]*batch[\s:]*(\d+)'
            ],
            "part_rev_no_date": [
                r'part[\s:]+rev[\s:]*(\d+)',
                r'(?:^|\n)[\s:]*part[\s:]*rev[\s:]*(\d+)'
            ],
            "material_description": [
                r'material[\s:]+description[\s:]*(.+?)(?:\s+(?:surface|end)|$)',
                r'(?:^|\n)[\s:]*material[\s:]*description[\s:]*(.+?)(?:\s+(?:surface|end)|$)'
            ],
            "surface_treatment": [
                r'surface[\s:]+treatment[\s:]*(.+?)(?:\s+(?:end)|$)',
                r'(?:^|\n)[\s:]*surface[\s:]*treatment[\s:]*(.+?)(?:\s+(?:end)|$)'
            ],
            "end_coil_finishing": [
                r'end[\s:]+coil[\s:]+finishing[\s:]*(.+?)(?:\s+set|safety|$)',
                r'(?:^|\n)[\s:]*end[\s:]*coil[\s:]*finishing[\s:]*(.+?)(?:\s+set|safety|$)'
            ]
        }
        
        # Try multiple patterns for each parameter
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, cleaned, re.IGNORECASE)
                if match:
                    extracted[key] = match.group(1).strip()
                    break
        
        # Find set points with more flexible patterns
        set_points = {}
        
        # First find all set point indices
        for match in re.finditer(r'set[\s:]+(?:poin?t|poni)[\s\-:]+(\d+)', cleaned, re.IGNORECASE):
            try:
                index = int(match.group(1))
                if index not in set_points:
                    set_points[index] = {"index": index}
            except ValueError:
                continue
        
        # For each set point, find position and load with multiple pattern attempts
        for index in set_points:
            # Position patterns
            pos_patterns = [
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]+in[\s:]+mm[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[^0-9]*?(\d+\.?\d*)[\s]*(?:mm)?'
            ]
            
            for pattern in pos_patterns:
                pos_match = re.search(pattern, cleaned, re.IGNORECASE)
                if pos_match:
                    set_points[index]["position"] = pos_match.group(1).strip()
                    break
            
            # Load patterns
            load_patterns = [
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]+load[\s:]+in[\s:]+n[\s:]*(\d+\.?\d*)(?:±([\d.]+)%)?[\s]*(?:n)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]+load[\s:]*(\d+\.?\d*)(?:±([\d.]+)%)?[\s]*(?:n)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'.*?load.*?(\d+\.?\d*)(?:±([\d.]+)%)?[\s]*(?:n)?'
            ]
            
            for pattern in load_patterns:
                load_match = re.search(pattern, cleaned, re.IGNORECASE)
                if load_match:
                    set_points[index]["load"] = load_match.group(1).strip()
                    set_points[index]["tolerance"] = load_match.group(2).strip() if load_match.group(2) else "10"
                    break
        
        # Build the formatted output with consistent format
        if 'part_name' in extracted:
            formatted_output += f"Part Name: {extracted['part_name']}\n"
        
        if 'part_number' in extracted:
            formatted_output += f"Part Number: {extracted['part_number']}\n"
        
        if 'part_id' in extracted:
            formatted_output += f"ID: {extracted['part_id']}\n"
        
        if 'free_length' in extracted:
            formatted_output += f"Free Length: {extracted['free_length']} mm\n"
        
        if 'coil_count' in extracted:
            formatted_output += f"No of Coils: {extracted['coil_count']}\n"
        
        if 'wire_dia' in extracted:
            formatted_output += f"Wire Dia: {extracted['wire_dia']} mm\n"
        
        if 'outer_dia' in extracted:
            formatted_output += f"OD: {extracted['outer_dia']} mm\n"
        
        if 'safety_limit' in extracted:
            formatted_output += f"Safety limit: {extracted['safety_limit']} N\n"
        
        if 'force_unit' in extracted:
            formatted_output += f"Force Unit: {extracted['force_unit']}\n"
        
        if 'test_mode' in extracted:
            formatted_output += f"Test Mode: {extracted['test_mode']}\n"
        
        if 'component_type' in extracted:
            formatted_output += f"Component Type: {extracted['component_type']}\n"
        
        if 'first_speed' in extracted:
            formatted_output += f"First Speed: {extracted['first_speed']} mm/s\n"
        
        if 'second_speed' in extracted:
            formatted_output += f"Second Speed: {extracted['second_speed']} mm/s\n"
        
        if 'offer_number' in extracted:
            formatted_output += f"Offer Number: {extracted['offer_number']}\n"
        
        if 'production_batch_number' in extracted:
            formatted_output += f"Production Batch: {extracted['production_batch_number']}\n"
        
        if 'part_rev_no_date' in extracted:
            formatted_output += f"Part Revision: {extracted['part_rev_no_date']}\n"
        
        if 'material_description' in extracted:
            formatted_output += f"Material: {extracted['material_description']}\n"
        
        if 'surface_treatment' in extracted:
            formatted_output += f"Surface Treatment: {extracted['surface_treatment']}\n"
        
        if 'end_coil_finishing' in extracted:
            formatted_output += f"End Coil Finishing: {extracted['end_coil_finishing']}\n"
        
        # Add set points in order
        for index in sorted(set_points.keys()):
            sp = set_points[index]
            if "position" in sp:
                formatted_output += f"Set Point-{index} in mm: {sp['position']} mm\n"
            if "load" in sp and "tolerance" in sp:
                formatted_output += f"Set Point-{index} Load In N: {sp['load']}±{sp['tolerance']}% N\n"
        
        # If we didn't extract anything meaningful, try line-by-line analysis
        if not formatted_output.strip():
            # Split into lines and process each one
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if any(key in line.lower() for key in ['part name', 'part number', 'id:', 'free length', 
                                                      'coils', 'colis', 'wire dia', 'wired', 'od:', 'set point', 'set poni', 'safety']):
                    formatted_output += line + '\n'
            
            # If still empty, return original
            if not formatted_output.strip():
                return text
        
        return formatted_output

    # New methods for API key and clear chat functionality
    def on_api_key_changed(self, api_key):
        """Handle API key changes.
        
        Args:
            api_key: New API key.
        """
        # Update settings
        self.settings_service.set_api_key(api_key)
        
        # Emit signal
        self.api_key_changed.emit(api_key)
    
    def on_clear_chat_clicked(self):
        """Handle clear chat button clicks."""
        # Emit signal
        self.clear_chat_clicked.emit()

    def create_text_input_tab(self):
        """Create the text input tab."""
        text_input_tab = QWidget()
        text_input_layout = QVBoxLayout()
        
        # Instructions
        instructions_label = QLabel("Paste or type spring specifications in the format below:")
        text_input_layout.addWidget(instructions_label)
        
        # Format hint
        format_hint = QLabel(
            "Format: Part Name, Part Number, ID, Free Length, No of Coils, "
            "Wire Dia, OD, Set Points, Safety Limit"
        )
        format_hint.setStyleSheet("color: gray; font-style: italic;")
        format_hint.setWordWrap(True)
        text_input_layout.addWidget(format_hint)
        
        # Upload button
        upload_layout = QHBoxLayout()
        upload_button = QPushButton("Upload PDF")
        upload_button.clicked.connect(self.on_upload_pdf)
        upload_layout.addWidget(upload_button)
        
        # Status label for upload
        self.upload_status = QLabel("")
        self.upload_status.setStyleSheet("color: gray; font-style: italic;")
        upload_layout.addWidget(self.upload_status, 1)  # Give it stretch factor
        
        text_input_layout.addLayout(upload_layout)
        
        # Text input
        input_label = QLabel("Enter specifications:")
        text_input_layout.addWidget(input_label)
        
        self.specs_text_input = QTextEdit()
        self.specs_text_input.setPlaceholderText("Paste specifications here...")
        text_input_layout.addWidget(self.specs_text_input)
        
        # Parse button
        parse_button = QPushButton("Parse Specifications")
        parse_button.clicked.connect(self.on_parse_specifications)
        text_input_layout.addWidget(parse_button)
        
        # Auto-update checkbox
        self.auto_update_checkbox = QCheckBox("Update specifications as you type")
        self.auto_update_checkbox.setChecked(False)
        self.auto_update_checkbox.stateChanged.connect(self.on_auto_update_changed)
        text_input_layout.addWidget(self.auto_update_checkbox)
        
        text_input_tab.setLayout(text_input_layout)
        return text_input_tab

    def on_reset_specifications_clicked(self):
        """Handle reset specifications button clicks."""
        # Ask for confirmation
        confirmation = QMessageBox.question(
            self,
            "Reset Specifications",
            "Are you sure you want to reset ALL specifications including set points? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirmation == QMessageBox.Yes:
            # Create a completely new default spring specification with NO set points
            default_spec = SpringSpecification(create_defaults=False)
            
            print("Reset: Created new specification with empty set points")
            
            # Set it in the settings service
            self.settings_service.set_spring_specification(default_spec)
            
            # Update our local copy
            self.specifications = default_spec
            
            # Refresh the UI
            self.load_specifications()
            
            # Inform the sequence generator of the change
            self.sequence_generator.set_spring_specification(default_spec)
            
            # Emit signal for specifications changed
            self.specifications_changed.emit(default_spec)
            
            # Show success message
            QMessageBox.information(
                self,
                "Reset Complete",
                "All specifications and set points have been reset to default values."
            ) 

    def _update_unit_suffixes(self):
        """Update suffixes based on unit selection."""
        disp_unit = self.unit_input.currentText()
        force_unit = self.force_unit_input.currentText()
        
        # Update displacement unit suffixes
        self.free_length_input.setSuffix(f" {disp_unit}")
        self.wire_dia_input.setSuffix(f" {disp_unit}")
        self.outer_dia_input.setSuffix(f" {disp_unit}")
        
        # Update force unit suffixes
        self.safety_limit_input.setSuffix(f" {force_unit}")
        
        # Note: First and Second Speed inputs have fixed "mm/s" suffix
        # and are not updated here
        
        # Update set point widgets if they exist
        for sp_widget in self.set_point_widgets:
            sp_widget.position_input.setSuffix(f" {disp_unit}")
            sp_widget.load_input.setSuffix(f" {force_unit}")
            
        print(f"Updated UI unit suffixes: displacement={disp_unit}, force={force_unit}") 