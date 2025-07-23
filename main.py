#!/usr/bin/env python3
"""
FM Radio Enhanced - 메인 실행 파일
GitHub Actions에서 빌드된 실행 파일이 바로 작동할 수 있도록 하는 진입점
"""

import sys
import os
import platform

# 현재 스크립트의 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """메인 함수"""
    try:
        # Qt 애플리케이션 import
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # 메인 애플리케이션 import
        from ic100_radio_gui import ModernRadioApp
        
        # macOS에서 high DPI 지원
        if platform.system() == "Darwin":
            os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 애플리케이션 정보 설정
        app.setApplicationName("FM Radio Enhanced")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("FM Radio Enhanced")
        
        # 라디오 앱 생성 및 표시
        radio_app = ModernRadioApp()
        radio_app.show()
        
        # 이벤트 루프 시작
        exit_code = app.exec()
        sys.exit(exit_code)
        
    except ImportError as e:
        print(f"Required modules not found: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
