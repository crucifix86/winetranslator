"""
Add Application Dialog for WineTranslator.

Easy-to-use wizard for adding Windows applications.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GObject, Gio
import os
import threading
import logging

from ..database.db import Database
from ..core.runner_manager import RunnerManager
from ..core.prefix_manager import PrefixManager
from ..core.dependency_manager import DependencyManager

# Set up logging
logger = logging.getLogger(__name__)


class AddAppDialog(Adw.Window):
    """Dialog for adding a new application with automatic dependency detection."""

    __gsignals__ = {
        'app-added': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, parent, db: Database, runner_manager: RunnerManager,
                 prefix_manager: PrefixManager, dep_manager: DependencyManager):
        """Initialize the add application dialog."""
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(600, 500)
        self.set_title("Add Application")

        self.db = db
        self.runner_manager = runner_manager
        self.prefix_manager = prefix_manager
        self.dep_manager = dep_manager

        # State
        self.selected_exe = None
        self.selected_prefix_id = None
        self.detected_deps = set()

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header
        header = Adw.HeaderBar()
        main_box.append(header)

        # Content box with clamp
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        main_box.append(clamp)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_spacing(24)
        clamp.set_child(content_box)

        # Title
        title = Gtk.Label(label="Add Windows Application")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        content_box.append(title)

        # Step 1: Select executable
        exec_group = Adw.PreferencesGroup()
        exec_group.set_title("1. Select Executable")
        content_box.append(exec_group)

        exec_row = Adw.ActionRow()
        exec_row.set_title("Windows Executable (.exe)")
        self.exec_button = Gtk.Button(label="Choose File...")
        self.exec_button.set_valign(Gtk.Align.CENTER)
        self.exec_button.connect("clicked", self._on_choose_exe_clicked)
        exec_row.add_suffix(self.exec_button)
        exec_group.add(exec_row)

        self.exec_label = Gtk.Label(label="No file selected")
        self.exec_label.set_halign(Gtk.Align.START)
        self.exec_label.add_css_class("dim-label")
        self.exec_label.add_css_class("caption")
        self.exec_label.set_margin_start(12)
        self.exec_label.set_wrap(True)
        exec_group.add(self.exec_label)

        # Step 2: Application name
        name_group = Adw.PreferencesGroup()
        name_group.set_title("2. Application Name")
        content_box.append(name_group)

        self.name_entry = Adw.EntryRow()
        self.name_entry.set_title("Name")
        name_group.add(self.name_entry)

        # Step 3: Prefix selection
        prefix_group = Adw.PreferencesGroup()
        prefix_group.set_title("3. Wine Prefix")
        prefix_group.set_description("Prefixes isolate applications from each other")
        content_box.append(prefix_group)

        # Prefix combo row
        self.prefix_combo = Adw.ComboRow()
        self.prefix_combo.set_title("Prefix")

        # Create prefix list model
        self.prefix_list = Gtk.StringList()
        self.prefix_combo.set_model(self.prefix_list)
        prefix_group.add(self.prefix_combo)

        # New prefix option
        new_prefix_row = Adw.ActionRow()
        new_prefix_row.set_title("Create New Prefix")
        new_prefix_button = Gtk.Button(label="Create...")
        new_prefix_button.set_valign(Gtk.Align.CENTER)
        new_prefix_button.connect("clicked", self._on_create_prefix_clicked)
        new_prefix_row.add_suffix(new_prefix_button)
        prefix_group.add(new_prefix_row)

        # Step 4: Dependencies (shown after exe selected)
        self.dep_group = Adw.PreferencesGroup()
        self.dep_group.set_title("4. Dependencies")
        self.dep_group.set_description("Recommended dependencies will be installed automatically")
        self.dep_group.set_visible(False)
        content_box.append(self.dep_group)

        self.dep_label = Gtk.Label()
        self.dep_label.set_halign(Gtk.Align.START)
        self.dep_label.set_wrap(True)
        self.dep_label.set_margin_start(12)
        self.dep_group.add(self.dep_label)

        # Bottom bar with buttons
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bottom_box.set_margin_top(12)
        bottom_box.set_margin_bottom(12)
        bottom_box.set_margin_start(12)
        bottom_box.set_margin_end(12)
        bottom_box.set_spacing(12)
        bottom_box.set_halign(Gtk.Align.END)
        main_box.append(bottom_box)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda b: self.close())
        bottom_box.append(cancel_button)

        self.add_button = Gtk.Button(label="Add Application")
        self.add_button.add_css_class("suggested-action")
        self.add_button.set_sensitive(False)
        self.add_button.connect("clicked", self._on_add_clicked)
        bottom_box.append(self.add_button)

        # Load prefixes
        self._load_prefixes()

    def _load_prefixes(self):
        """Load available prefixes into combo box."""
        prefixes = self.prefix_manager.get_all_prefixes()

        self.prefix_list.splice(0, self.prefix_list.get_n_items(), [])
        self.prefix_ids = []

        if not prefixes:
            # Create default prefix
            runner = self.runner_manager.get_default_runner()
            if runner:
                success, msg, prefix_id = self.prefix_manager.get_or_create_default_prefix(runner['id'])
                if success:
                    prefixes = self.prefix_manager.get_all_prefixes()

        for prefix in prefixes:
            self.prefix_list.append(prefix['name'])
            self.prefix_ids.append(prefix['id'])

        if prefixes:
            self.prefix_combo.set_selected(0)

    def _on_choose_exe_clicked(self, button):
        """Handle choose executable button click."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Windows Executable")

        # Filter for .exe files
        filter_exe = Gtk.FileFilter()
        filter_exe.set_name("Windows Executables")
        filter_exe.add_pattern("*.exe")
        filter_exe.add_pattern("*.EXE")

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_exe)
        filters.append(filter_all)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_exe)

        dialog.open(self, None, self._on_exe_selected)

    def _on_exe_selected(self, dialog, result):
        """Handle executable file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                self.selected_exe = file.get_path()
                self.exec_label.set_text(self.selected_exe)

                # Auto-fill name if empty
                if not self.name_entry.get_text():
                    filename = os.path.basename(self.selected_exe)
                    name = os.path.splitext(filename)[0]
                    self.name_entry.set_text(name)

                # Detect dependencies
                self._detect_dependencies()

                # Enable add button
                self._update_add_button()

        except GLib.Error as e:
            if e.code != 2:  # Ignore dismiss
                print(f"Error selecting file: {e}")

    def _detect_dependencies(self):
        """Detect required dependencies for the selected executable."""
        if not self.selected_exe:
            return

        self.detected_deps = self.dep_manager.detect_required_dependencies(self.selected_exe)

        if self.detected_deps:
            dep_text = "Will install: " + ", ".join(sorted(self.detected_deps))
            self.dep_label.set_text(dep_text)
            self.dep_group.set_visible(True)
        else:
            self.dep_group.set_visible(False)

    def _on_create_prefix_clicked(self, button):
        """Handle create new prefix button click."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Create New Prefix")
        dialog.set_body("Enter a name for the new Wine prefix:")

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)

        entry = Gtk.Entry()
        entry.set_placeholder_text("Prefix name")
        entry.set_margin_top(12)
        entry.set_margin_bottom(12)
        entry.set_margin_start(12)
        entry.set_margin_end(12)

        # Add entry to dialog content
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(entry)
        dialog.set_extra_child(box)

        dialog.connect("response", self._on_create_prefix_response, entry)
        dialog.present()

    def _on_create_prefix_response(self, dialog, response, entry):
        """Handle create prefix dialog response."""
        if response == "create":
            name = entry.get_text().strip()
            if name:
                self._create_prefix(name)

    def _create_prefix(self, name: str):
        """Create a new Wine prefix."""
        runner = self.runner_manager.get_default_runner()
        if not runner:
            return

        # Show progress dialog
        progress_dialog = Adw.MessageDialog.new(self)
        progress_dialog.set_heading("Creating Prefix")
        progress_dialog.set_body(f"Creating Wine prefix '{name}'...")
        progress_dialog.present()

        def create_thread():
            success, message, prefix_id = self.prefix_manager.create_prefix(name, runner['id'])
            GLib.idle_add(self._on_prefix_created, success, message, progress_dialog)

        thread = threading.Thread(target=create_thread, daemon=True)
        thread.start()

    def _on_prefix_created(self, success, message, progress_dialog):
        """Handle prefix creation completion."""
        progress_dialog.close()

        if success:
            self._load_prefixes()
            # Select the newly created prefix
            self.prefix_combo.set_selected(len(self.prefix_ids) - 1)
        else:
            error_dialog = Adw.MessageDialog.new(self)
            error_dialog.set_heading("Error Creating Prefix")
            error_dialog.set_body(message)
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def _update_add_button(self):
        """Update the add button sensitivity."""
        can_add = (self.selected_exe is not None and
                  self.name_entry.get_text().strip() != "" and
                  self.prefix_combo.get_selected() != Gtk.INVALID_LIST_POSITION)
        self.add_button.set_sensitive(can_add)

    def _on_add_clicked(self, button):
        """Handle add application button click."""
        name = self.name_entry.get_text().strip()
        if not name or not self.selected_exe:
            return

        selected_idx = self.prefix_combo.get_selected()
        if selected_idx == Gtk.INVALID_LIST_POSITION:
            return

        prefix_id = self.prefix_ids[selected_idx]

        # Show progress dialog
        self.add_button.set_sensitive(False)
        progress_dialog = Adw.MessageDialog.new(self)
        progress_dialog.set_heading("Adding Application")
        progress_dialog.set_body("Starting...")
        progress_dialog.present()

        def update_progress(message):
            """Update progress dialog message."""
            progress_dialog.set_body(message)
            return False

        def add_thread():
            # Add application to database
            GLib.idle_add(update_progress, "Adding application to database...")

            from ..core.app_launcher import AppLauncher
            launcher = AppLauncher(self.db)
            success, message, app_id = launcher.add_application(
                name=name,
                executable_path=self.selected_exe,
                prefix_id=prefix_id
            )

            if not success or not app_id:
                GLib.idle_add(self._on_add_complete, False, message, progress_dialog)
                return

            # Install dependencies
            if self.detected_deps and self.dep_manager.is_winetricks_available():
                prefix = self.prefix_manager.get_prefix(prefix_id)
                if prefix:
                    deps_list = sorted(self.detected_deps)
                    total = len(deps_list)
                    for idx, dep in enumerate(deps_list, 1):
                        GLib.idle_add(update_progress, f"Installing dependency {idx} of {total}: {dep}...")
                        self.dep_manager.install_dependency(
                            prefix['path'],
                            dep,
                            prefix.get('runner_path')
                        )

            GLib.idle_add(self._on_add_complete, True, f"Application '{name}' added successfully", progress_dialog)

        thread = threading.Thread(target=add_thread, daemon=True)
        thread.start()

    def _on_add_complete(self, success, message, progress_dialog):
        """Handle application add completion."""
        progress_dialog.close()

        if success:
            self.emit('app-added')
            self.close()
        else:
            error_dialog = Adw.MessageDialog.new(self)
            error_dialog.set_heading("Error")
            error_dialog.set_body(message)
            error_dialog.add_response("ok", "OK")
            error_dialog.present()
            self.add_button.set_sensitive(True)
