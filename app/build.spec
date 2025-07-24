# PyInstaller 설정 파일
# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# 플랫폼별 설정
if sys.platform == 'darwin':  # macOS
    platform_name = 'macOS-arm64'
    target_arch = 'arm64'
elif sys.platform == 'win32':  # Windows
    platform_name = 'Windows-x64'
    target_arch = None
else:
    platform_name = 'Linux-x64'
    target_arch = None

# 숨겨진 import들
hidden_imports = [
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

# 데이터 파일들
datas = []

# 바이너리 파일들 (USB 라이브러리)
binaries = []

# 제외할 모듈들 (크기 최적화)
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'IPython',
    'jupyter',
    'notebook',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'FM-Radio-Enhanced-{platform_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 애플리케이션이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 제거
)

# macOS용 앱 번들 생성 (아이콘 제거)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name=f'FM-Radio-Enhanced-{platform_name}.app',
        icon=None,  # 아이콘 제거
        bundle_identifier='com.alphaorderly.fm-radio-enhanced',
        info_plist={
            'CFBundleName': 'FM Radio Enhanced',
            'CFBundleDisplayName': 'FM Radio Enhanced',
            'CFBundleIdentifier': 'com.alphaorderly.fm-radio-enhanced',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleInfoDictionaryVersion': '6.0',
            'LSMinimumSystemVersion': '11.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSApplicationCategoryType': 'public.app-category.utilities',
            'NSHumanReadableCopyright': '© 2025 AlphaOrderly. All rights reserved.',
        }
    )
