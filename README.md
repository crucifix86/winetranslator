# WineTranslator

A simple, easy-to-use Wine GUI for running Windows applications on Linux with automatic dependency management.

## Features

- **Beautiful dark theme** - Modern gradient UI with smooth animations and hover effects
- **Easy-to-use GTK4 interface** - Native Linux design using Libadwaita
- **Tested Apps Library** - Curated list of Windows apps known to work perfectly with Wine
- **Desktop shortcuts** - Create shortcuts on your Desktop for quick access
- **Context menu** - Right-click apps for quick actions (open directory, edit arguments, etc.)
- **Launch arguments** - Add command-line arguments per-app (like -console, -windowed, -fullscreen)
- **Wine C: drive access** - Quick button to open the Wine prefix drive_c folder
- **Audio support** - Automatic audio configuration (PulseAudio/PipeWire/ALSA detection)
- **Memory management** - Large Address Aware setting for big game installers (FitGirl repacks)
- **Smart removal** - Choose to keep files or delete them when removing apps
- **Custom storage location** - Store Wine prefixes on any drive (perfect for multi-drive setups)
- **Isolated Wine prefixes** - Each application gets its own clean environment
- **Multiple Wine versions** - Support for Wine, Wine-Staging, Proton, and custom builds
- **Automatic dependency detection** - Detects Unity, Unreal, .NET, XNA games and apps
- **Winetricks integration** - Auto-installs VC++ runtimes, DirectX, fonts, and more
- **Dependency caching** - Download dependencies once, reuse across all apps (optional)
- **Per-app error logging** - Each app gets its own log file for troubleshooting
- **Dependency profiles** - Tracks what dependencies each app needs for future reference
- **One-click launching** - Simple application library with launch statistics
- **Smart runner detection** - Automatically finds Wine installations on your system
- **Built-in updater** - Update WineTranslator from within the app
- **GitHub-powered tested apps** - Tested apps list updates automatically from GitHub

## Why WineTranslator?

Unlike other Wine tools, WineTranslator focuses on **ease of use**:

- **No manual winetricks needed** - Dependencies are detected and installed automatically
- **Isolated environments** - Applications never conflict with each other
- **Simple setup** - Add an app in 3 clicks: choose .exe → name it → done
- **Beginner-friendly** - No need to understand Wine prefixes, WINEPREFIX, or environment variables

## Installation

### AppImage (Easiest - Recommended for Most Users)

**Download and run** - no installation needed!

```bash
# Download the AppImage
wget https://github.com/crucifix86/winetranslator/releases/latest/download/WineTranslator-x86_64.AppImage

# Make it executable
chmod +x WineTranslator-x86_64.AppImage

# Run it!
./WineTranslator-x86_64.AppImage
```

The AppImage is **portable** and works on any Linux distribution. On first run, it will check for required system dependencies (Wine, GTK4, Libadwaita) and show install instructions if needed.

📖 **See [APPIMAGE.md](APPIMAGE.md) for detailed AppImage documentation**

---

### Automatic Installation (For Developers)

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

### Manual Installation (Advanced)

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

2. **Easy Way: Install from Tested Apps**
   - Click the **Tested Apps** tab
   - Browse verified Windows applications
   - Click **Download & Install** on any app (e.g., WinSCP)
   - Wait for automatic download and installation
   - App appears in your Library - ready to launch!

3. **Manual Way: Add your own application**
   - Click the **+** button in the header
   - Select your Windows .exe file
   - Give it a name
   - Choose or create a Wine prefix
   - Click **Add Application**

4. **Automatic magic happens**
   - WineTranslator detects if your app needs DirectX, .NET, VC++ runtimes, etc.
   - Dependencies are installed automatically in the background
   - Your app is ready to run!

5. **Launch your app**
   - Go to **Library** tab
   - Click the application card
   - Click **Launch**

## Key Features Explained

### Beautiful Dark Theme

WineTranslator features a modern dark theme with:
- Gradient backgrounds on app cards
- Smooth hover animations that lift cards
- Blue glowing buttons for suggested actions
- Custom styled scrollbars and UI elements
- Professional Libadwaita design language

Everything is designed to look native to modern Linux desktops!

### Desktop Shortcuts

Create desktop shortcuts for your Windows apps:

