"""
FM Radio GUI 스타일시트
"""

def get_main_stylesheet():
    """메인 윈도우 스타일시트"""
    return """
    QWidget {
        background-color: #ffffff;
        color: #09090b;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
    }
    
    QLabel#header {
        font-size: 28px;
        font-weight: 700;
        color: #1f2937;
        margin: 8px 0;
    }
    
    QLabel#device-status {
        font-size: 11px;
        color: #059669;
        font-weight: 500;
    }
    
    QLabel#device-info {
        font-size: 10px;
        color: #6b7280;
    }
    
    QPushButton#device-btn {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 10px;
        min-width: 60px;
        max-height: 24px;
    }
    
    QPushButton#device-btn:hover {
        background-color: #e5e7eb;
    }
    
    QFrame#freq-display {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                   stop:0 #f8fafc, stop:1 #e2e8f0);
        border: 2px solid #cbd5e1;
        border-radius: 12px;
        margin: 8px 0;
    }
    
    QLabel#freq-number {
        font-size: 48px;
        font-weight: 700;
        color: #1e293b;
        margin: 0;
    }
    
    QLabel#freq-unit {
        font-size: 16px;
        font-weight: 500;
        color: #64748b;
        margin: 0;
    }
    
    QLabel#section-label {
        font-size: 14px;
        font-weight: 600;
        color: #374151;
        margin-bottom: 4px;
    }
    
    QLabel#signal-bar {
        font-size: 12px;
        color: #d1d5db;
        margin: 0 1px;
    }
    
    QLabel#signal-bar[active="true"] {
        color: #10b981;
    }
    
    QLabel#rssi-value {
        font-size: 11px;
        color: #6b7280;
        font-family: "SF Mono", Consolas, monospace;
        margin-left: 8px;
    }
    
    QPushButton#freq-btn {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        padding: 12px;
        min-width: 60px;
        min-height: 48px;
    }
    
    QPushButton#freq-btn:hover {
        background-color: #2563eb;
    }
    
    QPushButton#freq-btn:pressed {
        background-color: #1d4ed8;
    }
    
    QPushButton#freq-btn-small {
        background-color: #6b7280;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        padding: 8px;
        min-width: 50px;
        min-height: 36px;
    }
    
    QPushButton#freq-btn-small:hover {
        background-color: #4b5563;
    }
    
    QGroupBox {
        font-weight: 600;
        font-size: 14px;
        color: #374151;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        background-color: #ffffff;
    }
    
    QPushButton#secondary-btn {
        background-color: #f8fafc;
        color: #374151;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
        font-weight: 500;
    }
    
    QPushButton#secondary-btn:hover {
        background-color: #f1f5f9;
        border-color: #cbd5e1;
    }
    
    QLabel#preset-info {
        font-size: 11px;
        color: #6b7280;
        font-style: italic;
        margin: 4px 0 8px 0;
    }
    
    QPushButton#preset-btn {
        background-color: #f9fafb;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        font-weight: 500;
        padding: 8px;
    }
    
    QPushButton#preset-btn:hover {
        background-color: #f3f4f6;
        border-color: #9ca3af;
    }
    
    QPushButton#preset-btn[data-state="saved"] {
        background-color: #dbeafe;
        color: #1e40af;
        border-color: #3b82f6;
    }
    
    QPushButton#scan-btn {
        background-color: #059669;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 16px;
        font-weight: 600;
    }
    
    QPushButton#scan-btn:hover {
        background-color: #047857;
    }
    
    QLabel#volume-value {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        min-width: 20px;
    }
    
    QSlider#volume-slider {
        min-height: 20px;
    }
    
    QSlider#volume-slider::groove:horizontal {
        border: 1px solid #d1d5db;
        height: 6px;
        background: #f3f4f6;
        border-radius: 3px;
    }
    
    QSlider#volume-slider::handle:horizontal {
        background: #3b82f6;
        border: 2px solid #ffffff;
        width: 16px;
        height: 16px;
        border-radius: 8px;
        margin: -6px 0;
    }
    
    QSlider#volume-slider::handle:horizontal:hover {
        background: #2563eb;
    }
    
    QSlider#volume-slider::sub-page:horizontal {
        background: #3b82f6;
        border-radius: 3px;
    }
    
    QLabel#rds-station {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 4px;
    }
    
    QLabel#rds-text {
        font-size: 12px;
        color: #6b7280;
        line-height: 1.4;
    }
    
    QPushButton#power-btn {
        background-color: #dc2626;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        padding: 12px 20px;
        min-height: 44px;
    }
    
    QPushButton#power-btn:hover {
        background-color: #b91c1c;
    }
    
    QPushButton#power-btn[data-state="on"] {
        background-color: #16a34a;
    }
    
    QPushButton#power-btn[data-state="on"]:hover {
        background-color: #15803d;
    }
    
    QPushButton#power-btn[data-state="off"] {
        background-color: #6b7280;
    }
    
    QPushButton#power-btn[data-state="off"]:hover {
        background-color: #4b5563;
    }
    
    QPushButton#secondary-btn[data-state="active"] {
        background-color: #fbbf24;
        color: #ffffff;
        border-color: #f59e0b;
    }
    
    QPushButton#secondary-btn[data-state="active"]:hover {
        background-color: #f59e0b;
    }
    
    QPushButton#record-btn[data-state="recording"] {
        background-color: #dc2626;
        animation: pulse 1s infinite;
    }
    
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    QScrollBar:vertical {
        background-color: #f3f4f6;
        width: 8px;
        border-radius: 4px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #d1d5db;
        border-radius: 4px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #9ca3af;
    }
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    """

def get_dialog_stylesheet():
    """다이얼로그 스타일시트"""
    return """
    QDialog {
        background-color: #ffffff;
        color: #09090b;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    QGroupBox {
        font-weight: 600;
        font-size: 14px;
        color: #374151;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-top: 8px;
        padding-top: 8px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
    }
    
    QPushButton {
        background-color: #09090b;
        color: #fafafa;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        min-width: 80px;
    }
    
    QPushButton:hover {
        background-color: #18181b;
    }
    
    QPushButton:disabled {
        background-color: #9ca3af;
        color: #6b7280;
    }
    
    QPushButton#secondary {
        background-color: #f8fafc;
        color: #374151;
        border: 1px solid #e2e8f0;
    }
    
    QPushButton#secondary:hover {
        background-color: #f1f5f9;
    }
    """
