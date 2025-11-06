"""
Wine utility functions for detection and version management.
"""

import os
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def find_wine_executables() -> List[Dict[str, str]]:
    """
    Find all available Wine executables on the system.

    Returns:
        List of dicts with 'name', 'path', 'version', and 'type' keys.
    """
    wine_executables = []

    # Common Wine executable names
    wine_names = ['wine', 'wine64', 'wine-staging', 'wine-devel']

    # Check PATH
    for wine_name in wine_names:
        wine_path = _which(wine_name)
        if wine_path:
            version = get_wine_version(wine_path)
            wine_executables.append({
                'name': wine_name,
                'path': wine_path,
                'version': version,
                'type': 'wine'
            })

    # Check common Wine installation directories
    common_dirs = [
        '/usr/bin',
        '/usr/local/bin',
        os.path.expanduser('~/.local/bin'),
        os.path.expanduser('~/.local/share/lutris/runners/wine'),
    ]

    for directory in common_dirs:
        if os.path.isdir(directory):
            # For Lutris-style directories, check subdirectories
            if 'lutris' in directory:
                wine_executables.extend(_scan_lutris_runners(directory))
            else:
                for wine_name in wine_names:
                    wine_path = os.path.join(directory, wine_name)
                    if os.path.isfile(wine_path) and os.access(wine_path, os.X_OK):
                        # Avoid duplicates
                        if not any(w['path'] == wine_path for w in wine_executables):
                            version = get_wine_version(wine_path)
                            wine_executables.append({
                                'name': wine_name,
                                'path': wine_path,
                                'version': version,
                                'type': 'wine'
                            })

    # Check for Proton installations (Steam)
    proton_executables = _find_proton_installations()
    wine_executables.extend(proton_executables)

    return wine_executables


