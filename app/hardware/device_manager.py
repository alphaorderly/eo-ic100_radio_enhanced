"""
BesFM 장치 관리자
"""
import usb.core
from .besfm_core import BesFM


class DeviceManager:
    """BesFM 장치 관리 클래스"""
    
    @staticmethod
    def find_all_devices():
        """모든 호환 가능한 FM 라디오 기기 찾기"""
        return BesFM.find_all_devices()
    
    @staticmethod
    def get_device_name(product_id):
        """Product ID에 따른 기기 이름 반환"""
        return BesFM.get_device_name(product_id)
    
    @staticmethod
    def create_besfm_instance(device):
        """USB 디바이스로부터 BesFM 인스턴스 생성"""
        try:
            return BesFM(device)
        except Exception as e:
            raise RuntimeError(f"Failed to create BesFM instance: {e}")
    
    @staticmethod
    def check_device_compatibility(device):
        """기기 호환성 확인"""
        if device.idVendor != 0x04e8:
            return False
        return device.idProduct in [0xa054, 0xa059, 0xa05b]
