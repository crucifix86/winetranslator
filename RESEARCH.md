# Wine GUI Research - WineTranslator Project

## Overview of Existing Tools

This document summarizes research on existing Wine GUI tools to inform the design of WineTranslator.

---

## 1. Proton (Valve)

**Repository**: https://github.com/ValveSoftware/Proton
**License**: Open Source
**Language**: C/C++ (Wine-based), Python scripts

### Architecture

- **Foundation**: Modified Wine with gaming-specific patches
- **Graphics Stack**:
  - DXVK: Direct3D 10/11 to Vulkan translation
  - vkd3d-proton: Direct3D 12 to Vulkan translation
  - Optional wined3d: DirectX to OpenGL fallback
- **Steam Integration**: `lsteamclient` bridges Windows Steam API to Linux client
- **Build System**: Docker/Podman-based containerized builds, Makefile-driven

### Key Features

- Extensive per-game configuration via environment variables
- `user_settings.py` for runtime tuning without modifying Wine prefix
- Modular component rebuilding (can rebuild DXVK, vkd3d independently)
- Debug builds with symbol preservation

### Takeaways

- Modular graphics stack is critical for gaming
- Per-application configuration without prefix pollution is valuable
- Containerized builds ensure reproducibility
- Environment variable tuning provides flexibility

---

## 2. Lutris

**Repository**: https://github.com/lutris/lutris
**License**: GPL-3.0
**Language**: 99.7% Python

### Architecture

- **Runner System**: Abstraction layer for Wine, emulators, engines
- **Prefix Management**:
  - Runners stored in `~/.local/share/lutris/runners/*`
  - Per-runner YAML configurations (`runners/*.yml`)
- **Database**: SQLite (`pga.db`) tracks installations and runner versions
- **Configuration Hierarchy**: Game settings → Runner settings → System defaults

### Key Features

- Unified interface for multiple runners (not just Wine)
- Automatic runner download and management via CLI
- Direct execution from source (`./bin/lutris`) for development
- Community-driven with 11,000+ commits across 359 contributors

### Takeaways

- **Runner abstraction** is powerful - supports Wine versions, Proton, custom builds
- Hierarchical configuration prevents duplication
- SQLite database for state management is lightweight and effective
- Python enables rapid development and community contributions

---

## 3. Bottles

**Repository**: https://github.com/bottlesdevs/Bottles
**License**: GPL-3.0
**Language**: 98.4% Python, GTK4

### Architecture

- **GUI Framework**: GTK4 + Libadwaita (modern GNOME design)
- **Distribution**: Flatpak containerization
- **Prefix Isolation**: Each "bottle" is an isolated Wine prefix
- **Runner Management**: Multiple Wine/Proton versions supported

### Key Features

- Modern, accessible UI following GNOME HIG
- Flatpak distribution ensures cross-distro compatibility
- Isolated environments prevent configuration conflicts
- Strong internationalization (extensive translations)

### Development Infrastructure

- Meson build system
- Pre-commit hooks for code quality
- mypy type checking
- Comprehensive contribution guidelines

### Takeaways

- **GTK4 provides modern, native Linux UI**
- Flatpak simplifies distribution and dependency management
- Type checking improves code quality
- Accessibility and i18n should be first-class concerns

---

## Comparison Matrix

| Feature | Proton | Lutris | Bottles |
|---------|--------|--------|---------|
| **Target** | Steam games | All games/emulators | Wine applications |
| **UI** | None (Steam integrated) | GTK3 | GTK4+Libadwaita |
| **Language** | C/C++/Python | Python | Python |
| **Prefix Management** | Steam-managed | Runner-based | Bottle-based |
| **Configuration** | Environment vars | YAML hierarchy | GUI-driven |
| **Graphics** | DXVK/vkd3d built-in | Runner-dependent | Runner-dependent |
| **Distribution** | Steam bundled | Native packages | Flatpak |

---

## Recommendations for WineTranslator

### Architecture Decisions

1. **Language**: Python for rapid development, easy maintenance
2. **GUI Framework**: GTK4 + Libadwaita for modern, native Linux experience
3. **Prefix Management**: Isolated prefixes per application (like Bottles)
4. **Runner System**: Support multiple Wine versions (like Lutris)
5. **Database**: SQLite for configuration and application tracking
6. **Configuration**: Hierarchical (global → runner → app) with GUI overrides

### Core Components

```
winetranslator/
├── core/
│   ├── prefix_manager.py    # Wine prefix creation/management
│   ├── runner_manager.py    # Wine version downloads/management
│   ├── app_launcher.py      # Application execution with env setup
│   └── config_manager.py    # Hierarchical configuration
├── gui/
│   ├── main_window.py       # GTK4 main interface
│   ├── app_config_dialog.py # Per-app settings
│   └── prefix_dialog.py     # Prefix management UI
├── database/
│   └── db.py                # SQLite schema and queries
└── utils/
    ├── wine_utils.py        # Wine detection, version checks
    └── env_builder.py       # Environment variable setup
```

### Feature Priorities

**Phase 1: Core Functionality**
- Wine version detection and management
- Prefix creation and isolation
- Basic application launching
- Simple GTK4 interface

**Phase 2: Enhanced Features**
- Multiple Wine runner support (Wine, Wine-GE, Proton)
- Per-app configuration (DLLs, environment variables)
- DXVK/VKD3D integration toggles
- Application library management

**Phase 3: Advanced Features**
- Winetricks integration
- Custom installer scripts
- Import from Steam/Lutris/Bottles
- Performance monitoring
- Per-app Wine log viewing

### Design Philosophy

- **Simplicity First**: Focus on common use cases, make simple tasks easy
- **Power User Options**: Advanced settings available but not required
- **Isolation**: Prevent application conflicts through prefix separation
- **Transparency**: Show Wine commands being executed, allow debugging
- **Native Integration**: Follow Linux desktop conventions (GTK, Flatpak, XDG dirs)

---

## Next Steps

1. Design database schema for apps, prefixes, runners
2. Implement basic prefix manager
3. Create GTK4 skeleton interface
4. Implement Wine runner detection
5. Build basic app launcher with environment setup