1. Click on any installed app in the Library tab
2. Click **"Create Desktop Shortcut"**
3. A shortcut icon will appear on your Desktop
4. Double-click the icon to launch your app!

Shortcuts use the `winetranslator-launch` command and work perfectly with your desktop environment.

### Context Menu (Right-Click)

**Right-click any app card** in the Library tab to open a context menu with quick actions:

**Available actions:**
- **Open Install Directory** - Opens the app's installation folder in your file manager
- **Edit Launch Arguments** - Add command-line arguments (like `-console`, `-windowed`, `-fullscreen`)

Perfect for:
- Modifying configuration files
- Adding mods or DLCs
- Setting game launch options
- Quick file access

### Launch Arguments

Add command-line arguments to your apps for advanced configuration:

1. Right-click any app in Library
2. Select **"Edit Launch Arguments"**
3. Enter arguments like: `-console -windowed -fullscreen`
4. Click **Save**
5. Arguments are automatically applied when launching

Common examples:
- `-console` - Enable developer console
- `-windowed` - Run in windowed mode
- `-fullscreen` - Force fullscreen
- `-skipintro` - Skip intro videos

### Wine C: Drive Access

Quick access to Wine prefix files:

1. Click on any app in Library
2. Click **"Open Wine C: Drive"**
3. Browse the Windows C: drive (drive_c folder)

Perfect for finding game files, save locations, or manually installing mods.

### Smart Removal

When removing apps from your library, WineTranslator gives you control over what happens to the files:

1. Click **Remove** on any app
2. Choose from three options:
   - **Cancel** - Don't remove anything
   - **Remove from Library Only** - Keep all files, just remove from WineTranslator
   - **Remove and Delete Files** - Permanently delete the app's directory

**Use cases:**
- **Installers**: Remove the installer from library but keep files to run actual setup later
- **Portable apps**: Keep files when testing different Wine versions
- **Cleanup**: Delete everything when uninstalling completely

The delete option includes double confirmation to prevent accidents.

### Wine Memory Settings

Fix memory-related crashes in large game installers:

**Large Address Aware** (enabled by default):
- Allows 32-bit Wine apps to use up to 4GB of memory
- Fixes crashes in compressed game installers (FitGirl repacks, etc.)
- Sets `WINE_LARGE_ADDRESS_AWARE=1` environment variable

**Why this matters:**
Wine has virtual memory limits separate from your physical RAM. Even with 64GB of system RAM, Wine's default 32-bit process limit is much lower. Large installers that decompress huge archives can hit this limit and crash with "out of memory" errors.

Enable/disable in: **Menu → Preferences → Wine Memory Settings**

### Container Apps (Manual Installation)

Some apps don't have direct download links or come as portable/extracted archives. Container apps solve this:

**What are containers?**
- Pre-configured Wine prefixes with dependencies installed
- A dedicated folder where you place the app files manually
- Perfect for portable apps, GOG installers, or extracted archives

**How to use:**
1. Go to **Tested Apps** tab
2. Find a container app (shows "Setup Container" button)
3. Click **"Setup Container"**
4. Wine prefix and dependencies are installed automatically
5. A folder opens - place your app files there
6. Use the **+** button to add the .exe to your library
7. Right-click the container card to reopen the folder anytime

### Tested Apps Library

Pre-tested Windows applications known to work perfectly:
- **Fetches from GitHub** - Always up-to-date list
- **One-click install** - Downloads and installs automatically
- **Automatic .exe detection** - Finds the real app after installation
- **Pre-configured dependencies** - Everything set up for you
- **Two types**: Download (automatic) and Container (manual)

Add more apps by editing `tested_apps.json` on GitHub!

## Preferences

Access via Menu → Preferences

### Dependency Caching

Enable dependency caching to speed up installations and save bandwidth:

1. Open Preferences
2. Toggle **"Enable Dependency Caching"** ON
3. Click **"Choose Folder..."** to select cache location (default: `~/.local/share/winetranslator/dep_cache/`)
4. Dependencies will now be downloaded once and reused across all apps

Benefits:
- Faster app installations
- Reduced bandwidth usage
- Can backup/share cache folder
- Eventually host cache for easy distribution

### Wine Memory Settings

Configure Wine's memory limits for applications:

**Large Address Aware** (enabled by default):
- Toggle ON to allow 32-bit apps to use up to 4GB of memory
- Fixes "out of memory" crashes in large game installers (FitGirl repacks, DODI repacks, etc.)
- Automatically sets `WINE_LARGE_ADDRESS_AWARE=1` environment variable for all apps

