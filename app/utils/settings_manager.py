"""
설정 관리 유틸리티
"""
import json
import os


class SettingsManager:
    def __init__(self, settings_file="radio_settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            'presets': [None] * 6,
            'last_frequency': 88.5,
            'last_volume': 8,
            'language': 'korean',  # 'korean' 또는 'english'
            'rds_enabled': False,
            'device_settings': {}
        }
    
    def load_settings(self):
        """설정 파일에서 설정 로드"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 기본 설정으로 누락된 키 채우기
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings):
        """설정을 파일에 저장"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_preset(self, settings, index):
        """특정 인덱스의 프리셋 가져오기"""
        presets = settings.get('presets', [])
        if 0 <= index < len(presets):
            return presets[index]
        return None
    
    def save_preset(self, settings, index, frequency, name=None):
        """프리셋 저장"""
        presets = settings.get('presets', [None] * 6)
        if 0 <= index < len(presets):
            preset_data = {
                'frequency': frequency,
                'name': name or f'{frequency:.1f} MHz',
                'saved_at': None  # 필요시 타임스탬프 추가
            }
            presets[index] = preset_data
            settings['presets'] = presets
        return settings
    
    def clear_preset(self, settings, index):
        """프리셋 삭제"""
        presets = settings.get('presets', [])
        if 0 <= index < len(presets):
            presets[index] = None
            settings['presets'] = presets
        return settings
