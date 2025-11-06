"""
Logging configuration for WineTranslator.
"""

import logging
import os
from pathlib import Path


def setup_logging():
    """
    Set up logging for WineTranslator.

    Logs go to:
    - ~/.local/share/winetranslator/winetranslator.log
    - Console (stdout)
    """
    # Create log directory
    data_home = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    log_dir = os.path.join(data_home, 'winetranslator')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'winetranslator.log')

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger('winetranslator')
    logger.info(f"Logging initialized. Log file: {log_file}")

    return logger
