"""
프리셋 버튼 위젯
"""
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal


class PresetButtonsWidget(QWidget):
    # 시그널 정의
    preset_recalled = Signal(int)  # 프리셋 불러오기
    preset_save_requested = Signal(int)  # 프리셋 저장 요청
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets = [None] * 6  # 6개 프리셋
        self.preset_buttons = []
        self.is_korean = True  # 기본 언어 설정
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 언어 변경 버튼
        language_layout = QHBoxLayout()
        language_layout.addStretch()
        self.language_btn = QPushButton(self.get_text("🌍 English", "🌍 한국어"))
        self.language_btn.setObjectName("secondary-btn")
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setFixedWidth(80)
        language_layout.addWidget(self.language_btn)
        layout.addLayout(language_layout)
        
        # 프리셋 사용법 안내
        self.preset_info = QLabel(self.get_text("💾 클릭: 저장된 방송 불러오기  |  우클릭: 현재 주파수 저장", 
                                                "💾 Click: Load station  |  Right-click: Save current frequency"))
        self.preset_info.setObjectName("preset-info")
        self.preset_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preset_info)
        
        # 프리셋 버튼들을 2행 3열로 배치
        preset_buttons_container = QWidget()
        preset_buttons_layout = QGridLayout(preset_buttons_container)
        preset_buttons_layout.setSpacing(8)
        
        for i in range(6):
            btn = QPushButton(f"P{i+1}")
            btn.setObjectName("preset-btn")
            btn.clicked.connect(lambda checked, idx=i: self.recall_preset(idx))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, idx=i: self.save_preset_menu(idx))
            btn.setToolTip(self.get_preset_tooltip(i))
            btn.setMinimumHeight(60)  # 버튼 높이 증가
            btn.setMinimumWidth(80)   # 버튼 너비 증가
            
            # 2행 3열로 배치
            row = i // 3
            col = i % 3
            preset_buttons_layout.addWidget(btn, row, col)
            
            self.preset_buttons.append(btn)
        
        layout.addWidget(preset_buttons_container)
    
    def get_text(self, korean_text, english_text):
        """언어 설정에 따른 텍스트 반환"""
        return korean_text if self.is_korean else english_text
    
    def toggle_language(self):
        """언어 토글"""
        self.is_korean = not self.is_korean
        self.update_texts()
    
    def update_texts(self):
        """텍스트 업데이트"""
        self.language_btn.setText(self.get_text("🌍 English", "🌍 한국어"))
        self.preset_info.setText(self.get_text("💾 클릭: 저장된 방송 불러오기  |  우클릭: 현재 주파수 저장", 
                                               "💾 Click: Load station  |  Right-click: Save current frequency"))
        self.update_preset_buttons()
    
    def recall_preset(self, index):
        """프리셋 불러오기"""
        if index < len(self.presets) and self.presets[index] is not None:
            self.preset_recalled.emit(index)
    
    def save_preset_menu(self, index):
        """프리셋 저장 요청"""
        self.preset_save_requested.emit(index)
    
    def update_presets(self, presets):
        """프리셋 데이터 업데이트"""
        self.presets = presets
        self.update_preset_buttons()
    
    def update_preset_buttons(self):
        """프리셋 버튼 표시 업데이트"""
        for i, btn in enumerate(self.preset_buttons):
            if i < len(self.presets) and self.presets[i] is not None:
                # 단순한 주파수 값 처리
                freq = self.presets[i]
                btn.setText(f"P{i+1}\\n📻 {freq:.1f}")
                btn.setProperty("data-state", "saved")
            else:
                btn.setText(f"P{i+1}\\n💾 {self.get_text('비어있음', 'Empty')}")
                btn.setProperty("data-state", "")
            
            btn.setToolTip(self.get_preset_tooltip(i))
            # 스타일 새로고침
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def get_preset_tooltip(self, index):
        """프리셋 버튼 툴팁 생성"""
        if index < len(self.presets) and self.presets[index] is not None:
            freq = self.presets[index]
            return self.get_text(f"프리셋 {index+1}: {freq:.1f} MHz\\n클릭: 불러오기 | 우클릭: 저장",
                                f"Preset {index+1}: {freq:.1f} MHz\\nClick: Load | Right-click: Save")
        else:
            return self.get_text(f"프리셋 {index+1}: 비어있음\\n우클릭하여 현재 주파수 저장",
                                f"Preset {index+1}: Empty\\nRight-click to save current frequency")
    
    def get_language_setting(self):
        """현재 언어 설정 반환"""
        return self.is_korean
    
    def set_language_setting(self, is_korean):
        """언어 설정 변경"""
        self.is_korean = is_korean
        self.update_texts()
