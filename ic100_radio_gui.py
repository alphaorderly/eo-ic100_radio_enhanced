import sys
import time
import usb.core
import besfm
import json
import os
from threading import Thread

from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, 
                               QSlider, QGridLayout, QHBoxLayout, QVBoxLayout,
                               QFrame, QSizePolicy, QSpacerItem, QDialog, 
                               QListWidget, QListWidgetItem, QMessageBox,
                               QGroupBox, QTextEdit, QProgressDialog, QComboBox,
                               QCheckBox, QLineEdit, QDockWidget, QTabWidget,
                               QScrollArea, QSplitter)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QThread, QObject, Signal
from PySide6.QtGui import QFont, QAction

class StationScanner(QObject):
    station_found = Signal(float, int)  # frequency, strength
    scan_progress = Signal(float)  # current frequency
    scan_finished = Signal(list)  # list of found stations
    
    def __init__(self, fm_device):
        super().__init__()
        self.fm = fm_device
        self.should_stop = False
        
    def scan(self):
        """주파수 스캔 실행"""
        found_stations = []
        current_freq = 88.0
        
        while current_freq <= 108.0 and not self.should_stop:
            self.scan_progress.emit(current_freq)
            
            try:
                if self.fm is not None:
                    self.fm.set_channel(current_freq)
                    time.sleep(0.5)  # 안정화 대기
                    
                    status = self.fm.get_status()
                    if status.get('type') in ['tune', 'seek'] and status.get('success'):
                        strength = status.get('strength', 0)
                        if strength > 30:  # 신호 강도 임계값
                            station_info = {
                                'frequency': current_freq,
                                'strength': strength,
                                'name': f"{current_freq:.1f} MHz"
                            }
                            found_stations.append(station_info)
                            self.station_found.emit(current_freq, strength)
                            
            except Exception as e:
                print(f"Scan error at {current_freq}: {e}")
            
            current_freq += 0.2  # 200kHz 간격
            
        self.scan_finished.emit(found_stations)
    
    def stop(self):
        self.should_stop = True

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
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e2e8f0;
            }
            QListWidget::item:hover {
                background-color: #f1f5f9;
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
        
        self.demo_btn = QPushButton("Demo Mode")
        self.demo_btn.setObjectName("secondary")
        self.demo_btn.clicked.connect(self.select_demo_mode)
        button_layout.addWidget(self.demo_btn)
        
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
    
    def select_demo_mode(self):
        """데모 모드 선택"""
        self.selected_device = None
        self.accept()

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
        
        # 프리셋 및 스테이션 데이터
        self.presets = [None] * 6  # 6개 프리셋
        self.found_stations = []
        self.settings_file = "radio_settings.json"
        
        # 스캔 관련
        self.scan_thread = None
        self.scan_worker = None
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
            self.selected_device = dialog.selected_device
            self.init_hardware()
        else:
            # 사용자가 취소했으면 종료
            sys.exit(0)
    
    def init_hardware(self):
        """하드웨어 초기화"""
        if self.selected_device is None:
            print("Running in demo mode - no hardware control")
            return
            
        try:
            self.fm = besfm.BesFM(self.selected_device)
            
            # 연결 상태 확인
            if not self.fm.is_connected():
                raise Exception("Device not responding")
                
            print("Hardware connected successfully!")
            
            # 하드웨어 초기 상태 가져오기
            self.is_powered = self.fm.get_power()
            self.is_recording = self.fm.get_recording()
            
            if self.is_powered or self.is_recording:
                # 하드웨어에서 현재 값들 읽어오기
                channel = self.fm.get_channel()
                self.current_freq = channel
                self.volume = self.fm.get_volume()
                self.is_muted = self.fm.get_mute()
            
        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            QMessageBox.warning(self, "Hardware Error", 
                              f"Failed to initialize hardware:\n{str(e)}\n\nRunning in demo mode.")
            self.fm = None
    
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
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarNever)
        
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
        if self.fm is not None:
            device_status = "🟢 Hardware Connected"
            device_info = f"Product ID: 0x{self.selected_device.idProduct:04x}"
        else:
            device_status = "🔴 Demo Mode"
            device_info = "No hardware detected"
        
        self.device_status_label = QLabel(device_status)
        self.device_status_label.setObjectName("device-status")
        self.device_status_label.setAlignment(Qt.AlignRight)
        device_layout.addWidget(self.device_status_label)
        
        self.device_info_label = QLabel(device_info)
        self.device_info_label.setObjectName("device-info")
        self.device_info_label.setAlignment(Qt.AlignRight)
        device_layout.addWidget(self.device_info_label)
        
        # 기기 변경 버튼
        self.change_device_btn = QPushButton("Change Device")
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
        
        signal_label = QLabel("Signal:")
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
        preset_group = QGroupBox("Station Presets & Scan")
        preset_layout = QVBoxLayout(preset_group)
        
        # 프리셋 버튼들
        preset_buttons_layout = QHBoxLayout()
        self.preset_buttons = []
        for i in range(6):
            btn = QPushButton(f"P{i+1}")
            btn.setObjectName("preset-btn")
            btn.clicked.connect(lambda checked, idx=i: self.recall_preset(idx))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, idx=i: self.save_preset_menu(idx))
            btn.setToolTip("Click to recall preset, Right-click to save current frequency")
            self.preset_buttons.append(btn)
            preset_buttons_layout.addWidget(btn)
        
        preset_layout.addLayout(preset_buttons_layout)
        
        # 스캔 버튼들
        scan_layout = QHBoxLayout()
        
        self.scan_up_btn = QPushButton("Scan ↑")
        self.scan_up_btn.setObjectName("scan-btn")
        self.scan_up_btn.clicked.connect(self.scan_up)
        scan_layout.addWidget(self.scan_up_btn)
        
        self.scan_down_btn = QPushButton("Scan ↓")
        self.scan_down_btn.setObjectName("scan-btn")
        self.scan_down_btn.clicked.connect(self.scan_down)
        scan_layout.addWidget(self.scan_down_btn)
        
        self.auto_scan_btn = QPushButton("Auto Scan")
        self.auto_scan_btn.setObjectName("secondary-btn")
        self.auto_scan_btn.clicked.connect(self.auto_scan_stations)
        scan_layout.addWidget(self.auto_scan_btn)
        
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
        vol_label = QLabel("Volume")
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
        rds_group = QGroupBox("RDS Information")
        rds_layout = QVBoxLayout(rds_group)
        
        # RDS 스테이션 이름
        self.rds_station = QLabel("No RDS Data")
        self.rds_station.setObjectName("rds-station")
        rds_layout.addWidget(self.rds_station)
        
        # RDS 텍스트
        self.rds_text = QLabel("")
        self.rds_text.setObjectName("rds-text")
        self.rds_text.setWordWrap(True)
        rds_layout.addWidget(self.rds_text)
        
        # RDS 활성화 버튼
        self.rds_btn = QPushButton("Enable RDS")
        self.rds_btn.setObjectName("secondary-btn")
        self.rds_btn.clicked.connect(self.toggle_rds)
        rds_layout.addWidget(self.rds_btn)
        
        parent_layout.addWidget(rds_group)
    
    def create_bottom_controls(self, parent_layout):
        # 하단 컨트롤 버튼들
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        # 파워 버튼
        self.power_btn = QPushButton("Power")
        self.power_btn.setObjectName("power-btn")
        self.power_btn.clicked.connect(self.toggle_power)
        controls_layout.addWidget(self.power_btn)
        
        # 뮤트 버튼
        self.mute_btn = QPushButton("Mute")
        self.mute_btn.setObjectName("secondary-btn")
        self.mute_btn.clicked.connect(self.toggle_mute)
        controls_layout.addWidget(self.mute_btn)
        
        # 레코드 버튼
        self.record_btn = QPushButton("Record")
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
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("secondary-btn")
        self.settings_btn.clicked.connect(self.show_settings)
        settings_layout.addWidget(self.settings_btn)
        
        parent_layout.addLayout(settings_layout)
    
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
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: 500;
            min-width: 40px;
        }
        
        #preset-btn:hover {
            background-color: #d1d5db;
        }
        
        #preset-btn[data-state="saved"] {
            background-color: #3b82f6;
            color: white;
            border-color: #2563eb;
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
        if not self.is_powered:
            return
        
        old_freq = self.current_freq
        self.current_freq = max(88.0, min(108.0, self.current_freq + step))
        self.freq_label.setText(f"{self.current_freq:.1f}")
        
        # 하드웨어가 있으면 실제 주파수 변경
        if self.fm is not None:
            try:
                # 주파수를 하드웨어 단위로 변환 (MHz * 100)
                freq_val = int(self.current_freq * 100)
                
                if step > 0:  # 주파수 증가
                    freq_val = min(freq_val, 10700)  # 최대 107MHz
                    self.set_freq_hardware(freq_val)
                else:  # 주파수 감소
                    freq_val = max(freq_val, 7600)   # 최소 76MHz  
                    self.set_freq_hardware(freq_val)
                    
            except Exception as e:
                print(f"Hardware frequency change failed: {e}")
                # 하드웨어 실패 시 이전 값으로 복원
                self.current_freq = old_freq
                self.freq_label.setText(f"{self.current_freq:.1f}")
    
    def set_freq_hardware(self, freq_val):
        """하드웨어 주파수 설정"""
        if self.fm is not None:
            self.fm.set_channel(freq_val / 100.0)
            # 하드웨어에서 실제 설정된 값 읽어오기
            actual_freq = self.fm.get_channel()
            self.current_freq = actual_freq
            self.freq_label.setText(f"{actual_freq:.1f}")
    
    def update_from_hardware(self):
        """하드웨어에서 현재 상태 업데이트"""
        if self.fm is None:
            return
            
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
        
        # 하드웨어가 있으면 실제 볼륨 변경
        if self.fm is not None:
            try:
                self.fm.set_volume(value)
            except Exception as e:
                print(f"Hardware volume change failed: {e}")
        
        # 뮤트 상태이면 자동으로 해제
        if self.is_muted and value > 0:
            self.is_muted = False
            self.update_mute_state()
            if self.fm is not None:
                try:
                    self.fm.set_mute(False)
                except Exception as e:
                    print(f"Hardware unmute failed: {e}")
    
    def toggle_power(self):
        old_powered = self.is_powered
        
        if self.is_powered:
            # 파워 오프
            self.is_powered = False
            if self.fm is not None:
                try:
                    self.fm.set_power(False)
                except Exception as e:
                    print(f"Hardware power off failed: {e}")
                    self.is_powered = old_powered  # 실패 시 복원
        elif self.is_recording:
            # 레코딩 중이면 레코딩 중지
            self.is_recording = False
            if self.fm is not None:
                try:
                    self.fm.set_recording(False)
                except Exception as e:
                    print(f"Hardware recording stop failed: {e}")
                    self.is_recording = True  # 실패 시 복원
        else:
            # 파워 온
            self.is_powered = True
            if self.fm is not None:
                try:
                    self.fm.set_power(True)
                    time.sleep(0.2)
                    self.fm.set_volume(6)
                    # 하드웨어 리셋
                    self.reset_hardware()
                except Exception as e:
                    print(f"Hardware power on failed: {e}")
                    self.is_powered = False  # 실패 시 복원
        
        self.update_power_state()
        
        # 파워 오프 시 레코딩 중지
        if not self.is_powered and self.is_recording:
            self.toggle_record()
    
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
        
        if self.fm is not None:
            try:
                self.fm.set_mute(self.is_muted)
            except Exception as e:
                print(f"Hardware mute toggle failed: {e}")
                self.is_muted = old_muted  # 실패 시 복원
        
        self.update_mute_state()
    
    def toggle_record(self):
        if not self.is_powered:
            return
        
        old_recording = self.is_recording
        self.is_recording = not self.is_recording
        
        if self.fm is not None:
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
                self.is_recording = old_recording  # 실패 시 복원
        
        self.update_record_state()
    
    def update_power_state(self):
        if self.is_powered:
            self.power_btn.setText("ON")
            self.power_btn.setProperty("data-state", "on")
        else:
            self.power_btn.setText("OFF")
            self.power_btn.setProperty("data-state", "off")
        
        # 스타일 다시 적용
        self.power_btn.style().unpolish(self.power_btn)
        self.power_btn.style().polish(self.power_btn)
        
        # 다른 컨트롤들 활성화/비활성화
        enabled = self.is_powered
        for btn in [self.btn_freq_up_big, self.btn_freq_up_small, 
                   self.btn_freq_down_big, self.btn_freq_down_small,
                   self.mute_btn, self.record_btn, self.volume_slider]:
            btn.setEnabled(enabled)
    
    def update_mute_state(self):
        if self.is_muted:
            self.mute_btn.setText("Unmute")
            self.mute_btn.setProperty("data-state", "active")
        else:
            self.mute_btn.setText("Mute")
            self.mute_btn.setProperty("data-state", "")
        
        # 스타일 다시 적용
        self.mute_btn.style().unpolish(self.mute_btn)
        self.mute_btn.style().polish(self.mute_btn)
    
    def update_record_state(self):
        if self.is_recording:
            self.record_btn.setText("Stop")
            self.record_btn.setProperty("data-state", "recording")
            self.record_timer.start(800)  # 800ms 간격으로 깜빡임
        else:
            self.record_btn.setText("Record")
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
                    self.fm.set_power(False)
                if self.is_recording:
                    self.fm.set_recording(False)
            except:
                pass
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
        if self.fm is not None:
            device_status = "🟢 Hardware Connected"
            # besfm의 get_device_name 사용
            device_name = besfm.BesFM.get_device_name(self.selected_device.idProduct)
            device_info = f"{device_name}"
            self.device_status_label.setStyleSheet("color: #059669;")
        else:
            device_status = "🔴 Demo Mode"
            device_info = "No hardware detected"
            self.device_status_label.setStyleSheet("color: #dc2626;")
        
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
        except Exception as e:
            print(f"Settings load failed: {e}")
            self.presets = [None] * 6
    
    def save_settings(self):
        """설정 저장"""
        try:
            settings = {
                'presets': self.presets,
                'last_frequency': self.current_freq,
                'last_volume': self.volume
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
            
            # 하드웨어에 설정
            if self.fm is not None:
                try:
                    self.fm.set_channel(freq)
                    # 실제 설정된 주파수 확인
                    actual_freq = self.fm.get_channel()
                    self.current_freq = actual_freq
                    self.freq_label.setText(f"{actual_freq:.1f}")
                except Exception as e:
                    print(f"Preset recall failed: {e}")
                    self.current_freq = old_freq
                    self.freq_label.setText(f"{old_freq:.1f}")
    
    def save_preset_menu(self, index):
        """프리셋 저장 (우클릭 메뉴)"""
        if not self.is_powered:
            return
            
        self.presets[index] = self.current_freq
        self.update_preset_buttons()
        self.save_settings()
        
        # 사용자에게 피드백
        btn = self.preset_buttons[index]
        original_text = btn.text()
        btn.setText("Saved!")
        QTimer.singleShot(1000, lambda: btn.setText(original_text))
    
    def update_preset_buttons(self):
        """프리셋 버튼 상태 업데이트"""
        for i, btn in enumerate(self.preset_buttons):
            if i < len(self.presets) and self.presets[i] is not None:
                btn.setText(f"P{i+1}\n{self.presets[i]:.1f}")
                btn.setProperty("data-state", "saved")
            else:
                btn.setText(f"P{i+1}")
                btn.setProperty("data-state", "")
            
            # 스타일 다시 적용
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def scan_up(self):
        """위쪽 주파수 스캔"""
        if not self.is_powered or self.fm is None:
            return
        try:
            self.fm.seek_up()
            self.fm._wait(timeout=5000)
            actual_freq = self.fm.get_channel()
            self.current_freq = actual_freq
            self.freq_label.setText(f"{actual_freq:.1f}")
        except Exception as e:
            print(f"Scan up failed: {e}")
    
    def scan_down(self):
        """아래쪽 주파수 스캔"""
        if not self.is_powered or self.fm is None:
            return
        try:
            self.fm.seek_down()
            self.fm._wait(timeout=5000)
            actual_freq = self.fm.get_channel()
            self.current_freq = actual_freq
            self.freq_label.setText(f"{actual_freq:.1f}")
        except Exception as e:
            print(f"Scan down failed: {e}")
    
    def auto_scan_stations(self):
        """자동으로 모든 방송국 스캔"""
        if not self.is_powered or self.fm is None:
            return
        
        self.found_stations = []
        self.scan_progress = QProgressDialog("Scanning stations...", "Cancel", 88, 108, self)
        self.scan_progress.setWindowModality(Qt.WindowModal)
        self.scan_progress.setValue(88)
        
        # 별도 스레드에서 스캔 실행
        self.scan_thread = QThread()
        self.scan_worker = StationScanner(self.fm)
        self.scan_worker.moveToThread(self.scan_thread)
        
        self.scan_worker.station_found.connect(self.on_station_found)
        self.scan_worker.scan_progress.connect(self.on_scan_progress)
        self.scan_worker.scan_finished.connect(self.on_scan_finished)
        self.scan_thread.started.connect(self.scan_worker.scan)
        
        self.scan_progress.canceled.connect(self.scan_worker.stop)
        self.scan_thread.start()
    
    def on_station_found(self, frequency, strength):
        """스캔에서 방송국 발견시"""
        station = {
            'frequency': frequency,
            'strength': strength,
            'name': f"{frequency:.1f} MHz"
        }
        self.found_stations.append(station)
        print(f"Found station: {frequency:.1f} MHz (Strength: {strength})")
    
    def on_scan_progress(self, frequency):
        """스캔 진행 상황 업데이트"""
        if self.scan_progress:
            self.scan_progress.setValue(int(frequency))
    
    def on_scan_finished(self, stations):
        """스캔 완료"""
        if self.scan_progress:
            self.scan_progress.close()
            
        if self.scan_thread:
            self.scan_thread.quit()
            self.scan_thread.wait()
            
        # 결과 표시
        if stations:
            msg = f"Found {len(stations)} stations:\n\n"
            for station in stations:
                msg += f"{station['frequency']:.1f} MHz (Signal: {station['strength']})\n"
            QMessageBox.information(self, "Scan Complete", msg)
        else:
            QMessageBox.information(self, "Scan Complete", "No stations found")
    
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
                    self.rds_station.setText("RDS Disabled")
                    self.rds_text.setText("")
                    
            except Exception as e:
                print(f"RDS toggle failed: {e}")
    
    def update_rds_button(self):
        """RDS 버튼 상태 업데이트"""
        if self.rds_enabled:
            self.rds_btn.setText("Disable RDS")
            self.rds_btn.setProperty("data-state", "active")
        else:
            self.rds_btn.setText("Enable RDS")
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
        dialog.setWindowTitle("Settings")
        dialog.setFixedSize(350, 400)
        dialog.setStyleSheet(self.get_main_stylesheet())
        
        layout = QVBoxLayout(dialog)
        
        # 주파수 대역 설정
        band_group = QGroupBox("Frequency Band")
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
        spacing_group = QGroupBox("Channel Spacing")
        spacing_layout = QVBoxLayout(spacing_group)
        
        self.spacing_combo = QComboBox()
        self.spacing_combo.addItems(["200 kHz", "100 kHz", "50 kHz"])
        spacing_layout.addWidget(self.spacing_combo)
        layout.addWidget(spacing_group)
        
        # 모노/스테레오 설정
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QVBoxLayout(audio_group)
        
        self.mono_checkbox = QCheckBox("Force Mono")
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
        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("secondary-btn")
        apply_btn.clicked.connect(lambda: self.apply_settings(dialog))
        cancel_btn = QPushButton("Cancel")
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
                    self.fm.set_power(False)
                if self.is_recording:
                    self.fm.set_recording(False)
            except:
                pass
        
        # 타이머 정리
        if hasattr(self, 'rds_timer'):
            self.rds_timer.stop()
        if hasattr(self, 'signal_timer'):
            self.signal_timer.stop()
        if hasattr(self, 'record_timer'):
            self.record_timer.stop()
            
        # 스캔 스레드 정리
        if hasattr(self, 'scan_thread') and self.scan_thread:
            if hasattr(self, 'scan_worker'):
                self.scan_worker.stop()
            self.scan_thread.quit()
            self.scan_thread.wait()
        
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 시스템 기본 스타일 사용
    app.setStyle('Fusion')
    
    window = ModernRadioApp()
    window.show()
    
    sys.exit(app.exec())
