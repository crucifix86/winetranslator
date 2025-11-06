"""
Dependency Manager for WineTranslator.

Handles installation of Wine dependencies using winetricks and detects
required dependencies for applications.
"""

import os
import subprocess
import shutil
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path


class DependencyManager:
    """Manages Wine dependencies and winetricks integration."""

    # Common dependencies that most games/apps need
    ESSENTIAL_DEPS = [
        'corefonts',      # Microsoft Core Fonts
        'vcrun2019',      # Visual C++ 2019 Redistributable
        'dotnet48',       # .NET Framework 4.8
        'd3dx9',          # DirectX 9
        'dxvk',           # Vulkan-based D3D11/10/9 implementation
    ]

    # Additional common dependencies
    COMMON_DEPS = [
        'vcrun2015',      # Visual C++ 2015
        'vcrun2017',      # Visual C++ 2017
        'vcrun2013',      # Visual C++ 2013
        'vcrun2012',      # Visual C++ 2012
        'vcrun2010',      # Visual C++ 2010
        'vcrun2008',      # Visual C++ 2008
        'dotnet40',       # .NET Framework 4.0
        'dotnet35',       # .NET Framework 3.5
        'directx9',       # DirectX 9
        'xna40',          # XNA Framework 4.0
        'physx',          # PhysX
        'quartz',         # QuickTime alternative
        'wmp10',          # Windows Media Player 10
        'xvid',           # Xvid codec
    ]

    # Font packages
    FONT_DEPS = [
        'corefonts',      # Arial, Times New Roman, etc.
        'liberation',     # Liberation fonts
        'tahoma',         # Tahoma font
        'consolas',       # Consolas font
    ]

    # Audio packages
    AUDIO_DEPS = [
        'sound',          # Core audio support
        'dsound',         # DirectSound
        'xact',           # Microsoft XACT audio engine (games)
        'directmusic',    # DirectMusic support
        'l3codecx',       # MP3 codec
    ]

    def __init__(self, db=None):
        """Initialize the dependency manager.

        Args:
            db: Optional database instance for checking settings.
        """
        self.winetricks_path = self._find_winetricks()
        self.db = db

    def _find_winetricks(self) -> Optional[str]:
        """Find winetricks executable on the system."""
        return shutil.which('winetricks')

    def is_winetricks_available(self) -> bool:
        """Check if winetricks is available."""
        return self.winetricks_path is not None

    def install_dependency(self, prefix_path: str, dependency: str,
                          wine_path: str = None) -> Tuple[bool, str]:
        """
        Install a dependency using winetricks.

        Args:
            prefix_path: Path to the Wine prefix.
            dependency: Name of the dependency to install.
            wine_path: Optional path to Wine executable.

        Returns:
            Tuple of (success, message)
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self.is_winetricks_available():
            logger.error("winetricks is not installed")
            return False, "winetricks is not installed"

        logger.info(f"Starting installation of {dependency} in prefix {prefix_path}")

        env = os.environ.copy()
        env['WINEPREFIX'] = prefix_path
        if wine_path:
            env['WINE'] = wine_path

        # Check if caching is enabled
        cache_enabled = False
        cache_path = None
        if self.db:
            cache_enabled = self.db.get_setting('cache_dependencies', '0') == '1'
            if cache_enabled:
                cache_path = self.db.get_setting('cache_path', '')
                if cache_path:
                    # Create cache directory if it doesn't exist
                    os.makedirs(cache_path, exist_ok=True)
                    env['WINETRICKS_CACHE'] = cache_path
                    logger.info(f"Using dependency cache: {cache_path}")

        try:
            cmd = [self.winetricks_path, '-q', dependency]
            logger.debug(f"Running winetricks command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"Successfully installed {dependency}")
                return True, f"Successfully installed {dependency}"
            else:
                error = result.stderr or result.stdout
                logger.error(f"Failed to install {dependency}: {error}")
                return False, f"Failed to install {dependency}: {error}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout while installing {dependency}"
        except Exception as e:
            return False, f"Error installing {dependency}: {str(e)}"

    def install_essential_dependencies(self, prefix_path: str,
                                      wine_path: str = None,
                                      progress_callback=None) -> Dict[str, bool]:
        """
        Install essential dependencies for the prefix.

        Args:
            prefix_path: Path to the Wine prefix.
            wine_path: Optional path to Wine executable.
            progress_callback: Optional callback function(dep_name, success, message)

        Returns:
            Dict mapping dependency names to success status.
        """
        results = {}

        for dep in self.ESSENTIAL_DEPS:
            success, message = self.install_dependency(prefix_path, dep, wine_path)
            results[dep] = success

            if progress_callback:
                progress_callback(dep, success, message)

        return results

    def detect_required_dependencies(self, exe_path: str) -> Set[str]:
        """
        Detect which dependencies an executable might need.

        This is a heuristic-based detection looking at:
        - File name patterns (Unity, Unreal, etc.)
        - Directory structure
        - Associated files

        Args:
            exe_path: Path to the .exe file.

        Returns:
            Set of recommended dependency names.
        """
        required = set()
        exe_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path).lower()

        # Check for Unity games
        if 'unity' in exe_name or self._has_unity_files(exe_dir):
            required.update(['vcrun2019', 'd3dx9', 'dxvk'])
            # Unity games need audio
            required.update(['sound', 'dsound', 'xact'])

        # Check for Unreal Engine games
        if 'unreal' in exe_name or self._has_unreal_files(exe_dir):
            required.update(['vcrun2019', 'd3dx9', 'dxvk'])
            # Unreal games need audio
            required.update(['sound', 'dsound', 'xact'])

        # Check for .NET applications
        if self._has_dotnet_files(exe_dir):
            required.add('dotnet48')

        # Check for XNA games
        if self._has_xna_files(exe_dir):
            required.add('xna40')
            # XNA games need audio
            required.update(['sound', 'dsound', 'xact'])

        # Check if this looks like a game (common game patterns)
        game_patterns = ['game', 'launcher', 'skyrim', 'fallout', 'witcher',
                        'gta', 'grand theft auto', 'assassin', 'creed']
        is_game = any(marker in exe_name for marker in game_patterns)

        # Check for Special/Anniversary Edition markers (Skyrim, etc)
        is_enhanced_edition = any(marker in exe_name for marker in ['se.exe', 'ae.exe', 'special', 'anniversary'])

        if is_game or is_enhanced_edition:
            # Modern games need VC++ runtimes and DirectX
            required.update(['vcrun2019', 'vcrun2015', 'd3dx9', 'dxvk'])
            # Games typically need audio
            required.update(['sound', 'dsound'])
            # Add fonts for better text rendering
            required.add('corefonts')

        # Default: add essentials if nothing specific detected
        if not required:
            required.update(['vcrun2019', 'd3dx9', 'corefonts'])

        return required

    def _has_unity_files(self, directory: str) -> bool:
        """Check if directory contains Unity game files."""
        unity_markers = [
            'UnityPlayer.dll',
            'UnityCrashHandler64.exe',
            'UnityEngine.dll',
        ]
        return any(os.path.isfile(os.path.join(directory, marker))
                  for marker in unity_markers)

    def _has_unreal_files(self, directory: str) -> bool:
        """Check if directory contains Unreal Engine files."""
        # Check for Engine directory
        if os.path.isdir(os.path.join(directory, 'Engine')):
            return True

        unreal_markers = [
            'UE4PrereqSetup_x64.exe',
            'UnrealEngine.dll',
        ]
        return any(os.path.isfile(os.path.join(directory, marker))
                  for marker in unreal_markers)

    def _has_dotnet_files(self, directory: str) -> bool:
        """Check if directory contains .NET application files."""
        dotnet_markers = [
            '.dll.config',
            'app.config',
        ]

        # Check for .NET assemblies
        for file in os.listdir(directory):
            if file.endswith('.dll.config') or file.endswith('.exe.config'):
                return True

        return False

    def _has_xna_files(self, directory: str) -> bool:
        """Check if directory contains XNA game files."""
        xna_markers = [
            'Microsoft.Xna.Framework.dll',
            'XnaNative.dll',
        ]
        return any(os.path.isfile(os.path.join(directory, marker))
                  for marker in xna_markers)

    def get_available_dependencies(self) -> List[Dict[str, str]]:
        """
        Get a categorized list of available dependencies.

        Returns:
            List of dicts with 'name', 'category', and 'description' keys.
        """
        deps = []

        # Visual C++ Runtimes
        deps.extend([
            {'name': 'vcrun2019', 'category': 'Runtime', 'description': 'Visual C++ 2015-2019 Runtime'},
            {'name': 'vcrun2017', 'category': 'Runtime', 'description': 'Visual C++ 2017 Runtime'},
            {'name': 'vcrun2015', 'category': 'Runtime', 'description': 'Visual C++ 2015 Runtime'},
            {'name': 'vcrun2013', 'category': 'Runtime', 'description': 'Visual C++ 2013 Runtime'},
            {'name': 'vcrun2012', 'category': 'Runtime', 'description': 'Visual C++ 2012 Runtime'},
            {'name': 'vcrun2010', 'category': 'Runtime', 'description': 'Visual C++ 2010 Runtime'},
        ])

        # .NET Framework
        deps.extend([
            {'name': 'dotnet48', 'category': '.NET', 'description': '.NET Framework 4.8'},
            {'name': 'dotnet40', 'category': '.NET', 'description': '.NET Framework 4.0'},
            {'name': 'dotnet35', 'category': '.NET', 'description': '.NET Framework 3.5'},
        ])

        # Graphics
        deps.extend([
            {'name': 'dxvk', 'category': 'Graphics', 'description': 'Vulkan-based D3D11/10/9'},
            {'name': 'd3dx9', 'category': 'Graphics', 'description': 'DirectX 9'},
            {'name': 'directx9', 'category': 'Graphics', 'description': 'DirectX 9 (full)'},
        ])

        # Fonts
        deps.extend([
            {'name': 'corefonts', 'category': 'Fonts', 'description': 'Microsoft Core Fonts'},
            {'name': 'liberation', 'category': 'Fonts', 'description': 'Liberation Fonts'},
        ])

        # Gaming Libraries
        deps.extend([
            {'name': 'xna40', 'category': 'Gaming', 'description': 'XNA Framework 4.0'},
            {'name': 'physx', 'category': 'Gaming', 'description': 'NVIDIA PhysX'},
        ])

        # Media
        deps.extend([
            {'name': 'quartz', 'category': 'Media', 'description': 'QuickTime Alternative'},
            {'name': 'wmp10', 'category': 'Media', 'description': 'Windows Media Player 10'},
        ])

        # Audio
        deps.extend([
            {'name': 'sound', 'category': 'Audio', 'description': 'Core audio support'},
            {'name': 'dsound', 'category': 'Audio', 'description': 'DirectSound'},
            {'name': 'xact', 'category': 'Audio', 'description': 'Microsoft XACT audio engine'},
            {'name': 'directmusic', 'category': 'Audio', 'description': 'DirectMusic support'},
            {'name': 'l3codecx', 'category': 'Audio', 'description': 'MP3 codec'},
        ])

        return deps

    def list_installed_dependencies(self, prefix_path: str) -> List[str]:
        """
        List dependencies already installed in a prefix.

        This is approximate - checks for marker files/directories.

        Args:
            prefix_path: Path to the Wine prefix.

        Returns:
            List of likely installed dependencies.
        """
        installed = []

        # Check for common markers
        drive_c = os.path.join(prefix_path, 'drive_c')
        if not os.path.isdir(drive_c):
            return installed

        # Check for .NET
        dotnet_dir = os.path.join(drive_c, 'windows', 'Microsoft.NET', 'Framework')
        if os.path.isdir(dotnet_dir):
            installed.append('dotnet (some version)')

        # Check for DirectX
        d3dx9_dll = os.path.join(drive_c, 'windows', 'system32', 'd3dx9_43.dll')
        if os.path.isfile(d3dx9_dll):
            installed.append('d3dx9')

        # Check for VC runtimes
        vcrun_dlls = [
            'msvcp140.dll',  # 2015-2019
            'msvcp120.dll',  # 2013
            'msvcp110.dll',  # 2012
        ]
        system32 = os.path.join(drive_c, 'windows', 'system32')
        for dll in vcrun_dlls:
            if os.path.isfile(os.path.join(system32, dll)):
                if dll == 'msvcp140.dll':
                    installed.append('vcrun2019/2017/2015')
                elif dll == 'msvcp120.dll':
                    installed.append('vcrun2013')
                elif dll == 'msvcp110.dll':
                    installed.append('vcrun2012')

        return installed
