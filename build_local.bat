@echo off
REM 로컬 빌드 스크립트 (Windows)

echo 🚀 FM Radio Enhanced - Local Build Script
echo ==========================================

REM Python 가상환경 확인
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  가상환경이 활성화되지 않았습니다.
    echo    다음 명령으로 가상환경을 만들고 활성화하세요:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo.
)

REM 의존성 설치
echo 📦 Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM libusb-win32 설치 안내
echo 📚 libusb-win32가 필요할 수 있습니다:
echo    https://sourceforge.net/projects/libusb-win32/files/libusb-win32-releases/
echo.

REM 빌드 실행
echo 🔨 Building executable for Windows-x64...
pyinstaller --onefile ^
    --windowed ^
    --name "FM-Radio-Enhanced-Windows-x64" ^
    --icon="assets/icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import=usb.backend.libusb1 ^
    --hidden-import=usb.backend.libusb0 ^
    --hidden-import=usb.backend.openusb ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtGui ^
    --collect-all=usb ^
    ic100_radio_gui.py

REM 결과 확인
if exist "dist\FM-Radio-Enhanced-Windows-x64.exe" (
    echo ✅ Build successful!
    echo 📍 Executable location: dist\FM-Radio-Enhanced-Windows-x64.exe
    echo.
    echo 🎯 Next steps:
    echo    1. Test the executable: dist\FM-Radio-Enhanced-Windows-x64.exe
    echo    2. Create a GitHub tag to trigger release: git tag v1.0.0 ^&^& git push origin v1.0.0
    echo.
) else (
    echo ❌ Build failed! Check the output above for errors.
    exit /b 1
)

pause
