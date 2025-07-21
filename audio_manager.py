"""
오디오 호환성 및 pop sound 방지를 위한 오디오 매니저 모듈
"""
import time
import threading
import platform
from typing import Optional, Dict, Any

class AudioManager:
    """
    FM 라디오의 오디오 제어를 위한 매니저 클래스
    Pop sound 방지 및 호환성 개선을 위한 기능 제공
    """
    
    def __init__(self, fm_device):
        self.fm = fm_device
        self.current_volume = 0
        self.target_volume = 0
        self.is_fading = False
        self.fade_thread = None
        self.fade_lock = threading.Lock()
        
        # 플랫폼별 설정
        self.platform_config = self._get_platform_config()
        
    def _get_platform_config(self) -> Dict[str, Any]:
        """플랫폼별 최적 설정 반환"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return {
                'fade_steps': 15,
                'fade_delay': 0.008,  # 8ms
                'volume_change_delay': 0.005,  # 5ms
                'mute_fade_time': 0.1,  # 100ms
            }
        elif system == "Windows":
            return {
                'fade_steps': 12,
                'fade_delay': 0.010,  # 10ms
                'volume_change_delay': 0.008,  # 8ms
                'mute_fade_time': 0.12,  # 120ms
            }
        else:  # Linux
            return {
                'fade_steps': 10,
                'fade_delay': 0.012,  # 12ms
                'volume_change_delay': 0.010,  # 10ms
                'mute_fade_time': 0.15,  # 150ms
            }
    
    def set_volume_smooth(self, target_volume: int) -> bool:
        """
        점진적 볼륨 변경으로 pop sound 방지
        
        Args:
            target_volume (int): 목표 볼륨 (0-15)
            
        Returns:
            bool: 성공 여부
        """
        if not 0 <= target_volume <= 15:
            return False
            
        if self.fm is None:
            return False
        
        # 현재 볼륨 가져오기
        try:
            self.current_volume = self.fm.get_volume()
        except Exception:
            self.current_volume = 0
        
        self.target_volume = target_volume
        
        # 이미 페이딩 중이면 중단
        if self.is_fading:
            self._stop_fade()
        
        # 볼륨 차이가 작으면 즉시 변경
        volume_diff = abs(self.target_volume - self.current_volume)
        if volume_diff <= 1:
            return self._set_volume_immediate(target_volume)
        
        # 점진적 볼륨 변경 시작
        self.fade_thread = threading.Thread(target=self._fade_volume)
        self.fade_thread.daemon = True
        self.fade_thread.start()
        
        return True
    
    def _fade_volume(self):
        """백그라운드에서 점진적 볼륨 변경"""
        with self.fade_lock:
            self.is_fading = True
            
            try:
                steps = self.platform_config['fade_steps']
                delay = self.platform_config['fade_delay']
                
                volume_diff = self.target_volume - self.current_volume
                step_size = volume_diff / steps
                
                for i in range(steps):
                    if not self.is_fading:  # 중단 요청 시
                        break
                        
                    new_volume = self.current_volume + (step_size * (i + 1))
                    new_volume = max(0, min(15, round(new_volume)))
                    
                    if self._set_volume_immediate(new_volume):
                        time.sleep(delay)
                    else:
                        break
                
                # 최종 볼륨으로 정확히 설정
                if self.is_fading:
                    self._set_volume_immediate(self.target_volume)
                    
            except Exception as e:
                print(f"Volume fade error: {e}")
            finally:
                self.is_fading = False
    
    def _set_volume_immediate(self, volume: int) -> bool:
        """즉시 볼륨 설정 (내부용)"""
        try:
            self.fm.set_volume(volume)
            self.current_volume = volume
            time.sleep(self.platform_config['volume_change_delay'])
            return True
        except Exception as e:
            print(f"Volume set error: {e}")
            return False
    
    def _stop_fade(self):
        """페이딩 중단"""
        self.is_fading = False
        if self.fade_thread and self.fade_thread.is_alive():
            self.fade_thread.join(timeout=0.5)
    
    def soft_mute(self, enable: bool) -> bool:
        """
        부드러운 뮤트/언뮤트
        
        Args:
            enable (bool): True면 뮤트, False면 언뮤트
            
        Returns:
            bool: 성공 여부
        """
        if self.fm is None:
            return False
        
        try:
            if enable:
                # 현재 볼륨 저장하고 0으로 페이드
                self.current_volume = self.fm.get_volume()
                if self.current_volume > 0:
                    self.set_volume_smooth(0)
                    time.sleep(self.platform_config['mute_fade_time'])
                
                # 하드웨어 뮤트 설정
                self.fm.set_mute(True)
            else:
                # 하드웨어 뮤트 해제
                self.fm.set_mute(False)
                time.sleep(0.02)  # 안정화 대기
                
                # 볼륨 복원
                if hasattr(self, '_saved_volume') and self._saved_volume > 0:
                    self.set_volume_smooth(self._saved_volume)
                else:
                    current_vol = self.fm.get_volume()
                    if current_vol > 0:
                        self.set_volume_smooth(current_vol)
            
            return True
            
        except Exception as e:
            print(f"Soft mute error: {e}")
            return False
    
    def frequency_change_prepare(self):
        """주파수 변경 전 준비 (pop sound 방지)"""
        if self.fm is None:
            return
        
        try:
            # 현재 볼륨 저장
            self._saved_volume = self.fm.get_volume()
            
            # 볼륨을 점진적으로 낮춤
            if self._saved_volume > 3:
                self.set_volume_smooth(3)
                time.sleep(0.05)  # 50ms 대기
                
        except Exception as e:
            print(f"Frequency change prepare error: {e}")
    
    def frequency_change_complete(self):
        """주파수 변경 후 복원"""
        if self.fm is None:
            return
        
        try:
            # 안정화 대기
            time.sleep(0.1)
            
            # 볼륨 복원
            if hasattr(self, '_saved_volume'):
                self.set_volume_smooth(self._saved_volume)
                
        except Exception as e:
            print(f"Frequency change complete error: {e}")
    
    def power_on_sequence(self) -> bool:
        """전원 켜기 시퀀스 (pop sound 최소화)"""
        if self.fm is None:
            return False
        
        try:
            # 1. 볼륨을 0으로 설정
            self.fm.set_volume(0)
            time.sleep(0.02)
            
            # 2. 전원 켜기
            self.fm.set_power(True)
            time.sleep(0.1)  # 안정화 대기
            
            # 3. 뮤트 해제
            self.fm.set_mute(False)
            time.sleep(0.02)
            
            # 4. 기본 볼륨으로 점진적 증가
            self.set_volume_smooth(6)
            
            return True
            
        except Exception as e:
            print(f"Power on sequence error: {e}")
            return False
    
    def power_off_sequence(self) -> bool:
        """전원 끄기 시퀀스 (pop sound 최소화)"""
        if self.fm is None:
            return False
        
        try:
            # 1. 볼륨을 점진적으로 0으로
            current_vol = self.fm.get_volume()
            if current_vol > 0:
                self.set_volume_smooth(0)
                time.sleep(0.15)  # 페이딩 완료 대기
            
            # 2. 뮤트 설정
            self.fm.set_mute(True)
            time.sleep(0.02)
            
            # 3. 전원 끄기
            self.fm.set_power(False)
            
            return True
            
        except Exception as e:
            print(f"Power off sequence error: {e}")
            return False
    
    def recording_start_sequence(self) -> bool:
        """레코딩 시작 시퀀스"""
        if self.fm is None:
            return False
        
        try:
            # 레코딩 모드는 볼륨이 높아야 하므로 점진적 증가
            self.fm.set_recording(True)
            time.sleep(0.1)
            
            # 최대 볼륨으로 점진적 증가
            self.set_volume_smooth(15)
            
            return True
            
        except Exception as e:
            print(f"Recording start sequence error: {e}")
            return False
    
    def recording_stop_sequence(self) -> bool:
        """레코딩 중지 시퀀스"""
        if self.fm is None:
            return False
        
        try:
            # 볼륨을 먼저 낮춤
            self.set_volume_smooth(0)
            time.sleep(0.1)
            
            # 레코딩 중지
            self.fm.set_recording(False)
            
            return True
            
        except Exception as e:
            print(f"Recording stop sequence error: {e}")
            return False
    
    def cleanup(self):
        """리소스 정리"""
        self._stop_fade()
        self.fm = None
