"""
윈도우 USB 설정 진단 및 테스트 스크립트
WinUSB 드라이버 설정 후 동작 확인용
"""

import sys
import os

# 프로젝트 루트 경로를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.hardware.device_manager_hybrid import HybridDeviceManager
from app.hardware.besfm_core import BesFM
import platform


def main():
    """메인 진단 함수"""
    print("=== BesFM Windows USB 진단 도구 ===")
    print(f"플랫폼: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print()
    
    # 1. 시스템 진단
    print("1. 시스템 진단 실행 중...")
    HybridDeviceManager.diagnose_system()
    print()
    
    # 2. 디바이스 검색 테스트
    print("2. 디바이스 검색 테스트...")
    try:
        devices = HybridDeviceManager.find_all_devices()
        if devices:
            print(f"✓ {len(devices)}개의 FM 라디오 디바이스 발견:")
            for i, device_info in enumerate(devices):
                print(f"  [{i+1}] {device_info['description']}")
                print(f"      Vendor ID: 0x{device_info['vendor_id']:04x}")
                print(f"      Product ID: 0x{device_info['product_id']:04x}")
                if device_info.get('serial_number'):
                    print(f"      Serial: {device_info['serial_number']}")
                if device_info.get('backend'):
                    print(f"      Backend: {device_info['backend']}")
                print()
        else:
            print("✗ 호환 가능한 FM 라디오 디바이스를 찾을 수 없습니다.")
            print()
            print("해결 방법:")
            print("1. Samsung Galaxy 기기가 USB로 연결되어 있는지 확인")
            print("2. Zadig 설정 확인:")
            print("   - Options > List All Devices 활성화")
            print("   - Samsung 디바이스의 Interface 4 선택")
            print("   - WinUSB 드라이버로 교체")
            print("3. 디바이스 재연결")
            print("4. 관리자 권한으로 실행")
            return
            
    except Exception as e:
        print(f"✗ 디바이스 검색 중 오류 발생: {e}")
        print(f"오류 타입: {type(e).__name__}")
        return
    
    # 3. 디바이스 연결 테스트
    print("3. 디바이스 연결 테스트...")
    try:
        device_info = devices[0]  # 첫 번째 디바이스 사용
        print(f"테스트 대상: {device_info['description']}")
        
        device = device_info['device']
        if device is None:
            print("✗ 디바이스 객체가 None입니다 (WMI 검색 결과일 가능성)")
            return
            
        # BesFM 인스턴스 생성 시도
        fm = BesFM(device)
        print("✓ BesFM 인스턴스 생성 성공")
        
        # 4. 기본 명령 테스트
        print("4. 기본 명령 테스트...")
        
        # 전원 상태 확인
        try:
            power_state = fm.get_power()
            print(f"✓ 전원 상태 확인 성공: {'ON' if power_state else 'OFF'}")
        except Exception as e:
            print(f"✗ 전원 상태 확인 실패: {e}")
            return
            
        # 주파수 확인
        try:
            if not power_state:
                print("  전원을 켜는 중...")
                fm.set_power(True)
                import time
                time.sleep(0.1)
                
            frequency = fm.get_channel()
            print(f"✓ 주파수 확인 성공: {frequency:.1f} MHz")
        except Exception as e:
            print(f"✗ 주파수 확인 실패: {e}")
            
        # 볼륨 확인
        try:
            volume = fm.get_volume()
            print(f"✓ 볼륨 확인 성공: {volume}/15")
        except Exception as e:
            print(f"✗ 볼륨 확인 실패: {e}")
            
        print()
        print("=== 테스트 완료 ===")
        print("모든 테스트가 성공했다면 Windows USB 설정이 올바르게 완료되었습니다!")
        
    except PermissionError as e:
        print(f"✗ 권한 오류: {e}")
        print()
        print("권한 문제 해결 방법:")
        print("1. 관리자 권한으로 프로그램 실행")
        print("2. Zadig 설정 재확인")
        print("3. 안티바이러스 소프트웨어 일시 비활성화")
        
    except ConnectionError as e:
        print(f"✗ 연결 오류: {e}")
        
    except Exception as e:
        print(f"✗ 예상치 못한 오류: {e}")
        print(f"오류 타입: {type(e).__name__}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
    input("\n아무 키나 누르면 종료됩니다...")
