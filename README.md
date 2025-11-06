# WineTranslator

A simple, easy-to-use Wine GUI for running Windows applications on Linux with automatic dependency management.

## Features

- **Easy-to-use GTK4 interface** - Modern, native Linux design using Libadwaita
- **Isolated Wine prefixes** - Each application gets its own clean environment
- **Multiple Wine versions** - Support for Wine, Wine-Staging, Proton, and custom builds
- **Automatic dependency detection** - Detects Unity, Unreal, .NET, XNA games and apps
- **Winetricks integration** - Auto-installs VC++ runtimes, DirectX, fonts, and more
- **One-click launching** - Simple application library with launch statistics
- **Smart runner detection** - Automatically finds Wine installations on your system

## Why WineTranslator?

Unlike other Wine tools, WineTranslator focuses on **ease of use**:

- **No manual winetricks needed** - Dependencies are detected and installed automatically
- **Isolated environments** - Applications never conflict with each other
- **Simple setup** - Add an app in 3 clicks: choose .exe → name it → done
- **Beginner-friendly** - No need to understand Wine prefixes, WINEPREFIX, or environment variables

## Installation

### Automatic Installation (Recommended)

We provide an automatic installation script that detects your Linux distribution and installs all dependencies:

```bash
cd /media/doug/stuff/winetranslator
./install.sh
```

The script supports:
- Debian/Ubuntu/Linux Mint/Pop!_OS
- Fedora
- Arch Linux/Manjaro/EndeavourOS
- openSUSE

### Manual Installation

#### System Dependencies

**Debian/Ubuntu:**
```bash
sudo apt install python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 wine winetricks
```

**Fedora:**
```bash
sudo dnf install python3 python3-gobject gtk4 libadwaita wine winetricks
```

**Arch Linux:**
```bash
sudo pacman -S python python-gobject gtk4 libadwaita wine winetricks
```

#### Install WineTranslator

```bash
cd /media/doug/stuff/winetranslator
pip3 install -e .
```

Or run directly without installation:
```bash
./run.sh
```

## Quick Start

1. **Launch WineTranslator**
   ```bash
   winetranslator
   # or
   ./run.sh
   ```

2. **Add an application**
   - Click the **+** button in the header
   - Select your Windows .exe file
   - Give it a name
   - Choose or create a Wine prefix
   - Click **Add Application**

3. **Automatic magic happens**
   - WineTranslator detects if your app needs DirectX, .NET, VC++ runtimes, etc.
   - Dependencies are installed automatically in the background
   - Your app is ready to run!

4. **Launch your app**
   - Click the application card
   - Click **Launch**

## Updating WineTranslator

WineTranslator includes built-in update functionality when installed from git!

### GUI Update (Recommended)

1. Open WineTranslator
2. Click the menu button (three lines) in the top-right
3. Select **"Check for Updates"**
4. If updates are available, click **"Update"**
5. Restart WineTranslator when prompted

### Command Line Update

```bash
cd /media/doug/stuff/winetranslator
./update.sh
```

Or manually:
```bash
git pull origin main
pip3 install --user -e .
```

The update feature:
- ✅ Checks GitHub for new commits
- ✅ Shows what will be updated
- ✅ Downloads and installs updates
- ✅ Offers to restart automatically
- ✅ No need to reinstall from scratch!

## Architecture

WineTranslator is built with simplicity and maintainability in mind:

```
winetranslator/
├── core/                    # Business logic
│   ├── runner_manager.py    # Wine version management
│   ├── prefix_manager.py    # Isolated prefix creation
│   ├── app_launcher.py      # Application execution
│   └── dependency_manager.py # Winetricks integration
├── gui/                     # GTK4 interface
│   ├── main_window.py       # Application library
│   └── add_app_dialog.py    # Setup wizard
├── database/                # SQLite storage
│   └── db.py               # Schema and queries
└── utils/                   # Utilities
    └── wine_utils.py       # Wine detection and execution
```

## Key Design Decisions

