"""
Tested Applications Database for WineTranslator.

Curated list of Windows applications known to work well with Wine.
"""

TESTED_APPS = [
    {
        'name': 'WinSCP',
        'version': '6.5.4',
        'description': 'Free SFTP, SCP, S3 and FTP client for Windows',
        'url': 'https://winscp.net/download/WinSCP-6.5.4-Setup.exe',
        'icon_url': 'https://winscp.net/eng/data/media/icons/winscp.png',
        'category': 'File Transfer',
        'install_notes': '⚠️ IMPORTANT: During installation, select "Install for all users" option. Do NOT select "Install for me only" or the application will fail to run.',
        'dependencies': ['vcrun2019', 'd3dx9', 'corefonts'],
        'tested_date': '2025-11-06',
        'working': True,
    },
    # More apps can be added here
]

CATEGORIES = [
    'All',
    'File Transfer',
    'Development',
    'Productivity',
    'Gaming',
    'Media',
    'Utilities',
]
