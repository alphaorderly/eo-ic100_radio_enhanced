"""
언어 관리 유틸리티
"""


class LanguageManager:
    def __init__(self):
        self.translations = {
            'korean': {
                'window_title': 'FM Radio Enhanced',
                'signal': '신호:',
                'volume': '볼륨',
                'presets_scan': '스테이션 프리셋 & 스캔',
                'rds_info': 'RDS 정보',
                'power': '전원',
                'power_on': '켜짐',
                'power_off': '꺼짐',
                'mute': '음소거',
                'unmute': '음소거 해제',
                'record': '녹음',
                'stop_recording': '녹음 중지',
                'settings': '설정',
                'settings_coming_soon': '설정 기능은 곧 추가될 예정입니다.',
                'change_device': '기기 변경',
                'scan_up': '스캔 ↑',
                'scan_down': '스캔 ↓',
                'enable_rds': 'RDS 활성화',
                'disable_rds': 'RDS 비활성화',
                'no_rds_data': 'RDS 데이터 없음',
                'rds_disabled': 'RDS 비활성화됨',
                'empty_preset': '비어있음',
                'preset_tooltip_saved': '프리셋 {}: {} ({:.1f} MHz)\\n클릭: 불러오기 | 우클릭: 저장',
                'preset_tooltip_empty': '프리셋 {}: 비어있음\\n우클릭하여 현재 주파수 저장',
                'preset_info': '💾 클릭: 저장된 방송 불러오기  |  우클릭: 현재 주파수 저장',
                'language_toggle': '🌍 English'
            },
            'english': {
                'window_title': 'FM Radio Enhanced',
                'signal': 'Signal:',
                'volume': 'Volume',
                'presets_scan': 'Station Presets & Scan',
                'rds_info': 'RDS Information',
                'power': 'Power',
                'power_on': 'ON',
                'power_off': 'OFF',
                'mute': 'Mute',
                'unmute': 'Unmute',
                'record': 'Record',
                'stop_recording': 'Stop',
                'settings': 'Settings',
                'settings_coming_soon': 'Settings feature coming soon.',
                'change_device': 'Change Device',
                'scan_up': 'Scan ↑',
                'scan_down': 'Scan ↓',
                'enable_rds': 'Enable RDS',
                'disable_rds': 'Disable RDS',
                'no_rds_data': 'No RDS Data',
                'rds_disabled': 'RDS Disabled',
                'empty_preset': 'Empty',
                'preset_tooltip_saved': 'Preset {}: {} ({:.1f} MHz)\\nClick: Load | Right-click: Save',
                'preset_tooltip_empty': 'Preset {}: Empty\\nRight-click to save current frequency',
                'preset_info': '💾 Click: Load station  |  Right-click: Save current frequency',
                'language_toggle': '🌍 한국어'
            }
        }
        self.current_language = 'korean'
    
    def set_language(self, language):
        """언어 설정"""
        if language in self.translations:
            self.current_language = language
    
    def get_text(self, key, *args):
        """텍스트 가져오기"""
        text = self.translations[self.current_language].get(key, key)
        if args:
            return text.format(*args)
        return text
    
    def get_current_language(self):
        """현재 언어 반환"""
        return self.current_language
    
    def is_korean(self):
        """한국어 여부 확인"""
        return self.current_language == 'korean'
    
    def toggle_language(self):
        """언어 토글"""
        self.current_language = 'english' if self.current_language == 'korean' else 'korean'
        return self.current_language
