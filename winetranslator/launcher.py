"""
Desktop launcher for WineTranslator applications.

Allows launching apps directly from desktop shortcuts.
"""

import sys
import os
import logging

from .database.db import Database
from .core.app_launcher import AppLauncher
from .utils.logger import setup_logging


def launch():
    """Launch an application by ID from command line."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) < 2:
        print("Usage: winetranslator-launch <app_id>")
        sys.exit(1)

    try:
        app_id = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid app ID '{sys.argv[1]}'. Must be a number.")
        sys.exit(1)

    try:
        # Initialize database
        db = Database()

        # Launch the application
        launcher = AppLauncher(db)
        success, message, process = launcher.launch(app_id)

        if not success:
            logger.error(f"Failed to launch app {app_id}: {message}")
            print(f"Error: {message}")
            sys.exit(1)

        logger.info(f"Successfully launched app {app_id}")

    except Exception as e:
        logger.error(f"Error launching app {app_id}: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    launch()
