"""
메인 라디오 애플리케이션 윈도우
"""
import sys
import besfm
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSlider, QPushButton, QGroupBox, QScrollArea,
                               QFrame, QMessageBox, QDialog, QApplication)
from PySide6.QtCore import Qt, QTimer

from audio_manager import AudioManager
from gui.dialogs import DeviceSelectionDialog
from gui.widgets import FrequencyDisplayWidget, SignalStrengthWidget, PresetButtonsWidget
from gui.styles.stylesheets import get_main_stylesheet
from utils.settings_manager import SettingsManager
from utils.language_manager import LanguageManager


class ModernRadioApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # 매니저들 초기화
        self.settings_manager = SettingsManager()
        self.language_manager = LanguageManager()
        
        # 기본 상태 변수들
        self.current_freq = 88.5
        self.volume = 8
        self.is_muted = False
        self.is_powered = False
        self.is_recording = False
        self.rds_enabled = False
        
        # 하드웨어 초기화
        self.fm = None
        self.selected_device = None
        self.audio_manager = None
        
        # 프리셋 및 스테이션 데이터
        self.presets = [None] * 6
        
        # 스캔 관련
        self.scan_progress = None
        
        # 타이머들
        self.rds_timer = QTimer()
        self.rds_timer.timeout.connect(self.check_rds_data)
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(self.update_signal_strength)
        
        # 설정 로드
        self.load_settings()
        
        # 기기 선택 다이얼로그 표시
        self.show_device_selection()
        
        # UI 초기화
        self.init_ui()
        self.setup_animations()
        
        # 하드웨어가 있으면 초기 상태 업데이트
        if self.fm is not None:
            self.update_from_hardware()
            # 정기적 업데이트 시작
            self.signal_timer.start(2000)  # 2초마다 신호 강도 업데이트
    
    def show_device_selection(self):
        """기기 선택 다이얼로그 표시"""
        dialog = DeviceSelectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if dialog.selected_device is not None:
                self.selected_device = dialog.selected_device
                self.init_hardware()
            else:
                QMessageBox.critical(self, "No Device Selected", 
                                   "No FM Radio device was selected. The application will exit.")
                sys.exit(1)
        else:
            # 사용자가 취소했으면 종료
            sys.exit(0)
    
    def init_hardware(self):
        """하드웨어 초기화"""
        try:
            print(f"Initializing hardware with device: {self.selected_device}")
            self.fm = besfm.BesFM(self.selected_device)
            
            # 연결 상태 확인
            if not self.fm.is_connected():
                raise Exception("Device not responding")
                
            print("Hardware connected successfully!")
            
            # 오디오 매니저 초기화
            try:
                self.audio_manager = AudioManager(self.fm)
                print("Audio manager initialized")
            except Exception as e:
                print(f"Audio manager initialization failed: {e}")
                self.audio_manager = None
            
            # 하드웨어 초기 상태 가져오기
            try:
                self.is_powered = self.fm.get_power()
                self.is_recording = self.fm.get_recording()
                
                if self.is_powered or self.is_recording:
                    # 하드웨어에서 현재 값들 읽어오기
                    channel = self.fm.get_channel()
                    self.current_freq = channel
                    self.volume = self.fm.get_volume()
                    self.is_muted = self.fm.get_mute()
                    print(f"Hardware state: freq={self.current_freq:.1f}MHz, vol={self.volume}, muted={self.is_muted}")
                else:
                    print("Hardware is powered off")
                    
            except Exception as e:
                print(f"Warning: Could not read initial hardware state: {e}")
                # 기본값 사용
                self.current_freq = 88.5
                self.volume = 8
                self.is_muted = False
            
        except PermissionError as e:
            print(f"Permission error: {e}")
            error_msg = f"USB Device Access Permission Denied\\n\\n{str(e)}\\n\\n"
            error_msg += "Try running the application with:\\n"
            error_msg += "sudo python3 ic100_radio_gui.py\\n\\n"
            error_msg += "Or use the provided start_radio.sh script."
            QMessageBox.critical(self, "Permission Error", error_msg)
            sys.exit(1)
        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            error_msg = f"Failed to initialize hardware:\\n{str(e)}\\n\\n"
            error_msg += "Please check:\\n"
            error_msg += "1. USB device is properly connected\\n"
            error_msg += "2. No other applications are using the device\\n"
            error_msg += "3. Device drivers are installed correctly"
            QMessageBox.critical(self, "Hardware Error", error_msg)
            sys.exit(1)
    
    def setup_animations(self):
        """애니메이션 설정"""
        # 레코딩 애니메이션을 위한 타이머
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.toggle_record_indicator)
        self.record_blink = False
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(self.language_manager.get_text('window_title'))
        self.setFixedSize(600, 700)
        self.setStyleSheet(get_main_stylesheet())
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # 스크롤 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 스크롤 내용 위젯
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # UI 구성 요소들 생성
        self.create_header(scroll_layout)
        self.create_frequency_display(scroll_layout)
        self.create_signal_strength_display(scroll_layout)
        self.create_frequency_controls(scroll_layout)
        self.create_preset_section(scroll_layout)
        self.create_volume_section(scroll_layout)
        self.create_rds_section(scroll_layout)
        self.create_bottom_controls(scroll_layout)
        self.create_settings_button(scroll_layout)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def create_header(self, parent_layout):
        """헤더 생성"""
        header_layout = QHBoxLayout()
        
        # 제목
        header = QLabel("FM Radio")
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("header")
        header_layout.addWidget(header)
        
        # 기기 정보 및 변경 버튼
        device_layout = QVBoxLayout()
        device_layout.setSpacing(4)
        
        # 기기 상태 표시
        device_status = "🟢 Hardware Connected"
        device_info = f"Product ID: 0x{self.selected_device.idProduct:04x}"
        
        self.device_status_label = QLabel(device_status)
        self.device_status_label.setObjectName("device-status")
        self.device_status_label.setAlignment(Qt.AlignRight)
        device_layout.addWidget(self.device_status_label)
        
        self.device_info_label = QLabel(device_info)
        self.device_info_label.setObjectName("device-info") 
        self.device_info_label.setAlignment(Qt.AlignRight)
        device_layout.addWidget(self.device_info_label)
        
        # 기기 변경 버튼
        self.change_device_btn = QPushButton(self.language_manager.get_text('change_device'))
        self.change_device_btn.setObjectName("device-btn")
        self.change_device_btn.clicked.connect(self.change_device)
        device_layout.addWidget(self.change_device_btn)
        
        header_layout.addLayout(device_layout)
        parent_layout.addLayout(header_layout)
    
    def create_frequency_display(self, parent_layout):
        """주파수 디스플레이 생성"""
        self.freq_display = FrequencyDisplayWidget()
        self.freq_display.update_frequency(self.current_freq)
        parent_layout.addWidget(self.freq_display)
    
    def create_signal_strength_display(self, parent_layout):
        """신호 강도 표시 생성"""
        self.signal_strength = SignalStrengthWidget()
        parent_layout.addWidget(self.signal_strength)
    
    def create_frequency_controls(self, parent_layout):
        """주파수 컨트롤 생성"""
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # 큰 스텝 다운 버튼
        self.btn_freq_down_big = QPushButton("−1.0")
        self.btn_freq_down_big.setObjectName("freq-btn")
        self.btn_freq_down_big.clicked.connect(lambda: self.change_frequency(-1.0))
        controls_layout.addWidget(self.btn_freq_down_big)
        
        # 작은 스텝 다운 버튼
        self.btn_freq_down_small = QPushButton("−0.1")
        self.btn_freq_down_small.setObjectName("freq-btn-small")
        self.btn_freq_down_small.clicked.connect(lambda: self.change_frequency(-0.1))
        controls_layout.addWidget(self.btn_freq_down_small)
        
        # 스페이서
        controls_layout.addStretch()
        
        # 작은 스텝 업 버튼
        self.btn_freq_up_small = QPushButton("+0.1")
        self.btn_freq_up_small.setObjectName("freq-btn-small")
        self.btn_freq_up_small.clicked.connect(lambda: self.change_frequency(0.1))
        controls_layout.addWidget(self.btn_freq_up_small)
        
        # 큰 스텝 업 버튼
        self.btn_freq_up_big = QPushButton("+1.0")
        self.btn_freq_up_big.setObjectName("freq-btn")
        self.btn_freq_up_big.clicked.connect(lambda: self.change_frequency(1.0))
        controls_layout.addWidget(self.btn_freq_up_big)
        
        parent_layout.addLayout(controls_layout)
    
    def create_preset_section(self, parent_layout):
        """프리셋 섹션 생성"""
        preset_group = QGroupBox(self.language_manager.get_text('presets_scan'))
        preset_layout = QVBoxLayout(preset_group)
        
        # 프리셋 버튼 위젯
        self.preset_widget = PresetButtonsWidget()
        self.preset_widget.preset_recalled.connect(self.recall_preset)
        self.preset_widget.preset_save_requested.connect(self.save_preset_menu)
        self.preset_widget.update_presets(self.presets)
        preset_layout.addWidget(self.preset_widget)
        
        # 스캔 버튼들
        scan_layout = QHBoxLayout()
        
        self.scan_down_btn = QPushButton(self.language_manager.get_text('scan_down'))
        self.scan_down_btn.setObjectName("scan-btn")
        self.scan_down_btn.clicked.connect(self.scan_down)
        scan_layout.addWidget(self.scan_down_btn)
        
        self.scan_up_btn = QPushButton(self.language_manager.get_text('scan_up'))
        self.scan_up_btn.setObjectName("scan-btn")
        self.scan_up_btn.clicked.connect(self.scan_up)
        scan_layout.addWidget(self.scan_up_btn)
        
        preset_layout.addLayout(scan_layout)
        parent_layout.addWidget(preset_group)
    
    def create_volume_section(self, parent_layout):
        """볼륨 섹션 생성"""
        volume_layout = QVBoxLayout()
        volume_layout.setSpacing(8)
        
        # 볼륨 레이블과 값
        vol_header = QHBoxLayout()
        vol_label = QLabel(self.language_manager.get_text('volume'))
        vol_label.setObjectName("section-label")
        self.vol_value = QLabel(str(self.volume))
        self.vol_value.setObjectName("volume-value")
        
        vol_header.addWidget(vol_label)
        vol_header.addStretch()
        vol_header.addWidget(self.vol_value)
        volume_layout.addLayout(vol_header)
        
        # 볼륨 슬라이더
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 15)
        self.volume_slider.setValue(self.volume)
        self.volume_slider.setObjectName("volume-slider")
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        parent_layout.addLayout(volume_layout)
    
    def create_rds_section(self, parent_layout):
        """RDS 섹션 생성"""
        rds_group = QGroupBox(self.language_manager.get_text('rds_info'))
        rds_layout = QVBoxLayout(rds_group)
        
        # RDS 스테이션 이름
        self.rds_station = QLabel(self.language_manager.get_text('no_rds_data'))
        self.rds_station.setObjectName("rds-station")
        rds_layout.addWidget(self.rds_station)
        
        # RDS 텍스트
        self.rds_text = QLabel("")
        self.rds_text.setObjectName("rds-text")
        self.rds_text.setWordWrap(True)
        rds_layout.addWidget(self.rds_text)
        
        # RDS 활성화 버튼
        self.rds_btn = QPushButton(self.language_manager.get_text('enable_rds'))
        self.rds_btn.setObjectName("secondary-btn")
        self.rds_btn.clicked.connect(self.toggle_rds)
        rds_layout.addWidget(self.rds_btn)
        
        parent_layout.addWidget(rds_group)
    
    def create_bottom_controls(self, parent_layout):
        """하단 컨트롤 버튼들 생성"""
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        # 파워 버튼
        self.power_btn = QPushButton(self.language_manager.get_text('power'))
        self.power_btn.setObjectName("power-btn")
        self.power_btn.clicked.connect(self.toggle_power)
        controls_layout.addWidget(self.power_btn)
        
        # 뮤트 버튼
        self.mute_btn = QPushButton(self.language_manager.get_text('mute'))
        self.mute_btn.setObjectName("secondary-btn")
        self.mute_btn.clicked.connect(self.toggle_mute)
        controls_layout.addWidget(self.mute_btn)
        
        # 레코드 버튼
        self.record_btn = QPushButton(self.language_manager.get_text('record'))
        self.record_btn.setObjectName("record-btn")
        self.record_btn.clicked.connect(self.toggle_record)
        controls_layout.addWidget(self.record_btn)
        
        parent_layout.addLayout(controls_layout)
        
        # 초기 상태 업데이트
        self.update_power_state()
    
    def create_settings_button(self, parent_layout):
        """설정 버튼 생성"""
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        
        self.settings_btn = QPushButton(self.language_manager.get_text('settings'))
        self.settings_btn.setObjectName("secondary-btn")
        self.settings_btn.clicked.connect(self.show_settings)
        settings_layout.addWidget(self.settings_btn)
        
        parent_layout.addLayout(settings_layout)
    
    # 여기에 나머지 메서드들을 추가해야 합니다...
    # 이 부분은 원본 파일에서 계속 읽어와서 추가하겠습니다.
    
    def load_settings(self):
        """설정 로드"""
        settings = self.settings_manager.load_settings()
        self.presets = settings.get('presets', [None] * 6)
        self.current_freq = settings.get('last_frequency', 88.5)
        self.volume = settings.get('last_volume', 8)
        
        # 언어 설정
        language = settings.get('language', 'korean')
        self.language_manager.set_language(language)
        
        self.rds_enabled = settings.get('rds_enabled', False)
    
    def save_settings(self):
        """설정 저장"""
        settings = {
            'presets': self.presets,
            'last_frequency': self.current_freq,
            'last_volume': self.volume,
            'language': self.language_manager.get_current_language(),
            'rds_enabled': self.rds_enabled,
        }
        self.settings_manager.save_settings(settings)
    
    def change_frequency(self, step):
        """주파수 변경"""
        if not self.is_powered:
            print("Hardware not powered, cannot change frequency")
            return
        
        new_freq = self.current_freq + step
        
        # 주파수 범위 제한 (87.0 - 108.0 MHz)
        if new_freq < 87.0:
            new_freq = 87.0
        elif new_freq > 108.0:
            new_freq = 108.0
        
        old_freq = self.current_freq
        self.current_freq = new_freq
        
        # UI 즉시 업데이트
        self.freq_display.update_frequency(self.current_freq)
        
        # 하드웨어 설정
        self.set_freq_hardware(new_freq)
    
    def set_freq_hardware(self, frequency):
        """하드웨어에 주파수 설정"""
        if self.fm is None:
            return
        
        try:
            self.fm.set_channel(frequency)
            # 실제 설정된 주파수 확인
            actual_freq = self.fm.get_channel()
            if abs(actual_freq - frequency) > 0.01:
                self.current_freq = actual_freq
                self.freq_display.update_frequency(actual_freq)
        except Exception as e:
            print(f"Hardware frequency change failed: {e}")
    
    def update_from_hardware(self):
        """하드웨어에서 현재 상태 읽어와서 UI 업데이트"""
        if self.fm is None:
            return
        
        try:
            # 주파수 업데이트
            channel = self.fm.get_channel()
            if abs(channel - self.current_freq) > 0.01:
                self.current_freq = channel
                self.freq_display.update_frequency(self.current_freq)
            
            # 볼륨 업데이트
            volume = self.fm.get_volume()
            if volume != self.volume:
                self.volume = volume
                self.vol_value.setText(str(self.volume))
                self.volume_slider.setValue(self.volume)
            
            # 뮤트 상태 업데이트
            muted = self.fm.get_mute()
            if muted != self.is_muted:
                self.is_muted = muted
                self.update_mute_state()
            
        except Exception as e:
            print(f"Hardware state update failed: {e}")
    
    def on_volume_changed(self, value):
        """볼륨 슬라이더 변경"""
        if not self.is_powered:
            return
        
        self.volume = value
        self.vol_value.setText(str(value))
        
        # 오디오 매니저를 통한 부드러운 볼륨 변경
        if self.audio_manager:
            success = self.audio_manager.set_volume_smooth(value)
            if not success:
                print("Failed to set volume smoothly, trying direct method")
                try:
                    self.fm.set_volume(value)
                except Exception as e:
                    print(f"Hardware volume change failed: {e}")
        else:
            # 기존 방식 (오디오 매니저 없을 때)
            try:
                self.fm.set_volume(value)
            except Exception as e:
                print(f"Hardware volume change failed: {e}")
        
        # 뮤트 상태이면 자동으로 해제
        if self.is_muted and value > 0:
            self.is_muted = False
            self.update_mute_state()
            if self.audio_manager:
                self.audio_manager.soft_mute(False)
            else:
                try:
                    self.fm.set_mute(False)
                except Exception as e:
                    print(f"Hardware unmute failed: {e}")
    
    def toggle_power(self):
        """파워 토글"""
        if self.fm is None:
            print("Hardware not initialized")
            return
            
        old_powered = self.is_powered
        
        try:
            if self.is_powered:
                # 파워 오프 (오디오 매니저 사용)
                print("Turning power OFF")
                self.is_powered = False
                if self.audio_manager:
                    success = self.audio_manager.power_off_sequence()
                    if not success:
                        # 기존 방식으로 fallback
                        self.fm.set_power(False)
                else:
                    # 기존 방식
                    self.fm.set_power(False)
                    
            elif self.is_recording:
                # 레코딩 중이면 레코딩 중지
                print("Stopping recording")
                self.is_recording = False
                if self.audio_manager:
                    success = self.audio_manager.recording_stop_sequence()
                    if not success:
                        self.fm.set_recording(False)
                else:
                    self.fm.set_recording(False)
            else:
                # 파워 온 (오디오 매니저 사용)
                print("Turning power ON")
                self.is_powered = True
                if self.audio_manager:
                    success = self.audio_manager.power_on_sequence()
                    if not success:
                        # 기존 방식으로 fallback
                        self.fm.set_power(True)
                        import time
                        time.sleep(0.2)
                        self.fm.set_volume(6)
                        self.reset_hardware()
                else:
                    # 기존 방식
                    self.fm.set_power(True)
                    import time
                    time.sleep(0.2)
                    self.fm.set_volume(6)
                    self.reset_hardware()
            
            print(f"Power state changed: powered={self.is_powered}, recording={self.is_recording}")
            self.update_power_state()
            
            # 파워 오프 시 레코딩 중지
            if not self.is_powered and self.is_recording:
                self.toggle_record()
                
        except Exception as e:
            print(f"Power toggle failed: {e}")
            # 실패 시 이전 상태로 복원
            self.is_powered = old_powered
            self.update_power_state()
    
    def reset_hardware(self):
        """하드웨어 리셋"""
        if self.fm is None:
            return
            
        try:
            # 현재 주파수 설정
            self.fm.set_channel(self.current_freq)
            
            # 볼륨 업데이트
            self.fm.set_volume(self.volume)
            
            # 뮤트 해제
            self.is_muted = False
            self.fm.set_mute(False)
            self.update_mute_state()
            
        except Exception as e:
            print(f"Hardware reset failed: {e}")
    
    def toggle_mute(self):
        """뮤트 토글"""
        if not self.is_powered:
            return
        
        old_muted = self.is_muted
        self.is_muted = not self.is_muted
        
        # 오디오 매니저를 통한 부드러운 뮤트/언뮤트
        if self.audio_manager:
            success = self.audio_manager.soft_mute(self.is_muted)
            if not success:
                # 기존 방식으로 fallback
                try:
                    self.fm.set_mute(self.is_muted)
                except Exception as e:
                    print(f"Hardware mute toggle failed: {e}")
                    self.is_muted = old_muted
        else:
            # 기존 방식
            try:
                self.fm.set_mute(self.is_muted)
            except Exception as e:
                print(f"Hardware mute toggle failed: {e}")
                self.is_muted = old_muted
        
        self.update_mute_state()
    
    def toggle_record(self):
        """레코드 토글"""
        if not self.is_powered:
            return
        
        old_recording = self.is_recording
        self.is_recording = not self.is_recording
        
        # 오디오 매니저를 통한 부드러운 레코딩 시작/중지
        if self.audio_manager:
            if self.is_recording:
                success = self.audio_manager.recording_start_sequence()
            else:
                success = self.audio_manager.recording_stop_sequence()
            
            if not success:
                # 기존 방식으로 fallback
                try:
                    if self.is_recording:
                        self.fm.set_recording(True)
                        import time
                        time.sleep(0.2)
                        self.fm.set_volume(15)
                        self.reset_hardware()
                    else:
                        self.fm.set_recording(False)
                except Exception as e:
                    print(f"Hardware recording toggle failed: {e}")
                    self.is_recording = old_recording
        else:
            # 기존 방식
            try:
                if self.is_recording:
                    self.fm.set_recording(True)
                    import time
                    time.sleep(0.2)
                    self.fm.set_volume(15)
                    self.reset_hardware()
                else:
                    self.fm.set_recording(False)
            except Exception as e:
                print(f"Hardware recording toggle failed: {e}")
                self.is_recording = old_recording
        
        self.update_record_state()
    
    def update_power_state(self):
        """파워 상태 업데이트"""
        if self.is_powered:
            self.power_btn.setText(self.language_manager.get_text('power_on'))
            self.power_btn.setProperty("data-state", "on")
        else:
            self.power_btn.setText(self.language_manager.get_text('power_off'))
            self.power_btn.setProperty("data-state", "off")
        
        # 스타일 다시 적용
        self.power_btn.style().unpolish(self.power_btn)
        self.power_btn.style().polish(self.power_btn)
        
        # 다른 컨트롤들 활성화/비활성화
        enabled = self.is_powered
        for btn in [self.btn_freq_up_big, self.btn_freq_up_small, 
                   self.btn_freq_down_big, self.btn_freq_down_small,
                   self.scan_up_btn, self.scan_down_btn,
                   self.mute_btn, self.record_btn, self.volume_slider]:
            btn.setEnabled(enabled)
    
    def update_mute_state(self):
        """뮤트 상태 업데이트"""
        if self.is_muted:
            self.mute_btn.setText(self.language_manager.get_text('unmute'))
            self.mute_btn.setProperty("data-state", "active")
        else:
            self.mute_btn.setText(self.language_manager.get_text('mute'))
            self.mute_btn.setProperty("data-state", "")
        
        # 스타일 다시 적용
        self.mute_btn.style().unpolish(self.mute_btn)
        self.mute_btn.style().polish(self.mute_btn)
    
    def update_record_state(self):
        """레코드 상태 업데이트"""
        if self.is_recording:
            self.record_btn.setText(self.language_manager.get_text('stop_recording'))
            self.record_btn.setProperty("data-state", "recording")
            self.record_timer.start(800)  # 800ms 간격으로 깜빡임
        else:
            self.record_btn.setText(self.language_manager.get_text('record'))
            self.record_btn.setProperty("data-state", "")
            self.record_timer.stop()
        
        # 스타일 다시 적용
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
    
    def toggle_record_indicator(self):
        """레코딩 깜빡임 효과"""
        if self.is_recording:
            current_style = self.record_btn.styleSheet()
            if "background-color: #7f1d1d" in current_style:
                self.record_btn.setStyleSheet(current_style.replace("#7f1d1d", "#dc2626"))
            else:
                self.record_btn.setStyleSheet(current_style + "background-color: #7f1d1d;")
    
    def change_device(self):
        """기기 변경"""
        # 현재 연결 해제
        if self.fm is not None:
            try:
                if self.is_powered:
                    if self.audio_manager:
                        self.audio_manager.power_off_sequence()
                    else:
                        self.fm.set_power(False)
                if self.is_recording:
                    if self.audio_manager:
                        self.audio_manager.recording_stop_sequence()
                    else:
                        self.fm.set_recording(False)
            except:
                pass
            
            # 오디오 매니저 정리
            if self.audio_manager:
                self.audio_manager.cleanup()
                self.audio_manager = None
            
            self.fm = None
        
        # 새 기기 선택
        dialog = DeviceSelectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.selected_device = dialog.selected_device
            self.init_hardware()
            self.update_device_info()
            
            # 상태 초기화
            self.is_powered = False
            self.is_recording = False
            self.is_muted = False
            self.current_freq = 88.5
            self.volume = 8
            
            # GUI 업데이트
            self.freq_display.update_frequency(self.current_freq)
            self.vol_value.setText(str(self.volume))
            self.volume_slider.setValue(self.volume)
            self.update_power_state()
            self.update_mute_state()
            self.update_record_state()
            
            # 하드웨어가 있으면 초기 상태 업데이트
            if self.fm is not None:
                self.update_from_hardware()
    
    def update_device_info(self):
        """기기 정보 업데이트"""
        device_status = "🟢 Hardware Connected"
        # besfm의 get_device_name 사용
        device_name = besfm.BesFM.get_device_name(self.selected_device.idProduct)
        device_info = f"{device_name}"
        self.device_status_label.setStyleSheet("color: #059669;")
        
        self.device_status_label.setText(device_status)
        self.device_info_label.setText(device_info)
    
    def update_signal_strength(self):
        """신호 강도 업데이트"""
        if self.fm is not None and self.is_powered:
            try:
                status = self.fm.get_status()
                if 'strength' in status:
                    strength = status['strength']
                    self.signal_strength.update_signal(strength)
            except Exception as e:
                print(f"Signal strength update failed: {e}")
    
    def recall_preset(self, index):
        """프리셋 호출"""
        if not self.is_powered:
            return
            
        if 0 <= index < len(self.presets) and self.presets[index] is not None:
            freq = self.presets[index]
            old_freq = self.current_freq
            self.current_freq = freq
            self.freq_display.update_frequency(freq)
            
            # 하드웨어에 설정
            if self.fm is not None:
                try:
                    self.fm.set_channel(freq)
                    
                    # 실제 설정된 주파수 확인
                    actual_freq = self.fm.get_channel()
                    self.current_freq = actual_freq
                    self.freq_display.update_frequency(actual_freq)
                        
                except Exception as e:
                    print(f"Preset recall failed: {e}")
                    self.current_freq = old_freq
                    self.freq_display.update_frequency(old_freq)
    
    def save_preset_menu(self, index):
        """프리셋 저장"""
        if not self.is_powered:
            return
            
        self.presets[index] = self.current_freq
        self.preset_widget.update_presets(self.presets)
        self.save_settings()
    
    def scan_up(self):
        """위쪽 주파수 스캔"""
        if not self.is_powered or self.fm is None:
            print(f"Scan up blocked: powered={self.is_powered}, fm_available={self.fm is not None}")
            return
        
        print(f"Starting scan up from {self.current_freq:.1f} MHz")
        
        try:
            # 현재 주파수 저장
            start_freq = self.current_freq
            max_attempts = 10  # 안전장치: 최대 10번 시도
            
            for attempt in range(max_attempts):
                print(f"Scan up attempt {attempt + 1}/{max_attempts}")
                
                # 스캔 실행
                self.fm.seek_up()
                
                # 점진적으로 더 오래 대기
                import time
                wait_time = min(0.5 + (attempt * 0.2), 2.0)
                time.sleep(wait_time)
                
                # 새 주파수 읽기
                actual_freq = self.fm.get_channel()
                print(f"Scan up attempt {attempt + 1} result: {actual_freq:.1f} MHz")
                
                # 주파수가 실제로 변경되었는지 확인
                if abs(actual_freq - start_freq) > 0.05:
                    print(f"✅ Frequency successfully changed from {start_freq:.1f} to {actual_freq:.1f} MHz")
                    
                    # 주파수 업데이트
                    self.current_freq = actual_freq
                    self.freq_display.update_frequency(actual_freq)
                    
                    return  # 성공적으로 변경되었으므로 종료
                else:
                    print(f"❌ No frequency change in attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        print("🔄 Retrying scan with longer wait time...")
                        time.sleep(0.1)  # 재시도 전 잠시 대기
                    else:
                        print(f"⚠️ Maximum attempts ({max_attempts}) reached for scan up")
                        
        except Exception as e:
            print(f"Scan up failed: {e}")
    
    def scan_down(self):
        """아래쪽 주파수 스캔"""
        if not self.is_powered or self.fm is None:
            print(f"Scan down blocked: powered={self.is_powered}, fm_available={self.fm is not None}")
            return
        
        print(f"Starting scan down from {self.current_freq:.1f} MHz")
        
        try:
            # 현재 주파수 저장
            start_freq = self.current_freq
            max_attempts = 10  # 안전장치: 최대 10번 시도
            
            for attempt in range(max_attempts):
                print(f"Scan down attempt {attempt + 1}/{max_attempts}")
                
                # 스캔 실행
                self.fm.seek_down()
                
                # 점진적으로 더 오래 대기
                import time
                wait_time = min(0.5 + (attempt * 0.2), 2.0)
                time.sleep(wait_time)
                
                # 새 주파수 읽기
                actual_freq = self.fm.get_channel()
                print(f"Scan down attempt {attempt + 1} result: {actual_freq:.1f} MHz")
                
                # 주파수가 실제로 변경되었는지 확인
                if abs(actual_freq - start_freq) > 0.05:
                    print(f"✅ Frequency successfully changed from {start_freq:.1f} to {actual_freq:.1f} MHz")
                    
                    # 주파수 업데이트
                    self.current_freq = actual_freq
                    self.freq_display.update_frequency(actual_freq)
                    
                    return  # 성공적으로 변경되었으므로 종료
                else:
                    print(f"❌ No frequency change in attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        print("🔄 Retrying scan with longer wait time...")
                        time.sleep(0.1)  # 재시도 전 잠시 대기
                    else:
                        print(f"⚠️ Maximum attempts ({max_attempts}) reached for scan down")
                        
        except Exception as e:
            print(f"Scan down failed: {e}")
    
    def toggle_rds(self):
        """RDS 토글"""
        if not self.is_powered:
            return
        
        if self.fm is not None:
            try:
                current_rds = self.fm.get_rds()
                self.fm.set_rds(not current_rds)
                self.rds_enabled = not current_rds
                self.update_rds_button()
                
                if self.rds_enabled:
                    self.rds_timer.start(2000)  # 2초마다 RDS 체크
                else:
                    self.rds_timer.stop()
                    self.rds_station.setText(self.language_manager.get_text('rds_disabled'))
                    self.rds_text.setText("")
                    
            except Exception as e:
                print(f"RDS toggle failed: {e}")
    
    def update_rds_button(self):
        """RDS 버튼 상태 업데이트"""
        if self.rds_enabled:
            self.rds_btn.setText(self.language_manager.get_text('disable_rds'))
            self.rds_btn.setProperty("data-state", "active")
        else:
            self.rds_btn.setText(self.language_manager.get_text('enable_rds'))
            self.rds_btn.setProperty("data-state", "")
        
        self.rds_btn.style().unpolish(self.rds_btn)
        self.rds_btn.style().polish(self.rds_btn)
    
    def check_rds_data(self):
        """RDS 데이터 정기적 체크"""
        if self.fm is not None and self.rds_enabled:
            try:
                status = self.fm.get_status()
                if status.get('type') == 'rds':
                    rds_data = status.get('data', b'')
                    if rds_data:
                        self.parse_rds_data(rds_data)
            except Exception as e:
                print(f"RDS data check failed: {e}")
    
    def parse_rds_data(self, rds_data):
        """RDS 데이터 파싱 및 표시"""
        try:
            # 간단한 RDS 파싱
            if len(rds_data) >= 8:
                # PS 이름 (Program Service name)
                ps_name = rds_data[2:6].decode('ascii', errors='ignore').strip()
                
                if ps_name:
                    self.rds_station.setText(f"Station: {ps_name}")
                
                # RT (Radio Text) - 간단한 텍스트 추출
                if len(rds_data) > 6:
                    radio_text = rds_data[6:].decode('ascii', errors='ignore').strip()
                    if radio_text:
                        self.rds_text.setText(radio_text)
                        
        except Exception as e:
            print(f"RDS parsing failed: {e}")
    
    def show_settings(self):
        """설정 다이얼로그 표시"""
        # 간단한 설정 다이얼로그를 위해 메시지박스 사용
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, 
                              self.language_manager.get_text('settings'),
                              self.language_manager.get_text('settings_coming_soon'))
    
    def closeEvent(self, event):
        """애플리케이션 종료시 설정 저장"""
        self.save_settings()
        
        # 하드웨어 정리
        if self.fm is not None:
            try:
                if self.is_powered:
                    if self.audio_manager:
                        self.audio_manager.power_off_sequence()
                    else:
                        self.fm.set_power(False)
                if self.is_recording:
                    if self.audio_manager:
                        self.audio_manager.recording_stop_sequence()
                    else:
                        self.fm.set_recording(False)
            except:
                pass
        
        # 오디오 매니저 정리
        if self.audio_manager:
            self.audio_manager.cleanup()
        
        # 타이머 정리
        if hasattr(self, 'rds_timer'):
            self.rds_timer.stop()
        if hasattr(self, 'signal_timer'):
            self.signal_timer.stop()
        if hasattr(self, 'record_timer'):
            self.record_timer.stop()
        
        event.accept()
