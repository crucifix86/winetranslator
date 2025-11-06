# Installation Guide for WineTranslator

## Automatic Installation (Recommended)

The easiest way to install WineTranslator is using our automatic installation script:

```bash
cd /media/doug/stuff/winetranslator
./install.sh
```

The script will:
- Detect your Linux distribution automatically
- Install all required system dependencies
- Install WineTranslator Python package
- Verify the installation
- Offer to launch WineTranslator immediately

**Supported distributions:**
- Debian/Ubuntu/Linux Mint/Pop!_OS
- Fedora
- Arch Linux/Manjaro/EndeavourOS
- openSUSE

If you prefer manual installation or your distro isn't supported, see below.

---

## Quick Manual Install (Debian/Ubuntu)

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-gi python3-gi-cairo \
                 gir1.2-gtk-4.0 gir1.2-adw-1 wine winetricks

# 2. Navigate to WineTranslator directory
cd /media/doug/stuff/winetranslator

# 3. Install Python dependencies
pip3 install -e .

# 4. Run WineTranslator
./run.sh
# or
winetranslator
```

---

## Detailed Manual Installation

### Step 1: Install System Dependencies

#### Debian 12+ / Ubuntu 23.04+

```bash
sudo apt update
sudo apt install \
    python3 \
    python3-pip \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-adw-1 \
    wine \
    winetricks
```

#### Fedora 38+

```bash
sudo dnf install \
    python3 \
    python3-gobject \
    gtk4 \
    libadwaita \
    wine \
    winetricks
```

#### Arch Linux

```bash
sudo pacman -S \
    python \
    python-gobject \
    gtk4 \
    libadwaita \
    wine \
    winetricks
```

### Step 2: Install WineTranslator

#### Option A: Install with pip (Recommended)

```bash
cd /media/doug/stuff/winetranslator
pip3 install -e .
```

This installs WineTranslator in "editable" mode, so you can modify the code and see changes immediately.

#### Option B: Run without installation

```bash
cd /media/doug/stuff/winetranslator
./run.sh
```

### Step 3: Verify Installation

```bash
# Check Wine is installed
wine --version

# Check winetricks is installed
winetricks --version

# Check Python version (needs 3.10+)
python3 --version

# Test WineTranslator
python3 -m winetranslator
```

## Troubleshooting

### GTK4 or Libadwaita Not Found

If you get an error about GTK4 or Libadwaita:

**Debian/Ubuntu:**
```bash
sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1
```

**Fedora:**
```bash
sudo dnf install gtk4 libadwaita
```

**Arch:**
```bash
sudo pacman -S gtk4 libadwaita
```

### PyGObject Not Found

```bash
# Debian/Ubuntu
sudo apt install python3-gi python3-gi-cairo

# Fedora
sudo dnf install python3-gobject

# Arch
sudo pacman -S python-gobject
```

### Wine Not Found

```bash
# Debian/Ubuntu
sudo apt install wine

# Fedora
sudo dnf install wine

# Arch
sudo pacman -S wine
```

For better compatibility, consider installing Wine Staging:

```bash
# Debian/Ubuntu
sudo dpkg --add-architecture i386
wget -nc https://dl.winehq.org/wine-builds/winehq.key
sudo apt-key add winehq.key
sudo add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ focal main'
sudo apt update
sudo apt install --install-recommends wine-staging
```

### Older Distros (Ubuntu 22.04, Debian 11, etc.)

If your distro doesn't have GTK4 or Libadwaita in the default repos:

1. **Upgrade your distro** (recommended)
2. **Use Flatpak version** (future)
3. **Build GTK4 from source** (advanced)

## Running WineTranslator

After installation, you can run WineTranslator in several ways:

```bash
# Method 1: Direct command (if installed with pip)
winetranslator

# Method 2: Python module
python3 -m winetranslator

# Method 3: Run script
cd /media/doug/stuff/winetranslator
./run.sh
```

## First Run

On first run, WineTranslator will:

1. **Create database** at `~/.local/share/winetranslator/winetranslator.db`
2. **Scan for Wine** installations on your system
3. **Set default runner** (system Wine or first found)
4. **Create prefixes directory** at `~/.local/share/winetranslator/prefixes/`

If no Wine installation is found, you'll see an error. Install Wine and restart WineTranslator.

## Optional: Desktop Integration

To add WineTranslator to your application menu:

```bash
# Copy desktop file
mkdir -p ~/.local/share/applications
cp /media/doug/stuff/winetranslator/winetranslator.desktop ~/.local/share/applications/

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

## Uninstallation

```bash
# If installed with pip
pip3 uninstall winetranslator

# Remove data (optional)
rm -rf ~/.local/share/winetranslator

# Remove desktop file (if installed)
rm ~/.local/share/applications/winetranslator.desktop
```

## Development Setup

For contributors:

```bash
# Clone repository
cd /media/doug/stuff/winetranslator

# Install in development mode
pip3 install -e .

# Install development dependencies (coming soon)
pip3 install -r requirements-dev.txt

# Run directly
python3 -m winetranslator
```

## Next Steps

After installation:

1. Read the [README.md](README.md) for usage instructions
2. Check the [RESEARCH.md](RESEARCH.md) for architecture details
3. Add your first Windows application!

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Check Wine works: `wine notepad`
4. Report issues at GitHub (placeholder)
