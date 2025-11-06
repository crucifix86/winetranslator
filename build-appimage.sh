#!/bin/bash
# Build AppImage for WineTranslator
# This creates a standalone, portable application that runs on any Linux distro

set -e

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

    # Install winetranslator and dependencies
    pip3 install --target="$APP_DIR/usr/lib/python3/site-packages" \
        PyGObject \
        pycairo \
        .

    print_success "Dependencies installed"
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

    # Create a simple icon (using system icon for now)
    # In production, you'd want a custom icon
    if [ -f "/usr/share/icons/hicolor/256x256/apps/application-x-executable.png" ]; then
        cp "/usr/share/icons/hicolor/256x256/apps/application-x-executable.png" \
           "$APP_DIR/winetranslator.png"
    else
        # Create a placeholder icon
        print_info "Creating placeholder icon..."
        # This would need imagemagick, skip for now
    fi

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

# Check for Wine on first run
if ! command -v wine &> /dev/null; then
    zenity --error --text="Wine is not installed!\n\nPlease install Wine:\n\nDebian/Ubuntu: sudo apt install wine\nFedora: sudo dnf install wine\nArch: sudo pacman -S wine" --title="WineTranslator - Wine Required" 2>/dev/null || \
    echo "ERROR: Wine is not installed. Please install Wine to use WineTranslator." >&2
    exit 1
fi

# Check for GTK4 and Libadwaita
if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')" 2>/dev/null; then
    zenity --error --text="GTK4 or Libadwaita not found!\n\nPlease install:\n\nDebian/Ubuntu: sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1\nFedora: sudo dnf install gtk4 libadwaita\nArch: sudo pacman -S gtk4 libadwaita" --title="WineTranslator - Dependencies Required" 2>/dev/null || \
    echo "ERROR: GTK4 or Libadwaita not found. Please install them to use WineTranslator." >&2
    exit 1
fi

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
