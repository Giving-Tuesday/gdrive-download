# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for gdrive GUI application."""
import os
import sys

# Add the src directory to the path so imports work
spec_dir = os.path.dirname(os.path.abspath(SPEC))
src_dir = os.path.join(spec_dir, '..', 'src')

block_cipher = None

a = Analysis(
    [os.path.join(src_dir, 'gdrive_download', 'gui', 'app.py')],
    pathex=[src_dir],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Google API libraries
        'google.auth',
        'google.auth.transport',
        'google.auth.transport.requests',
        'google.oauth2',
        'google.oauth2.credentials',
        'google_auth_oauthlib',
        'google_auth_oauthlib.flow',
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.http',
        'googleapiclient.errors',
        'httplib2',
        # Document conversion
        'mammoth',
        'mammoth.docx',
        'markdownify',
        'docx',
        'lxml',
        'lxml.etree',
        # CLI modules (used by GUI)
        'gdrive_download.cli.search',
        'gdrive_download.cli.download',
        'gdrive_download.cli.manage',
        'gdrive_download.downloader',
        'gdrive_download.downloader.drive_downloader',
        'gdrive_download.downloader.drive_searcher',
        'gdrive_download.downloader.file_converter',
        'gdrive_download.downloader.relationship_tracker',
        'gdrive_download.config',
        'gdrive_download.utils',
        'gdrive_download.utils.logging',
        'gdrive_download.utils.file_utils',
        # Config and utilities
        'click',
        'pydantic',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        'pydantic_core',
        'rich',
        'rich.console',
        'rich.progress',
        'rich.table',
        'rich.prompt',
        'yaml',
        'pathspec',
        # Tkinter (usually bundled but ensure it's included)
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        # Standard library
        'pickle',
        'json',
        'csv',
        'queue',
        'threading',
        'email.mime.text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'IPython',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GDrive Tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)

# For macOS, create an app bundle
import sys
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='GDrive Tools.app',
        icon=None,  # Add .icns icon path here if available
        bundle_identifier='org.givingtuesday.gdrive-tools',
        info_plist={
            'CFBundleName': 'GDrive Tools',
            'CFBundleDisplayName': 'GDrive Tools',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
