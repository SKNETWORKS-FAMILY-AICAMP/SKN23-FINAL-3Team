# -*- coding: utf-8 -*-
"""
back/main.py
------------
uvicorn 실행 진입점 (back/ 디렉토리에서 실행 시 사용).

실행 방법::

    # back/ 디렉토리에서
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

api/ 디렉토리를 Python path에 추가한 뒤
실제 FastAPI 앱(back/api/main.py)을 임포트합니다.
"""

import sys
import os
import importlib.util

# back/api/main.py 를 직접 로드 (이름 충돌 방지)
_api_dir = os.path.join(os.path.dirname(__file__), "api")
sys.path.insert(0, _api_dir)

_spec = importlib.util.spec_from_file_location("api_main", os.path.join(_api_dir, "main.py"))
_module = importlib.util.module_from_spec(_spec)
sys.modules["api_main"] = _module
_spec.loader.exec_module(_module)

app = _module.app  # noqa: F401
