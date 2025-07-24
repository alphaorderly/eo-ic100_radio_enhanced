"""
주파수 디스플레이 위젯
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt


class FrequencyDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_freq = 88.5
        self.init_ui()
    
    def init_ui(self):
        # 주파수 디스플레이 컨테이너
        self.freq_container = QFrame()
        self.freq_container.setObjectName("freq-display")
        freq_layout = QVBoxLayout(self.freq_container)
        freq_layout.setContentsMargins(20, 16, 20, 16)
        freq_layout.setSpacing(4)
        
        # 주파수 표시
        self.freq_label = QLabel(f"{self.current_freq:.1f}")
        self.freq_label.setAlignment(Qt.AlignCenter)
        self.freq_label.setObjectName("freq-number")
        freq_layout.addWidget(self.freq_label)
        
        # MHz 단위
        mhz_label = QLabel("MHz")
        mhz_label.setAlignment(Qt.AlignCenter)
        mhz_label.setObjectName("freq-unit")
        freq_layout.addWidget(mhz_label)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.freq_container)
    
    def update_frequency(self, frequency):
        """주파수 업데이트"""
        self.current_freq = frequency
        self.freq_label.setText(f"{frequency:.1f}")
    
    def get_frequency(self):
        """현재 주파수 반환"""
        return self.current_freq
