# -*- coding: utf-8 -*-
"""pytest 공통 설정.

sys.path 등록은 pytest.ini pythonpath = api 로 처리.
모델 로드 등 무거운 fixture 는 각 테스트 모듈에서 monkeypatch 로 대체.
"""