def _which(program: str) -> Optional[str]:
    """Find program in PATH (similar to 'which' command)."""
    try:
        result = subprocess.run(['which', program], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _scan_lutris_runners(base_dir: str) -> List[Dict[str, str]]:
    """Scan Lutris runners directory for Wine versions."""
    runners = []
    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                # Look for wine binary in bin subdirectory
                wine_bin = os.path.join(item_path, 'bin', 'wine')
                if os.path.isfile(wine_bin) and os.access(wine_bin, os.X_OK):
                    version = get_wine_version(wine_bin)
                    runners.append({
                        'name': f'Lutris - {item}',
                        'path': wine_bin,
                        'version': version,
                        'type': 'wine'
                    })
    except OSError:
        pass
    return runners


def _find_proton_installations() -> List[Dict[str, str]]:
    """Find Proton installations from Steam."""
    proton_installations = []
    steam_dirs = [
        os.path.expanduser('~/.steam/steam/steamapps/common'),
        os.path.expanduser('~/.local/share/Steam/steamapps/common'),
    ]

    for steam_dir in steam_dirs:
        if not os.path.isdir(steam_dir):
            continue

        try:
            for item in os.listdir(steam_dir):
                if item.startswith('Proton'):
                    proton_path = os.path.join(steam_dir, item)
                    wine_bin = os.path.join(proton_path, 'files', 'bin', 'wine')
                    if os.path.isfile(wine_bin) and os.access(wine_bin, os.X_OK):
                        version = get_wine_version(wine_bin)
                        proton_installations.append({
                            'name': item,
                            'path': wine_bin,
                            'version': version,
                            'type': 'proton'
                        })
        except OSError:
            continue

    return proton_installations


def get_wine_version(wine_path: str) -> str:
    """
    Get the version of a Wine executable.

    Args:
        wine_path: Path to the Wine executable.

    Returns:
        Version string or 'Unknown' if detection fails.
    """
    try:
        result = subprocess.run(
            [wine_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse version from output like "wine-9.0" or "wine-8.0.1 (Staging)"
            version_match = re.search(r'wine[- ](\d+\.\d+(?:\.\d+)?)', result.stdout)
            if version_match:
                return version_match.group(1)
            return result.stdout.strip()
    except Exception:
        pass
    return 'Unknown'


def check_wine_dependencies() -> Dict[str, bool]:
    """
    Check if Wine and related dependencies are installed.

    Returns:
        Dict with dependency names as keys and availability as values.
    """
    dependencies = {
        'wine': False,
        'winetricks': False,
        'cabextract': False,
    }

    for dep in dependencies:
        dependencies[dep] = _which(dep) is not None

    return dependencies


def get_wine_prefix_info(prefix_path: str) -> Dict[str, any]:
    """
    Get information about a Wine prefix.

    Args:
        prefix_path: Path to the Wine prefix.

    Returns:
        Dict with prefix information.
    """
    info = {
        'exists': os.path.isdir(prefix_path),
        'arch': None,
        'windows_version': None,
        'size': 0,
    }

    if not info['exists']:
        return info

    # Detect architecture
    system_reg = os.path.join(prefix_path, 'system.reg')
    if os.path.isfile(system_reg):
        try:
            with open(system_reg, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # Read first 1KB
                if 'win64' in content.lower() or 'amd64' in content.lower():
                    info['arch'] = 'win64'
                else:
                    info['arch'] = 'win32'
        except Exception:
            pass

    # Get prefix size
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(prefix_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        info['size'] = total_size
    except Exception:
        pass

    return info


def create_wine_prefix(wine_path: str, prefix_path: str, arch: str = 'win64') -> Tuple[bool, str]:
    """
    Create a new Wine prefix.

    Args:
        wine_path: Path to the Wine executable.
        prefix_path: Path where the prefix should be created.
        arch: Architecture ('win32' or 'win64').

    Returns:
        Tuple of (success: bool, message: str).
    """
    os.makedirs(prefix_path, exist_ok=True)

    env = os.environ.copy()
    env['WINEPREFIX'] = prefix_path
    env['WINEARCH'] = arch

    try:
        # Initialize prefix with wineboot
        result = subprocess.run(
            [wine_path, 'wineboot', '-i'],
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return True, f"Wine prefix created successfully at {prefix_path}"
        else:
            return False, f"Failed to create prefix: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Timeout while creating Wine prefix"
    except Exception as e:
        return False, f"Error creating Wine prefix: {str(e)}"


def _detect_audio_driver() -> str:
    """
    Detect the best audio driver to use for Wine.

    Returns:
        Audio driver name ('pulse' for PulseAudio, 'alsa' for ALSA, or '' for auto).
    """
    # Check if PulseAudio is running
    try:
        result = subprocess.run(['pactl', 'info'], capture_output=True, timeout=1)
        if result.returncode == 0:
            return 'pulse'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check if PipeWire is running (uses pulseaudio compatibility)
    try:
        result = subprocess.run(['pw-cli', 'info'], capture_output=True, timeout=1)
        if result.returncode == 0:
            return 'pulse'  # PipeWire supports PulseAudio protocol
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Default to ALSA
    return 'alsa'


def launch_wine_application(wine_path: str, prefix_path: str, exe_path: str,
                           args: List[str] = None, working_dir: str = None,
                           env_vars: Dict[str, str] = None, app_name: str = None) -> subprocess.Popen:
    """
    Launch a Windows application with Wine.

    Args:
        wine_path: Path to the Wine executable.
        prefix_path: Path to the Wine prefix.
        exe_path: Path to the .exe file.
        args: Additional arguments for the application.
        working_dir: Working directory for the application.
        env_vars: Additional environment variables.
        app_name: Name of the application (for logging).

    Returns:
        Subprocess Popen object.
    """
    import logging
    logger = logging.getLogger(__name__)

    env = os.environ.copy()
    env['WINEPREFIX'] = prefix_path

    # Set audio driver (auto-detect PulseAudio/ALSA)
    audio_driver = _detect_audio_driver()
    env['WINEAUDIODRIVER'] = audio_driver
    logger.info(f"Using audio driver: {audio_driver}")

    # Set DirectSound to use native Wine implementation
    # This helps with audio compatibility in games
    if 'WINEDLLOVERRIDES' in env:
        # Append to existing overrides
        env['WINEDLLOVERRIDES'] = f"{env['WINEDLLOVERRIDES']};dsound=n,b"
    else:
        env['WINEDLLOVERRIDES'] = 'dsound=n,b'

    # Add custom environment variables
    if env_vars:
        env.update(env_vars)

    # Build command
    cmd = [wine_path, exe_path]
    if args:
        cmd.extend(args)

    # Create app-specific log file
    log_dir = os.path.join(os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')), 'winetranslator', 'app_logs')
    os.makedirs(log_dir, exist_ok=True)

    if app_name:
        # Sanitize app name for filename
        safe_name = "".join(c for c in app_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        log_file = os.path.join(log_dir, f"{safe_name}.log")
    else:
        log_file = os.path.join(log_dir, 'unknown_app.log')

    logger.info(f"Launching app: {app_name or exe_path}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info(f"Log file: {log_file}")

    # Launch application with output redirected to log file
    try:
        log_handle = open(log_file, 'a')
        log_handle.write(f"\n{'='*60}\n")
        log_handle.write(f"Launch: {app_name or exe_path}\n")
        log_handle.write(f"Time: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}\n")
        log_handle.write(f"Command: {' '.join(cmd)}\n")
        log_handle.write(f"{'='*60}\n\n")
        log_handle.flush()

        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=working_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT  # Combine stderr with stdout
        )

        # Store log handle on process object so it can be closed later
        process._log_handle = log_handle

    except Exception as e:
        logger.error(f"Failed to launch {app_name or exe_path}: {str(e)}")
        raise

    return process
