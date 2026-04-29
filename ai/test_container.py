# 프로젝트 루트에서 실행
# python test_container.py

from container import AIContainer

container = AIContainer(openai_api_key="test-key")
print("✅ places_chain:", container.places_chain)
print("✅ diary_chain:", container.diary_chain)
print("🎉 모든 의존성 주입 성공!")