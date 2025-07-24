"""
기기 선택 다이얼로그
"""
import besfm
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGroupBox, QListWidget, QListWidgetItem, 
                               QPushButton, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt


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