This setting is especially important for:
- Compressed game installers that need memory for decompression
- Large setup.exe files (over 10GB)
- Games with high-resolution texture packs
- Modded applications with memory-intensive operations

**Note**: This is a Wine virtual memory limit, not your physical RAM. Even with plenty of system RAM, Wine's 32-bit processes have default memory limits that can cause crashes.

### Storage Location

Choose where Wine prefixes are stored - perfect for multi-drive setups:

1. Open Preferences
2. Scroll to **"Storage Location"**
3. Click **"Choose Folder..."**
4. Select a directory on your preferred drive
5. All new prefixes will be stored there

**Use cases:**
- **Multiple drives**: Store large games on bigger secondary drive (e.g., 500GB main + 2TB secondary)
- **Fast storage**: Put prefixes on SSD for better performance
- **Backups**: Easier to backup when all prefixes are in one custom location
- **Network storage**: Store prefixes on NAS (with good network speed)

**Important notes:**
- Only affects **new** Wine prefixes - existing prefixes stay where they are
- Default location: `~/.local/share/winetranslator/prefixes/`
- Make sure the drive has enough space for large game installations (50GB+ for AAA games)

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
├── core/                      # Business logic
│   ├── runner_manager.py      # Wine version management
│   ├── prefix_manager.py      # Isolated prefix creation
│   ├── app_launcher.py        # Application execution
│   ├── dependency_manager.py  # Winetricks integration
│   └── updater.py            # Built-in update system
├── gui/                       # GTK4 interface
│   ├── main_window.py         # Application library with tabs
│   ├── add_app_dialog.py      # Setup wizard
│   ├── tested_apps_view.py    # Tested apps browser
│   └── preferences_dialog.py  # Settings
├── database/                  # SQLite storage
│   └── db.py                 # Schema and queries
├── data/                      # Application data
│   └── tested_apps.py        # Curated app database
└── utils/                     # Utilities
    ├── wine_utils.py         # Wine detection and execution
    └── logger.py             # Logging setup
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
- **App Logs**: `~/.local/share/winetranslator/app_logs/` - Per-app Wine output logs
- **Main Log**: `~/.local/share/winetranslator/winetranslator.log` - Application debug log
- **Dependency Cache**: `~/.local/share/winetranslator/dep_cache/` - Cached winetricks downloads (if enabled)

## Roadmap

### Phase 1: Core Functionality ✅ DONE
- [x] Wine runner detection and management
- [x] Isolated prefix creation
- [x] Basic GTK4 interface
- [x] Application library
- [x] One-click launching
- [x] Automatic dependency detection

### Phase 2: Enhanced Features ✅ DONE
- [x] Beautiful dark theme with gradients and animations
- [x] Preferences dialog
- [x] Dependency caching system
- [x] Per-app error logging
- [x] Dependency profile tracking
- [x] Tested Apps library (GitHub-powered)
- [x] Built-in update system
- [x] Desktop shortcut creation
- [x] Right-click to open app directories
- [x] Container apps for manual installation
- [x] Automatic .exe detection after installation
- [ ] Runner version switching per-app
- [ ] DXVK/VKD3D toggle switches
- [ ] Application log viewer UI

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
3. **Check the app's log file**: `tail -f ~/.local/share/winetranslator/app_logs/YourAppName.log`
4. **Check the main log**: `tail -f ~/.local/share/winetranslator/winetranslator.log`
5. Try running from terminal: `WINEPREFIX=/path/to/prefix wine /path/to/app.exe`

### Debugging Tips

**Per-App Logs:**
Every app launch creates a log file in `~/.local/share/winetranslator/app_logs/` with Wine's output. This helps debug crashes and errors.

```bash
# Watch an app's log in real-time
tail -f ~/.local/share/winetranslator/app_logs/WinSCP-6.5.4-Setup.log

# Find errors in app logs
grep -i error ~/.local/share/winetranslator/app_logs/*.log
```

**Main Application Log:**
WineTranslator's own debug log shows what's happening behind the scenes:

```bash
# Watch the main log
tail -f ~/.local/share/winetranslator/winetranslator.log

# Find warnings
grep -i warning ~/.local/share/winetranslator/winetranslator.log
```

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
