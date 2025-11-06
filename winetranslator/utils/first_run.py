"""
First-run setup helper for WineTranslator.

Checks for required system dependencies and helps the user install them.
"""

import subprocess
import shutil
from typing import Tuple, List


class FirstRunChecker:
    """Checks system dependencies on first run."""

    def __init__(self):
        """Initialize the first run checker."""
        self.missing_deps = []

    def check_wine(self) -> bool:
        """Check if Wine is installed."""
        return shutil.which('wine') is not None

    def check_winetricks(self) -> bool:
        """Check if Winetricks is installed."""
        return shutil.which('winetricks') is not None

    def check_gtk4(self) -> bool:
        """Check if GTK4 Python bindings are available."""
        try:
            import gi
            gi.require_version('Gtk', '4.0')
            return True
        except (ImportError, ValueError):
            return False

    def check_libadwaita(self) -> bool:
        """Check if Libadwaita Python bindings are available."""
        try:
            import gi
            gi.require_version('Adw', '1')
            return True
        except (ImportError, ValueError):
            return False

    def check_all(self) -> Tuple[bool, List[str]]:
        """
        Check all required dependencies.

        Returns:
            Tuple of (all_ok, missing_dependencies_list)
        """
        missing = []

        if not self.check_wine():
            missing.append("Wine")

        if not self.check_winetricks():
            missing.append("Winetricks (optional)")

        if not self.check_gtk4():
            missing.append("GTK4")

        if not self.check_libadwaita():
            missing.append("Libadwaita")

        return len([m for m in missing if "optional" not in m]) == 0, missing

    def get_install_instructions(self, distro: str = None) -> str:
        """
        Get installation instructions for missing dependencies.

        Args:
            distro: Linux distribution name (auto-detected if None)

        Returns:
            Installation command string
        """
        if distro is None:
            distro = self._detect_distro()

        instructions = {
            'debian': 'sudo apt install wine winetricks python3-gi gir1.2-gtk-4.0 gir1.2-adw-1',
            'ubuntu': 'sudo apt install wine winetricks python3-gi gir1.2-gtk-4.0 gir1.2-adw-1',
            'fedora': 'sudo dnf install wine winetricks python3-gobject gtk4 libadwaita',
            'arch': 'sudo pacman -S wine winetricks python-gobject gtk4 libadwaita',
            'opensuse': 'sudo zypper install wine winetricks python3-gobject gtk4 libadwaita-1-0',
        }

        return instructions.get(distro.lower(),
                               "Please install: Wine, Winetricks, GTK4, Libadwaita, and PyGObject")

    def _detect_distro(self) -> str:
        """Detect the Linux distribution."""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        return line.split('=')[1].strip().strip('"')
        except:
            pass
        return 'unknown'

    def get_friendly_message(self) -> str:
        """
        Get a user-friendly message about missing dependencies.

        Returns:
            Formatted message string
        """
        all_ok, missing = self.check_all()

        if all_ok:
            return "All required dependencies are installed!"

        distro = self._detect_distro()
        cmd = self.get_install_instructions(distro)

        message = "WineTranslator requires the following dependencies:\n\n"
        message += "\n".join(f"  • {dep}" for dep in missing)
        message += "\n\nTo install them, run:\n\n"
        message += f"  {cmd}\n"

        return message
