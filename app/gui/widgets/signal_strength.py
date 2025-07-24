"""
신호 강도 표시 위젯
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class SignalStrengthWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signal_bars = []
        self.rssi_value = 0
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 신호 강도 레이블
        signal_label = QLabel("Signal:")
        signal_label.setObjectName("section-label")
        layout.addWidget(signal_label)
        
        # 신호 강도 바들
        for i in range(5):
            bar = QLabel("▬")
            bar.setObjectName("signal-bar")
            bar.setProperty("active", False)
            self.signal_bars.append(bar)
            layout.addWidget(bar)
        
        # RSSI 값 표시
        self.rssi_label = QLabel("0 dBm")
        self.rssi_label.setObjectName("rssi-value")
        layout.addWidget(self.rssi_label)
        
        layout.addStretch()
    
    def update_signal_strength(self, rssi_value):
        """신호 강도 업데이트"""
        self.rssi_value = rssi_value
        self.rssi_label.setText(f"{rssi_value} dBm")
        
        # RSSI 값에 따라 신호 바 개수 결정
        # RSSI는 보통 -120 ~ -30 dBm 범위
        # -30이 가장 강하고, -120이 가장 약함
        if rssi_value >= -50:
            active_bars = 5
        elif rssi_value >= -60:
            active_bars = 4
        elif rssi_value >= -70:
            active_bars = 3
        elif rssi_value >= -80:
            active_bars = 2
        elif rssi_value >= -90:
            active_bars = 1
        else:
            active_bars = 0
        
        # 신호 바 업데이트
        for i, bar in enumerate(self.signal_bars):
            is_active = i < active_bars
            bar.setProperty("active", is_active)
            bar.style().unpolish(bar)
            bar.style().polish(bar)
    
    def update_signal(self, rssi_value):
        """신호 강도 업데이트 (호환성을 위한 별칭)"""
        self.update_signal_strength(rssi_value)
