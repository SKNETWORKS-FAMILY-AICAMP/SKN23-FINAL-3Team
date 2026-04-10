import os
import httpx
import chromadb
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../chroma_db")
COLLECTION_NAME = "dog_breeds"
MODEL_NAME = "jhgan/ko-sroberta-multitask"
DOG_API_URL = "https://api.thedogapi.com/v1/breeds"
DOG_API_KEY = os.getenv("DOG_API_KEY")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def fetch_breeds() -> list:
    """The Dog API에서 전체 견종 데이터 수집"""
    print("The Dog API 호출 중...")
    headers = {}
    if DOG_API_KEY:
        headers["x-api-key"] = DOG_API_KEY

    response = httpx.get(DOG_API_URL, headers=headers, timeout=30)
    breeds = response.json()
    print(f"총 {len(breeds)}개 견종 수집 완료!")
    return breeds


def translate_breed_name(breed_name: str) -> str:
    """영문 견종명 → 한국어 번역 (GPT-4.1-mini)"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "강아지 견종명을 한국어로 번역해주세요. 한국어 견종명만 답하세요. 번역이 없으면 영문 그대로 답하세요."},
            {"role": "user", "content": breed_name}
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()


def translate_temperament(temperament: str) -> str:
    """영문 temperament → 한국어 번역 (GPT-4.1-mini)"""
    if not temperament:
        return "활발하고 친근한 성격"

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "강아지 성격 키워드를 한국어로 번역해주세요. 쉼표로 구분된 짧은 키워드 형태로만 답하세요."},
            {"role": "user", "content": temperament}
        ],
        max_tokens=100
    )
    return response.choices[0].message.content.strip()


def generate_personality_document(breed_name_ko: str, temperament_ko: str, activity_level: str) -> str:
    """견종 성격 풍부한 문장 생성 (GPT-4.1-mini)"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "강아지 견종의 성격을 자연스러운 한국어 문장으로 설명해주세요. 3문장 이내로 작성하세요."},
            {"role": "user", "content": f"견종: {breed_name_ko}, 성격 키워드: {temperament_ko}, 활동 특성: {activity_level}"}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()


def get_activity_level(energy_level) -> str:
    """에너지 레벨 → 활동 특성 변환"""
    if energy_level is None:
        return "medium"
    if energy_level >= 4:
        return "high"
    elif energy_level >= 3:
        return "medium"
    else:
        return "low"


def load_and_process(breeds: list) -> list:
    """견종 데이터 전처리 — GPT 번역 + 문장 생성"""
    print(f"\n총 {len(breeds)}개 견종 처리 시작...")
    processed = []

    for i, breed in enumerate(breeds):
        breed_id = breed.get("id")
        breed_name = breed.get("name", "")
        temperament = breed.get("temperament", "")
        activity_level = get_activity_level(breed.get("energy_level"))

        print(f"  [{i+1}/{len(breeds)}] {breed_name} 처리 중...")

        breed_name_ko = translate_breed_name(breed_name)
        temperament_ko = translate_temperament(temperament)
        document = generate_personality_document(breed_name_ko, temperament_ko, activity_level)

        processed.append({
            "breed_id": breed_id,
            "breed_name": breed_name.lower(),
            "breed_name_ko": breed_name_ko,
            "activity_level": activity_level,
            "temperament_ko": temperament_ko,
            "document": document,
        })

    return processed


def embed_and_store(processed: list):
    """임베딩 생성 및 ChromaDB 저장"""
    print(f"\n임베딩 모델 로드 중: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("모델 로드 완료!")

    print(f"\nChromaDB 초기화: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제")
    except:
        pass

    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"'{COLLECTION_NAME}' 컬렉션 생성 완료")

    documents = [p["document"] for p in processed]
    metadatas = [
        {
            "breed_name": p["breed_name"],
            "breed_name_ko": p["breed_name_ko"],
            "activity_level": p["activity_level"],
            "temperament": p["temperament_ko"],
        }
        for p in processed
    ]
    ids = [f"breed_{p['breed_id']}" for p in processed]

    print("\n임베딩 생성 중...")
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    print(f"\n✅ Vector DB 적재 완료! 총 {collection.count()}개 저장됨")


def main():
    breeds = fetch_breeds()
    processed = load_and_process(breeds)
    embed_and_store(processed)


if __name__ == "__main__":
    main()