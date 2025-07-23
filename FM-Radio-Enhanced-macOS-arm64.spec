# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('audio_manager.py', '.'),
    ('besfm.py', '.'),
]
binaries = []
hiddenimports = [
    'usb.backend.libusb1', 
    'usb.backend.libusb0', 
    'usb.backend.openusb', 
    'PySide6.QtCore', 
    'PySide6.QtWidgets', 
    'PySide6.QtGui',
    'besfm',
    'audio_manager',
    'json',
    'os',
    'sys',
    'time',
    'threading',
    'platform'
]
tmp_ret = collect_all('usb')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FM-Radio-Enhanced-macOS-arm64',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='FM-Radio-Enhanced-macOS-arm64.app',
    bundle_identifier=None,
)
