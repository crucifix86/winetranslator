"""
Application Launcher for WineTranslator.

Handles launching Windows applications with Wine.
"""

import os
import subprocess
from typing import Optional, List, Dict
from ..database.db import Database
from ..utils.wine_utils import launch_wine_application


class AppLauncher:
    """Manages launching Windows applications."""

    def __init__(self, db: Database):
        """
        Initialize the application launcher.

        Args:
            db: Database instance.
        """
        self.db = db

    def launch(self, app_id: int) -> tuple[bool, str, Optional[subprocess.Popen]]:
        """
        Launch an application.

        Args:
            app_id: ID of the application to launch.

        Returns:
            Tuple of (success, message, process)
        """
        # Get application details
        app = self.db.get_application(app_id)
        if not app:
            return False, "Application not found", None

        # Verify executable exists
        if not os.path.isfile(app['executable_path']):
            return False, f"Executable not found: {app['executable_path']}", None

        # Get runner path
        if not app['runner_path']:
            return False, "Wine runner not configured for this application", None

        # Prepare arguments
        args = []
        if app['arguments']:
            args = app['arguments'].split()

        # Prepare working directory
        working_dir = app['working_directory']
        if not working_dir or not os.path.isdir(working_dir):
            # Default to executable's directory
            working_dir = os.path.dirname(app['executable_path'])

        # Get environment variables
        env_vars = self.db.get_env_vars(app_id)

        try:
            # Launch the application
            process = launch_wine_application(
                wine_path=app['runner_path'],
                prefix_path=app['prefix_path'],
                exe_path=app['executable_path'],
                args=args,
                working_dir=working_dir,
                env_vars=env_vars,
                app_name=app['name']
            )

            # Update play statistics
            self.db.update_application_play_time(app_id)

            return True, f"Launched {app['name']}", process

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to launch {app['name']}: {str(e)}", exc_info=True)
            return False, f"Failed to launch application: {str(e)}", None

    def add_application(self, name: str, executable_path: str, prefix_id: int,
                       icon_path: str = None, working_directory: str = None,
                       arguments: str = None, description: str = None) -> tuple[bool, str, Optional[int]]:
        """
        Add a new application to the library.

        Args:
            name: Application name.
            executable_path: Path to the .exe file.
            prefix_id: ID of the Wine prefix to use.
            icon_path: Optional path to icon file.
            working_directory: Optional working directory.
            arguments: Optional launch arguments.
            description: Optional description.

        Returns:
            Tuple of (success, message, app_id)
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"AppLauncher.add_application called: name={name}, exe={executable_path}, prefix_id={prefix_id}")

        # Verify executable exists
        if not os.path.isfile(executable_path):
            logger.error(f"Executable not found: {executable_path}")
            return False, f"Executable not found: {executable_path}", None

        logger.info("Executable exists, getting prefix")
        # Verify prefix exists
        prefix = self.db.get_prefix(prefix_id)
        if not prefix:
            logger.error(f"Invalid prefix: {prefix_id}")
            return False, "Invalid prefix", None

        logger.info(f"Prefix found: {prefix['name']}")
        # Set default working directory if not provided
        if not working_directory:
            working_directory = os.path.dirname(executable_path)
        logger.info(f"Working directory: {working_directory}")

        try:
            logger.info("Calling db.add_application...")
            app_id = self.db.add_application(
                name=name,
                executable_path=executable_path,
                prefix_id=prefix_id,
                icon_path=icon_path,
                working_directory=working_directory,
                arguments=arguments,
                description=description
            )
            logger.info(f"db.add_application returned app_id={app_id}")
            return True, f"Application '{name}' added successfully", app_id

        except Exception as e:
            logger.error(f"Exception in add_application: {str(e)}", exc_info=True)
            return False, f"Failed to add application: {str(e)}", None

    def remove_application(self, app_id: int) -> tuple[bool, str]:
        """
        Remove an application from the library.

        Args:
            app_id: ID of the application to remove.

        Returns:
            Tuple of (success, message)
        """
        app = self.db.get_application(app_id)
        if not app:
            return False, "Application not found"

        try:
            self.db.delete_application(app_id)
            return True, f"Application '{app['name']}' removed"
        except Exception as e:
            return False, f"Failed to remove application: {str(e)}"

    def get_all_applications(self) -> List[Dict[str, any]]:
        """Get all applications in the library."""
        return self.db.get_applications()

    def get_application(self, app_id: int) -> Optional[Dict[str, any]]:
        """Get a specific application by ID."""
        return self.db.get_application(app_id)
