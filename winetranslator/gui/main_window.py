"""
Main Window for WineTranslator.

GTK4 application window with application library and management interface.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import os
import threading
import logging
from typing import Optional

from ..database.db import Database
from ..core.runner_manager import RunnerManager
from ..core.prefix_manager import PrefixManager
from ..core.app_launcher import AppLauncher
from ..core.dependency_manager import DependencyManager
from ..core.updater import Updater

# Set up logging
logger = logging.getLogger(__name__)


class MainWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, app, db: Database):
        """
        Initialize the main window.

        Args:
            app: Gtk.Application instance.
            db: Database instance.
        """
        super().__init__(application=app)
        self.db = db

        # Initialize managers
        self.runner_manager = RunnerManager(db)
        self.prefix_manager = PrefixManager(db)
        self.app_launcher = AppLauncher(db)
        self.dep_manager = DependencyManager(db)
        self.updater = Updater()

        # Window properties
        self.set_title("WineTranslator")
        self.set_default_size(1000, 700)

        # Build UI
        self._build_ui()

        # Initialize system
        GLib.idle_add(self._initialize_system)

    def _build_ui(self):
        """Build the user interface."""
        # Main box container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Add button in header
        add_button = Gtk.Button(icon_name="list-add-symbolic")
        add_button.set_tooltip_text("Add Application")
        add_button.connect("clicked", self._on_add_app_clicked)
        header.pack_start(add_button)

        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append("Check for Updates", "app.update")
        menu.append("Preferences", "app.preferences")
        menu.append("About", "app.about")
        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)

        # Toolbar view for content
        toolbar_view = Adw.ToolbarView()
        main_box.append(toolbar_view)

        # Main content - scrolled window with application grid
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        toolbar_view.set_content(scrolled)

        # Flow box for application icons
        self.app_flow_box = Gtk.FlowBox()
        self.app_flow_box.set_valign(Gtk.Align.START)
        self.app_flow_box.set_max_children_per_line(6)
        self.app_flow_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.app_flow_box.set_margin_top(12)
        self.app_flow_box.set_margin_bottom(12)
        self.app_flow_box.set_margin_start(12)
        self.app_flow_box.set_margin_end(12)
        self.app_flow_box.set_row_spacing(12)
        self.app_flow_box.set_column_spacing(12)
        scrolled.set_child(self.app_flow_box)

        # Empty state
        self.empty_state = self._create_empty_state()

        # Status page placeholder (shown when no apps)
        self.status_page = Adw.StatusPage()
        self.status_page.set_title("No Applications Yet")
        self.status_page.set_description("Add Windows applications to get started")
        self.status_page.set_icon_name("application-x-executable-symbolic")

    def _create_empty_state(self) -> Gtk.Box:
        """Create empty state widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_spacing(12)

        label = Gtk.Label(label="No applications yet")
        label.add_css_class("title-1")
        box.append(label)

        sublabel = Gtk.Label(label="Click the + button to add a Windows application")
        sublabel.add_css_class("dim-label")
        box.append(sublabel)

        return box

    def _initialize_system(self):
        """Initialize Wine runners and load applications."""
        # Ensure we have at least one Wine runner
        try:
            self.runner_manager.ensure_default_runner()
        except RuntimeError as e:
            self._show_error_dialog("Wine Not Found", str(e))
            return

        # Load applications
        self._refresh_applications()

    def _refresh_applications(self):
        """Refresh the application list."""
        # Clear existing items
        child = self.app_flow_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.app_flow_box.remove(child)
            child = next_child

        # Load applications from database
        apps = self.app_launcher.get_all_applications()

        if not apps:
            # Show empty state
            self.app_flow_box.append(self.empty_state)
            return

        # Add application cards
        for app in apps:
            card = self._create_app_card(app)
            self.app_flow_box.append(card)

    def _create_app_card(self, app: dict) -> Gtk.Box:
        """Create an application card widget."""
        # Main card container
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.set_size_request(150, 180)
        card.add_css_class("card")

        # Button for clicking
        button = Gtk.Button()
        button.set_has_frame(False)
        button.connect("clicked", self._on_app_card_clicked, app['id'])

        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        button_box.set_spacing(8)
        button_box.set_margin_top(12)
        button_box.set_margin_bottom(12)
        button_box.set_margin_start(12)
        button_box.set_margin_end(12)
        button.set_child(button_box)

        # Icon
        if app['icon_path'] and os.path.isfile(app['icon_path']):
            icon = Gtk.Image.new_from_file(app['icon_path'])
        else:
            icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        icon.set_pixel_size(64)
        button_box.append(icon)

        # Application name
        name_label = Gtk.Label(label=app['name'])
        name_label.set_wrap(True)
        name_label.set_max_width_chars(20)
        name_label.set_justify(Gtk.Justification.CENTER)
        button_box.append(name_label)

        # Prefix name (smaller text)
        prefix_label = Gtk.Label(label=app['prefix_name'])
        prefix_label.add_css_class("dim-label")
        prefix_label.add_css_class("caption")
        button_box.append(prefix_label)

        card.append(button)

        return card

    def _on_app_card_clicked(self, button, app_id: int):
        """Handle application card click."""
        # Show app details dialog with launch button
        self._show_app_dialog(app_id)

    def _show_app_dialog(self, app_id: int):
        """Show application details dialog."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(app['name'])
        dialog.set_body(f"Prefix: {app['prefix_name']}\nRunner: {app['runner_name']}")

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("launch", "Launch")
        dialog.add_response("remove", "Remove")
        dialog.set_response_appearance("launch", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)

        dialog.connect("response", self._on_app_dialog_response, app_id)
        dialog.present()

    def _on_app_dialog_response(self, dialog, response, app_id: int):
        """Handle app dialog response."""
        if response == "launch":
            self._launch_application(app_id)
        elif response == "remove":
            self._remove_application(app_id)

    def _launch_application(self, app_id: int):
        """Launch an application."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Show launching toast
        toast = Adw.Toast.new(f"Launching {app['name']}...")
        toast.set_timeout(2)

        # Launch in background thread
        def launch_thread():
            success, message, process = self.app_launcher.launch(app_id)

            GLib.idle_add(self._on_launch_complete, success, message, app['name'])

        thread = threading.Thread(target=launch_thread, daemon=True)
        thread.start()

    def _on_launch_complete(self, success: bool, message: str, app_name: str):
        """Handle launch completion."""
        if success:
            toast = Adw.Toast.new(f"{app_name} launched successfully")
        else:
            toast = Adw.Toast.new(f"Failed to launch {app_name}: {message}")
        toast.set_timeout(3)

    def _remove_application(self, app_id: int):
        """Remove an application."""
        success, message = self.app_launcher.remove_application(app_id)

        if success:
            self._refresh_applications()
            toast = Adw.Toast.new(message)
        else:
            toast = Adw.Toast.new(f"Error: {message}")

        toast.set_timeout(2)

    def _on_add_app_clicked(self, button):
        """Handle add application button click."""
        logger.info("Add application button clicked")
        try:
            from .add_app_dialog import AddAppDialog
            logger.info("Creating AddAppDialog")
            dialog = AddAppDialog(self, self.db, self.runner_manager, self.prefix_manager, self.dep_manager)
            dialog.connect("app-added", self._on_app_added)
            logger.info("Presenting AddAppDialog")
            dialog.present()
        except Exception as e:
            logger.error(f"Error opening add app dialog: {e}", exc_info=True)
            self._show_error_dialog("Error", f"Failed to open add application dialog: {str(e)}")

    def _on_app_added(self, dialog):
        """Handle application added event."""
        self._refresh_applications()

    def _show_error_dialog(self, title: str, message: str):
        """Show an error dialog."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(title)
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()
