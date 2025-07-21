#!/bin/bash
# 로컬 빌드 스크립트 (macOS/Linux)

echo "🚀 FM Radio Enhanced - Local Build Script"
echo "=========================================="

# Python 가상환경 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다."
    echo "   다음 명령으로 가상환경을 만들고 활성화하세요:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo ""
fi

# 의존성 설치
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# 플랫폼 확인
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS-arm64"
    ICON="assets/icon.icns"
    ARCH_FLAG="--target-arch=arm64"
    
    # libusb 설치 확인
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew가 설치되지 않았습니다. libusb 설치를 건너뜁니다."
    else
        echo "🍺 Installing libusb via Homebrew..."
        brew install libusb
    fi
else
    PLATFORM="Linux-x64"
    ICON="assets/icon.png"
    ARCH_FLAG=""
fi

# 빌드 실행
echo "🔨 Building executable for $PLATFORM..."
pyinstaller --onefile \
    --windowed \
    --name "FM-Radio-Enhanced-$PLATFORM" \
    --icon="$ICON" \
    --add-data "assets:assets" \
    --hidden-import=usb.backend.libusb1 \
    --hidden-import=usb.backend.libusb0 \
    --hidden-import=usb.backend.openusb \
    --hidden-import=PySide6.QtCore \
    --hidden-import=PySide6.QtWidgets \
    --hidden-import=PySide6.QtGui \
    --collect-all=usb \
    $ARCH_FLAG \
    ic100_radio_gui.py

# 결과 확인
if [ -f "dist/FM-Radio-Enhanced-$PLATFORM" ]; then
    echo "✅ Build successful!"
    echo "📍 Executable location: dist/FM-Radio-Enhanced-$PLATFORM"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Test the executable: ./dist/FM-Radio-Enhanced-$PLATFORM"
    echo "   2. Create a GitHub tag to trigger release: git tag v1.0.0 && git push origin v1.0.0"
    echo ""
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi
