#!/bin/bash
# WineTranslator Installation Script
# Automatically detects your Linux distro and installs all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  WineTranslator Installation Script${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        DISTRO=$DISTRIB_ID
        VERSION=$DISTRIB_RELEASE
    else
        DISTRO="unknown"
        VERSION="unknown"
    fi

    # Convert to lowercase
    DISTRO=$(echo "$DISTRO" | tr '[:upper:]' '[:lower:]')
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root!"
        print_info "The script will ask for sudo password when needed."
        exit 1
    fi
}

# Install dependencies for Debian/Ubuntu
install_debian() {
    print_info "Detected Debian/Ubuntu-based system"
    print_info "Updating package lists..."

    sudo apt update

    print_info "Installing system dependencies..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-gi \
        python3-gi-cairo \
        gir1.2-gtk-4.0 \
        gir1.2-adw-1 \
        wine \
        winetricks

    print_success "Debian/Ubuntu dependencies installed successfully!"
}

# Install dependencies for Fedora
install_fedora() {
    print_info "Detected Fedora system"
    print_info "Installing system dependencies..."

    sudo dnf install -y \
        python3 \
        python3-pip \
        python3-gobject \
        gtk4 \
        libadwaita \
        wine \
        winetricks

    print_success "Fedora dependencies installed successfully!"
}

# Install dependencies for Arch Linux
install_arch() {
    print_info "Detected Arch Linux system"
    print_info "Installing system dependencies..."

    sudo pacman -S --needed --noconfirm \
        python \
        python-pip \
        python-gobject \
        gtk4 \
        libadwaita \
        wine \
        winetricks

    print_success "Arch Linux dependencies installed successfully!"
}

# Install dependencies for openSUSE
install_opensuse() {
    print_info "Detected openSUSE system"
    print_info "Installing system dependencies..."

    sudo zypper install -y \
        python3 \
        python3-pip \
        python3-gobject \
        gtk4 \
        libadwaita-1-0 \
        wine \
        winetricks

    print_success "openSUSE dependencies installed successfully!"
}

# Install Python package
install_python_package() {
    print_info "Installing WineTranslator Python package..."

    # Install in editable mode
    pip3 install --user -e .

    print_success "WineTranslator installed successfully!"
}

# Verify installations
verify_installation() {
    print_info "Verifying installation..."

    ERRORS=0

    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
    else
        print_error "Python 3 not found!"
        ERRORS=$((ERRORS + 1))
    fi

    # Check Wine
    if command -v wine &> /dev/null; then
        WINE_VERSION=$(wine --version)
        print_success "Wine found: $WINE_VERSION"
    else
        print_error "Wine not found!"
        ERRORS=$((ERRORS + 1))
    fi

    # Check winetricks
    if command -v winetricks &> /dev/null; then
        print_success "Winetricks found"
    else
        print_warning "Winetricks not found (optional but recommended)"
    fi

    # Check GTK4
    if python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
        print_success "GTK4 Python bindings found"
    else
        print_error "GTK4 Python bindings not found!"
        ERRORS=$((ERRORS + 1))
    fi

    # Check Libadwaita
    if python3 -c "import gi; gi.require_version('Adw', '1')" 2>/dev/null; then
        print_success "Libadwaita Python bindings found"
    else
        print_error "Libadwaita Python bindings not found!"
        ERRORS=$((ERRORS + 1))
    fi

    echo ""

    if [ $ERRORS -eq 0 ]; then
        print_success "All dependencies verified successfully!"
        return 0
    else
        print_error "Some dependencies are missing. Please install them manually."
        return 1
    fi
}

# Main installation function
main() {
    print_header

    check_root
    detect_distro

    print_info "Detected distribution: $DISTRO $VERSION"
    echo ""

    # Install based on distribution
    case "$DISTRO" in
        ubuntu|debian|linuxmint|pop)
            install_debian
            ;;
        fedora)
            install_fedora
            ;;
        arch|manjaro|endeavouros)
            install_arch
            ;;
        opensuse*|sles)
            install_opensuse
            ;;
        *)
            print_error "Unsupported distribution: $DISTRO"
            print_info "Please install dependencies manually:"
            echo ""
            echo "Required packages:"
            echo "  - Python 3.10+"
            echo "  - GTK4"
            echo "  - Libadwaita"
            echo "  - PyGObject (python3-gi)"
            echo "  - Wine"
            echo "  - Winetricks (optional)"
            echo ""
            exit 1
            ;;
    esac

    echo ""
    install_python_package
    echo ""

    if verify_installation; then
        echo ""
        print_header
        print_success "WineTranslator has been installed successfully!"
        echo ""
        print_info "To run WineTranslator, use one of these commands:"
        echo ""
        echo "  ./run.sh"
        echo "  winetranslator"
        echo "  python3 -m winetranslator"
        echo ""
        print_info "Note: You may need to add ~/.local/bin to your PATH:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        print_info "Add this line to your ~/.bashrc or ~/.zshrc to make it permanent."
        echo ""

        # Ask if user wants to run now
        read -p "Would you like to run WineTranslator now? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Launching WineTranslator..."
            ./run.sh
        fi
    else
        echo ""
        print_error "Installation completed with errors. Please check the messages above."
        exit 1
    fi
}

# Run main function
main
