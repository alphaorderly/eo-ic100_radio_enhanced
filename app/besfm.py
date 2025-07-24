"""
BesFM 라디오 하드웨어 모듈 - 호환성을 위한 래퍼
"""
# 하드웨어 모듈에서 클래스들을 import
from hardware.besfm_core import BesFM
from hardware.besfm_enums import BesCmd, BesFM_Enums

# 호환성을 위해 기존 import 경로 유지
__all__ = ['BesFM', 'BesCmd', 'BesFM_Enums']
