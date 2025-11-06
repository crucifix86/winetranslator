"""
Database management for WineTranslator.

Handles SQLite database for storing applications, prefixes, runners, and configurations.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    """Manages the WineTranslator SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database connection.

        Args:
            db_path: Path to the database file. If None, uses XDG_DATA_HOME.
        """
        if db_path is None:
            data_home = os.environ.get('XDG_DATA_HOME',
                                      os.path.expanduser('~/.local/share'))
            db_dir = os.path.join(data_home, 'winetranslator')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'winetranslator.db')

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Runners table (Wine versions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL,
                version TEXT,
                runner_type TEXT NOT NULL DEFAULT 'wine',
                is_default INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Prefixes table (Wine prefixes/bottles)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prefixes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL UNIQUE,
                runner_id INTEGER,
                arch TEXT DEFAULT 'win64',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (runner_id) REFERENCES runners(id)
            )
        """)

        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                executable_path TEXT NOT NULL,
                prefix_id INTEGER NOT NULL,
                icon_path TEXT,
                working_directory TEXT,
                arguments TEXT,
                description TEXT,
                last_played TEXT,
                play_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prefix_id) REFERENCES prefixes(id)
            )
        """)

        # Configuration table (key-value pairs for app-specific settings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                UNIQUE(app_id, key),
                FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
            )
        """)

        # Environment variables table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS env_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                UNIQUE(app_id, key),
                FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    # Runner operations
    def add_runner(self, name: str, path: str, version: str = None,
                   runner_type: str = 'wine', is_default: bool = False) -> int:
        """Add a Wine runner to the database."""
        cursor = self.conn.cursor()

        if is_default:
            # Unset other defaults
            cursor.execute("UPDATE runners SET is_default = 0")

        cursor.execute("""
            INSERT INTO runners (name, path, version, runner_type, is_default)
            VALUES (?, ?, ?, ?, ?)
        """, (name, path, version, runner_type, 1 if is_default else 0))

        self.conn.commit()
        return cursor.lastrowid

    def get_runners(self) -> List[Dict[str, Any]]:
        """Get all Wine runners."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM runners ORDER BY is_default DESC, name ASC")
        return [dict(row) for row in cursor.fetchall()]

    def get_default_runner(self) -> Optional[Dict[str, Any]]:
        """Get the default Wine runner."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM runners WHERE is_default = 1 LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

    def set_default_runner(self, runner_id: int):
        """Set a runner as the default."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE runners SET is_default = 0")
        cursor.execute("UPDATE runners SET is_default = 1 WHERE id = ?", (runner_id,))
        self.conn.commit()

    # Prefix operations
    def add_prefix(self, name: str, path: str, runner_id: int,
                   arch: str = 'win64') -> int:
        """Add a Wine prefix to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO prefixes (name, path, runner_id, arch)
            VALUES (?, ?, ?, ?)
        """, (name, path, runner_id, arch))
        self.conn.commit()
        return cursor.lastrowid

    def get_prefixes(self) -> List[Dict[str, Any]]:
        """Get all Wine prefixes."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, r.name as runner_name
            FROM prefixes p
            LEFT JOIN runners r ON p.runner_id = r.id
            ORDER BY p.name ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_prefix(self, prefix_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific prefix by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, r.name as runner_name, r.path as runner_path
            FROM prefixes p
            LEFT JOIN runners r ON p.runner_id = r.id
            WHERE p.id = ?
        """, (prefix_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # Application operations
    def add_application(self, name: str, executable_path: str, prefix_id: int,
                       icon_path: str = None, working_directory: str = None,
                       arguments: str = None, description: str = None) -> int:
        """Add an application to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO applications
            (name, executable_path, prefix_id, icon_path, working_directory,
             arguments, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, executable_path, prefix_id, icon_path, working_directory,
              arguments, description))
        self.conn.commit()
        return cursor.lastrowid

    def get_applications(self) -> List[Dict[str, Any]]:
        """Get all applications."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, p.name as prefix_name, p.path as prefix_path
            FROM applications a
            LEFT JOIN prefixes p ON a.prefix_id = p.id
            ORDER BY a.name ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific application by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, p.name as prefix_name, p.path as prefix_path,
                   r.path as runner_path, r.name as runner_name
            FROM applications a
            LEFT JOIN prefixes p ON a.prefix_id = p.id
            LEFT JOIN runners r ON p.runner_id = r.id
            WHERE a.id = ?
        """, (app_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_application_play_time(self, app_id: int):
        """Update the last played time and increment play count."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE applications
            SET last_played = ?, play_count = play_count + 1
            WHERE id = ?
        """, (datetime.now().isoformat(), app_id))
        self.conn.commit()

    def delete_application(self, app_id: int):
        """Delete an application."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        self.conn.commit()

    # Configuration operations
    def set_config(self, app_id: int, key: str, value: str):
        """Set a configuration value for an application."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO configurations (app_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(app_id, key) DO UPDATE SET value = excluded.value
        """, (app_id, key, value))
        self.conn.commit()

    def get_config(self, app_id: int, key: str) -> Optional[str]:
        """Get a configuration value for an application."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value FROM configurations
            WHERE app_id = ? AND key = ?
        """, (app_id, key))
        row = cursor.fetchone()
        return row['value'] if row else None

    def get_all_configs(self, app_id: int) -> Dict[str, str]:
        """Get all configuration values for an application."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT key, value FROM configurations WHERE app_id = ?
        """, (app_id,))
        return {row['key']: row['value'] for row in cursor.fetchall()}

    # Environment variable operations
    def set_env_var(self, app_id: int, key: str, value: str):
        """Set an environment variable for an application."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO env_variables (app_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(app_id, key) DO UPDATE SET value = excluded.value
        """, (app_id, key, value))
        self.conn.commit()

    def get_env_vars(self, app_id: int) -> Dict[str, str]:
        """Get all environment variables for an application."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT key, value FROM env_variables WHERE app_id = ?
        """, (app_id,))
        return {row['key']: row['value'] for row in cursor.fetchall()}

    def delete_env_var(self, app_id: int, key: str):
        """Delete an environment variable for an application."""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM env_variables WHERE app_id = ? AND key = ?
        """, (app_id, key))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
