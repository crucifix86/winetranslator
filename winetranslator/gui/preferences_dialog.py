"""
Preferences Dialog for WineTranslator.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
import os
import logging

from ..database.db import Database

logger = logging.getLogger(__name__)


class PreferencesDialog(Adw.PreferencesWindow):
    """Preferences dialog for WineTranslator settings."""

    def __init__(self, parent, db: Database):
        """Initialize the preferences dialog."""
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title("Preferences")

        self.db = db

        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        """Build the preferences UI."""
        # General page
        general_page = Adw.PreferencesPage()
        general_page.set_title("General")
        general_page.set_icon_name("preferences-system-symbolic")
        self.add(general_page)

        # Dependency caching group
        cache_group = Adw.PreferencesGroup()
        cache_group.set_title("Dependency Caching")
        cache_group.set_description("Cache downloaded dependencies locally for faster installation")
        general_page.add(cache_group)

        # Enable caching switch
        self.cache_switch_row = Adw.SwitchRow()
        self.cache_switch_row.set_title("Enable Dependency Caching")
        self.cache_switch_row.set_subtitle("Download and store dependencies locally")
        self.cache_switch_row.connect("notify::active", self._on_cache_toggle)
        cache_group.add(self.cache_switch_row)

        # Cache location row
        self.cache_location_row = Adw.ActionRow()
        self.cache_location_row.set_title("Cache Location")
        self.cache_location_button = Gtk.Button(label="Choose Folder...")
        self.cache_location_button.set_valign(Gtk.Align.CENTER)
        self.cache_location_button.connect("clicked", self._on_choose_cache_location)
        self.cache_location_row.add_suffix(self.cache_location_button)
        cache_group.add(self.cache_location_row)

        # Cache path label
        self.cache_path_label = Gtk.Label()
        self.cache_path_label.set_halign(Gtk.Align.START)
        self.cache_path_label.set_wrap(True)
        self.cache_path_label.add_css_class("dim-label")
        self.cache_path_label.add_css_class("caption")
        self.cache_path_label.set_margin_start(12)
        cache_group.add(self.cache_path_label)

        # Cache info
        cache_info = Gtk.Label()
        cache_info.set_text("Cached dependencies will be stored locally and reused across applications, reducing download time and bandwidth usage.")
        cache_info.set_wrap(True)
        cache_info.set_halign(Gtk.Align.START)
        cache_info.add_css_class("dim-label")
        cache_info.set_margin_start(12)
        cache_info.set_margin_top(6)
        cache_group.add(cache_info)

    def _load_settings(self):
        """Load settings from database."""
        # Load cache enabled setting
        cache_enabled = self.db.get_setting('cache_dependencies', '0') == '1'
        self.cache_switch_row.set_active(cache_enabled)

        # Load cache path
        cache_path = self.db.get_setting('cache_path', '')
        if not cache_path:
            # Set default cache path
            data_home = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            cache_path = os.path.join(data_home, 'winetranslator', 'dep_cache')

        self.cache_path_label.set_text(cache_path)
        self._update_cache_ui()

    def _update_cache_ui(self):
        """Update cache UI based on enabled state."""
        enabled = self.cache_switch_row.get_active()
        self.cache_location_row.set_sensitive(enabled)
        self.cache_location_button.set_sensitive(enabled)

    def _on_cache_toggle(self, switch, param):
        """Handle cache toggle."""
        enabled = switch.get_active()
        logger.info(f"Cache dependencies toggled: {enabled}")

        self.db.set_setting('cache_dependencies', '1' if enabled else '0')

        # If enabling and no path set, set default
        if enabled:
            cache_path = self.db.get_setting('cache_path', '')
            if not cache_path:
                data_home = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
                cache_path = os.path.join(data_home, 'winetranslator', 'dep_cache')
                self.db.set_setting('cache_path', cache_path)
                self.cache_path_label.set_text(cache_path)

                # Create cache directory
                os.makedirs(cache_path, exist_ok=True)
                logger.info(f"Created cache directory: {cache_path}")

        self._update_cache_ui()

    def _on_choose_cache_location(self, button):
        """Handle choose cache location button click."""
        logger.info("Choose cache location button clicked")

        dialog = Gtk.FileDialog()
        dialog.set_title("Select Cache Location")

        # Set initial folder
        current_path = self.cache_path_label.get_text()
        logger.info(f"Current cache path: {current_path}")

        if current_path and os.path.exists(current_path):
            initial_folder = Gio.File.new_for_path(current_path)
            dialog.set_initial_folder(initial_folder)
            logger.info(f"Set initial folder: {current_path}")

        logger.info("Opening folder selection dialog")
        dialog.select_folder(self, None, self._on_cache_location_selected)

    def _on_cache_location_selected(self, dialog, result):
        """Handle cache location selection."""
        try:
            logger.info("Folder selection callback triggered")
            folder = dialog.select_folder_finish(result)
            logger.info(f"Folder selected: {folder}")

            if folder:
                cache_path = folder.get_path()
                logger.info(f"Cache location selected: {cache_path}")

                # Create directory if it doesn't exist
                os.makedirs(cache_path, exist_ok=True)

                # Save to database
                self.db.set_setting('cache_path', cache_path)
                self.cache_path_label.set_text(cache_path)
                logger.info(f"Cache path saved to database: {cache_path}")
            else:
                logger.warning("No folder selected (folder is None)")

        except GLib.Error as e:
            # GTK dismissal is not an error
            if e.code == 2:  # Dismissed
                logger.info("Folder selection dismissed by user")
            else:
                logger.error(f"GLib error selecting cache location: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error selecting cache location: {e}", exc_info=True)
