# -*- coding: utf-8 -*-
"""pytest 공통 설정.

sys.path 등록은 pytest.ini pythonpath = api 로 처리.
모델 로드 등 무거운 fixture 는 각 테스트 모듈에서 monkeypatch 로 대체.

프로젝트 루트를 sys.path 에 추가하여 ai.* 패키지 import 가능하게 설정.
"""

import sys
import os

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
