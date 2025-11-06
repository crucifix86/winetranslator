"""
Main entry point for WineTranslator.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio
import sys

from .database.db import Database
from .gui.main_window import MainWindow


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
        # Initialize database
        if not self.db:
            self.db = Database()

        # Create main window
        window = MainWindow(self, self.db)
        window.present()

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
            version="0.1.0",
            website="https://github.com/winetranslator/winetranslator",
            issue_url="https://github.com/winetranslator/winetranslator/issues",
            license_type=Gtk.License.GPL_3_0,
            comments="A simple, easy-to-use Wine GUI for running Windows applications on Linux"
        )
        about.present()

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
