"""
Main Window for WineTranslator.

GTK4 application window with application library and management interface.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
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

        # Setup context menu actions
        self._setup_context_actions()

        # Window properties
        self.set_title("WineTranslator")
        self.set_default_size(1000, 700)

        # Build UI
        self._build_ui()

        # Initialize system
        GLib.idle_add(self._initialize_system)

    def _setup_context_actions(self):
        """Setup actions for context menu."""
        # Get the application
        app = self.get_application()

        # Open directory action (with parameter)
        open_dir_action = Gio.SimpleAction.new("open-directory", GLib.VariantType.new("s"))
        open_dir_action.connect("activate", self._on_open_directory_action)
        app.add_action(open_dir_action)

        # Edit arguments action (with parameter)
        edit_args_action = Gio.SimpleAction.new("edit-arguments", GLib.VariantType.new("s"))
        edit_args_action.connect("activate", self._on_edit_arguments_action)
        app.add_action(edit_args_action)

        # Change executable action (with parameter)
        change_exe_action = Gio.SimpleAction.new("change-executable", GLib.VariantType.new("s"))
        change_exe_action.connect("activate", self._on_change_executable_action)
        app.add_action(change_exe_action)

        # Manage dependencies action (with parameter)
        manage_deps_action = Gio.SimpleAction.new("manage-dependencies", GLib.VariantType.new("s"))
        manage_deps_action.connect("activate", self._on_manage_dependencies_action)
        app.add_action(manage_deps_action)

        # Enable controller action (with parameter)
        enable_controller_action = Gio.SimpleAction.new("enable-controller", GLib.VariantType.new("s"))
        enable_controller_action.connect("activate", self._on_enable_controller_action)
        app.add_action(enable_controller_action)

        # Remap controller action (with parameter)
        remap_controller_action = Gio.SimpleAction.new("remap-controller", GLib.VariantType.new("s"))
        remap_controller_action.connect("activate", self._on_remap_controller_action)
        app.add_action(remap_controller_action)

        # Toggle virtual desktop action (with parameter)
        toggle_virtual_desktop_action = Gio.SimpleAction.new("toggle-virtual-desktop", GLib.VariantType.new("s"))
        toggle_virtual_desktop_action.connect("activate", self._on_toggle_virtual_desktop_action)
        app.add_action(toggle_virtual_desktop_action)

    def _on_open_directory_action(self, action, parameter):
        """Handle open directory action from context menu."""
        app_id = int(parameter.get_string())
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        exe_path = app.get('executable_path', '')
        if exe_path and os.path.exists(exe_path):
            exe_dir = os.path.dirname(exe_path)
            self._open_directory(exe_dir)
        else:
            logger.warning(f"Executable path not found for app {app_id}")

    def _on_edit_arguments_action(self, action, parameter):
        """Handle edit arguments action from context menu."""
        app_id = int(parameter.get_string())
        self._show_edit_arguments_dialog(app_id)

    def _on_change_executable_action(self, action, parameter):
        """Handle change executable action from context menu."""
        app_id = int(parameter.get_string())
        self._show_change_executable_dialog(app_id)

    def _show_change_executable_dialog(self, app_id: int):
        """Show dialog to change the executable for an app."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Create file dialog
        dialog = Gtk.FileDialog()
        dialog.set_title("Select New Executable")

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

        # Set initial folder to current executable's directory
        current_exe = app.get('executable_path', '')
        if current_exe and os.path.exists(current_exe):
            exe_dir = os.path.dirname(current_exe)
            initial_folder = Gio.File.new_for_path(exe_dir)
            dialog.set_initial_folder(initial_folder)

        dialog.open(self, None, lambda d, result: self._on_executable_selected(d, result, app_id))

    def _on_executable_selected(self, dialog, result, app_id: int):
        """Handle new executable file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                new_exe_path = file.get_path()
                logger.info(f"Changing executable for app {app_id} to {new_exe_path}")

                # Update the database
                self.db.update_application(app_id, executable_path=new_exe_path)

                # Refresh the UI
                self._refresh_applications()

                # Show success toast
                toast = Adw.Toast.new(f"Executable changed to {os.path.basename(new_exe_path)}")
                toast.set_timeout(3)
                self.toast_overlay.add_toast(toast)

        except GLib.Error as e:
            if e.code != 2:  # Ignore dismiss
                logger.error(f"Error selecting executable: {e}", exc_info=True)

    def _on_manage_dependencies_action(self, action, parameter):
        """Handle manage dependencies action from context menu."""
        app_id = int(parameter.get_string())
        self._show_manage_dependencies_dialog(app_id)

    def _show_manage_dependencies_dialog(self, app_id: int):
        """Show dialog to manually install dependencies for an app."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Create dialog window
        dialog = Adw.Window()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_default_size(500, 600)
        dialog.set_title(f"Manage Dependencies - {app['name']}")

        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dialog.set_content(main_box)

        # Header
        header = Adw.HeaderBar()
        main_box.append(header)

        # Content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        # Create list box for dependencies
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list")
        scrolled.set_child(list_box)

        # Get available dependencies
        from ..core.dependency_manager import DependencyManager
        dep_manager = DependencyManager(self.db)
        available_deps = dep_manager.get_available_dependencies()

        # Group by category
        categories = {}
        for dep in available_deps:
            category = dep['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(dep)

        # Add dependencies by category
        for category, deps in sorted(categories.items()):
            # Category header
            category_row = Adw.PreferencesGroup()
            category_row.set_title(category)
            list_box.append(category_row)

            for dep in deps:
                row = Adw.ActionRow()
                row.set_title(dep['name'])
                row.set_subtitle(dep['description'])

                # Install button
                install_btn = Gtk.Button(label="Install")
                install_btn.set_valign(Gtk.Align.CENTER)
                install_btn.connect("clicked", self._on_install_dependency_clicked,
                                  app_id, dep['name'], dialog)
                row.add_suffix(install_btn)

                category_row.add(row)

        dialog.present()

    def _on_install_dependency_clicked(self, button, app_id: int, dep_name: str, parent_dialog):
        """Handle install dependency button click."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        prefix_id = app['prefix_id']
        prefix = self.prefix_manager.get_prefix(prefix_id)
        if not prefix:
            return

        # Disable button during installation
        button.set_sensitive(False)
        button.set_label("Installing...")

        def install_thread():
            from ..core.dependency_manager import DependencyManager
            dep_manager = DependencyManager(self.db)

            success, message = dep_manager.install_dependency(
                prefix['path'],
                dep_name,
                prefix.get('runner_path')
            )

            GLib.idle_add(self._on_dependency_installed, success, message, dep_name, button)

        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()

    def _on_dependency_installed(self, success: bool, message: str, dep_name: str, button):
        """Handle dependency installation completion."""
        if success:
            button.set_label("Installed ✓")
            toast = Adw.Toast.new(f"{dep_name} installed successfully")
        else:
            button.set_label("Failed ✗")
            button.set_sensitive(True)
            toast = Adw.Toast.new(f"Failed to install {dep_name}: {message}")

        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
        return False

    def _on_enable_controller_action(self, action, parameter):
        """Handle enable controller action from context menu."""
        app_id = int(parameter.get_string())
        self._show_enable_controller_dialog(app_id)

    def _on_remap_controller_action(self, action, parameter):
        """Handle remap controller action from context menu."""
        app_id = int(parameter.get_string())
        self._show_remap_controller_dialog(app_id)

    def _on_toggle_virtual_desktop_action(self, action, parameter):
        """Handle toggle virtual desktop action from context menu."""
        app_id = int(parameter.get_string())
        self._show_virtual_desktop_dialog(app_id)

    def _show_virtual_desktop_dialog(self, app_id: int):
        """Show dialog to configure virtual desktop settings."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Check current state
        vd_enabled = self.db.get_env_var(app_id, 'WINE_VIRTUAL_DESKTOP_ENABLED')
        current_resolution = self.db.get_env_var(app_id, 'WINE_VIRTUAL_DESKTOP_RESOLUTION') or '1920x1080'

        if vd_enabled == '1':
            # Currently enabled - show disable confirmation
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Disable Virtual Desktop?")
            dialog.set_body(
                f"Virtual Desktop mode is currently enabled for {app['name']}.\n\n"
                "Disabling it will allow the game to use fullscreen mode, which may "
                "take over your entire screen and make Alt+Tab difficult."
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("disable", "Disable")
            dialog.set_response_appearance("disable", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", self._on_virtual_desktop_disable_response, app_id)
        else:
            # Currently disabled - show enable dialog with resolution options
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Enable Virtual Desktop?")
            dialog.set_body(
                f"Virtual Desktop mode will run {app['name']} in a contained Wine window.\n\n"
                "This prevents fullscreen games from taking over your entire screen, "
                "making it easy to Alt+Tab to other applications.\n\n"
                "Choose a resolution for the virtual desktop window:"
            )

            # Add resolution selection
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(10)
            box.set_margin_end(10)

            # Resolution dropdown
            resolution_label = Gtk.Label(label="Resolution:")
            resolution_label.set_xalign(0)
            box.append(resolution_label)

            resolutions = [
                "1920x1080", "2560x1440", "3840x2160",  # Common 16:9
                "1680x1050", "1920x1200", "2560x1600",  # Common 16:10
                "1366x768", "1600x900", "1280x720"      # Other common
            ]

            resolution_dropdown = Gtk.DropDown.new_from_strings(resolutions)
            # Set current selection
            try:
                current_idx = resolutions.index(current_resolution)
                resolution_dropdown.set_selected(current_idx)
            except ValueError:
                resolution_dropdown.set_selected(0)  # Default to 1920x1080

            box.append(resolution_dropdown)

            dialog.set_extra_child(box)
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("enable", "Enable")
            dialog.set_response_appearance("enable", Adw.ResponseAppearance.SUGGESTED)

            dialog.resolution_dropdown = resolution_dropdown  # Store reference
            dialog.connect("response", self._on_virtual_desktop_enable_response, app_id)

        dialog.present()

    def _on_virtual_desktop_enable_response(self, dialog, response, app_id: int):
        """Handle virtual desktop enable response."""
        if response == "enable":
            # Get selected resolution
            selected_idx = dialog.resolution_dropdown.get_selected()
            resolutions = [
                "1920x1080", "2560x1440", "3840x2160",
                "1680x1050", "1920x1200", "2560x1600",
                "1366x768", "1600x900", "1280x720"
            ]
            resolution = resolutions[selected_idx]

            # Enable virtual desktop
            self.db.set_env_var(app_id, 'WINE_VIRTUAL_DESKTOP_ENABLED', '1')
            self.db.set_env_var(app_id, 'WINE_VIRTUAL_DESKTOP_RESOLUTION', resolution)

            app = self.app_launcher.get_application(app_id)
            toast = Adw.Toast.new(f"Virtual Desktop enabled for {app['name']} ({resolution})")
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)

            logger.info(f"Enabled virtual desktop for app {app_id} with resolution {resolution}")

    def _on_virtual_desktop_disable_response(self, dialog, response, app_id: int):
        """Handle virtual desktop disable response."""
        if response == "disable":
            # Disable virtual desktop
            self.db.set_env_var(app_id, 'WINE_VIRTUAL_DESKTOP_ENABLED', '0')

            app = self.app_launcher.get_application(app_id)
            toast = Adw.Toast.new(f"Virtual Desktop disabled for {app['name']}")
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)

            logger.info(f"Disabled virtual desktop for app {app_id}")

    def _show_remap_controller_dialog(self, app_id: int):
        """Show controller button remapping dialog."""
        from .controller_remap_dialog import ControllerRemapDialog

        # Get current mapping if any
        current_mapping = self.db.get_config(app_id, 'controller_mapping')

        # Show remapping dialog
        try:
            dialog = ControllerRemapDialog(self, app_id, current_mapping)
            dialog.present()
        except RuntimeError as e:
            # No controller detected
            error_dialog = Adw.MessageDialog.new(self)
            error_dialog.set_heading("No Controller Detected")
            error_dialog.set_body("Please connect an Xbox controller and try again.")
            error_dialog.add_response("ok", "OK")
            error_dialog.present()
            logger.error(f"Failed to open controller remapping dialog: {e}")

    def _detect_xbox_controllers(self):
        """Detect connected Xbox controllers."""
        controllers = []
        try:
            # Check /dev/input/js* devices
            import glob
            js_devices = glob.glob('/dev/input/js*')

            for device in js_devices:
                try:
                    # Try to read device name
                    device_num = device.replace('/dev/input/js', '')
                    event_device = f'/sys/class/input/js{device_num}/device/name'

                    if os.path.exists(event_device):
                        with open(event_device, 'r') as f:
                            name = f.read().strip()

                        # Check if it's an Xbox controller
                        if any(x in name.lower() for x in ['xbox', 'x-box', 'microsoft']):
                            controllers.append({
                                'device': device,
                                'name': name,
                                'number': device_num
                            })
                except Exception as e:
                    logger.debug(f"Error reading device {device}: {e}")

        except Exception as e:
            logger.error(f"Error detecting controllers: {e}")

        return controllers

    def _detect_controller_api(self, app_id: int):
        """Detect which controller API a game likely uses (DirectInput or XInput)."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return "unknown"

        exe_path = app.get('executable_path', '').lower()

        # Check for common XInput indicators
        xinput_indicators = [
            'skyrim',           # Skyrim uses XInput
            'fallout4',         # Fallout 4 uses XInput
            'fallout3',         # Fallout 3 uses XInput
            'witcher3',         # Witcher 3 uses XInput
            'darksouls',        # Dark Souls uses XInput
            'sekiro',           # Sekiro uses XInput
            'eldenring',        # Elden Ring uses XInput
        ]

        # Check for common DirectInput indicators (older games)
        dinput_indicators = [
            'morrowind',        # Older Elder Scrolls games
            'oblivion',         # Oblivion can use DirectInput
            'gta_sa',           # GTA San Andreas
            'nfs',              # Need for Speed series
        ]

        for indicator in xinput_indicators:
            if indicator in exe_path:
                return "xinput"

        for indicator in dinput_indicators:
            if indicator in exe_path:
                return "dinput"

        # Default to auto-detect (will check for xinput DLLs in game directory)
        return "unknown"

    def _show_enable_controller_dialog(self, app_id: int):
        """Show dialog to enable controller support for an app."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Detect controllers
        controllers = self._detect_xbox_controllers()
        detected_api = self._detect_controller_api(app_id)

        # Create dialog with custom content
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(f"Enable Controller Support - {app['name']}")

        # Build dialog body
        body_text = ""
        if controllers:
            controller_list = "\n".join([f"• {c['name']}" for c in controllers])
            body_text = f"Detected Xbox controllers:\n{controller_list}\n\n"
        else:
            body_text = "No Xbox controllers detected. Make sure your controller is connected.\n\n"

        # Add API detection info
        if detected_api == "xinput":
            body_text += "This game appears to use XInput (modern controller API)."
        elif detected_api == "dinput":
            body_text += "This game appears to use DirectInput (legacy controller API)."
        else:
            body_text += "Controller API could not be detected automatically."

        body_text += "\n\nChoose controller API:"
        dialog.set_body(body_text)

        # Add response options for different controller APIs
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("auto", "Auto-Detect")
        dialog.add_response("dinput", "DirectInput (Legacy)")
        dialog.add_response("xinput", "XInput (Modern)")

        # Set suggested response based on detection
        if detected_api == "xinput":
            dialog.set_response_appearance("xinput", Adw.ResponseAppearance.SUGGESTED)
        elif detected_api == "dinput":
            dialog.set_response_appearance("dinput", Adw.ResponseAppearance.SUGGESTED)
        else:
            dialog.set_response_appearance("auto", Adw.ResponseAppearance.SUGGESTED)

        dialog.connect("response", self._on_enable_controller_response, app_id)
        dialog.present()

    def _on_enable_controller_response(self, dialog, response, app_id: int):
        """Handle enable controller dialog response."""
        if response == "cancel":
            return

        # Determine which API to use
        api_mode = response  # "auto", "dinput", or "xinput"

        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        prefix_id = app['prefix_id']
        prefix = self.prefix_manager.get_prefix(prefix_id)
        if not prefix:
            return

        # Auto-detect mode: check game directory for xinput DLLs
        if api_mode == "auto":
            exe_path = app.get('executable_path', '')
            if exe_path:
                game_dir = os.path.dirname(exe_path)
                # Check if game has xinput DLLs
                has_xinput = any(os.path.exists(os.path.join(game_dir, f"xinput{ver}.dll"))
                                for ver in ['1_4', '1_3', '1_2', '1_1', '9_1_0'])

                if has_xinput:
                    api_mode = "xinput"
                    logger.info("Auto-detected XInput (found xinput DLLs in game directory)")
                else:
                    # Default to DirectInput for older/unknown games
                    api_mode = "dinput"
                    logger.info("Auto-detected DirectInput (no xinput DLLs found)")
            else:
                # Fallback to DirectInput if we can't check
                api_mode = "dinput"
                logger.info("Auto-detect fallback: using DirectInput")

        # Show progress
        progress_dialog = Adw.MessageDialog.new(self)
        progress_dialog.set_heading("Enabling Controller Support")
        if api_mode == "xinput":
            progress_dialog.set_body("Configuring XInput controller support...")
        else:
            progress_dialog.set_body("Configuring DirectInput controller support...")
        progress_dialog.present()

        # Store API mode for completion message
        self._controller_api_mode = api_mode

        def enable_thread():
            import subprocess
            from ..core.dependency_manager import DependencyManager
            dep_manager = DependencyManager(self.db)

            # Set common environment variables for controller support
            self.db.set_env_var(app_id, 'SDL_GAMECONTROLLERCONFIG', 'auto')
            self.db.set_env_var(app_id, 'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS', '1')
            self.db.set_env_var(app_id, 'WINE_ENABLE_GAMEPAD', '1')
            self.db.set_env_var(app_id, 'WINE_ENABLE_HIDRAW', '1')

            env = os.environ.copy()
            env['WINEPREFIX'] = prefix['path']
            if prefix.get('runner_path'):
                env['WINE'] = prefix['runner_path']

            if api_mode == "dinput":
                # DirectInput mode: Use Wine's built-in DirectInput support
                logger.info("Configuring DirectInput controller support")

                # Set xinput DLLs to builtin (use Wine's implementation)
                xinput_dlls = ['xinput1_4', 'xinput1_3', 'xinput1_2', 'xinput1_1', 'xinput9_1_0', 'xinputuap']
                for dll in xinput_dlls:
                    try:
                        subprocess.run(
                            ['wine', 'reg', 'add', 'HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides',
                             '/v', f'*{dll}', '/t', 'REG_SZ', '/d', 'builtin', '/f'],
                            env=env,
                            capture_output=True,
                            timeout=10
                        )
                        logger.info(f"Set {dll} to builtin (Wine DirectInput)")
                    except Exception as e:
                        logger.warning(f"Failed to set override for {dll}: {e}")

                GLib.idle_add(self._on_controller_enabled, True, "DirectInput controller support enabled", progress_dialog)

            else:  # xinput mode
                # XInput mode: Use Wine's built-in XInput support (DirectInput translation)
                logger.info("Configuring XInput controller support (Wine builtin)")

                # Set xinput DLLs to builtin (use Wine's implementation which supports DirectInput)
                xinput_dlls = ['xinput1_4', 'xinput1_3', 'xinput1_2', 'xinput1_1', 'xinput9_1_0', 'xinputuap']
                for dll in xinput_dlls:
                    try:
                        subprocess.run(
                            ['wine', 'reg', 'add', 'HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides',
                             '/v', f'*{dll}', '/t', 'REG_SZ', '/d', 'builtin', '/f'],
                            env=env,
                            capture_output=True,
                            timeout=10
                        )
                        logger.info(f"Set {dll} to builtin (Wine XInput)")
                    except Exception as e:
                        logger.warning(f"Failed to set override for {dll}: {e}")

                GLib.idle_add(self._on_controller_enabled, True, "XInput controller support enabled (Wine builtin)", progress_dialog)

        thread = threading.Thread(target=enable_thread, daemon=True)
        thread.start()

    def _on_controller_enabled(self, success: bool, message: str, progress_dialog):
        """Handle controller enablement completion."""
        progress_dialog.close()

        if success:
            result_dialog = Adw.MessageDialog.new(self)
            result_dialog.set_heading("Controller Support Enabled")

            # Show appropriate message based on API mode
            api_mode = getattr(self, '_controller_api_mode', 'unknown')
            if "xinput" in message.lower() or api_mode == "xinput":
                body = "XInput support has been configured.\n\nWine's built-in XInput will translate DirectInput controller signals.\n\nYour Xbox controller should now work!"
            elif "directinput" in message.lower() or api_mode == "dinput":
                body = "DirectInput support has been configured.\n\nYour Xbox controller will work through Wine's DirectInput.\n\nYour Xbox controller should now work!"
            else:
                body = "Controller support has been enabled.\n\nYour Xbox controller should now work in this game!"

            result_dialog.set_body(body)
            result_dialog.add_response("ok", "OK")
            result_dialog.present()

            toast = Adw.Toast.new("Controller support enabled successfully")
        else:
            result_dialog = Adw.MessageDialog.new(self)
            result_dialog.set_heading("Failed to Enable Controller")
            result_dialog.set_body(f"Error: {message}")
            result_dialog.add_response("ok", "OK")
            result_dialog.present()

            toast = Adw.Toast.new(f"Failed: {message}")

        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
        return False

    def _show_edit_arguments_dialog(self, app_id: int):
        """Show dialog to edit launch arguments."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Create dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(f"Edit Launch Arguments - {app['name']}")
        dialog.set_body("Enter command-line arguments to pass to the application when launching.\nExample: -console -windowed -fullscreen")

        # Add response buttons
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        # Create entry for arguments
        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        entry_box.set_margin_start(12)
        entry_box.set_margin_end(12)
        entry_box.set_margin_top(12)
        entry_box.set_margin_bottom(12)

        entry = Gtk.Entry()
        entry.set_placeholder_text("Launch arguments...")
        current_args = app.get('arguments', '') or ''
        entry.set_text(current_args)
        entry_box.append(entry)

        dialog.set_extra_child(entry_box)

        dialog.connect("response", self._on_edit_arguments_response, app_id, entry)
        dialog.present()

    def _on_edit_arguments_response(self, dialog, response, app_id: int, entry: Gtk.Entry):
        """Handle edit arguments dialog response."""
        if response == "save":
            arguments = entry.get_text().strip()
            # Update in database
            self.db.update_application(app_id, arguments=arguments)
            logger.info(f"Updated launch arguments for app {app_id}: {arguments}")

            toast = Adw.Toast.new("Launch arguments updated")
            toast.set_timeout(2)
            self.toast_overlay.add_toast(toast)

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
        """Handle application card right-click - show context menu."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Create context menu
        menu = Gio.Menu()
        menu.append("Open Install Directory", f"app.open-directory::{app_id}")
        menu.append("Edit Launch Arguments", f"app.edit-arguments::{app_id}")
        menu.append("Change Executable", f"app.change-executable::{app_id}")
        menu.append("Manage Dependencies", f"app.manage-dependencies::{app_id}")
        menu.append("Enable Controller Support", f"app.enable-controller::{app_id}")
        menu.append("Remap Controller Buttons", f"app.remap-controller::{app_id}")

        # Check if virtual desktop is currently enabled
        vd_enabled = self.db.get_env_var(app_id, 'WINE_VIRTUAL_DESKTOP_ENABLED')
        vd_label = "Disable Virtual Desktop" if vd_enabled == '1' else "Enable Virtual Desktop"
        menu.append(vd_label, f"app.toggle-virtual-desktop::{app_id}")

        # Create popover menu
        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        popover.set_parent(gesture.get_widget())

        # Position at click location
        rect = Gdk.Rectangle()
        rect.x = x
        rect.y = y
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)

        popover.popup()

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
        dialog.add_response("prefix", "Open Wine C: Drive")
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
        elif response == "prefix":
            # Open Wine C: drive for this app's prefix
            app = self.app_launcher.get_application(app_id)
            if app and app.get('prefix_path'):
                drive_c = os.path.join(app['prefix_path'], 'drive_c')
                if os.path.exists(drive_c):
                    self._open_directory(drive_c)

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
        """Remove an application - show dialog to ask about deleting files."""
        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        # Create confirmation dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(f"Remove {app['name']}?")
        dialog.set_body("Do you want to delete the application files or just remove it from the library?")

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove-only", "Remove from Library Only")
        dialog.add_response("delete-files", "Remove and Delete Files")

        dialog.set_response_appearance("remove-only", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_response_appearance("delete-files", Adw.ResponseAppearance.DESTRUCTIVE)

        dialog.connect("response", self._on_remove_dialog_response, app_id)
        dialog.present()

    def _on_remove_dialog_response(self, dialog, response, app_id: int):
        """Handle remove confirmation dialog response."""
        if response == "cancel":
            return

        app = self.app_launcher.get_application(app_id)
        if not app:
            return

        delete_files = (response == "delete-files")

        # Remove from database
        success, message = self.app_launcher.remove_application(app_id)

        if success:
            # If user wants to delete files, delete the executable and its directory
            if delete_files:
                try:
                    exe_path = app.get('executable_path', '')
                    if exe_path and os.path.exists(exe_path):
                        exe_dir = os.path.dirname(exe_path)

                        # Ask for final confirmation before deleting
                        confirm_dialog = Adw.MessageDialog.new(self)
                        confirm_dialog.set_heading("Delete Files?")
                        confirm_dialog.set_body(f"This will permanently delete:\n{exe_dir}\n\nThis cannot be undone!")
                        confirm_dialog.add_response("cancel", "Cancel")
                        confirm_dialog.add_response("delete", "Delete Files")
                        confirm_dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
                        confirm_dialog.connect("response", self._on_delete_files_response, exe_dir, app['name'])
                        confirm_dialog.present()
                    else:
                        logger.warning(f"Executable path not found for deletion: {exe_path}")
                except Exception as e:
                    logger.error(f"Error preparing file deletion: {e}", exc_info=True)
                    toast = Adw.Toast.new(f"Error: {str(e)}")
                    toast.set_timeout(3)
                    self.toast_overlay.add_toast(toast)

            self._refresh_applications()
            toast = Adw.Toast.new(f"Removed {app['name']} from library")
        else:
            toast = Adw.Toast.new(f"Error: {message}")

        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)

    def _on_delete_files_response(self, dialog, response, directory: str, app_name: str):
        """Handle final delete files confirmation."""
        if response == "delete":
            try:
                import shutil
                if os.path.exists(directory):
                    shutil.rmtree(directory)
                    logger.info(f"Deleted directory: {directory}")
                    toast = Adw.Toast.new(f"Deleted files for {app_name}")
                else:
                    toast = Adw.Toast.new(f"Directory not found: {directory}")
            except Exception as e:
                logger.error(f"Error deleting directory: {e}", exc_info=True)
                toast = Adw.Toast.new(f"Error deleting files: {str(e)}")

            toast.set_timeout(3)
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
            # Desktop directory (where user can see the icon)
            desktop_dir = os.path.expanduser('~/Desktop')
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
