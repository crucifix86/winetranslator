# WineTranslator Development Guide

## Project Overview

**Repository**: https://github.com/crucifix86/winetranslator
**Language**: Python 3.10+
**UI Framework**: GTK4 + Libadwaita
**Distribution**: AppImage (portable)
**Update System**: Git-based auto-update from GitHub

---

## Development Workflow

### 1. Making Changes

Edit files in `/media/doug/stuff/winetranslator/`:

```bash
cd /media/doug/stuff/winetranslator

# Edit source files
nano winetranslator/gui/main_window.py
nano winetranslator/core/runner_manager.py
# etc...
```

### 2. Testing Changes Locally

**Option A: Run directly (fastest for testing)**
```bash
python3 -m winetranslator
```

**Option B: Install in development mode**
```bash
pip3 install --user -e .
winetranslator
```

### 3. Committing Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "Fix: description of what you fixed"

# Push to GitHub
git push origin main
```

### 4. Building the AppImage

**Build script**: `./build-appimage.sh`

```bash
cd /media/doug/stuff/winetranslator

# Clean old build
rm -rf WineTranslator.AppDir WineTranslator-x86_64.AppImage

# Build new AppImage
./build-appimage.sh

# Output: WineTranslator-x86_64.AppImage (portable app)
```

**What the build does:**
1. Creates `WineTranslator.AppDir/` structure
2. Copies Python code into AppDir
3. Creates launcher scripts (AppRun, winetranslator)
4. Generates desktop integration files
5. Uses `appimagetool` to package into `.AppImage`

**Build artifacts:**
- `WineTranslator-x86_64.AppImage` - The distributable app
- `WineTranslator.AppDir/` - Build directory (not needed after)
- `appimagetool-x86_64.AppImage` - Build tool (auto-downloaded)

### 5. Testing the AppImage

```bash
# Run the AppImage
./WineTranslator-x86_64.AppImage

# Check logs
tail -f ~/.local/share/winetranslator/winetranslator.log
```

---

## Update System

### How Updates Work

WineTranslator has a built-in updater that pulls from GitHub:

**User side:**
1. User clicks **Menu → Check for Updates**
2. App checks GitHub for new commits
3. Shows "Update available (X commits behind)"
4. User clicks **Update**
5. App runs `git pull origin main`
6. App runs `pip3 install --user --break-system-packages -e .`
7. User clicks **Restart Now**
8. App relaunches with new code

**Code location**: `winetranslator/core/updater.py`

### Testing the Update System

**Setup for testing:**

```bash
# 1. Pull latest from GitHub
git pull origin main

# 2. Make a small change
echo "# Test change" >> README.md
git add README.md
git commit -m "Test update system"
git push origin main

# 3. Reset local repo to previous commit
git reset --hard HEAD~1

# 4. Rebuild AppImage (so it has the updater code)
./build-appimage.sh

# 5. Run AppImage and test update
./WineTranslator-x86_64.AppImage
# Click Menu → Check for Updates
# Should show 1 commit behind
# Click Update → should pull the test change
```

### Update Flow Diagram

```
Local Repo (commit A)  →  GitHub (commit B)
        ↓
User clicks "Check for Updates"
        ↓
git fetch origin
        ↓
Compare: local vs origin/main
        ↓
"Update available (1 commits behind)"
        ↓
User clicks "Update"
        ↓
git pull origin main
        ↓
pip3 install --user --break-system-packages -e .
        ↓
"Update successful! Restart now?"
        ↓
User clicks "Restart Now"
        ↓
os.execv() → Relaunches app with new code
```

---

## GitHub Workflow

### Current Setup

**Repository**: crucifix86/winetranslator
**Branch**: main (default)
**Auth**: GitHub CLI (gh) already configured

### Common Git Commands

```bash
# Check status
git status

# See recent commits
git log --oneline -10

# View what changed
git diff

# Stage all changes
git add .

