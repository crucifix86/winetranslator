# WineTranslator AppImage

This document explains how to build and use the WineTranslator AppImage.

## What is an AppImage?

An AppImage is a portable, standalone application format for Linux that:
- **Runs anywhere** - Works on any Linux distribution
- **No installation required** - Just download and run
- **Self-contained** - Bundles most dependencies
- **Portable** - Can run from USB drive or any location

## Quick Start (Users)

### Download and Run

1. **Download** the AppImage:
   ```bash
   wget https://github.com/crucifix86/winetranslator/releases/latest/download/WineTranslator-x86_64.AppImage
   ```

2. **Make it executable**:
   ```bash
   chmod +x WineTranslator-x86_64.AppImage
   ```

3. **Run it**:
   ```bash
   ./WineTranslator-x86_64.AppImage
   ```

That's it! WineTranslator will run and check for system dependencies on first launch.

### System Requirements

The AppImage bundles Python and most dependencies, but you still need:

**Required:**
- **Wine** - The Windows compatibility layer
- **GTK4** - UI toolkit
- **Libadwaita** - Modern GNOME widgets

**Optional:**
- **Winetricks** - For automatic dependency installation

### Installing System Dependencies

**Debian/Ubuntu:**
```bash
sudo apt install wine winetricks gir1.2-gtk-4.0 gir1.2-adw-1
```

**Fedora:**
```bash
sudo dnf install wine winetricks gtk4 libadwaita
```

**Arch Linux:**
```bash
sudo pacman -S wine winetricks gtk4 libadwaita
```

**openSUSE:**
```bash
sudo zypper install wine winetricks gtk4 libadwaita-1-0
```

### First Run

On first run, WineTranslator will:
1. Check for required system dependencies
2. Show a helpful dialog if anything is missing
3. Provide install commands for your distribution
4. Let you continue anyway or quit to install dependencies

### Desktop Integration

To add WineTranslator to your application menu:

```bash
# Move AppImage to a permanent location
mv WineTranslator-x86_64.AppImage ~/.local/bin/

# The AppImage will automatically integrate with your desktop
```

Or manually:
```bash
# Extract the desktop file
./WineTranslator-x86_64.AppImage --appimage-extract

# Copy to applications
cp squashfs-root/winetranslator.desktop ~/.local/share/applications/
```

---

## Building the AppImage (Developers)

### Prerequisites

**Build Dependencies:**
- Python 3.10+
- pip3
- wget (for downloading appimagetool)

**Note:** You don't need GTK4/Libadwaita to *build* the AppImage, only to *run* it.

### Build Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/crucifix86/winetranslator.git
   cd winetranslator
   ```

2. **Run the build script**:
   ```bash
   ./build-appimage.sh
   ```

The script will:
- Create the AppDir structure
- Install Python dependencies
- Copy application files
- Create the AppRun launcher
- Download appimagetool
- Build the final AppImage

3. **Output**:
   ```
   WineTranslator-x86_64.AppImage
   ```

### Build Script Details

The `build-appimage.sh` script:

1. **Creates AppDir structure** - Standard AppImage directory layout
2. **Installs dependencies** - Uses pip to install into AppDir
3. **Bundles the application** - Copies winetranslator package
4. **Creates launchers** - AppRun and startup scripts
5. **Desktop integration** - .desktop file and icon
6. **Builds AppImage** - Uses appimagetool to create final .AppImage

### What's Bundled vs System

**Bundled in AppImage:**
- ✅ Python packages (PyGObject, pycairo, etc.)
- ✅ WineTranslator application code
- ✅ Python standard library

**Uses System Libraries:**
- 📦 Wine (system-dependent, can't bundle)
- 📦 GTK4 (too complex to bundle)
- 📦 Libadwaita (depends on GTK4)
- 📦 System Python 3 (for compatibility)

This hybrid approach ensures:
- AppImage works across distributions
- Wine integration works correctly
- UI matches system theme
- File size stays reasonable

### Testing the AppImage

After building:

```bash
# Run directly
./WineTranslator-x86_64.AppImage

# Test on a different distro (Docker)
docker run -it --rm -v $(pwd):/app ubuntu:22.04 bash
apt update && apt install wine gir1.2-gtk-4.0 gir1.2-adw-1
/app/WineTranslator-x86_64.AppImage

