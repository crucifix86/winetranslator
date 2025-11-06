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
        # Toast overlay for showing notifications
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Main box container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

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

        # Tab view for Library and Tested Apps
        self.tab_view = Adw.TabView()
        self.tab_view.set_vexpand(True)
        main_box.append(self.tab_view)

        # Tab bar
        tab_bar = Adw.TabBar()
        tab_bar.set_view(self.tab_view)
        tab_bar.set_autohide(False)
        main_box.insert_child_after(tab_bar, header)

        # Library tab (existing functionality)
        library_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        library_page = self.tab_view.append(library_box)
        library_page.set_title("Library")
        library_page.set_icon(Gio.ThemedIcon.new("folder-symbolic"))

        # Scrolled window for library
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        library_box.append(scrolled)

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

        # Tested Apps tab
        from .tested_apps_view import TestedAppsView
        tested_apps_view = TestedAppsView(
            self.db,
            self.runner_manager,
            self.prefix_manager,
            self.dep_manager
        )
        tested_page = self.tab_view.append(tested_apps_view)
        tested_page.set_title("Tested Apps")
        tested_page.set_icon(Gio.ThemedIcon.new("starred-symbolic"))

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
        card.set_size_request(150, 200)
        card.add_css_class("card")
        card.add_css_class("app-card")

        # Button for clicking
        button = Gtk.Button()
        button.set_has_frame(False)
        button.connect("clicked", self._on_app_card_clicked, app['id'])

        # Add right-click handler
        right_click = Gtk.GestureClick.new()
        right_click.set_button(3)  # Right mouse button
        right_click.connect("pressed", self._on_app_card_right_clicked, app['id'])
        button.add_controller(right_click)

        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        button_box.set_spacing(8)
        button_box.set_margin_top(12)
        button_box.set_margin_bottom(12)
        button_box.set_margin_start(12)
        button_box.set_margin_end(12)
        button.set_child(button_box)

        # Icon with styled background
        icon_box = Gtk.Box()
        icon_box.set_halign(Gtk.Align.CENTER)
        icon_box.add_css_class("app-icon")

        if app['icon_path'] and os.path.isfile(app['icon_path']):
            icon = Gtk.Image.new_from_file(app['icon_path'])
        else:
            icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        icon.set_pixel_size(64)
        icon_box.append(icon)
        button_box.append(icon_box)

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

    def _on_app_card_right_clicked(self, gesture, n_press, x, y, app_id: int):
        """Handle application card right-click."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Get the executable directory
        exe_path = app.get('executable_path', '')
        if exe_path and os.path.exists(exe_path):
            exe_dir = os.path.dirname(exe_path)
            self._open_directory(exe_dir)
        else:
            logger.warning(f"Executable path not found for app {app_id}")

    def _open_directory(self, directory: str):
        """Open a directory in the file manager."""
        try:
            import subprocess
            subprocess.Popen(['xdg-open', directory])
            logger.info(f"Opened directory: {directory}")
        except Exception as e:
            logger.error(f"Error opening directory: {e}", exc_info=True)
            self._show_error_dialog("Error", f"Failed to open directory: {str(e)}")

    def _show_app_dialog(self, app_id: int):
        """Show application details dialog."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(app['name'])
        dialog.set_body(f"Prefix: {app['prefix_name']}\nRunner: {app['runner_name']}")

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("shortcut", "Create Desktop Shortcut")
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
        elif response == "shortcut":
            self._create_desktop_shortcut(app_id)

    def _launch_application(self, app_id: int):
        """Launch an application."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Show launching toast
        toast = Adw.Toast.new(f"Launching {app['name']}...")
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)

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
        self.toast_overlay.add_toast(toast)

    def _remove_application(self, app_id: int):
        """Remove an application."""
        success, message = self.app_launcher.remove_application(app_id)

        if success:
            self._refresh_applications()
            toast = Adw.Toast.new(message)
        else:
            toast = Adw.Toast.new(f"Error: {message}")

        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)

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

    def _create_desktop_shortcut(self, app_id: int):
        """Create a desktop shortcut for an application."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        try:
            # Desktop entry directory
            desktop_dir = os.path.join(os.path.expanduser('~/.local/share/applications'))
            os.makedirs(desktop_dir, exist_ok=True)

            # Sanitize app name for filename
            safe_name = "".join(c for c in app['name'] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '-')
            desktop_file = os.path.join(desktop_dir, f'winetranslator-{safe_name}.desktop')

            # Check if shortcut already exists
            if os.path.exists(desktop_file):
                toast = Adw.Toast.new(f"Desktop shortcut already exists for {app['name']}")
                toast.set_timeout(3)
                self.toast_overlay.add_toast(toast)
                return

            # Create .desktop file content
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={app['name']}
Comment=Launch {app['name']} with WineTranslator
Exec=winetranslator-launch {app_id}
Icon=application-x-executable
Terminal=false
Categories=Wine;
"""

            # Write .desktop file
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)

            # Make executable
            os.chmod(desktop_file, 0o755)

            logger.info(f"Created desktop shortcut: {desktop_file}")

            toast = Adw.Toast.new(f"Desktop shortcut created for {app['name']}")
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)

        except Exception as e:
            logger.error(f"Error creating desktop shortcut: {e}", exc_info=True)
            self._show_error_dialog("Error", f"Failed to create desktop shortcut: {str(e)}")
