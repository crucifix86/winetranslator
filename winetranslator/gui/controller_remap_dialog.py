"""
Controller button remapping dialog.

Interactive GUI for remapping Xbox controller buttons.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import threading
import logging
from typing import Optional, Dict
from ..utils.controller_input import ControllerInput

logger = logging.getLogger(__name__)


class ControllerRemapDialog(Adw.Window):
    """Dialog for remapping controller buttons."""

    # Xbox controller button layout
    BUTTONS = {
        'a': 'A Button',
        'b': 'B Button',
        'x': 'X Button',
        'y': 'Y Button',
        'back': 'Back Button',
        'start': 'Start Button',
        'guide': 'Guide/Home Button',
        'leftshoulder': 'Left Bumper (LB)',
        'rightshoulder': 'Right Bumper (RB)',
        'leftstick': 'Left Stick Click (L3)',
        'rightstick': 'Right Stick Click (R3)',
        'leftx': 'Left Stick X-Axis',
        'lefty': 'Left Stick Y-Axis',
        'rightx': 'Right Stick X-Axis',
        'righty': 'Right Stick Y-Axis',
        'lefttrigger': 'Left Trigger (LT)',
        'righttrigger': 'Right Trigger (RT)',
        'dpup': 'D-Pad Up',
        'dpdown': 'D-Pad Down',
        'dpleft': 'D-Pad Left',
        'dpright': 'D-Pad Right',
    }

    def __init__(self, parent, app_id: int, current_mapping: Optional[str] = None):
        """
        Initialize the controller remapping dialog.

        Args:
            parent: Parent window
            app_id: Application ID
            current_mapping: Current SDL mapping string (if any)
        """
        super().__init__()
        self.app_id = app_id
        self.parent_window = parent
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(700, 600)
        self.set_title("Remap Controller Buttons")

        # Initialize controller input
        try:
            self.controller = ControllerInput()
            self.controller_name = self.controller.device_name
            self.controller_guid = self.controller.guid
        except Exception as e:
            logger.error(f"Failed to initialize controller: {e}")
            self.show_error("No controller detected. Please connect a controller and try again.")
            return

        # Parse current mapping or use defaults
        self.button_mapping = self._parse_mapping(current_mapping) if current_mapping else {}
        self.default_mapping = self._parse_mapping(self.controller.get_default_mapping())

        # Current remapping button
        self.remapping_button = None
        self.remapping_thread = None

        self._build_ui()

    def _parse_mapping(self, mapping_str: str) -> Dict[str, str]:
        """
        Parse SDL mapping string into a dictionary.

        Args:
            mapping_str: SDL mapping string

        Returns:
            Dictionary of button name -> mapping value
        """
        if not mapping_str:
            return {}

        parts = mapping_str.split(',')
        if len(parts) < 3:
            return {}

        # Skip GUID and name, parse button mappings
        mapping_dict = {}
        for part in parts[2:]:
            if ':' in part:
                key, value = part.split(':', 1)
                mapping_dict[key.strip()] = value.strip()

        return mapping_dict

    def _build_mapping_string(self) -> str:
        """
        Build SDL mapping string from current button mappings.

        Returns:
            Complete SDL mapping string
        """
        # Start with GUID and name
        mapping_parts = [self.controller_guid, self.controller_name]

        # Add button mappings
        for button_name in self.BUTTONS.keys():
            if button_name in self.button_mapping:
                mapping_parts.append(f"{button_name}:{self.button_mapping[button_name]}")
            elif button_name in self.default_mapping:
                mapping_parts.append(f"{button_name}:{self.default_mapping[button_name]}")

        return ','.join(mapping_parts)

    def show_error(self, message: str):
        """Show error message and close dialog."""
        dialog = Adw.MessageDialog.new(self.parent_window)
        dialog.set_heading("Controller Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()
        self.close()

    def _build_ui(self):
        """Build the dialog UI."""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Save button
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self._on_save_clicked)
        header.pack_end(save_button)

        # Reset button
        reset_button = Gtk.Button(label="Reset to Defaults")
        reset_button.connect("clicked", self._on_reset_clicked)
        header.pack_start(reset_button)

        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        main_box.append(content_box)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>Controller: {self.controller_name}</b>")
        title_label.set_halign(Gtk.Align.START)
        content_box.append(title_label)

        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<i>Click a button below, then press the physical button/axis you want to map to it.\n"
            "Leave unmapped to use default Xbox controller layout.</i>"
        )
        instructions.set_halign(Gtk.Align.START)
        instructions.set_wrap(True)
        content_box.append(instructions)

        # Scrolled window for button list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_box.append(scrolled)

        # List box for buttons
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")
        scrolled.set_child(self.list_box)

        # Add button rows
        self.button_rows = {}
        for button_id, button_name in self.BUTTONS.items():
            row = self._create_button_row(button_id, button_name)
            self.list_box.append(row)
            self.button_rows[button_id] = row

    def _create_button_row(self, button_id: str, button_name: str) -> Adw.ActionRow:
        """Create a row for a button mapping."""
        row = Adw.ActionRow()
        row.set_title(button_name)

        # Current mapping label
        mapping_label = Gtk.Label()
        mapping_label.set_halign(Gtk.Align.END)
        mapping_label.add_css_class("dim-label")

        # Get current or default mapping
        if button_id in self.button_mapping:
            current = self.button_mapping[button_id]
            mapping_label.set_text(current)
        elif button_id in self.default_mapping:
            current = self.default_mapping[button_id]
            mapping_label.set_text(f"{current} (default)")
        else:
            mapping_label.set_text("Not mapped")

        row.add_suffix(mapping_label)

        # Remap button
        remap_button = Gtk.Button(label="Remap")
        remap_button.set_valign(Gtk.Align.CENTER)
        remap_button.connect("clicked", self._on_remap_button_clicked, button_id, mapping_label)
        row.add_suffix(remap_button)

        # Clear button (only show if custom mapping exists)
        if button_id in self.button_mapping:
            clear_button = Gtk.Button(icon_name="edit-clear-symbolic")
            clear_button.set_valign(Gtk.Align.CENTER)
            clear_button.set_tooltip_text("Clear custom mapping")
            clear_button.connect("clicked", self._on_clear_button_clicked, button_id, mapping_label)
            row.add_suffix(clear_button)
            # Store for later reference
            row.clear_button = clear_button

        row.mapping_label = mapping_label
        return row

    def _on_remap_button_clicked(self, button: Gtk.Button, button_id: str, mapping_label: Gtk.Label):
        """Handle remap button click."""
        # Show remapping dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(f"Remap {self.BUTTONS[button_id]}")
        dialog.set_body(f"Press the physical button or move the axis you want to map to {self.BUTTONS[button_id]}.\n\nWaiting for input...")
        dialog.add_response("cancel", "Cancel")
        dialog.present()

        self.remapping_button = button_id
        self.remapping_dialog = dialog

        # Start input detection thread
        def detect_input():
            try:
                with ControllerInput() as controller:
                    result = controller.wait_for_input(timeout=15.0)
                    if result:
                        input_type, input_value = result
                        # Build mapping string
                        if input_type == 'button':
                            mapping_str = f"b{input_value}"
                        else:  # axis
                            mapping_str = input_value  # Already formatted as "aX+" or "aX-"

                        GLib.idle_add(self._on_input_detected, button_id, mapping_str, mapping_label)
                    else:
                        GLib.idle_add(self._on_input_timeout)
            except Exception as e:
                logger.error(f"Input detection error: {e}")
                GLib.idle_add(self._on_input_timeout)

        self.remapping_thread = threading.Thread(target=detect_input, daemon=True)
        self.remapping_thread.start()

    def _on_input_detected(self, button_id: str, mapping_str: str, mapping_label: Gtk.Label):
        """Handle input detection completion."""
        # Close remapping dialog
        if hasattr(self, 'remapping_dialog'):
            self.remapping_dialog.close()

        # Update mapping
        self.button_mapping[button_id] = mapping_str
        mapping_label.set_text(mapping_str)

        # Add clear button if it doesn't exist
        row = self.button_rows[button_id]
        if not hasattr(row, 'clear_button'):
            clear_button = Gtk.Button(icon_name="edit-clear-symbolic")
            clear_button.set_valign(Gtk.Align.CENTER)
            clear_button.set_tooltip_text("Clear custom mapping")
            clear_button.connect("clicked", self._on_clear_button_clicked, button_id, mapping_label)
            row.add_suffix(clear_button)
            row.clear_button = clear_button

        return False

    def _on_input_timeout(self):
        """Handle input detection timeout."""
        if hasattr(self, 'remapping_dialog'):
            self.remapping_dialog.close()

        error_dialog = Adw.MessageDialog.new(self)
        error_dialog.set_heading("Timeout")
        error_dialog.set_body("No input detected. Please try again.")
        error_dialog.add_response("ok", "OK")
        error_dialog.present()

        return False

    def _on_clear_button_clicked(self, button: Gtk.Button, button_id: str, mapping_label: Gtk.Label):
        """Handle clear button click."""
        # Remove custom mapping
        if button_id in self.button_mapping:
            del self.button_mapping[button_id]

        # Update label to show default
        if button_id in self.default_mapping:
            mapping_label.set_text(f"{self.default_mapping[button_id]} (default)")
        else:
            mapping_label.set_text("Not mapped")

        # Remove clear button
        row = self.button_rows[button_id]
        if hasattr(row, 'clear_button'):
            row.remove(row.clear_button)
            delattr(row, 'clear_button')

    def _on_reset_clicked(self, button: Gtk.Button):
        """Handle reset to defaults button click."""
        confirm_dialog = Adw.MessageDialog.new(self)
        confirm_dialog.set_heading("Reset to Defaults?")
        confirm_dialog.set_body("This will clear all custom button mappings and restore the default Xbox controller layout.")
        confirm_dialog.add_response("cancel", "Cancel")
        confirm_dialog.add_response("reset", "Reset")
        confirm_dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        confirm_dialog.connect("response", self._on_reset_confirmed)
        confirm_dialog.present()

    def _on_reset_confirmed(self, dialog: Adw.MessageDialog, response: str):
        """Handle reset confirmation."""
        if response == "reset":
            # Clear all custom mappings
            self.button_mapping.clear()

            # Update all labels
            for button_id, row in self.button_rows.items():
                mapping_label = row.mapping_label

                # Update to default
                if button_id in self.default_mapping:
                    mapping_label.set_text(f"{self.default_mapping[button_id]} (default)")
                else:
                    mapping_label.set_text("Not mapped")

                # Remove clear button if it exists
                if hasattr(row, 'clear_button'):
                    row.remove(row.clear_button)
                    delattr(row, 'clear_button')

    def _on_save_clicked(self, button: Gtk.Button):
        """Handle save button click."""
        # Build final mapping string
        mapping_str = self._build_mapping_string()

        # Store in database
        from ..database.db import Database
        db = Database()
        db.set_config(self.app_id, 'controller_mapping', mapping_str)
        db.close()

        # Show success message
        toast_overlay = self.parent_window.toast_overlay
        toast = Adw.Toast.new("Controller mapping saved")
        toast.set_timeout(2)
        toast_overlay.add_toast(toast)

        logger.info(f"Saved controller mapping for app {self.app_id}: {mapping_str}")

        self.close()

    def get_mapping(self) -> str:
        """Get the current mapping string."""
        return self._build_mapping_string()