# Extract and inspect contents
./WineTranslator-x86_64.AppImage --appimage-extract
ls squashfs-root/
```

### Troubleshooting Build Issues

**Issue: "pip3 not found"**
```bash
sudo apt install python3-pip  # Debian/Ubuntu
sudo dnf install python3-pip  # Fedora
```

**Issue: "appimagetool download fails"**
```bash
# Manually download
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

**Issue: "AppImage won't run"**
- Ensure FUSE is installed: `sudo apt install fuse`
- Check file is executable: `chmod +x WineTranslator-x86_64.AppImage`
- Try extracting: `./WineTranslator-x86_64.AppImage --appimage-extract`

---

## AppImage Features

### Automatic Dependency Checking

The AppImage includes smart first-run checks:
- Detects missing Wine, GTK4, Libadwaita
- Shows distribution-specific install commands
- Lets users continue anyway or quit to install

### Update Support

The AppImage includes the same update feature as the regular installation:
- Menu → Check for Updates
- Pulls from GitHub
- Reinstalls package inside AppImage

**Note:** Updates modify the AppImage contents, which may require re-running after update.

### Portable Mode

The AppImage creates user data in:
```
~/.local/share/winetranslator/
  ├── winetranslator.db     # Application database
  └── prefixes/             # Wine prefixes
```

To use truly portable mode:
```bash
export APPDATA=/path/to/usb/winetranslator-data
./WineTranslator-x86_64.AppImage
```

---

## Distribution

### GitHub Releases

Upload to GitHub releases:

```bash
# Tag a release
git tag v0.1.0
git push origin v0.1.0

# Upload AppImage to release
gh release create v0.1.0 WineTranslator-x86_64.AppImage \
  --title "WineTranslator v0.1.0" \
  --notes "Initial AppImage release"
```

### AppImageHub

To list on [AppImageHub](https://appimage.github.io/):

1. Fork https://github.com/AppImage/appimage.github.io
2. Add entry to `database.yml`
3. Submit pull request

### Direct Download

Host the AppImage on your own server:
```bash
# Users download with:
wget https://your-server.com/WineTranslator-x86_64.AppImage
chmod +x WineTranslator-x86_64.AppImage
./WineTranslator-x86_64.AppImage
```

---

## Advantages of AppImage

**For Users:**
- ✅ No installation required
- ✅ Works on any Linux distro
- ✅ No system pollution
- ✅ Easy to remove (just delete file)
- ✅ Can run from USB drive

**For Developers:**
- ✅ Single build for all distros
- ✅ No packaging for each distro
- ✅ Users always get latest version
- ✅ Easier testing across distros

**For WineTranslator:**
- ✅ Faster to get started
- ✅ No complex installation
- ✅ Self-contained dependencies
- ✅ Perfect for testing

---

## Alternative: Flatpak

If you need even better sandboxing and system integration, consider using Flatpak instead:
- Better GTK4/Libadwaita bundling
- Automatic updates through Flathub
- Better desktop integration
- Full sandboxing

See `FLATPAK.md` (coming soon) for Flatpak build instructions.

---

## FAQ

**Q: Can I bundle Wine in the AppImage?**
A: No, Wine is too system-dependent and requires kernel-level integration.

**Q: Why does it need system GTK4?**
A: GTK4 is complex to bundle and should match the system theme for best UX.

**Q: How big is the AppImage?**
A: Approximately 20-30MB (Python + dependencies, without Wine/GTK4).

**Q: Does it work offline?**
A: Yes, once downloaded. Updates require internet.

**Q: Can I use this in production?**
A: Yes! AppImages are production-ready. Many popular apps use them.

**Q: How do I uninstall?**
A: Just delete the .AppImage file and `~/.local/share/winetranslator/`

---

## Support

For AppImage-specific issues:
- Check Wine is installed: `wine --version`
- Check GTK4 is installed: `pkg-config --modversion gtk4`
- Run with debug: `./WineTranslator-x86_64.AppImage --verbose`
- Extract and inspect: `./WineTranslator-x86_64.AppImage --appimage-extract`

For general WineTranslator issues:
- GitHub Issues: https://github.com/crucifix86/winetranslator/issues
- Check logs: `~/.local/share/winetranslator/`
