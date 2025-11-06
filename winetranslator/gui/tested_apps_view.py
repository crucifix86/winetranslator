"""
Tested Apps View for WineTranslator.

Shows curated list of tested Windows applications.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import os
import urllib.request
import threading
import logging

from ..database.db import Database
from ..core.runner_manager import RunnerManager
from ..core.prefix_manager import PrefixManager
from ..core.dependency_manager import DependencyManager
from ..data.tested_apps import TESTED_APPS, CATEGORIES

logger = logging.getLogger(__name__)


class TestedAppsView(Gtk.Box):
    """View for browsing and installing tested applications."""

    def __init__(self, db: Database, runner_manager: RunnerManager,
                 prefix_manager: PrefixManager, dep_manager: DependencyManager):
        """Initialize the tested apps view."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.db = db
        self.runner_manager = runner_manager
        self.prefix_manager = prefix_manager
        self.dep_manager = dep_manager

        self._build_ui()

    def _build_ui(self):
        """Build the tested apps UI."""
        # Toolbar with category filter
        toolbar = Adw.HeaderBar()
        toolbar.add_css_class("flat")
        self.append(toolbar)

        # Category dropdown
        category_model = Gtk.StringList()
        for cat in CATEGORIES:
            category_model.append(cat)

        self.category_dropdown = Gtk.DropDown()
        self.category_dropdown.set_model(category_model)
        self.category_dropdown.set_selected(0)  # "All"
        self.category_dropdown.connect("notify::selected", self._on_category_changed)
        toolbar.set_title_widget(self.category_dropdown)

        # Scrolled window for apps list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.append(scrolled)

        # Apps list box
        self.apps_list = Gtk.ListBox()
        self.apps_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.apps_list.add_css_class("boxed-list")
        scrolled.set_child(self.apps_list)

        # Clamp for better width
        clamp = Adw.Clamp()
        clamp.set_maximum_size(1200)
        clamp.set_child(self.apps_list)
        scrolled.set_child(clamp)

        # Load apps
        self._load_apps()

    def _load_apps(self, category='All'):
        """Load tested apps into the list."""
        # Clear existing
        while True:
            row = self.apps_list.get_row_at_index(0)
            if row is None:
                break
            self.apps_list.remove(row)

        # Filter by category
        apps = TESTED_APPS
        if category != 'All':
            apps = [app for app in TESTED_APPS if app['category'] == category]

        # Add app cards
        for app in apps:
            card = self._create_app_card(app)
            self.apps_list.append(card)

    def _create_app_card(self, app):
        """Create a card for a tested app."""
        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        row.set_activatable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_spacing(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        row.set_child(box)

        # Header with name and install button
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_spacing(12)
        box.append(header)

        # App info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        info_box.set_spacing(4)
        info_box.set_hexpand(True)
        header.append(info_box)

        # Name and version
        name_label = Gtk.Label()
        name_label.set_markup(f"<b>{app['name']}</b> {app['version']}")
        name_label.set_halign(Gtk.Align.START)
        info_box.append(name_label)

        # Category badge
        category_label = Gtk.Label(label=app['category'])
        category_label.set_halign(Gtk.Align.START)
        category_label.add_css_class("dim-label")
        category_label.add_css_class("caption")
        info_box.append(category_label)

        # Install button
        install_button = Gtk.Button(label="Download & Install")
        install_button.add_css_class("suggested-action")
        install_button.set_valign(Gtk.Align.CENTER)
        install_button.connect("clicked", self._on_install_clicked, app)
        header.append(install_button)

        # Description
        desc_label = Gtk.Label(label=app['description'])
        desc_label.set_wrap(True)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_margin_top(4)
        box.append(desc_label)

        # Install notes (warning)
        if app.get('install_notes'):
            notes_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            notes_box.set_spacing(8)
            notes_box.set_margin_top(8)
            notes_box.add_css_class("warning")
            box.append(notes_box)

            warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
            notes_box.append(warning_icon)

            notes_label = Gtk.Label(label=app['install_notes'])
            notes_label.set_wrap(True)
            notes_label.set_halign(Gtk.Align.START)
            notes_label.set_hexpand(True)
            notes_box.append(notes_label)

        return row

    def _on_category_changed(self, dropdown, param):
        """Handle category filter change."""
        selected = dropdown.get_selected()
        category = CATEGORIES[selected]
        self._load_apps(category)

    def _on_install_clicked(self, button, app):
        """Handle install button click."""
        logger.info(f"Installing tested app: {app['name']}")

        # Show progress dialog
        progress_dialog = Adw.MessageDialog.new(self.get_root())
        progress_dialog.set_heading(f"Installing {app['name']}")
        progress_dialog.set_body("Downloading installer...")
        progress_dialog.present()

        def download_and_install():
            try:
                # Download installer
                downloads_dir = os.path.expanduser('~/Downloads')
                filename = os.path.basename(app['url'])
                dest_path = os.path.join(downloads_dir, filename)

                logger.info(f"Downloading from {app['url']} to {dest_path}")
                GLib.idle_add(lambda: progress_dialog.set_body(f"Downloading {filename}..."))

                urllib.request.urlretrieve(app['url'], dest_path)
                logger.info(f"Download complete: {dest_path}")

                # Get or create default prefix
                GLib.idle_add(lambda: progress_dialog.set_body("Setting up Wine prefix..."))
                runner = self.runner_manager.get_default_runner()
                if not runner:
                    GLib.idle_add(self._on_install_error, "No Wine runner available", progress_dialog)
                    return

                success, msg, prefix_id = self.prefix_manager.get_or_create_default_prefix(runner['id'])
                if not success:
                    GLib.idle_add(self._on_install_error, f"Failed to create prefix: {msg}", progress_dialog)
                    return

                # Add to database
                GLib.idle_add(lambda: progress_dialog.set_body("Adding to library..."))
                from ..core.app_launcher import AppLauncher
                launcher = AppLauncher(self.db)

                success, message, app_id = launcher.add_application(
                    name=app['name'],
                    executable_path=dest_path,
                    prefix_id=prefix_id,
                    description=app['description']
                )

                if not success or not app_id:
                    GLib.idle_add(self._on_install_error, message, progress_dialog)
                    return

                # Save dependency profile
                if app.get('dependencies'):
                    for dep in app['dependencies']:
                        self.db.add_app_dependency(app_id, dep, auto_detected=False)

                # Install dependencies
                if app.get('dependencies') and self.dep_manager.is_winetricks_available():
                    prefix = self.prefix_manager.get_prefix(prefix_id)
                    if prefix:
                        total = len(app['dependencies'])
                        for idx, dep in enumerate(app['dependencies'], 1):
                            GLib.idle_add(lambda d=dep, i=idx, t=total: progress_dialog.set_body(
                                f"Installing dependency {i} of {t}: {d}..."
                            ))
                            success, msg = self.dep_manager.install_dependency(
                                prefix['path'],
                                dep,
                                prefix.get('runner_path')
                            )
                            if success:
                                self.db.mark_dependency_installed(app_id, dep)

                GLib.idle_add(self._on_install_complete, app['name'], progress_dialog)

            except Exception as e:
                logger.error(f"Error installing {app['name']}: {e}", exc_info=True)
                GLib.idle_add(self._on_install_error, str(e), progress_dialog)

        thread = threading.Thread(target=download_and_install, daemon=True)
        thread.start()

    def _on_install_complete(self, app_name, progress_dialog):
        """Handle successful installation."""
        progress_dialog.close()

        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading("Installation Complete")
        dialog.set_body(f"{app_name} has been installed successfully!\n\nYou can now find it in your Library.")
        dialog.add_response("ok", "OK")
        dialog.present()

        return False

    def _on_install_error(self, error_msg, progress_dialog):
        """Handle installation error."""
        progress_dialog.close()

        dialog = Adw.MessageDialog.new(self.get_root())
        dialog.set_heading("Installation Failed")
        dialog.set_body(error_msg)
        dialog.add_response("ok", "OK")
        dialog.present()

        return False
