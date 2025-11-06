"""
Main entry point for WineTranslator.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
import sys
import threading
import logging

from .database.db import Database
from .gui.main_window import MainWindow
from .core.updater import Updater
from .utils.first_run import FirstRunChecker
from .utils.logger import setup_logging

# Set up logging
logger = setup_logging()


class WineTranslatorApp(Adw.Application):
    """Main WineTranslator application."""

    def __init__(self):
        """Initialize the application."""
        super().__init__(
            application_id='com.winetranslator.WineTranslator',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.db = None

    def do_activate(self):
        """Activate the application."""
        logger.info("Application activated")

        # Check dependencies on first run
        checker = FirstRunChecker()
        all_ok, missing = checker.check_all()

        if not all_ok:
            logger.warning(f"Missing dependencies: {missing}")
            # Show dependency warning dialog
            self._show_dependency_warning(checker)
            return

        logger.info("All dependencies present")

        # Initialize database
        if not self.db:
            logger.info("Initializing database")
            self.db = Database()

        # Create main window
        logger.info("Creating main window")
        window = MainWindow(self, self.db)
        window.present()

    def _show_dependency_warning(self, checker: FirstRunChecker):
        """Show warning dialog for missing dependencies."""
        # Create a minimal window to show the dialog
        window = Adw.Window()
        window.set_title("WineTranslator - Setup Required")
        window.set_default_size(600, 400)

        dialog = Adw.MessageDialog.new(window)
        dialog.set_heading("Dependencies Required")
        dialog.set_body(checker.get_friendly_message())
        dialog.add_response("quit", "Quit")
        dialog.add_response("continue", "Continue Anyway")
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_dependency_warning_response)

        window.present()
        dialog.present()

    def _on_dependency_warning_response(self, dialog, response):
        """Handle dependency warning response."""
        if response == "continue":
            # User wants to continue anyway
            if not self.db:
                self.db = Database()
            window = MainWindow(self, self.db)
            window.present()
        else:
            # Quit the application
            self.quit()

    def do_startup(self):
        """Application startup."""
        Adw.Application.do_startup(self)

        # Create actions
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)

        update_action = Gio.SimpleAction.new("update", None)
        update_action.connect("activate", self.on_update)
        self.add_action(update_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def on_about(self, action, param):
        """Show about dialog."""
        about = Adw.AboutWindow(
            transient_for=self.get_active_window(),
            application_name="WineTranslator",
            application_icon="application-x-executable-symbolic",
            developer_name="WineTranslator Team",
            version="0.3.0",
            website="https://github.com/crucifix86/winetranslator",
            issue_url="https://github.com/crucifix86/winetranslator/issues",
            license_type=Gtk.License.GPL_3_0,
            comments="A simple, easy-to-use Wine GUI for running Windows applications on Linux"
        )
        about.present()

    def on_update(self, action, param):
        """Show update dialog."""
        updater = Updater()

        if not updater.is_git_repo():
            dialog = Adw.MessageDialog.new(self.get_active_window())
            dialog.set_heading("Updates Not Available")
            dialog.set_body("WineTranslator is not installed from git. To enable updates, reinstall from the GitHub repository.")
            dialog.add_response("ok", "OK")
            dialog.present()
            return

        # Show checking dialog
        check_dialog = Adw.MessageDialog.new(self.get_active_window())
        check_dialog.set_heading("Checking for Updates")
        check_dialog.set_body("Checking GitHub for updates...")
        check_dialog.present()

        # Check for updates in background
        def check_thread():
            has_updates, message, remote_commit = updater.check_for_updates()
            GLib.idle_add(self._on_update_check_complete, has_updates, message, check_dialog, updater)

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def _on_update_check_complete(self, has_updates, message, check_dialog, updater):
        """Handle update check completion."""
        check_dialog.close()

        if has_updates:
            # Show update available dialog
            dialog = Adw.MessageDialog.new(self.get_active_window())
            dialog.set_heading("Update Available")
            dialog.set_body(f"{message}\n\nWould you like to update now?")
            dialog.add_response("cancel", "Not Now")
            dialog.add_response("update", "Update")
            dialog.set_response_appearance("update", Adw.ResponseAppearance.SUGGESTED)
            dialog.connect("response", self._on_update_response, updater)
            dialog.present()
        else:
            # Show up to date dialog
            dialog = Adw.MessageDialog.new(self.get_active_window())
            dialog.set_heading("No Updates Available")
            dialog.set_body(message)
            dialog.add_response("ok", "OK")
            dialog.present()

    def _on_update_response(self, dialog, response, updater):
        """Handle update dialog response."""
        if response == "update":
            # Show updating dialog
            progress_dialog = Adw.MessageDialog.new(self.get_active_window())
            progress_dialog.set_heading("Updating")
            progress_dialog.set_body("Downloading and installing update...")
            progress_dialog.present()

            # Update in background
            def update_thread():
                success, message = updater.update()
                GLib.idle_add(self._on_update_complete, success, message, progress_dialog)

            thread = threading.Thread(target=update_thread, daemon=True)
            thread.start()

    def _on_update_complete(self, success, message, progress_dialog):
        """Handle update completion."""
        progress_dialog.close()

        dialog = Adw.MessageDialog.new(self.get_active_window())
        if success:
            dialog.set_heading("Update Successful")
            dialog.set_body(f"{message}\n\nPlease restart WineTranslator to use the new version.")
            dialog.add_response("ok", "OK")
            dialog.add_response("restart", "Restart Now")
            dialog.set_response_appearance("restart", Adw.ResponseAppearance.SUGGESTED)
            dialog.connect("response", self._on_restart_response)
        else:
            dialog.set_heading("Update Failed")
            dialog.set_body(message)
            dialog.add_response("ok", "OK")

        dialog.present()

    def _on_restart_response(self, dialog, response):
        """Handle restart response."""
        if response == "restart":
            # Restart the application
            import os
            import sys
            os.execv(sys.executable, ['python3', '-m', 'winetranslator'])

    def on_preferences(self, action, param):
        """Show preferences dialog."""
        # TODO: Implement preferences dialog
        dialog = Adw.MessageDialog.new(self.get_active_window())
        dialog.set_heading("Preferences")
        dialog.set_body("Preferences dialog coming soon!")
        dialog.add_response("ok", "OK")
        dialog.present()


def main():
    """Main entry point."""
    app = WineTranslatorApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    main()