# Commit
git commit -m "Your message here"

# Push to GitHub
git push origin main

# Pull from GitHub
git pull origin main

# Reset to previous commit (CAREFUL!)
git reset --hard HEAD~1

# Reset to specific commit
git reset --hard <commit-hash>
```

### Commit Message Format

Use clear, descriptive messages:

```
Fix: [what you fixed]
Add: [what you added]
Update: [what you updated]
Remove: [what you removed]
```

Examples:
```bash
git commit -m "Fix: + button not working due to missing Gio import"
git commit -m "Add: logging system for debugging"
git commit -m "Update: version to 0.2.1"
```

---

## AppImage Build Process (Detailed)

### What Gets Bundled

**Included in AppImage:**
- ✅ WineTranslator Python code
- ✅ Python standard library modules
- ✅ AppRun launcher script

**Uses System Libraries:**
- 📦 Python 3 interpreter (system python3)
- 📦 PyGObject (system python3-gi)
- 📦 GTK4 (system gir1.2-gtk-4.0)
- 📦 Libadwaita (system gir1.2-adw-1)
- 📦 Wine (system wine)
- 📦 Winetricks (system winetricks)

### Build Script Breakdown

**File**: `build-appimage.sh`

**Steps:**
1. `create_appdir()` - Creates directory structure
2. `install_dependencies()` - Prepares Python environment
3. `copy_app_files()` - Copies winetranslator package
4. `create_desktop_file()` - Creates .desktop and icon
5. `create_apprun()` - Creates AppRun launcher with dependency checking
6. `get_appimagetool()` - Downloads appimagetool if needed
7. `build_appimage()` - Packages everything into .AppImage

**AppRun script features:**
- Detects missing dependencies (Wine, GTK4, etc.)
- Shows GUI dialog asking to install
- Uses pkexec/sudo to auto-install dependencies
- Runs the app after dependencies are met

### AppImage Structure

```
WineTranslator.AppDir/
├── AppRun                    # Main launcher
├── winetranslator.desktop    # Desktop integration
├── winetranslator.png        # Icon
└── usr/
    ├── bin/
    │   └── winetranslator    # Python launcher script
    ├── lib/
    │   └── python3/
    │       └── site-packages/
    │           └── winetranslator/  # Our code
    └── share/
        └── applications/
            └── winetranslator.desktop
```

---

## Logging System

### Log Location

```bash
~/.local/share/winetranslator/winetranslator.log
```

### Viewing Logs

```bash
# View entire log
cat ~/.local/share/winetranslator/winetranslator.log

# View last 50 lines
tail -50 ~/.local/share/winetranslator/winetranslator.log

# Live tail (updates as app runs)
tail -f ~/.local/share/winetranslator/winetranslator.log
```

### Adding Logging to Code

```python
import logging

logger = logging.getLogger(__name__)

# In your function
logger.info("Something happened")
logger.warning("Something might be wrong")
logger.error("Something failed", exc_info=True)  # Includes stack trace
```

### Log Levels

- `DEBUG` - Detailed info for diagnosing problems
- `INFO` - General information messages
- `WARNING` - Something unexpected but not fatal
- `ERROR` - Something failed, includes stack traces

---

## Quick Reference

### Full Development Cycle

```bash
# 1. Make changes
cd /media/doug/stuff/winetranslator
nano winetranslator/gui/main_window.py

# 2. Test locally (optional)
python3 -m winetranslator

# 3. Commit and push
git add .
git commit -m "Fix: whatever you fixed"
git push origin main

# 4. Build AppImage
rm -rf WineTranslator.AppDir WineTranslator-x86_64.AppImage
./build-appimage.sh

# 5. Test AppImage
./WineTranslator-x86_64.AppImage

# 6. Users can update via Menu → Check for Updates
```

### Testing Updates

```bash
# After building AppImage with latest code:

# 1. Make a test change and push
echo "# Test" >> README.md
git add README.md
git commit -m "Test update"
git push origin main

