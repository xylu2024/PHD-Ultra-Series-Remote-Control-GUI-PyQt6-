# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build specification for PHD Ultra Series Remote Control GUI.
Build command: pyinstaller main.spec
"""

import os
import sys

block_cipher = None

datas = [
    ('json/commands.json', 'json'),
    ('json/logsConfig.json', 'json'),
    ('qss/origin_style.qss', 'qss'),
]

hiddenimports = [
    'qdarktheme',
    'numpy',
    'serial',
    'serial.tools.list_ports',
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'global_hotkeys',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5'],
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
    name='PHD_Ultra_Remote_Control_v1.0.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None
)
