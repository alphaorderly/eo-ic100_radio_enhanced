"""
BesFM 라디오 하드웨어 핵심 클래스
"""
import usb.core
import struct
import platform
import time
from .besfm_enums import BesCmd, BesFM_Enums


class BesFM:
    """Samsung BesFM 라디오 하드웨어 제어 클래스"""
    
    def __init__(self, dev: usb.core.Device):
        self._dev = dev
        self._device_info = {
            'vendor_id': dev.idVendor,
            'product_id': dev.idProduct,
            'bus': dev.bus,
            'address': dev.address,
            'serial_number': dev.serial_number,
            'manufacturer': dev.manufacturer,
            'product': dev.product
        }
        
        # macOS에서 권한 문제 해결을 위한 추가 처리
        try:
            # 기존 커널 드라이버 분리
            if self._dev.is_kernel_driver_active(4):
                self._dev.detach_kernel_driver(4)
        except usb.core.USBError as e:
            if platform.system() == "Darwin":  # macOS
                print(f"Warning: Could not detach kernel driver (this is normal on macOS): {e}")
            else:
                raise e
        
        try:
            # macOS에서 권한 문제 해결을 위해 명시적으로 configuration 설정
            if platform.system() == "Darwin":
                try:
                    self._dev.set_configuration()
                except usb.core.USBError as e:
                    if "Access denied" in str(e) or "Permission denied" in str(e):
                        raise PermissionError(
                            "USB device access denied. On macOS, you may need to:\\n"
                            "1. Run the application with sudo privileges\\n"
                            "2. Or grant USB device access in System Preferences\\n"
                            "3. Or install using homebrew with proper permissions\\n"
                            f"Original error: {e}"
                        )
                    raise e
            
            self._notify_ep = self._dev.get_active_configuration()[4,0][0]
            
        except usb.core.USBError as e:
            if "Access denied" in str(e) or "Permission denied" in str(e):
                if platform.system() == "Darwin":  # macOS
                    raise PermissionError(
                        "USB device access denied. On macOS, you may need to:\\n"
                        "1. Run the application with 'sudo' privileges:\\n"
                        "   sudo ./FM-Radio-Enhanced-macOS-arm64\\n"
                        "2. Or add USB device access permissions:\\n"
                        "   - Go to System Preferences → Security & Privacy → Privacy\\n"
                        "   - Add your application to 'USB' or 'Accessibility' if available\\n"
                        "3. Try disconnecting and reconnecting the USB device\\n"
                        
                        f"Original error: {e}"
                    )
                else:
                    raise PermissionError(f"USB device access denied: {e}")
            raise e
    
    @staticmethod
    def find_all_devices():
        """모든 호환 가능한 FM 라디오 기기 찾기"""
        compatible_devices = []
        try:
            devices = list(usb.core.find(find_all=True, idVendor=0x04e8))
            for device in devices:
                if device.idProduct in [0xa054, 0xa059, 0xa05b]:
                    device_info = {
                        'device': device,
                        'vendor_id': device.idVendor,
                        'product_id': device.idProduct,
                        'bus': device.bus,
                        'address': device.address,
                        'serial_number': device.serial_number,
                        'manufacturer': device.manufacturer or 'Samsung',
                        'product': device.product or 'FM Radio',
                        'description': f"Samsung FM Radio (0x{device.idProduct:04x})"
                    }
                    compatible_devices.append(device_info)
        except Exception as e:
            print(f"Error scanning for devices: {e}")
        
        return compatible_devices
    
    @staticmethod
    def get_device_name(product_id):
        """Product ID에 따른 기기 이름 반환"""
        device_names = {
            0xa054: "Samsung Galaxy FM Radio (Type A)",
            0xa059: "Samsung Galaxy FM Radio (Type B)", 
            0xa05b: "Samsung Galaxy FM Radio (Type C)"
        }
        return device_names.get(product_id, f"Samsung FM Radio (0x{product_id:04x})")
    
    def get_device_info(self):
        """현재 기기 정보 반환"""
        return self._device_info.copy()
    
    def is_connected(self):
        """기기 연결 상태 확인"""
        try:
            # 간단한 명령을 보내서 기기가 응답하는지 확인
            self._get(BesCmd.GET_FM_IC_POWER_ON_STATE.value)
            return True
        except:
            return False

    def _set(self, cmd, value):
        """USB 명령 전송 with retry mechanism"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._dev.ctrl_transfer(
                    BesCmd.READ.value,
                    BesCmd.SET.value,
                    cmd, value, bytearray(BesCmd.SET_DATA_LENGTH.value)
                )
                # 작은 지연으로 USB 안정성 향상
                time.sleep(0.001)  # 1ms
                return
            except usb.core.USBError as e:
                if attempt < max_retries - 1:
                    time.sleep(0.01)  # 10ms 대기 후 재시도
                    continue
                raise e

    def _get(self, cmd):
        """USB 명령 수신 with retry mechanism"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self._dev.ctrl_transfer(
                    BesCmd.READ.value,
                    BesCmd.GET.value,
                    cmd, BesCmd.GET_FM_INDEX.value,
                    bytearray(BesCmd.GET_DATA_LENGTH.value)
                )
                # 작은 지연으로 USB 안정성 향상
                time.sleep(0.001)  # 1ms
                return result
            except usb.core.USBError as e:
                if attempt < max_retries - 1:
                    time.sleep(0.01)  # 10ms 대기 후 재시도
                    continue
                raise e

    def _query(self):
        """USB 쿼리 명령"""
        return self._dev.ctrl_transfer(
            BesCmd.READ.value,
            BesCmd.QUERY.value,
            0, 0,
            bytearray(12)
        )

    def _wait(self, timeout=None):
        """USB 알림 대기"""
        try:
            resp = self._notify_ep.read(5, timeout=timeout).tobytes()
        except usb.core.USBError as e:
                if e.errno != 110:
                    raise e
        else:
            if resp[0:3] == b'\\x01\\x00\\x08':
                return True

    def set_power(self, b):
        """전원 설정"""
        if self.get_recording():
            return
        # 전원 변경 시 지연 추가 (pop sound 방지)
        if b:
            self._set(
                BesCmd.SET_POWER_STATE.value,
                BesCmd.SET_FM_IC_POWER_ON.value
            )
        else:
            self._set(
                BesCmd.SET_POWER_STATE.value,
                BesCmd.SET_FM_IC_POWER_OFF.value
            )
        time.sleep(0.010)  # 10ms 지연

    def get_power(self):
        """전원 상태 조회"""
        if self._get(BesCmd.GET_FM_IC_POWER_ON_STATE.value)[0]:
            return True
        else:
            return False

    def set_recording(self, b):
        """녹음 모드 설정"""
        if self.get_power():
            return
        if b:
            self._set(
                BesCmd.SET_RECORDING_MODE.value,
                BesCmd.SET_FM_IC_POWER_ON.value
            )
        else:
            self._set(
                BesCmd.SET_RECORDING_MODE.value,
                BesCmd.SET_FM_IC_POWER_OFF.value
            )

    def get_recording(self):
        """녹음 모드 상태 조회"""
        if self._get(BesCmd.GET_FM_RECORDING_MODE_STATUS.value)[0]:
            return True
        else:
            return False

    def set_band(self, band):
        """주파수 대역 설정"""
        assert band in BesFM_Enums
        self._set(BesCmd.SET_FM_BAND.value, band.value)

    def get_band(self):
        """주파수 대역 조회"""
        return self._get(BesCmd.GET_CURRENT_FM_BAND.value)[0]

    def set_rssi_threshold(self, value):
        """RSSI 임계값 설정 (미구현)"""
        raise NotImplementedError

    def get_rssi_threshold(self):
        """RSSI 임계값 조회 (미구현)"""
        raise NotImplementedError

    def set_channel_spacing(self, spacing):
        """채널 간격 설정"""
        assert spacing in BesFM_Enums
        self._set(BesCmd.SET_CHAN_SPACING.value, spacing.value)

    def get_channel_spacing(self):
        """채널 간격 조회"""
        return self._get(BesCmd.GET_CURRENT_SPACING.value)[0]

    def set_mute(self, b):
        """음소거 설정"""
        # 뮤트 변경 시 지연 추가 (pop sound 방지)
        if b:
            self._set(BesCmd.SET_MUTE.value, 1)
        else:
            self._set(BesCmd.SET_MUTE.value, 0)
        time.sleep(0.003)  # 3ms 지연

    def get_mute(self):
        """음소거 상태 조회"""
        if self._get(BesCmd.GET_MUTE_STATE.value)[0]:
            return True
        else:
            return False

    def set_volume(self, volume):
        """볼륨 설정 (0-15)"""
        assert 0 <= volume <= 15
        # 볼륨 변경 시 약간의 지연 추가 (pop sound 방지)
        self._set(BesCmd.SET_VOLUME.value, volume)
        time.sleep(0.002)  # 2ms 지연

    def get_volume(self):
        """볼륨 조회"""
        return self._get(BesCmd.GET_CURRENT_VOLUME.value)[0]

    def set_mono(self, b):
        """모노 모드 설정"""
        if b:
            self._set(BesCmd.SET_MONO_MODE.value, 1)
        else:
            self._set(BesCmd.SET_MONO_MODE.value, 0)

    def get_mono(self):
        """모노 모드 상태 조회"""
        if self._get(BesCmd.GET_FORCED_MONO_STATE.value)[0]:
            return True
        else:
            return False

    def _set_seek(self, seek):
        """시크 명령 설정"""
        self._set(BesCmd.SET_SEEK_START.value, seek.value)

    def seek_up(self):
        """위쪽 주파수 스캔"""
        self._set_seek(BesCmd.SET_SEEK_UP)

    def seek_down(self):
        """아래쪽 주파수 스캔"""
        self._set_seek(BesCmd.SET_SEEK_DOWN)

    def seek_stop(self):
        """스캔 중지"""
        self._set(BesCmd.SET_SEEK_STOP.value, 0)

    def set_channel(self, freq):
        """주파수 설정"""
        # 주파수 변경 시 지연 추가 (pop sound 방지)
        self._set(
            BesCmd.SET_CHANNEL.value, int(freq * 100)
            )
        time.sleep(0.005)  # 5ms 지연

    def get_channel(self):
        """현재 주파수 조회"""
        return struct.unpack('<H',self._get(BesCmd.GET_CURRENT_CHANNEL.value))[0] / 100

    def set_rds(self, b):
        """RDS 설정"""
        if b:
            self._set(BesCmd.SET_RDS.value, 1)
        else:
            self._set(BesCmd.SET_RDS.value, 0)

    def get_rds(self):
        """RDS 상태 조회"""
        if self._get(BesCmd.GET_RDS_STATUS.value)[0]:
            return True
        else:
            return False

    def set_dc_threshold(self, value):
        """DC 임계값 설정 (미구현)"""
        raise NotImplementedError

    def get_dc_threshold(self):
        """DC 임계값 조회 (미구현)"""
        raise NotImplementedError

    def set_spike_threshold(self, value):
        """Spike 임계값 설정 (미구현)"""
        raise NotImplementedError

    def get_spike_threshold(self):
        """Spike 임계값 조회 (미구현)"""
        raise NotImplementedError

    def get_status(self):
        """하드웨어 상태 조회"""
        res = self._query()
        if res[0] == 0:
            success, freq, strength = struct.unpack('<?HB', res[1:5])
            return {'type': 'seek', 'success':success, 'freq':freq/100, 'strength':strength}
        elif res[0] == 1:
            success, freq, strength = struct.unpack('<?HB', res[1:5])
            return {'type': 'tune', 'success':success, 'freq':freq/100, 'strength':strength}
        elif res[0] == 2:
            error, strength = struct.unpack('<BB', res[1:3])
            rds = res[3:-1].tobytes()
            return {'type': 'rds', 'error':error, 'strength':strength, 'data':rds[1::-1]+rds[3:1:-1]+rds[5:3:-1]+rds[7:5:-1]}
        else:
            return res