# 2. Reset local (so we're "behind")
git reset --hard HEAD~1

# 3. Run AppImage
./WineTranslator-x86_64.AppImage

# 4. Click Menu → Check for Updates
# Should detect 1 commit behind

# 5. Click Update
# Should pull and reinstall

# 6. Click Restart Now
# Should show new version
```

---

## Common Issues

### Issue: "externally managed environment"

**Error**: `pip3 install` fails with externally managed environment

**Fix**: Use `--break-system-packages` flag
```python
# In updater.py
pip3 install --user --break-system-packages -e .
```

### Issue: "+ button doesn't work"

**Error**: "could not create signal" or no response

**Causes**:
- Missing `Gio` import
- Duplicate `GObject.signal_new()` call
- Dialog class not properly initialized

**Check**:
```bash
tail -50 ~/.local/share/winetranslator/winetranslator.log
```

### Issue: "Update says already up to date"

**Cause**: Local repo is already at latest commit

**Fix**:
```bash
# Check current position
git log --oneline -3

# Make sure you're behind GitHub
git reset --hard <older-commit>

# Or pull latest then reset
git pull origin main
git reset --hard HEAD~1
```

### Issue: AppImage won't run

**Error**: Permission denied or "No such file or directory"

**Fix**:
```bash
# Make executable
chmod +x WineTranslator-x86_64.AppImage

# Run with full path
/media/doug/stuff/winetranslator/WineTranslator-x86_64.AppImage
```

---

## File Structure

```
winetranslator/
├── .git/                     # Git repository
├── .gitignore               # Git ignore rules
├── build-appimage.sh        # AppImage build script
├── install.sh               # Dependency installer
├── run.sh                   # Quick run script
├── update.sh                # Manual update script
├── pyproject.toml           # Python project config
├── requirements.txt         # Python dependencies
├── LICENSE                  # GPL-3.0 license
├── README.md                # User documentation
├── INSTALL.md               # Installation guide
├── RESEARCH.md              # Architecture research
├── APPIMAGE.md              # AppImage documentation
├── DEVELOPMENT.md           # This file!
├── PROJECT_SUMMARY.md       # Project overview
├── winetranslator.desktop   # Desktop entry
└── winetranslator/          # Main package
    ├── __init__.py
    ├── __main__.py
    ├── main.py              # Application entry point
    ├── core/                # Business logic
    │   ├── __init__.py
    │   ├── runner_manager.py
    │   ├── prefix_manager.py
    │   ├── app_launcher.py
    │   ├── dependency_manager.py
    │   └── updater.py       # Update system
    ├── gui/                 # GTK4 interface
    │   ├── __init__.py
    │   ├── main_window.py
    │   └── add_app_dialog.py
    ├── database/            # SQLite storage
    │   ├── __init__.py
    │   └── db.py
    └── utils/               # Utilities
        ├── __init__.py
        ├── wine_utils.py
        ├── logger.py
        └── first_run.py

Build artifacts (gitignored):
├── WineTranslator.AppDir/        # Build directory
├── WineTranslator-x86_64.AppImage # Final app
└── appimagetool-x86_64.AppImage  # Build tool
```

---

## Resources

- **GitHub Repo**: https://github.com/crucifix86/winetranslator
- **Logs**: `~/.local/share/winetranslator/winetranslator.log`
- **Data**: `~/.local/share/winetranslator/`
- **Database**: `~/.local/share/winetranslator/winetranslator.db`
- **Prefixes**: `~/.local/share/winetranslator/prefixes/`

---

## Next Steps

- [ ] Fix update system completely
- [ ] Test + button with new AppImage
- [ ] Add more comprehensive error handling
- [ ] Implement preferences dialog
- [ ] Add icon extraction from .exe files
- [ ] Create desktop shortcuts for apps
- [ ] Add app categories/tags
- [ ] Implement search functionality
