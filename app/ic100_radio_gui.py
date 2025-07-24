import sys
import time
import besfm
import json
import os

from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, 
                               QSlider, QHBoxLayout, QVBoxLayout,
                               QFrame, QDialog, 
                               QListWidget, QListWidgetItem, QMessageBox,
                               QGroupBox, QTextEdit, QProgressDialog, QComboBox,
                               QCheckBox, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, QTimer, QThread, QObject, Signal

# 오디오 매니저 import
from audio_manager import AudioManager

class DeviceSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_device = None
        self.available_devices = []
        self.init_ui()
        self.scan_devices()
    
    def init_ui(self):
        self.setWindowTitle("FM Radio Device Selection")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
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
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #f8fafc;
                selection-background-color: #3b82f6;
                selection-color: white;
                font-size: 13px;
                color: #1f2937;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e2e8f0;
                color: #1f2937;
                background-color: transparent;
            }
            QListWidget::item:hover {
                background-color: #f1f5f9;
                color: #1f2937;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            QListWidget::item:selected:hover {
                background-color: #2563eb;
                color: white;
            }
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #f8fafc;
                font-family: "SF Mono", Consolas, monospace;
                font-size: 11px;
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 제목
        title = QLabel("Select FM Radio Device")
        title.setStyleSheet("font-size: 18px; font-weight: 600; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # 기기 목록 그룹
        devices_group = QGroupBox("Available Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.device_list = QListWidget()
        self.device_list.itemSelectionChanged.connect(self.on_selection_changed)
        devices_layout.addWidget(self.device_list)
        
        layout.addWidget(devices_group)
        
        # 기기 정보 그룹
        info_group = QGroupBox("Device Information")
        info_layout = QVBoxLayout(info_group)
        
        self.device_info = QTextEdit()
        self.device_info.setMaximumHeight(100)
        self.device_info.setReadOnly(True)
        self.device_info.setPlainText("Select a device to see detailed information...")
        info_layout.addWidget(self.device_info)
        
        layout.addWidget(info_group)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.clicked.connect(self.scan_devices)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_selected)
        self.connect_btn.setEnabled(False)
        button_layout.addWidget(self.connect_btn)
        
        layout.addLayout(button_layout)
    
    def scan_devices(self):
        """USB 기기 스캔"""
        self.device_list.clear()
        self.available_devices.clear()
        
        try:
            # besfm의 정적 메서드 사용
            device_infos = besfm.BesFM.find_all_devices()
            
            for device_info in device_infos:
                self.available_devices.append(device_info['device'])
                
                # 기기 이름 생성 (besfm의 get_device_name 사용)
                device_name = besfm.BesFM.get_device_name(device_info['product_id'])
                
                # 리스트 아이템 생성
                item = QListWidgetItem(device_name)
                item.setData(Qt.UserRole, len(self.available_devices) - 1)  # 기기 인덱스 저장
                self.device_list.addItem(item)
            
            if not self.available_devices:
                item = QListWidgetItem("No FM Radio devices found")
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                item.setData(Qt.UserRole, -1)
                self.device_list.addItem(item)
                self.device_info.setPlainText("No compatible FM Radio devices detected.\nSupported devices:\n- Samsung Galaxy devices with FM radio capability\n- Product IDs: 0xa054, 0xa059, 0xa05b")
            else:
                self.device_info.setPlainText(f"Found {len(self.available_devices)} compatible device(s).")
                
        except Exception as e:
            item = QListWidgetItem(f"Error scanning devices: {str(e)}")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.device_list.addItem(item)
            self.device_info.setPlainText(f"Error occurred while scanning USB devices:\n{str(e)}")
    
    def on_selection_changed(self):
        """선택된 기기 정보 업데이트"""
        current_item = self.device_list.currentItem()
        if current_item is None:
            self.connect_btn.setEnabled(False)
            return
        
        device_index = current_item.data(Qt.UserRole)
        if device_index == -1:  # "No devices found" 아이템
            self.connect_btn.setEnabled(False)
            return
        
        if 0 <= device_index < len(self.available_devices):
            device = self.available_devices[device_index]
            self.connect_btn.setEnabled(True)
            
            # 상세 정보 표시
            info = f"""Device Information:
Vendor ID: 0x{device.idVendor:04x}
Product ID: 0x{device.idProduct:04x}
Bus: {device.bus}
Address: {device.address}
USB Version: {device.bcdUSB}
Device Class: {device.bDeviceClass}
Serial Number: {device.serial_number if device.serial_number else 'N/A'}
Manufacturer: {device.manufacturer if device.manufacturer else 'Samsung'}
Product: {device.product if device.product else 'FM Radio'}"""
            
            self.device_info.setPlainText(info)
        else:
            self.connect_btn.setEnabled(False)
    
    def connect_selected(self):
        """선택된 기기에 연결"""
        current_item = self.device_list.currentItem()
        if current_item is None:
            return
        
        device_index = current_item.data(Qt.UserRole)
        if 0 <= device_index < len(self.available_devices):
            self.selected_device = self.available_devices[device_index]
            self.accept()
        else:
            QMessageBox.warning(self, "No Device", "Please select a valid FM Radio device.")
            return

class ModernRadioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_freq = 88.5
        self.volume = 8
        self.is_muted = False
        self.is_powered = False
        self.is_recording = False
        self.rds_enabled = False
        
        # 하드웨어 초기화
        self.fm = None
        self.selected_device = None
        self.audio_manager = None  # 오디오 매니저 추가
        
        # 프리셋 및 스테이션 데이터
        self.presets = [None] * 6  # 6개 프리셋
        self.settings_file = "radio_settings.json"
        
        # 언어 설정 (기본: 한글)
        self.is_korean = True
        
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
            error_msg = f"USB Device Access Permission Denied\n\n{str(e)}\n\n"
            error_msg += "Try running the application with:\n"
            error_msg += "sudo python3 ic100_radio_gui.py\n\n"
            error_msg += "Or use the provided start_radio.sh script."
            QMessageBox.critical(self, "Permission Error", error_msg)
            sys.exit(1)
        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            error_msg = f"Failed to initialize hardware:\n{str(e)}\n\n"
            error_msg += "Please check:\n"
            error_msg += "1. USB device is properly connected\n"
            error_msg += "2. No other applications are using the device\n"
            error_msg += "3. Device drivers are installed correctly"
            QMessageBox.critical(self, "Hardware Error", error_msg)
            sys.exit(1)
    
    def setup_animations(self):
        # 레코딩 애니메이션을 위한 타이머
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.toggle_record_indicator)
        self.record_blink = False
    
    def init_ui(self):
        self.setWindowTitle("FM Radio Enhanced")
        self.setFixedSize(600, 700)
        self.setStyleSheet(self.get_main_stylesheet())
        
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
        
        # 헤더
        self.create_header(scroll_layout)
        
        # 주파수 디스플레이
        self.create_frequency_display(scroll_layout)
        
        # 신호 강도 표시
        self.create_signal_strength_display(scroll_layout)
        
        # 주파수 컨트롤
        self.create_frequency_controls(scroll_layout)
        
        # 프리셋 및 스캔 섹션
        self.create_preset_section(scroll_layout)
        
        # 볼륨 컨트롤
        self.create_volume_section(scroll_layout)
        
        # RDS 섹션
        self.create_rds_section(scroll_layout)
        
        # 하단 컨트롤 버튼들
        self.create_bottom_controls(scroll_layout)
        
        # 설정 버튼
        self.create_settings_button(scroll_layout)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def create_header(self, parent_layout):
        # 헤더 컨테이너
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
        self.change_device_btn = QPushButton(self.get_text("기기 변경", "Change Device"))
        self.change_device_btn.setObjectName("device-btn")
        self.change_device_btn.clicked.connect(self.change_device)
        device_layout.addWidget(self.change_device_btn)
        
        header_layout.addLayout(device_layout)
        parent_layout.addLayout(header_layout)
    
    def create_frequency_display(self, parent_layout):
        # 주파수 디스플레이 컨테이너
        freq_container = QFrame()
        freq_container.setObjectName("freq-display")
        freq_layout = QVBoxLayout(freq_container)
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
        
        parent_layout.addWidget(freq_container)
    
    def create_signal_strength_display(self, parent_layout):
        """신호 강도 표시 섹션"""
        signal_layout = QHBoxLayout()
        
        # 신호 강도 바
        signal_label = QLabel(self.get_text("신호:", "Signal:"))
        signal_label.setObjectName("section-label")
        signal_layout.addWidget(signal_label)
        
        # 신호 강도 바
        self.signal_bars = []
        for i in range(5):
            bar = QLabel("▬")
            bar.setObjectName("signal-bar")
            bar.setProperty("active", False)
            self.signal_bars.append(bar)
            signal_layout.addWidget(bar)
        
        # RSSI 값 표시
        self.rssi_label = QLabel("0 dBm")
        self.rssi_label.setObjectName("rssi-value")
        signal_layout.addWidget(self.rssi_label)
        
        signal_layout.addStretch()
        parent_layout.addLayout(signal_layout)
    
    def create_frequency_controls(self, parent_layout):
        # 주파수 컨트롤 그룹
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
        """프리셋 및 스캔 섹션"""
        preset_group = QGroupBox(self.get_text("스테이션 프리셋 & 스캔", "Station Presets & Scan"))
        preset_layout = QVBoxLayout(preset_group)
        
        # 언어 변경 버튼
        language_layout = QHBoxLayout()
        language_layout.addStretch()
        self.language_btn = QPushButton(self.get_text("🌍 English", "🌍 한국어"))
        self.language_btn.setObjectName("secondary-btn")
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setFixedWidth(80)
        language_layout.addWidget(self.language_btn)
        preset_layout.addLayout(language_layout)
        
        # 프리셋 사용법 안내
        preset_info = QLabel(self.get_text("💾 클릭: 저장된 방송 불러오기  |  우클릭: 현재 주파수 저장", "💾 Click: Load station  |  Right-click: Save current frequency"))
        preset_info.setObjectName("preset-info")
        preset_info.setAlignment(Qt.AlignCenter)
        preset_layout.addWidget(preset_info)
        
        # 프리셋 버튼들을 2행 3열로 배치
        preset_buttons_container = QWidget()
        preset_buttons_layout = QGridLayout(preset_buttons_container)
        preset_buttons_layout.setSpacing(8)
        
        self.preset_buttons = []
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
        
        preset_layout.addWidget(preset_buttons_container)
        
        # 스캔 버튼들
        scan_layout = QHBoxLayout()
        
        # 스캔 다운 버튼
        self.scan_down_btn = QPushButton(self.get_text("스캔 ↓", "Scan ↓"))
        self.scan_down_btn.setObjectName("scan-btn")
        self.scan_down_btn.clicked.connect(self.scan_down)
        scan_layout.addWidget(self.scan_down_btn)
        
        # 스캔 업 버튼
        self.scan_up_btn = QPushButton(self.get_text("스캔 ↑", "Scan ↑"))
        self.scan_up_btn.setObjectName("scan-btn")
        self.scan_up_btn.clicked.connect(self.scan_up)
        scan_layout.addWidget(self.scan_up_btn)
        
        preset_layout.addLayout(scan_layout)
        parent_layout.addWidget(preset_group)
        
        # 프리셋 업데이트
        self.update_preset_buttons()
    
    def create_volume_section(self, parent_layout):
        # 볼륨 섹션
        volume_layout = QVBoxLayout()
        volume_layout.setSpacing(8)
        
        # 볼륨 레이블과 값
        vol_header = QHBoxLayout()
        vol_label = QLabel(self.get_text("볼륨", "Volume"))
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
        """RDS 정보 섹션"""
        rds_group = QGroupBox(self.get_text("RDS 정보", "RDS Information"))
        rds_layout = QVBoxLayout(rds_group)
        
        # RDS 스테이션 이름
        self.rds_station = QLabel(self.get_text("RDS 데이터 없음", "No RDS Data"))
        self.rds_station.setObjectName("rds-station")
        rds_layout.addWidget(self.rds_station)
        
        # RDS 텍스트
        self.rds_text = QLabel("")
        self.rds_text.setObjectName("rds-text")
        self.rds_text.setWordWrap(True)
        rds_layout.addWidget(self.rds_text)
        
        # RDS 활성화 버튼
        self.rds_btn = QPushButton(self.get_text("RDS 활성화", "Enable RDS"))
        self.rds_btn.setObjectName("secondary-btn")
        self.rds_btn.clicked.connect(self.toggle_rds)
        rds_layout.addWidget(self.rds_btn)
        
        parent_layout.addWidget(rds_group)
    
    def create_bottom_controls(self, parent_layout):
        # 하단 컨트롤 버튼들
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        # 파워 버튼
        self.power_btn = QPushButton(self.get_text("전원", "Power"))
        self.power_btn.setObjectName("power-btn")
        self.power_btn.clicked.connect(self.toggle_power)
        controls_layout.addWidget(self.power_btn)
        
        # 뮤트 버튼
        self.mute_btn = QPushButton(self.get_text("음소거", "Mute"))
        self.mute_btn.setObjectName("secondary-btn")
        self.mute_btn.clicked.connect(self.toggle_mute)
        controls_layout.addWidget(self.mute_btn)
        
        # 레코드 버튼
        self.record_btn = QPushButton(self.get_text("녹음", "Record"))
        self.record_btn.setObjectName("record-btn")
        self.record_btn.clicked.connect(self.toggle_record)
        controls_layout.addWidget(self.record_btn)
        
        parent_layout.addLayout(controls_layout)
        
        # 초기 상태 업데이트
        self.update_power_state()
    
    def create_settings_button(self, parent_layout):
        """설정 버튼"""
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        
        self.settings_btn = QPushButton(self.get_text("설정", "Settings"))
        self.settings_btn.setObjectName("secondary-btn")
        self.settings_btn.clicked.connect(self.show_settings)
        settings_layout.addWidget(self.settings_btn)
        
        parent_layout.addLayout(settings_layout)
    
    def get_text(self, korean_text, english_text):
        """언어 설정에 따른 텍스트 반환"""
        return korean_text if self.is_korean else english_text
    
    def toggle_language(self):
        """언어 토글"""
        self.is_korean = not self.is_korean
        self.update_all_texts()
        
        # 설정 저장
        self.save_settings()
    
    def update_all_texts(self):
        """모든 UI 텍스트 업데이트"""
        # 언어 버튼 텍스트 업데이트
        self.language_btn.setText(self.get_text("🌍 English", "🌍 한국어"))
        
        # 그룹박스 제목 업데이트
        preset_group = self.findChild(QGroupBox)
        if preset_group:
            preset_group.setTitle(self.get_text("스테이션 프리셋 & 스캔", "Station Presets & Scan"))
        
        # 스캔 버튼 텍스트 업데이트
        self.scan_down_btn.setText(self.get_text("스캔 ↓", "Scan ↓"))
        self.scan_up_btn.setText(self.get_text("스캔 ↑", "Scan ↑"))
        
        # 안내 텍스트 업데이트
        preset_info = self.findChild(QLabel, "preset-info")
        if preset_info:
            preset_info.setText(self.get_text("💾 클릭: 저장된 방송 불러오기  |  우클릭: 현재 주파수 저장", "💾 Click: Load station  |  Right-click: Save current frequency"))
        
        # 프리셋 버튼 업데이트
        self.update_preset_buttons()
        
        # 다른 컨트롤 버튼들 업데이트
        if hasattr(self, 'power_btn'):
            self.power_btn.setText(self.get_text("전원" if not self.is_powered else "켜짐", "Power" if not self.is_powered else "ON"))
        if hasattr(self, 'mute_btn'):
            self.mute_btn.setText(self.get_text("음소거 해제" if self.is_muted else "음소거", "Unmute" if self.is_muted else "Mute"))
        if hasattr(self, 'record_btn'):
            self.record_btn.setText(self.get_text("녹음 중지" if self.is_recording else "녹음", "Stop" if self.is_recording else "Record"))
        if hasattr(self, 'rds_btn'):
            self.rds_btn.setText(self.get_text("RDS 비활성화" if self.rds_enabled else "RDS 활성화", "Disable RDS" if self.rds_enabled else "Enable RDS"))
        if hasattr(self, 'settings_btn'):
            self.settings_btn.setText(self.get_text("설정", "Settings"))
        if hasattr(self, 'change_device_btn'):
            self.change_device_btn.setText(self.get_text("기기 변경", "Change Device"))
    
    def get_preset_tooltip(self, index):
        """프리셋 버튼 툴팁 생성"""
        if index < len(self.presets) and self.presets[index] is not None:
            return self.get_text(
                f"📻 프리셋 {index+1}: {self.presets[index]:.1f} MHz\n클릭: 이 방송국 불러오기\n우클릭: 현재 주파수 저장 ({self.current_freq:.1f} MHz)",
                f"📻 Preset {index+1}: {self.presets[index]:.1f} MHz\nLeft-click: Load this station\nRight-click: Save current frequency ({self.current_freq:.1f} MHz)"
            )
        else:
            return self.get_text(
                f"💾 빈 프리셋 {index+1}\n우클릭: 현재 주파수 저장 ({self.current_freq:.1f} MHz)",
                f"💾 Empty Preset {index+1}\nRight-click: Save current frequency ({self.current_freq:.1f} MHz)"
            )
    
    def get_main_stylesheet(self):
        return """
        /* shadcn/ui 스타일 기반 */
        QWidget {
            background-color: #ffffff;
            color: #09090b;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
        }
        
        QScrollArea {
            border: none;
            background-color: #ffffff;
        }
        
        QScrollBar:vertical {
            background-color: #f1f5f9;
            width: 8px;
            border-radius: 4px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #cbd5e1;
            border-radius: 4px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #94a3b8;
        }
        
        #header {
            font-size: 24px;
            font-weight: 600;
            color: #09090b;
            margin-bottom: 8px;
        }
        
        #device-status {
            font-size: 11px;
            font-weight: 500;
            color: #059669;
        }
        
        #device-info {
            font-size: 10px;
            color: #6b7280;
            font-family: "SF Mono", Consolas, monospace;
        }
        
        #device-btn {
            background-color: #f1f5f9;
            color: #374151;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 10px;
            font-weight: 500;
            max-width: 100px;
        }
        
        #device-btn:hover {
            background-color: #e5e7eb;
        }
        
        #freq-display {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
        }
        
        #freq-number {
            font-size: 48px;
            font-weight: 700;
            color: #0f172a;
            font-family: "SF Mono", Consolas, monospace;
        }
        
        #freq-unit {
            font-size: 14px;
            color: #64748b;
            font-weight: 500;
        }
        
        #freq-btn {
            background-color: #09090b;
            color: #fafafa;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 60px;
        }
        
        #freq-btn:hover {
            background-color: #18181b;
        }
        
        #freq-btn:pressed {
            background-color: #27272a;
        }
        
        #freq-btn-small {
            background-color: #f1f5f9;
            color: #0f172a;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 500;
            min-width: 50px;
        }
        
        #freq-btn-small:hover {
            background-color: #e2e8f0;
        }
        
        #freq-btn-small:pressed {
            background-color: #cbd5e1;
        }
        
        #section-label {
            font-weight: 500;
            color: #374151;
        }
        
        #volume-value {
            font-weight: 600;
            color: #09090b;
            font-size: 16px;
        }
        
        #volume-slider {
            height: 20px;
        }
        
        #volume-slider::groove:horizontal {
            border: none;
            height: 4px;
            background-color: #e2e8f0;
            border-radius: 2px;
        }
        
        #volume-slider::handle:horizontal {
            background-color: #09090b;
            border: none;
            width: 16px;
            height: 16px;
            border-radius: 8px;
            margin: -6px 0;
        }
        
        #volume-slider::handle:horizontal:hover {
            background-color: #18181b;
        }
        
        #power-btn {
            background-color: #22c55e;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            min-width: 80px;
        }
        
        #power-btn:hover {
            background-color: #16a34a;
        }
        
        #power-btn:pressed {
            background-color: #15803d;
        }
        
        #power-btn[data-state="off"] {
            background-color: #6b7280;
        }
        
        #power-btn[data-state="off"]:hover {
            background-color: #4b5563;
        }
        
        #secondary-btn {
            background-color: #f8fafc;
            color: #374151;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            min-width: 80px;
        }
        
        #secondary-btn:hover {
            background-color: #f1f5f9;
        }
        
        #secondary-btn:pressed {
            background-color: #e2e8f0;
        }
        
        #secondary-btn[data-state="active"] {
            background-color: #fbbf24;
            color: #ffffff;
            border-color: #f59e0b;
        }
        
        #secondary-btn[data-state="active"]:hover {
            background-color: #f59e0b;
        }
        
        #record-btn {
            background-color: #ef4444;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            min-width: 80px;
        }
        
        #record-btn:hover {
            background-color: #dc2626;
        }
        
        #record-btn:pressed {
            background-color: #b91c1c;
        }
        
        #record-btn[data-state="recording"] {
            background-color: #dc2626;
            animation: pulse 1s infinite;
        }
        
        /* 새로운 스타일들 */
        #rds-station {
            font-size: 16px;
            font-weight: 600;
            color: #059669;
            padding: 4px;
        }
        
        #rds-text {
            font-size: 12px;
            color: #6b7280;
            padding: 4px;
            background-color: #f8fafc;
            border-radius: 4px;
            min-height: 40px;
        }
        
        #preset-btn {
            background-color: #e5e7eb;
            color: #374151;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 500;
            min-width: 80px;
            min-height: 60px;
            font-size: 12px;
        }
        
        #preset-btn:hover {
            background-color: #d1d5db;
        }
        
        #preset-btn[data-state="saved"] {
            background-color: #3b82f6;
            color: white;
            border-color: #2563eb;
        }
        
        #preset-info {
            font-size: 11px;
            color: #6b7280;
            font-style: italic;
            padding: 4px;
            background-color: #f8fafc;
            border-radius: 4px;
            margin-bottom: 8px;
        }
        
        #signal-bar {
            font-size: 12px;
            color: #e5e7eb;
            margin: 0 1px;
        }
        
        #signal-bar[active="true"] {
            color: #22c55e;
        }
        
        #rssi-value {
            font-size: 11px;
            color: #6b7280;
            font-family: "SF Mono", Consolas, monospace;
            margin-left: 8px;
        }
        
        #scan-btn {
            background-color: #f59e0b;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 80px;
        }
        
        #scan-btn:hover {
            background-color: #d97706;
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
        """
    
    def change_frequency(self, step):
        if not self.is_powered or self.fm is None:
            print(f"Cannot change frequency: powered={self.is_powered}, fm_device={self.fm is not None}")
            return
        
        old_freq = self.current_freq
        new_freq = self.current_freq + step
        
        # 주파수 범위 검증 (88.0 ~ 108.0 MHz)
        new_freq = max(88.0, min(108.0, new_freq))
        
        if new_freq == self.current_freq:
            print(f"Frequency already at limit: {self.current_freq:.1f} MHz")
            return
            
        print(f"Changing frequency from {old_freq:.1f} to {new_freq:.1f} MHz")
        
        # 하드웨어에 실제 주파수 변경
        try:
            # 주파수 설정 (오디오 매니저 없이 단순하게)
            success = self.set_freq_hardware(new_freq)
            
            if success:
                self.current_freq = new_freq
                self.freq_label.setText(f"{self.current_freq:.1f}")
                
                # UI 강제 업데이트
                self.freq_label.repaint()
                QApplication.processEvents()
                
                print(f"Frequency successfully changed to {self.current_freq:.1f} MHz")
            else:
                print(f"Failed to set frequency to {new_freq:.1f} MHz")
                # 실패 시 이전 값 유지
                self.freq_label.setText(f"{self.current_freq:.1f}")
                
        except Exception as e:
            print(f"Hardware frequency change failed: {e}")
            # 하드웨어 실패 시 이전 값으로 복원
            self.current_freq = old_freq
            self.freq_label.setText(f"{self.current_freq:.1f}")
    
    def set_freq_hardware(self, frequency):
        """하드웨어 주파수 설정"""
        try:
            if self.fm is None:
                print("FM device not available")
                return False
                
            # 주파수 범위 재검증
            if frequency < 88.0 or frequency > 108.0:
                print(f"Frequency {frequency:.1f} MHz out of range (88.0-108.0)")
                return False
                
            print(f"Setting hardware frequency to {frequency:.1f} MHz")
            
            # 하드웨어에 주파수 설정
            self.fm.set_channel(frequency)
            
            # 잠시 대기 후 실제 설정된 값 확인
            time.sleep(0.1)
            actual_freq = self.fm.get_channel()
            
            print(f"Hardware reports frequency as {actual_freq:.1f} MHz")
            
            # 설정된 주파수가 요청한 주파수와 비슷한지 확인 (0.2 MHz 오차 허용)
            if abs(actual_freq - frequency) <= 0.2:
                return True
            else:
                print(f"Frequency mismatch: requested {frequency:.1f}, got {actual_freq:.1f}")
                return False
                
        except Exception as e:
            print(f"Error setting hardware frequency: {e}")
            return False
    
    def update_from_hardware(self):
        """하드웨어에서 현재 상태 업데이트"""
        try:
            # 파워 상태 업데이트
            power_changed = self.is_powered != self.fm.get_power()
            record_changed = self.is_recording != self.fm.get_recording()
            
            self.is_powered = self.fm.get_power()
            self.is_recording = self.fm.get_recording()
            
            if power_changed or record_changed:
                self.update_power_state()
                self.update_record_state()
            
            if self.is_powered or self.is_recording:
                # 주파수 업데이트
                channel = self.fm.get_channel()
                self.current_freq = channel
                self.freq_label.setText(f"{channel:.1f}")
                
                # 볼륨 업데이트
                vol = self.fm.get_volume()
                if vol != self.volume:
                    self.volume = vol
                    self.vol_value.setText(str(vol))
                    self.volume_slider.setValue(vol)
                
                # 뮤트 상태 업데이트
                mute = self.fm.get_mute()
                if mute != self.is_muted:
                    self.is_muted = mute
                    self.update_mute_state()
                    
        except Exception as e:
            print(f"Hardware status update failed: {e}")
    
    def on_volume_changed(self, value):
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
                        time.sleep(0.2)
                        self.fm.set_volume(6)
                        self.reset_hardware()
                else:
                    # 기존 방식
                    self.fm.set_power(True)
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
            freq_val = int(self.current_freq * 100)
            self.fm.set_channel(freq_val / 100.0)
            
            # 볼륨 업데이트
            self.fm.set_volume(self.volume)
            
            # 뮤트 해제
            self.is_muted = False
            self.fm.set_mute(False)
            self.update_mute_state()
            
        except Exception as e:
            print(f"Hardware reset failed: {e}")
    
    def toggle_mute(self):
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
        if self.is_powered:
            self.power_btn.setText(self.get_text("켜짐", "ON"))
            self.power_btn.setProperty("data-state", "on")
        else:
            self.power_btn.setText(self.get_text("꺼짐", "OFF"))
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
        if self.is_muted:
            self.mute_btn.setText(self.get_text("음소거 해제", "Unmute"))
            self.mute_btn.setProperty("data-state", "active")
        else:
            self.mute_btn.setText(self.get_text("음소거", "Mute"))
            self.mute_btn.setProperty("data-state", "")
        
        # 스타일 다시 적용
        self.mute_btn.style().unpolish(self.mute_btn)
        self.mute_btn.style().polish(self.mute_btn)
    
    def update_record_state(self):
        if self.is_recording:
            self.record_btn.setText(self.get_text("녹음 중지", "Stop"))
            self.record_btn.setProperty("data-state", "recording")
            self.record_timer.start(800)  # 800ms 간격으로 깜빡임
        else:
            self.record_btn.setText(self.get_text("녹음", "Record"))
            self.record_btn.setProperty("data-state", "")
            self.record_timer.stop()
        
        # 스타일 다시 적용
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
    
    def toggle_record_indicator(self):
        # 레코딩 중 깜빡임 효과
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
            self.freq_label.setText(f"{self.current_freq:.1f}")
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

    # 새로운 기능 메서드들
    def load_settings(self):
        """설정 로드"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.presets = settings.get('presets', [None] * 6)
                    self.is_korean = settings.get('is_korean', True)  # 기본값: 한글
        except Exception as e:
            print(f"Settings load failed: {e}")
            self.presets = [None] * 6
            self.is_korean = True
    
    def save_settings(self):
        """설정 저장"""
        try:
            settings = {
                'presets': self.presets,
                'last_frequency': self.current_freq,
                'last_volume': self.volume,
                'is_korean': self.is_korean
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Settings save failed: {e}")
    
    def update_signal_strength(self):
        """신호 강도 업데이트"""
        if self.fm is not None and self.is_powered:
            try:
                status = self.fm.get_status()
                if 'strength' in status:
                    strength = status['strength']
                    self.rssi_label.setText(f"{strength} dBm")
                    
                    # 신호 바 업데이트 (0-100 범위를 5개 바로 변환)
                    bars_active = min(5, max(0, int(strength / 20)))
                    for i, bar in enumerate(self.signal_bars):
                        bar.setProperty("active", i < bars_active)
                        bar.style().unpolish(bar)
                        bar.style().polish(bar)
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
            self.freq_label.setText(f"{freq:.1f}")
            
            # UI 강제 업데이트
            self.freq_label.repaint()
            QApplication.processEvents()
            
            # 프리셋 로드 피드백
            btn = self.preset_buttons[index]
            original_text = btn.text()
            btn.setText(f"📻 {self.get_text('불러오는 중', 'Loading')}\n{freq:.1f}")
            btn.setStyleSheet("background-color: #f59e0b; color: white;")
            
            # 하드웨어에 설정 (단순하게)
            if self.fm is not None:
                try:
                    self.fm.set_channel(freq)
                    
                    # 실제 설정된 주파수 확인
                    actual_freq = self.fm.get_channel()
                    self.current_freq = actual_freq
                    self.freq_label.setText(f"{actual_freq:.1f}")
                    
                    # UI 강제 업데이트
                    self.freq_label.repaint()
                    QApplication.processEvents()
                    
                    # 성공 피드백
                    btn.setText(f"✅ {self.get_text('불러옴', 'Loaded')}\n{actual_freq:.1f}")
                    btn.setStyleSheet("background-color: #10b981; color: white;")
                        
                except Exception as e:
                    print(f"Preset recall failed: {e}")
                    self.current_freq = old_freq
                    self.freq_label.setText(f"{old_freq:.1f}")
                    
                    # 실패 피드백
                    btn.setText(f"❌ {self.get_text('실패', 'Failed')}\n{freq:.1f}")
                    btn.setStyleSheet("background-color: #ef4444; color: white;")
            
            # 1.5초 후 원래 상태로 복원
            QTimer.singleShot(1500, lambda: [
                btn.setText(original_text),
                btn.setStyleSheet(""),
                btn.style().unpolish(btn),
                btn.style().polish(btn)
            ])
    
    def save_preset_menu(self, index):
        """프리셋 저장 (우클릭 메뉴)"""
        if not self.is_powered:
            return
            
        self.presets[index] = self.current_freq
        self.update_preset_buttons()
        self.save_settings()
        
        # 사용자에게 명확한 피드백
        btn = self.preset_buttons[index]
        original_text = btn.text()
        btn.setText(f"✅ {self.get_text('저장됨!', 'Saved!')}\n{self.current_freq:.1f}")
        btn.setStyleSheet("background-color: #10b981; color: white;")
        
        # 2초 후 원래 상태로 복원
        QTimer.singleShot(2000, lambda: [
            btn.setText(original_text),
            btn.setStyleSheet(""),
            btn.style().unpolish(btn),
            btn.style().polish(btn)
        ])
    
    def update_preset_buttons(self):
        """프리셋 버튼 상태 업데이트"""
        for i, btn in enumerate(self.preset_buttons):
            if i < len(self.presets) and self.presets[i] is not None:
                # 저장된 주파수가 있으면 주파수 표시
                btn.setText(f"P{i+1}\n📻 {self.presets[i]:.1f}")
                btn.setProperty("data-state", "saved")
                btn.setToolTip(self.get_preset_tooltip(i))
            else:
                # 빈 슬롯이면 저장 안내 표시
                btn.setText(f"P{i+1}\n💾 {self.get_text('비어있음', 'Empty')}")
                btn.setProperty("data-state", "")
                btn.setToolTip(self.get_preset_tooltip(i))
            
            # 스타일 다시 적용
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
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
                
                # 스캔 실행 (USB 알림 대기 없이)
                self.fm.seek_up()
                
                # 점진적으로 더 오래 대기 (0.5초부터 시작, 매번 0.2초씩 증가, 최대 2.0초)
                import time
                wait_time = min(0.5 + (attempt * 0.2), 2.0)
                time.sleep(wait_time)
                
                # 새 주파수 읽기
                actual_freq = self.fm.get_channel()
                print(f"Scan up attempt {attempt + 1} result: {actual_freq:.1f} MHz (waited {wait_time:.1f}s)")
                
                # 주파수가 실제로 변경되었는지 확인
                if abs(actual_freq - start_freq) > 0.05:  # 0.05 MHz 이상 차이가 있으면 변경된 것
                    print(f"✅ Frequency successfully changed from {start_freq:.1f} to {actual_freq:.1f} MHz")
                    
                    # 주파수 업데이트
                    self.current_freq = actual_freq
                    self.freq_label.setText(f"{actual_freq:.1f}")
                    
                    # UI 강제 업데이트
                    self.freq_label.repaint()
                    QApplication.processEvents()
                    
                    return  # 성공적으로 변경되었으므로 종료
                else:
                    print(f"❌ No frequency change in attempt {attempt + 1}: {start_freq:.1f} -> {actual_freq:.1f}")
                    if attempt < max_attempts - 1:
                        print("🔄 Retrying scan with longer wait time...")
                        time.sleep(0.1)  # 재시도 전 잠시 대기
                    else:
                        print(f"⚠️ Maximum attempts ({max_attempts}) reached for scan up")
            
            # 최대 시도 횟수에 도달했지만 마지막 주파수라도 업데이트
            final_freq = self.fm.get_channel()
            if abs(final_freq - self.current_freq) > 0.01:  # 약간이라도 변경되었으면
                print(f"🔧 Updating to final frequency: {final_freq:.1f} MHz")
                self.current_freq = final_freq
                self.freq_label.setText(f"{final_freq:.1f}")
                self.freq_label.repaint()
                QApplication.processEvents()
                
        except Exception as e:
            print(f"Scan up failed: {e}")
            import traceback
            traceback.print_exc()
    
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
                
                # 스캔 실행 (USB 알림 대기 없이)
                self.fm.seek_down()
                
                # 점진적으로 더 오래 대기 (0.5초부터 시작, 매번 0.2초씩 증가, 최대 2.0초)
                import time
                wait_time = min(0.5 + (attempt * 0.2), 2.0)
                time.sleep(wait_time)
                
                # 새 주파수 읽기
                actual_freq = self.fm.get_channel()
                print(f"Scan down attempt {attempt + 1} result: {actual_freq:.1f} MHz (waited {wait_time:.1f}s)")
                
                # 주파수가 실제로 변경되었는지 확인
                if abs(actual_freq - start_freq) > 0.05:  # 0.05 MHz 이상 차이가 있으면 변경된 것
                    print(f"✅ Frequency successfully changed from {start_freq:.1f} to {actual_freq:.1f} MHz")
                    
                    # 주파수 업데이트
                    self.current_freq = actual_freq
                    self.freq_label.setText(f"{actual_freq:.1f}")
                    
                    # UI 강제 업데이트
                    self.freq_label.repaint()
                    QApplication.processEvents()
                    
                    return  # 성공적으로 변경되었으므로 종료
                else:
                    print(f"❌ No frequency change in attempt {attempt + 1}: {start_freq:.1f} -> {actual_freq:.1f}")
                    if attempt < max_attempts - 1:
                        print("🔄 Retrying scan with longer wait time...")
                        time.sleep(0.1)  # 재시도 전 잠시 대기
                    else:
                        print(f"⚠️ Maximum attempts ({max_attempts}) reached for scan down")
            
            # 최대 시도 횟수에 도달했지만 마지막 주파수라도 업데이트
            final_freq = self.fm.get_channel()
            if abs(final_freq - self.current_freq) > 0.01:  # 약간이라도 변경되었으면
                print(f"🔧 Updating to final frequency: {final_freq:.1f} MHz")
                self.current_freq = final_freq
                self.freq_label.setText(f"{final_freq:.1f}")
                self.freq_label.repaint()
                QApplication.processEvents()
                
        except Exception as e:
            print(f"Scan down failed: {e}")
            import traceback
            traceback.print_exc()
    
    
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
                    self.rds_station.setText(self.get_text("RDS 비활성화됨", "RDS Disabled"))
                    self.rds_text.setText("")
                    
            except Exception as e:
                print(f"RDS toggle failed: {e}")
    
    def update_rds_button(self):
        """RDS 버튼 상태 업데이트"""
        if self.rds_enabled:
            self.rds_btn.setText(self.get_text("RDS 비활성화", "Disable RDS"))
            self.rds_btn.setProperty("data-state", "active")
        else:
            self.rds_btn.setText(self.get_text("RDS 활성화", "Enable RDS"))
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
            # 간단한 RDS 파싱 (실제로는 더 복잡한 디코딩이 필요)
            if len(rds_data) >= 8:
                # PI 코드 (Program Identification)
                pi_code = rds_data[0:2]
                
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
        dialog = self.create_settings_dialog()
        if dialog.exec() == QDialog.Accepted:
            self.apply_settings_from_dialog(dialog)
    
    def create_settings_dialog(self):
        """설정 다이얼로그 생성"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.get_text("설정", "Settings"))
        dialog.setFixedSize(350, 400)
        dialog.setStyleSheet(self.get_main_stylesheet())
        
        layout = QVBoxLayout(dialog)
        
        # 주파수 대역 설정
        band_group = QGroupBox(self.get_text("주파수 대역", "Frequency Band"))
        band_layout = QVBoxLayout(band_group)
        
        self.band_combo = QComboBox()
        self.band_combo.addItems([
            "87.0 - 108.0 MHz (Worldwide)",
            "76.0 - 107.0 MHz (Japan)",
            "76.0 - 91.0 MHz (Japan narrow)",
            "64.0 - 76.0 MHz (Eastern Europe)"
        ])
        band_layout.addWidget(self.band_combo)
        layout.addWidget(band_group)
        
        # 채널 간격 설정
        spacing_group = QGroupBox(self.get_text("채널 간격", "Channel Spacing"))
        spacing_layout = QVBoxLayout(spacing_group)
        
        self.spacing_combo = QComboBox()
        self.spacing_combo.addItems(["200 kHz", "100 kHz", "50 kHz"])
        spacing_layout.addWidget(self.spacing_combo)
        layout.addWidget(spacing_group)
        
        # 모노/스테레오 설정
        audio_group = QGroupBox(self.get_text("오디오 설정", "Audio Settings"))
        audio_layout = QVBoxLayout(audio_group)
        
        self.mono_checkbox = QCheckBox(self.get_text("모노 강제", "Force Mono"))
        audio_layout.addWidget(self.mono_checkbox)
        layout.addWidget(audio_group)
        
        # 현재 설정 로드
        if self.fm is not None:
            try:
                current_band = self.fm.get_band()
                self.band_combo.setCurrentIndex(current_band)
                
                current_spacing = self.fm.get_channel_spacing()
                self.spacing_combo.setCurrentIndex(current_spacing)
                
                self.mono_checkbox.setChecked(self.fm.get_mono())
            except:
                pass
        
        # 버튼
        button_layout = QHBoxLayout()
        apply_btn = QPushButton(self.get_text("적용", "Apply"))
        apply_btn.setObjectName("secondary-btn")
        apply_btn.clicked.connect(lambda: self.apply_settings(dialog))
        cancel_btn = QPushButton(self.get_text("취소", "Cancel"))
        cancel_btn.setObjectName("secondary-btn")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(apply_btn)
        layout.addLayout(button_layout)
        
        return dialog
    
    def apply_settings(self, dialog):
        """설정 적용"""
        if self.fm is None:
            dialog.accept()
            return
            
        try:
            # 주파수 대역 설정
            band_index = self.band_combo.currentIndex()
            band_enum = [besfm.BesFM_Enums.BAND_87MHz_108MHz, 
                        besfm.BesFM_Enums.BAND_76MHz_107MHz,
                        besfm.BesFM_Enums.BAND_76MHz_91MHz,
                        besfm.BesFM_Enums.BAND_64MHz_76MHz][band_index]
            self.fm.set_band(band_enum)
            
            # 채널 간격 설정
            spacing_index = self.spacing_combo.currentIndex()
            spacing_enum = [besfm.BesFM_Enums.CHAN_SPACING_200KHz,
                           besfm.BesFM_Enums.CHAN_SPACING_100KHz,
                           besfm.BesFM_Enums.CHAN_SPACING_50KHz][spacing_index]
            self.fm.set_channel_spacing(spacing_enum)
            
            # 모노 설정
            self.fm.set_mono(self.mono_checkbox.isChecked())
            
            QMessageBox.information(dialog, "Settings", "Settings applied successfully!")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.warning(dialog, "Error", f"Failed to apply settings:\n{str(e)}")
    
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


# 라이브러리로 사용할 때를 위한 부분
# main.py에서 import 해서 사용합니다.
