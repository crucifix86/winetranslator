"""
Update Manager for WineTranslator.

Handles checking for updates and updating from GitHub.
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional


class Updater:
    """Manages application updates from GitHub."""

    def __init__(self):
        """Initialize the updater."""
        self.repo_url = "https://github.com/crucifix86/winetranslator"
        self.repo_path = self._find_repo_path()

    def _find_repo_path(self) -> Optional[str]:
        """
        Find the path to the WineTranslator repository.

        Returns:
            Path to the repository or None if not found.
        """
        # Try to find the git repository
        # Start from the module location
        module_path = Path(__file__).resolve().parent.parent.parent

        if (module_path / '.git').is_dir():
            return str(module_path)

        return None

    def is_git_repo(self) -> bool:
        """Check if WineTranslator is installed from a git repository."""
        return self.repo_path is not None and os.path.isdir(os.path.join(self.repo_path, '.git'))

    def get_current_commit(self) -> Optional[str]:
        """
        Get the current git commit hash.

        Returns:
            Commit hash or None if not a git repo.
        """
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def get_current_branch(self) -> Optional[str]:
        """
        Get the current git branch.

        Returns:
            Branch name or None if not a git repo.
        """
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def check_for_updates(self) -> Tuple[bool, str, Optional[str]]:
        """
        Check if updates are available.

        Returns:
            Tuple of (has_updates, message, remote_commit)
        """
        if not self.is_git_repo():
            return False, "Not installed from git repository", None

        try:
            # Fetch latest from remote
            result = subprocess.run(
                ['git', 'fetch', 'origin'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return False, f"Failed to fetch updates: {result.stderr}", None

            # Get current commit
            current = self.get_current_commit()
            if not current:
                return False, "Could not determine current version", None

            # Get remote commit
            branch = self.get_current_branch() or 'main'
            result = subprocess.run(
                ['git', 'rev-parse', f'origin/{branch}'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return False, f"Failed to check remote version: {result.stderr}", None

            remote = result.stdout.strip()

            if current == remote:
                return False, "Already up to date", remote
            else:
                # Get number of commits behind
                result = subprocess.run(
                    ['git', 'rev-list', '--count', f'{current}..{remote}'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                commits_behind = result.stdout.strip() if result.returncode == 0 else "?"
                return True, f"Update available ({commits_behind} commits behind)", remote

        except subprocess.TimeoutExpired:
            return False, "Timeout while checking for updates", None
        except Exception as e:
            return False, f"Error checking for updates: {str(e)}", None

    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes in the repository.
        Only checks for modified/staged tracked files, ignores untracked files.

        Returns:
            True if there are uncommitted changes.
        """
        if not self.is_git_repo():
            return False

        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Only count modified/staged files (M, A, D, R, C, U)
                # Ignore untracked files (??)
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and not line.startswith('??'):
                        return True
                return False

        except Exception:
            pass

        return False

    def update(self, force: bool = False) -> Tuple[bool, str]:
        """
        Update WineTranslator to the latest version.

        Args:
            force: If True, discard local changes and update anyway.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_git_repo():
            return False, "Not installed from git repository. Please reinstall from source."

        # Check for uncommitted changes
        if not force and self.has_uncommitted_changes():
            return False, "You have uncommitted changes. Commit or stash them first, or use force update."

        try:
            branch = self.get_current_branch() or 'main'

            if force:
                # Reset hard to remote
                result = subprocess.run(
                    ['git', 'reset', '--hard', f'origin/{branch}'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # Pull changes
                result = subprocess.run(
                    ['git', 'pull', 'origin', branch],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            if result.returncode != 0:
                return False, f"Failed to update: {result.stderr}"

            # Check if there were any changes
            if "Already up to date" in result.stdout:
                return True, "Already up to date"

            # Reinstall the package
            # Try with --break-system-packages for newer Python versions
            install_result = subprocess.run(
                ['pip3', 'install', '--user', '--break-system-packages', '-e', '.'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # If that fails, try without --break-system-packages
            if install_result.returncode != 0 and 'unrecognized arguments' in install_result.stderr:
                install_result = subprocess.run(
                    ['pip3', 'install', '--user', '-e', '.'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

            if install_result.returncode != 0:
                return False, f"Updated code but failed to reinstall package: {install_result.stderr}"

            return True, "Updated successfully! Please restart WineTranslator."

        except subprocess.TimeoutExpired:
            return False, "Timeout while updating"
        except Exception as e:
            return False, f"Error during update: {str(e)}"

    def get_changelog(self, since_commit: Optional[str] = None) -> Optional[str]:
        """
        Get changelog since a specific commit.

        Args:
            since_commit: Commit hash to get changes since. If None, gets last 10 commits.

        Returns:
            Changelog string or None on error.
        """
        if not self.is_git_repo():
            return None

        try:
            if since_commit:
                cmd = ['git', 'log', '--oneline', f'{since_commit}..HEAD']
            else:
                cmd = ['git', 'log', '--oneline', '-n', '10']

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception:
            pass

        return None

    def get_version_info(self) -> dict:
        """
        Get version information.

        Returns:
            Dict with version info.
        """
        info = {
            'is_git_repo': self.is_git_repo(),
            'repo_path': self.repo_path,
            'current_commit': None,
            'current_branch': None,
            'has_uncommitted_changes': False,
            'repo_url': self.repo_url,
        }

        if self.is_git_repo():
            info['current_commit'] = self.get_current_commit()
            info['current_branch'] = self.get_current_branch()
            info['has_uncommitted_changes'] = self.has_uncommitted_changes()

        return info
