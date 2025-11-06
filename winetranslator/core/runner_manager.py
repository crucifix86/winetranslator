"""
Wine Runner Manager for WineTranslator.

Manages Wine runners (Wine versions, Proton, etc.).
"""

import os
from typing import List, Dict, Optional
from ..database.db import Database
from ..utils.wine_utils import find_wine_executables, get_wine_version


class RunnerManager:
    """Manages Wine runners."""

    def __init__(self, db: Database):
        """
        Initialize the runner manager.

        Args:
            db: Database instance.
        """
        self.db = db

    def scan_system(self) -> List[Dict[str, str]]:
        """
        Scan the system for available Wine installations.

        Returns:
            List of found Wine executables.
        """
        return find_wine_executables()

    def auto_detect_and_add(self) -> int:
        """
        Auto-detect Wine installations and add them to the database.

        Returns:
            Number of runners added.
        """
        found_wines = self.scan_system()
        existing_runners = {r['path']: r for r in self.db.get_runners()}

        added_count = 0
        for wine in found_wines:
            # Skip if already in database
            if wine['path'] in existing_runners:
                continue

            # Add to database
            is_default = added_count == 0 and len(existing_runners) == 0
            self.db.add_runner(
                name=wine['name'],
                path=wine['path'],
                version=wine['version'],
                runner_type=wine['type'],
                is_default=is_default
            )
            added_count += 1

        return added_count

    def add_runner(self, name: str, path: str, is_default: bool = False) -> Optional[int]:
        """
        Add a Wine runner manually.

        Args:
            name: Display name for the runner.
            path: Path to the Wine executable.
            is_default: Set as default runner.

        Returns:
            Runner ID or None on failure.
        """
        # Verify the Wine executable exists and is executable
        if not os.path.isfile(path):
            return None
        if not os.access(path, os.X_OK):
            return None

        version = get_wine_version(path)
        runner_type = 'proton' if 'Proton' in path else 'wine'

        return self.db.add_runner(
            name=name,
            path=path,
            version=version,
            runner_type=runner_type,
            is_default=is_default
        )

    def get_all_runners(self) -> List[Dict[str, any]]:
        """Get all registered Wine runners."""
        return self.db.get_runners()

    def get_default_runner(self) -> Optional[Dict[str, any]]:
        """Get the default Wine runner."""
        return self.db.get_default_runner()

    def set_default(self, runner_id: int):
        """Set a runner as the default."""
        self.db.set_default_runner(runner_id)

    def ensure_default_runner(self):
        """
        Ensure there's at least one runner and one is set as default.
        Auto-detects if no runners exist.
        """
        runners = self.get_all_runners()

        if not runners:
            # No runners, try to auto-detect
            added = self.auto_detect_and_add()
            if added == 0:
                raise RuntimeError("No Wine installation found on system")
            return

        # Check if any runner is set as default
        if not any(r['is_default'] for r in runners):
            # Set the first one as default
            self.set_default(runners[0]['id'])