1. **Python + GTK4** - Rapid development, native Linux look and feel
2. **SQLite** - Lightweight, no server needed, easy backups
3. **Isolated prefixes** - Prevent application conflicts
4. **Hierarchical config** - Global → Runner → App settings
5. **Automatic dependency detection** - Check for Unity, Unreal, .NET markers
6. **Winetricks wrapper** - Leverage existing dependency management

## Dependency Detection

WineTranslator automatically detects:

- **Unity games** - Checks for `UnityPlayer.dll`, installs VC++, DirectX, DXVK
- **Unreal Engine** - Checks for `Engine/` directory, installs VC++, DirectX
- **.NET applications** - Checks for `.dll.config` files, installs .NET Framework
- **XNA games** - Checks for `Microsoft.Xna.Framework.dll`, installs XNA 4.0

## Advanced Usage

### Multiple Wine Versions

WineTranslator automatically detects:
- System Wine (`/usr/bin/wine`)
- Lutris runners (`~/.local/share/lutris/runners/wine/*`)
- Proton versions (`~/.steam/steam/steamapps/common/Proton*`)

Add custom Wine builds through the Preferences dialog (coming soon).

### Manual Dependency Installation

If auto-detection misses something, you can manually install dependencies:
1. Open application details
2. Click "Manage Dependencies"
3. Select from common dependencies (VC++, DirectX, fonts, etc.)
4. Click Install

### Environment Variables

Set per-app environment variables for advanced tweaking:
- `DXVK_HUD=1` - Show DXVK performance overlay
- `WINE_LARGE_ADDRESS_AWARE=1` - Enable 4GB memory for 32-bit apps
- `WINEDEBUG=-all` - Disable Wine debug output

## Data Storage

- **Database**: `~/.local/share/winetranslator/winetranslator.db`
- **Prefixes**: `~/.local/share/winetranslator/prefixes/`
- **Logs**: Application output is captured per-launch (coming soon)

## Roadmap

### Phase 1: Core Functionality (Done)
- [x] Wine runner detection and management
- [x] Isolated prefix creation
- [x] Basic GTK4 interface
- [x] Application library
- [x] One-click launching
- [x] Automatic dependency detection

### Phase 2: Enhanced Features (In Progress)
- [ ] Preferences dialog
- [ ] Runner version switching per-app
- [ ] DXVK/VKD3D toggle switches
- [ ] Application log viewer
- [ ] Icon extraction from .exe files
- [ ] Desktop shortcut creation

### Phase 3: Power User Features (Future)
- [ ] Import from Steam/Lutris/Bottles
- [ ] Custom installer script support
- [ ] Wine debug log analysis
- [ ] Performance monitoring
- [ ] Backup/restore prefixes
- [ ] Cloud save sync

## Contributing

Contributions welcome! This is a young project focused on ease of use.

Areas needing help:
- UI/UX improvements
- Better dependency detection heuristics
- Icon themes and design
- Testing on different distros
- Documentation and tutorials

## Troubleshooting

### Wine not detected
```bash
# Install Wine
sudo apt install wine  # Debian/Ubuntu
sudo dnf install wine  # Fedora
sudo pacman -S wine    # Arch
```

### GTK4/Libadwaita not found
```bash
# Install GTK4 and Libadwaita
sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1  # Debian/Ubuntu
sudo dnf install gtk4 libadwaita              # Fedora
sudo pacman -S gtk4 libadwaita                # Arch
```

### Winetricks not working
```bash
# Install winetricks
sudo apt install winetricks  # Debian/Ubuntu
sudo dnf install winetricks  # Fedora
sudo pacman -S winetricks    # Arch
```

### Application won't launch
1. Check Wine is installed: `wine --version`
2. Check the executable path is correct
3. Try running from terminal: `WINEPREFIX=/path/to/prefix wine /path/to/app.exe`
4. Check Wine logs in the prefix directory

## Inspiration

WineTranslator is inspired by:
- **Bottles** - Modern UI and prefix isolation
- **Lutris** - Runner system and configuration hierarchy
- **Proton** - Automatic dependency handling for games

## License

GPL-3.0 - See LICENSE file for details

## Contact

- GitHub: https://github.com/winetranslator/winetranslator (placeholder)
- Issues: https://github.com/winetranslator/winetranslator/issues (placeholder)
