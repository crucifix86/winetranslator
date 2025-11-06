#!/bin/bash
# Build AppImage for WineTranslator
# This creates a standalone, portable application that runs on any Linux distro

set -e

# Change to script directory
cd "$(dirname "$0")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  WineTranslator AppImage Builder${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
}

# Check dependencies
check_dependencies() {
    print_info "Checking build dependencies..."

    local missing=0

    if ! command -v python3 &> /dev/null; then
        print_error "python3 not found"
        missing=1
    fi

    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 not found"
        missing=1
    fi

    if [ $missing -eq 1 ]; then
        print_error "Missing required dependencies"
        exit 1
    fi

    print_success "All build dependencies found"
}

# Create AppDir structure
create_appdir() {
    print_info "Creating AppDir structure..."

    APP_DIR="WineTranslator.AppDir"

    # Clean old AppDir if exists
    rm -rf "$APP_DIR"

    # Create directory structure
    mkdir -p "$APP_DIR/usr/bin"
    mkdir -p "$APP_DIR/usr/lib"
    mkdir -p "$APP_DIR/usr/share/applications"
    mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$APP_DIR/usr/lib/python3/site-packages"

    print_success "AppDir structure created"
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies into AppDir..."

    # Note: PyGObject and pycairo come from system (can't bundle GTK4 easily)
    # We only need to bundle our application code

    print_success "Dependencies prepared (using system PyGObject/GTK4)"
}

# Copy application files
copy_app_files() {
    print_info "Copying application files..."

    # Copy the application package
    cp -r winetranslator "$APP_DIR/usr/lib/python3/site-packages/"

    # Create launcher script
    cat > "$APP_DIR/usr/bin/winetranslator" << 'EOF'
#!/bin/bash
# WineTranslator launcher script

APPDIR="${APPDIR:-$(dirname "$(dirname "$(readlink -f "$0")")")}"

export PYTHONPATH="$APPDIR/usr/lib/python3/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export GI_TYPELIB_PATH="$APPDIR/usr/lib/girepository-1.0:$GI_TYPELIB_PATH"

# Use system GTK4 and Libadwaita (can't be bundled easily)
exec python3 -m winetranslator "$@"
EOF

    chmod +x "$APP_DIR/usr/bin/winetranslator"

    print_success "Application files copied"
}

# Create desktop file
create_desktop_file() {
    print_info "Creating desktop integration files..."

    # Create desktop file
    cat > "$APP_DIR/winetranslator.desktop" << EOF
[Desktop Entry]
Type=Application
Name=WineTranslator
Comment=Run Windows applications on Linux with ease
Exec=winetranslator
Icon=winetranslator
Terminal=false
Categories=Game;Utility;
Keywords=wine;windows;emulator;compatibility;
EOF

    # Copy to share directory as well
    cp "$APP_DIR/winetranslator.desktop" "$APP_DIR/usr/share/applications/"

    # Create placeholder icon
    touch "$APP_DIR/winetranslator.png"

    print_success "Desktop files created"
}

