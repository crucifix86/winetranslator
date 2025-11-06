"""
Wine Prefix Manager for WineTranslator.

Manages Wine prefixes (isolated Windows environments).
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ..database.db import Database
from ..utils.wine_utils import create_wine_prefix, get_wine_prefix_info


class PrefixManager:
    """Manages Wine prefixes."""

    def __init__(self, db: Database, data_dir: Optional[str] = None):
        """
        Initialize the prefix manager.

        Args:
            db: Database instance.
            data_dir: Base directory for storing prefixes.
                     If None, uses XDG_DATA_HOME/winetranslator/prefixes
        """
        self.db = db

        if data_dir is None:
            xdg_data = os.environ.get('XDG_DATA_HOME',
                                     os.path.expanduser('~/.local/share'))
            data_dir = os.path.join(xdg_data, 'winetranslator', 'prefixes')

        self.prefixes_dir = data_dir
        os.makedirs(self.prefixes_dir, exist_ok=True)

    def create_prefix(self, name: str, runner_id: int,
                     arch: str = 'win64') -> Tuple[bool, str, Optional[int]]:
        """
        Create a new Wine prefix.

        Args:
            name: Name for the prefix.
            runner_id: ID of the Wine runner to use.
            arch: Architecture ('win32' or 'win64').

        Returns:
            Tuple of (success, message, prefix_id)
        """
        # Sanitize name for filesystem
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_name = safe_name.replace(' ', '_')

        if not safe_name:
            return False, "Invalid prefix name", None

        # Create prefix path
        prefix_path = os.path.join(self.prefixes_dir, safe_name)

        # Check if prefix already exists
        if os.path.exists(prefix_path):
            return False, f"Prefix '{name}' already exists", None

        # Get runner info
        runners = self.db.get_runners()
        runner = next((r for r in runners if r['id'] == runner_id), None)

        if not runner:
            return False, "Runner not found", None

        # Create the Wine prefix
        success, message = create_wine_prefix(runner['path'], prefix_path, arch)

        if not success:
            # Clean up on failure
            if os.path.exists(prefix_path):
                shutil.rmtree(prefix_path, ignore_errors=True)
            return False, message, None

        # Add to database
        try:
            prefix_id = self.db.add_prefix(name, prefix_path, runner_id, arch)
            return True, f"Prefix '{name}' created successfully", prefix_id
        except Exception as e:
            # Clean up on database error
            if os.path.exists(prefix_path):
                shutil.rmtree(prefix_path, ignore_errors=True)
            return False, f"Database error: {str(e)}", None

    def get_all_prefixes(self) -> List[Dict[str, any]]:
        """Get all registered Wine prefixes."""
        return self.db.get_prefixes()

    def get_prefix(self, prefix_id: int) -> Optional[Dict[str, any]]:
        """Get a specific prefix by ID."""
        return self.db.get_prefix(prefix_id)

    def delete_prefix(self, prefix_id: int, delete_files: bool = True) -> Tuple[bool, str]:
        """
        Delete a Wine prefix.

        Args:
            prefix_id: ID of the prefix to delete.
            delete_files: Whether to delete the prefix files from disk.

        Returns:
            Tuple of (success, message)
        """
        prefix = self.get_prefix(prefix_id)
        if not prefix:
            return False, "Prefix not found"

        # Check if any applications are using this prefix
        apps = self.db.get_applications()
        apps_using_prefix = [a for a in apps if a['prefix_id'] == prefix_id]

        if apps_using_prefix:
            app_names = ', '.join(a['name'] for a in apps_using_prefix)
            return False, f"Cannot delete prefix: used by applications: {app_names}"

        # Delete from filesystem if requested
        if delete_files and os.path.exists(prefix['path']):
            try:
                shutil.rmtree(prefix['path'])
            except Exception as e:
                return False, f"Failed to delete prefix files: {str(e)}"

        # Delete from database
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM prefixes WHERE id = ?", (prefix_id,))
            self.db.conn.commit()
            return True, "Prefix deleted successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"

    def get_prefix_info(self, prefix_id: int) -> Optional[Dict[str, any]]:
        """
        Get detailed information about a prefix.

        Args:
            prefix_id: ID of the prefix.

        Returns:
            Dict with prefix information including filesystem details.
        """
        prefix = self.get_prefix(prefix_id)
        if not prefix:
            return None

        # Get filesystem info
        fs_info = get_wine_prefix_info(prefix['path'])

        # Merge database and filesystem info
        return {**prefix, **fs_info}

    def get_or_create_default_prefix(self, runner_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Get the default prefix, or create one if it doesn't exist.

        Args:
            runner_id: Runner ID to use if creating a new prefix.

        Returns:
            Tuple of (success, message, prefix_id)
        """
        prefixes = self.get_all_prefixes()

        # Look for a prefix named "default"
        default_prefix = next((p for p in prefixes if p['name'].lower() == 'default'), None)

        if default_prefix:
            return True, "Using existing default prefix", default_prefix['id']

        # Create default prefix
        return self.create_prefix("default", runner_id, arch='win64')