# Create AppRun script
create_apprun() {
    print_info "Creating AppRun script..."

    cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/bash
# AppRun script for WineTranslator AppImage

APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")}"

# Export paths
export PYTHONPATH="$APPDIR/usr/lib/python3/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
export PATH="$APPDIR/usr/bin:$PATH"

# Detect distro
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

# Check and install dependencies
check_deps() {
    local missing=()

    # Check Wine
    if ! command -v wine &> /dev/null; then
        missing+=("wine")
    fi

    # Check winetricks
    if ! command -v winetricks &> /dev/null; then
        missing+=("winetricks")
    fi

    # Check GTK4
    if ! python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
        missing+=("gtk4")
    fi

    # Check Libadwaita
    if ! python3 -c "import gi; gi.require_version('Adw', '1')" 2>/dev/null; then
        missing+=("libadwaita")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        install_deps "${missing[@]}"
    fi
}

# Install missing dependencies
install_deps() {
    local distro=$(detect_distro)
    local deps=("$@")

    # Build package list based on distro
    case "$distro" in
        debian|ubuntu|linuxmint|pop)
            local pkgs="wine winetricks python3-gi gir1.2-gtk-4.0 gir1.2-adw-1"
            local install_cmd="apt install -y"
            ;;
        fedora)
            local pkgs="wine winetricks python3-gobject gtk4 libadwaita"
            local install_cmd="dnf install -y"
            ;;
        arch|manjaro)
            local pkgs="wine winetricks python-gobject gtk4 libadwaita"
            local install_cmd="pacman -S --noconfirm"
            ;;
        *)
            zenity --error --text="Unknown Linux distribution.\n\nPlease install manually:\n- Wine\n- Winetricks\n- GTK4\n- Libadwaita" --title="WineTranslator" 2>/dev/null
            exit 1
            ;;
    esac

    # Ask user permission
    if command -v zenity &> /dev/null; then
        zenity --question --text="WineTranslator needs to install dependencies:\n\n${pkgs}\n\nThis requires administrator permission. Continue?" --title="Install Dependencies" 2>/dev/null
        if [ $? -ne 0 ]; then
            exit 1
        fi
    fi

    # Try pkexec first, fall back to sudo
    if command -v pkexec &> /dev/null; then
        pkexec sh -c "$install_cmd $pkgs" 2>&1 | zenity --progress --pulsate --text="Installing dependencies..." --title="WineTranslator" --auto-close 2>/dev/null
    elif command -v sudo &> /dev/null; then
        x-terminal-emulator -e "sudo $install_cmd $pkgs" || xterm -e "sudo $install_cmd $pkgs" || sudo $install_cmd $pkgs
    else
        zenity --error --text="Cannot install dependencies automatically.\n\nPlease run:\nsudo $install_cmd $pkgs" --title="WineTranslator" 2>/dev/null
        exit 1
    fi
}

# Check dependencies on first run
check_deps

# Run the application
exec "$APPDIR/usr/bin/winetranslator" "$@"
EOF

    chmod +x "$APP_DIR/AppRun"

    print_success "AppRun script created"
}

# Download appimagetool if needed
get_appimagetool() {
    if [ -f "appimagetool-x86_64.AppImage" ]; then
        print_info "appimagetool already downloaded"
        return
    fi

    print_info "Downloading appimagetool..."

    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O appimagetool-x86_64.AppImage

    chmod +x appimagetool-x86_64.AppImage

    print_success "appimagetool downloaded"
}

# Build AppImage
build_appimage() {
    print_info "Building AppImage..."

    # Get appimagetool
    get_appimagetool

    # Build the AppImage
    ARCH=x86_64 ./appimagetool-x86_64.AppImage "$APP_DIR" WineTranslator-x86_64.AppImage

    print_success "AppImage built successfully!"
}

# Main build process
main() {
    print_header

    print_info "Starting WineTranslator AppImage build..."
    echo ""

    check_dependencies
    create_appdir
    install_dependencies
    copy_app_files
    create_desktop_file
    create_apprun
    build_appimage

    echo ""
    print_header
    print_success "WineTranslator AppImage created successfully!"
    echo ""
    echo "Output: WineTranslator-x86_64.AppImage"
    echo ""
    print_info "To run:"
    echo "  chmod +x WineTranslator-x86_64.AppImage"
    echo "  ./WineTranslator-x86_64.AppImage"
    echo ""
    print_info "To install system-wide:"
    echo "  mv WineTranslator-x86_64.AppImage ~/.local/bin/winetranslator"
    echo ""
    print_info "Note: Wine, GTK4, and Libadwaita must be installed on the system"
    echo "      (they cannot be bundled in the AppImage due to system integration)"
    echo ""
}

main "$@"
