# Team. 케르베로스

<div align="center">

  ![image](./assets/SKN23_FINAL_3TEAM_image.png)

  <table align="center">
    <tr>
      <td align="center">이승연</td>
      <td align="center">정유선</td>
      <td align="center">송민채</td>
    </tr>
    <tr>
      <th align="center">APM</th>
      <th align="center">PM</th>
      <th align="center">AI Engineer</th>
    </tr>
    <tr>
      <td align="center">
        <a href="https://github.com/OOOONBBOWQ">
          <img src="https://img.shields.io/badge/OOOONBBOWQ-181717?style=flat-square&logo=github&logoColor=white"/>
        </a>
      </td>
      <td align="center">
        <a href="https://github.com/JYS96">
          <img src="https://img.shields.io/badge/JYS96-181717?style=flat-square&logo=github&logoColor=white"/>
        </a>
      </td>
      <td align="center">
        <a href="https://github.com/MINCHAESONG">
          <img src="https://img.shields.io/badge/MINCHAESONG-181717?style=flat-square&logo=github&logoColor=white"/>
        </a>
      </td>
    </tr>
    <tr>
      <td align="center">
        서비스 기획<br/>
        화면 설계 및 구현<br/>
        프론트엔드 웹 개발 (UI·핵심 기능)<br/>
        모바일 앱 개발 (전면 재작성)<br/>
        AI 그림일기 생성·평가 플로우 설계 및 개발<br/>
        이미지 생성 프롬프트 최적화<br/>
        반려견 VLM 분석 (Qwen2.5-VL) 연동<br/>
        사진→그림 변환 흐름 개발
      </td>
      <td align="center">
        계정 및 리소스 결제 관리<br/>
        서버 구축 및 관리<br/>
        RDB 설계 및 관리<br/>
        FastAPI 구축 및 백엔드 개발<br/>
        프론트엔드 웹 (회원가입·약관·공통 컴포넌트)<br/>
        모바일 앱 초기 구축 + UX 폴리싱<br/>
        LLM 의도분류 모델 (KoELECTRA)<br/>
        OAuth 2.0 (Google·Kakao·Naver)<br/>
        시설정보 검색 API
      </td>
      <td align="center">
        데이터 수집 및 정제<br/>
        벡터DB 설계 및 관리<br/>
        장소 추천 RAG 파이프라인 개발<br/>
        Query Parsing 및 추천 재정렬 로직 개발<br/>
        성향분석·추천 이유 생성 로직 개발<br/>
        장소 추천 평가셋 구축 및 성능 평가
      </td>
    </tr>
  </table>

  <br />

---

  <br />

  <div align="center">
    <img src="./assets/logo.png" alt="logo"/>
  </div>

  <br />

  <table align="center">
    <tr>
      <td align="center"><b>기간</b></td>
      <td>2026-03-26 ~ 2026-05-20 (38일)</td>
    </tr>
    <tr>
      <td align="center"><b>소속</b></td>
      <td>SKN AI 부트캠프 SKN23기 5차/FINAL 프로젝트</td>
    </tr>
    <tr>
      <td align="center"><b>멘토</b></td>
      <td>조수현 (Data Scientist)</td>
    </tr>
    <tr>
      <td align="center"><b>운영 도메인</b></td>
      <td><a href="https://withdog.kro.kr">https://withdog.kro.kr</a></td>
    </tr>
    <tr>
      <td align="center"><b>API 문서</b></td>
      <td>
        <a href="https://documenter.getpostman.com/view/53095517/2sBXqCPipg">PostMan</a>
        <a href="https://withdog.kro.kr/api/docs">Swagger UI</a>
      </td>
    </tr>
  </table>

  <br />

</div>

# 1. 프로젝트 개요

###  withDOG, 강아지와  더 잘 놀고 더 잘 기억하기

withDOG는 반려견 동반 장소를 추천하고 실행부터 기록까지 하나의 흐름으로 연결하는 AI 기반 통합 서비스입니다.

반려동물 양육 가구가 늘며 반려견을 동반한 장소 방문, 여행 수요는 커지고 있지만,
현재 시장은 정보가 분산되어 있고 반려견 성향이나 보호자 라이프스타일을 반영한
개인화 추천 서비스는 부족합니다.

withDOG는 탐색부터 기록까지의 경험을 하나로 이어, 반려견과의 시간을 더 쉽고 감성적으로 남길 수 있도록 합니다.

---

# 2. 프로젝트 배경 및 목적

**국내 반려동물 양육 가구 비율은 약 30%에 달하며, 반려동물을 가족으로 여기는 '펫팸족' 문화가 확산**되고 있습니다.


이와 함께 반려견과 함께 방문할 수 있는 카페, 공원, 식당, 실내 공간 등에 대한 수요도 빠르게 증가하고 있습니다.
조선일보(2025.10.17)는 반려동물 동반 외출·관광 수요가 확대되면서 관련 장소와 인프라가 새로운 생활·관광 시장으로 주목받고 있다고 보도한 바 있다.
정부 역시 농림축산식품부 「제3차 동물복지 종합계획(2025~2029)」을 통해 **반려동물 친화 공간과 관련 인프라 확대를 추진** 중입니다.

그러나 **사용자가 실제로 반려견과 방문할 장소를 찾는 과정에서는 여전히 불편함이 존재**합니다.

한국관광공사의 「2024 반려동물 동반여행 현황 및 인식조사」에 따르면, 반려동물 동반 시 주요 장애 요인으로 숙박시설 부족 46.4%, 음식점·카페 부족 44.8%, 관광지 부족 35.7%가 제시되었다. 즉, 사용자는 반려견과 함께 갈 수 있는 장소 자체가 충분하지 않다고 느끼며, 동반 가능 여부와 이용 조건을 직접 확인해야 하는 탐색 부담을 겪고 있습니다.

따라서 **WithDOG**는 단순 추천 서비스가 아니라,
반려견의 성향과 보호자의 상황을 반영하여 일상 속 산책, 외출, 카페 방문, 실내 놀이 공간 등 다양한 반려견 동반 장소를 추천하는 AI 기반 장소 추천 서비스를 지향합니다.

---

<div align="center">

# 3. 수집 데이터 및 전처리

</div>

## 3.1. 데이터 출처 및 수집 방식

<table width="100%">
  <thead>
    <tr>
      <th>데이터</th>
      <th>출처</th>
      <th>수집 방식</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>반려동물 동반 가능 장소</td>
      <td>한국문화정보원 공공데이터 포털</td>
      <td>CSV 다운로드</td>
    </tr>
    <tr>
      <td>견종 정보</td>
      <td>The Dog API</td>
      <td>REST API 호출</td>
    </tr>
  </tbody>
</table>

- **장소 데이터**: `한국문화정보원_전국_반려동물_동반_가능_문화시설_위치_데이터_20250324.csv` 기준 전체 70,650건에서 반려동물 동반 가능 장소만 필터링
- **Tour API 장소 데이터**: 한국관광공사 Tour API에서 반려동물 동반 여행지 975건을 추가 수집하고, 기존 장소 데이터와 `content_id` 기준으로 병합·중복 제거
- **견종 데이터**: The Dog API에서 견종 정보 수집 후 GPT-4.1-mini로 한국어 번역, 국내 인기 TOP 10 마킹

## 3.2. 데이터 전처리 파이프라인
> #### 데이터 전처리 과정

  ```
  원본 CSV (70,650건)
    ↓ 반려동물 동반 가능(Y) 필터링
    ↓ 한반도 위경도 범위 검증 (위도 33~38.7, 경도 124~132)
    ↓ 필수 필드 누락 제거 (시설명, 주소)
    ↓ 중복 제거 (시설명 + 주소 기준)
    ↓ 카테고리 매핑 → sub_category, content_type_id
    ↓ 실내/실외 여부, 펫존 유형 변환
    ↓ content_id 생성 (name + address MD5 해시)
    ↓ 자연어 description 문장 생성 (벡터화용)
    ↓ 입장료 / 추가요금 정규화 (description → entrance_fee_* / extra_fee_* 4 컬럼)
    ↓
    ├── MySQL DB 적재 (배치 1,000건 단위)
    └── ChromaDB 벡터화 적재 (ko-sroberta-multitask, 배치 50건 단위)
  ```
    ▎ 최종 유효 장소: 약 22,102건 (한국문화정보원 + 한국관광공사 Tour API 통합)

> #### ChromaDB 설계 및 관리

  | 항목 | 내용 |
  |------|------|
  | 저장 경로 | `data/chroma_db` |
  | 장소 컬렉션 | `dog_places` |
  | 임베딩 모델 | `ko-sroberta-multitask` |
  | 적재 단위 | 50건 batch |
  | 벡터화 대상 | 장소별 자연어 `description` |
  | 검색 방식 | 사용자 쿼리 임베딩 후 cosine similarity 기반 의미 검색 |
  | 활용 위치 | 장소 추천 RAG 파이프라인의 의미 검색 단계 |

> #### 주요 전처리 시스템 및 스키마

  **벡터화용 description 문장 예시**

  "[장소명]은 서울특별시에 위치한 카페 장소로 반려견 동반이 가능하다.
  입장 가능 크기: 소형견. 이용 조건: 목줄 착용 필수.
  실내 이용 가능. 주차 가능. 운영시간: 10:00~21:00. 휴무일: 월요일."

  **Place DB 주요 스키마**

<table width="100%">
  <thead>
    <tr>
      <th>필드</th>
      <th>설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`content_id`</td>
      <td>name + address MD5 해시 (고유 식별자)</td>
    </tr>
    <tr>
      <td>`name` / `address`</td>
      <td>장소명 / 주소</td>
    </tr>
    <tr>
      <td>`sub_category`</td>
      <td>세부 카테고리 (카페, 공원, 동물병원 등)</td>
    </tr>
    <tr>
      <td>`is_indoor` / `is_outdoor`</td>
      <td>실내/실외 가능 여부</td>
    </tr>
    <tr>
      <td>`pet_zone_type`</td>
      <td>반려동물 구역 유형 (실내구역/실외구역/전구역)</td>
    </tr>
    <tr>
      <td>`pet_size_limit`</td>
      <td>입장 가능 크기 제한</td>
    </tr>
    <tr>
      <td>`pet_restrictions`</td>
      <td>이용 제한사항</td>
    </tr>
    <tr>
      <td>`has_parking`</td>
      <td>주차 가능 여부 (Y/N)</td>
    </tr>
    <tr>
      <td>`operation_info`</td>
      <td>운영시간 및 휴무일</td>
    </tr>
    <tr>
      <td>`description`</td>
      <td>ChromaDB 벡터화 소스 텍스트</td>
    </tr>
  </tbody>
</table>

## 3.3. 수집 데이터 현황
> #### 태그별 수집 개수

<table width="100%">
  <thead>
    <tr>
      <th>sub_category</th>
      <th>content_type_id</th>
      <th>설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>카페</td>
      <td>39</td>
      <td>반려견 동반 카페</td>
    </tr>
    <tr>
      <td>식당</td>
      <td>39</td>
      <td>반려동물 동반 음식점</td>
    </tr>
    <tr>
      <td>펜션</td>
      <td>32</td>
      <td>반려견 동반 숙박</td>
    </tr>
    <tr>
      <td>호텔</td>
      <td>32</td>
      <td>반려견 동반 호텔</td>
    </tr>
    <tr>
      <td>공원</td>
      <td>12</td>
      <td>반려견 입장 가능 공원</td>
    </tr>
    <tr>
      <td>관광지</td>
      <td>12</td>
      <td>반려견 동반 관광지</td>
    </tr>
    <tr>
      <td>반려견놀이터</td>
      <td>28</td>
      <td>반려견 전용 놀이터</td>
    </tr>
    <tr>
      <td>박물관 / 미술관 / 문예회관</td>
      <td>12</td>
      <td>반려견 동반 문화시설</td>
    </tr>
    <tr>
      <td>동물병원 / 동물약국</td>
      <td>14</td>
      <td>동물 의료시설</td>
    </tr>
    <tr>
      <td>반려동물용품</td>
      <td>38</td>
      <td>반려동물 용품점</td>
    </tr>
    <tr>
      <td>미용 / 위탁관리</td>
      <td>14</td>
      <td>반려동물 케어 시설</td>
    </tr>
  </tbody>
</table>


**최종 적재 현황**

- MySQL DB: 약 22,102건
- ChromaDB 벡터: 약 22,102건 (컬렉션명: dog_places)

**카테고리별 적재 분포 (Top 7 + 기타)**

<table width="100%">
  <thead>
    <tr>
      <th>sub_category</th>
      <th align="right">건수</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>동물약국</td>
      <td align="right">8,438</td>
    </tr>
    <tr>
      <td>동물병원</td>
      <td align="right">4,485</td>
    </tr>
    <tr>
      <td>반려동물용품</td>
      <td align="right">3,821</td>
    </tr>
    <tr>
      <td>미용</td>
      <td align="right">2,003</td>
    </tr>
    <tr>
      <td>관광지</td>
      <td align="right">938</td>
    </tr>
    <tr>
      <td>카페</td>
      <td align="right">822</td>
    </tr>
    <tr>
      <td>공원</td>
      <td align="right">545</td>
    </tr>
    <tr>
      <td>기타</td>
      <td align="right">1,050</td>
    </tr>
  </tbody>
</table>

---

<div align="center">

  # 4. 서비스 기능 및 모델/파이프라인 설계

  <p align="center">
    <img src="https://img.shields.io/badge/챗봇%20의도분류-5B8DEF?style=flat-square"/>
    <img src="https://img.shields.io/badge/반려견과%20보호자%20성향%20분석-FFB347?style=flat-square"/>
    <img src="https://img.shields.io/badge/AI%20장소%20추천-0F6E56?style=flat-square"/>
    <img src="https://img.shields.io/badge/AI%20그림일기-FF9A3C?style=flat-square"/>
  </p>

</div>

> #### RAG / LLM 모델 아키텍처

<div align="center">

  <img src="./assets/RAG_LLM_모델 아키텍처 설계.png" alt="RAG / LLM 모델 아키텍처 설계" width="100%" />

</div>

<br />

<table width="100%">
  <thead>
    <tr>
      <th width="23%">기능</th>
      <th>설명</th>
      <th>핵심 기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>챗봇 의도분류</td>
      <td>사용자 입력을 분석해 다이어리 작성, 장소추천, 시설정보, 기타 응답으로 라우팅합니다.</td>
      <td>KoELECTRA Fine-tuning, FastAPI, Intent Routing</td>
    </tr>
    <tr>
      <td>반려견과 보호자 성향 분석</td>
      <td>온보딩에서 선택한 반려견·보호자 태그를 각각 5축 점수로 수치화하여 성향을 분석하고, 태그 텍스트 임베딩 기반 KMeans 군집화를 통해 비슷한 의미의 태그가 가까운 그룹으로 묶이는지 확인합니다. 이를 통해 성향 축 정의가 임의적이지 않음을 설명하는 근거로 활용합니다.</td>
      <td>DogScorer, OwnerScorer, 태그 기반 벡터 점수화, Sentence-Transformers, KMeans, PCA, t-SNE</td>
    </tr>
    <tr>
      <td>AI 장소 추천</td>
      <td>사용자 검색어, 반려견 성향, 보호자 취향, 장소 특성을 결합해 반려견 동반 가능 장소를 개인화 추천합니다.</td>
      <td>ChromaDB 벡터 검색, 코사인 유사도, 룰 기반 점수, 카카오 지도 API</td>
    </tr>
    <tr>
      <td>AI 그림일기</td>
      <td>챗봇 대화를 바탕으로 텍스트 일기와 동화책 스타일 이미지를 생성하고 저장합니다.</td>
      <td>GPT-4.1-mini, gpt-image-1, ChromaDB RAG, S3</td>
    </tr>
  </tbody>
</table>

<br />

## 4.1. 챗봇 의도분류 모델

챗봇에 입력된 텍스트를 의도 분류 모델로 분석한 뒤, 각 기능에 맞는 처리 흐름으로 라우팅합니다.

<table width="100%">
  <thead>
    <tr>
      <th>항목</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>베이스 모델</td>
      <td>`monologg/koelectra-base-v3-discriminator`</td>
    </tr>
    <tr>
      <td>분류 클래스</td>
      <td>다이어리 작성 / 장소추천 / 시설정보 / 기타</td>
    </tr>
    <tr>
      <td>학습 설정</td>
      <td>epochs=5, batch=16, lr=3e-5, max_length=128</td>
    </tr>
    <tr>
      <td>평가 지표</td>
      <td>Accuracy, Classification Report, per-class F1</td>
    </tr>
    <tr>
      <td>학습 데이터</td>
      <td>1,117 샘플 (4 카테고리 — 다이어리 작성 / 장소추천 / 시설정보 / 기타)</td>
    </tr>
    <tr>
      <td>학습 결과</td>
      <td>**Accuracy 0.9955** (2026-04-28 GPU 재학습, RTX 3050, 5 epoch, epoch 3 베스트 저장)</td>
    </tr>
    <tr>
      <td>모델 저장</td>
      <td>`ai/intent/model/`</td>
    </tr>
    <tr>
      <td>서비스 구조</td>
      <td>메인 FastAPI 서버와 별도 포트에서 의도 분류 API 실행</td>
    </tr>
  </tbody>
</table>

> #### 의도 분류 흐름

```text
사용자 입력
    ↓
KoELECTRA Tokenizer
    ↓
KoELECTRA Sequence Classification
    ↓
Softmax → Intent Label 추론
    ↓
chat_response_service.py 라우팅
    ├─ 그림일기     → _handle_diary_mini_flow()
    ├─ 장소추천     → _handle_place_recommendation()
    ├─ 시설정보     → _handle_facility_info()
    └─ 기타         → 일반 GPT 응답
```

> #### 의도별 분류모델 처리 방식

<table width="100%">
  <thead>
    <tr>
      <th>의도</th>
      <th>처리 내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>그림일기</td>
      <td>사용자 대화를 수집하고, 정보가 충분하면 텍스트 일기와 그림일기 생성으로 연결합니다.</td>
    </tr>
    <tr>
      <td>장소추천</td>
      <td>사용자 검색어와 성향 정보를 기반으로 반려견 동반 장소를 추천합니다.</td>
    </tr>
    <tr>
      <td>시설정보</td>
      <td>동물병원, 동물약국, 미용, 위탁관리 등 목적 기반 시설 정보를 제공합니다.</td>
    </tr>
    <tr>
      <td>기타</td>
      <td>서비스 범위를 벗어난 일반 대화 또는 안내 응답을 제공합니다.</td>
    </tr>
  </tbody>
</table>

<br />

## 4.2. 반려견과 보호자 성향 분석

온보딩에서 선택한 반려견·보호자 태그를 기반으로 각각의 성향을 5축 점수로 수치화합니다.  
이 성향 점수는 이후 장소 추천에서 반려견 적합도와 보호자 취향 적합도를 계산하는 기준으로 사용됩니다.

KMeans는 실제 추천을 수행하는 모델이 아니라,  
온보딩 태그들이 의미적으로 유사한 그룹을 형성하는지 확인하여 성향 축 정의가 임의적이지 않음을 설명하는 검증 자료로 활용됩니다.

> #### 성향분석 파이프라인

<table width="100%">
  <thead>
    <tr>
      <th>단계</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>① 온보딩</td>
      <td>반려견 성향 태그와 보호자 취향 태그 선택</td>
    </tr>
    <tr>
      <td>② 반려견 점수화</td>
      <td>`DogScorer`로 반려견 태그를 5축 점수 벡터로 변환</td>
    </tr>
    <tr>
      <td>③ 보호자 점수화</td>
      <td>`OwnerScorer`로 보호자 태그를 5축 점수 벡터로 변환</td>
    </tr>
    <tr>
      <td>④ 대표 타입 분류</td>
      <td>각 5축 중 최고점 축을 기준으로 반려견 타입과 보호자 타입 분류</td>
    </tr>
    <tr>
      <td>⑤ 성향 검증</td>
      <td>태그 텍스트 임베딩 후 KMeans 군집화로 의미 유사 그룹 확인</td>
    </tr>
    <tr>
      <td>⑥ 추천 연동</td>
      <td>산출된 성향 점수를 AI 장소 추천의 `dog_score`, `owner_score` 계산에 활용</td>
    </tr>
  </tbody>
</table>

> #### 성향 타입 분류 방식

```text
dog_tags
  → DogScorer.calculate_vector()
  → DogScorer.classify_type()
  → dog_type / dog_type_name

owner_tags
  → OwnerScorer.calculate_vector()
  → OwnerScorer.classify_type()
  → owner_type / owner_type_name
```

태그가 없는 경우에는 타입 분류를 생략하고, 기본 장소 검색 흐름으로 진행합니다.

> #### 성향 축 정의

**DogScorer — 반려견 성향 5축**

<table width="100%">
  <thead>
    <tr>
      <th>축</th>
      <th>의미</th>
      <th>태그 예시</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>dog_a</td>
      <td>활동성·탐험</td>
      <td>에너자이저, 산책이 제일 좋아</td>
    </tr>
    <tr>
      <td>dog_b</td>
      <td>사회성·친화력</td>
      <td>애교쟁이, 강아지 친구 환영</td>
    </tr>
    <tr>
      <td>dog_c</td>
      <td>안정·실내 선호</td>
      <td>느긋한 편, 집이 편해요</td>
    </tr>
    <tr>
      <td>dog_d</td>
      <td>호기심·자유로움</td>
      <td>겁 없는 탐험가, 호기심 폭발</td>
    </tr>
    <tr>
      <td>dog_e</td>
      <td>예민함·신중함</td>
      <td>낯을 가려요, 예민한 편</td>
    </tr>
  </tbody>
</table>

**OwnerScorer — 보호자 취향 5축**

<table width="100%">
  <thead>
    <tr>
      <th>축</th>
      <th>의미</th>
      <th>태그 예시</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>owner_a</td>
      <td>자연 선호</td>
      <td>산, 숲, 계곡</td>
    </tr>
    <tr>
      <td>owner_b</td>
      <td>도시·핫플 선호</td>
      <td>핫플 인증, 새로운 곳 구경</td>
    </tr>
    <tr>
      <td>owner_c</td>
      <td>활동성 선호</td>
      <td>공원 산책, 신나게 뛰어놀기</td>
    </tr>
    <tr>
      <td>owner_d</td>
      <td>감성·느긋함 선호</td>
      <td>감성 충만, 느긋하게 쉬어가기</td>
    </tr>
    <tr>
      <td>owner_e</td>
      <td>먹거리·일상 선호</td>
      <td>카페 투어, 맛있는 거 먹으러</td>
    </tr>
  </tbody>
</table>

> #### KMeans 활용 방식

KMeans는 추천의 정답을 만드는 모델이 아니라,  
성향 축 정의의 설명력을 보완하는 검증 자료입니다.

<table width="100%">
  <thead>
    <tr>
      <th>구성 요소</th>
      <th>역할</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`DogScorer` / `OwnerScorer`</td>
      <td>사용자 성향 점수 계산 기준</td>
    </tr>
    <tr>
      <td>KMeans</td>
      <td>온보딩 태그의 의미적 유사 그룹 형성 여부 검증</td>
    </tr>
    <tr>
      <td>PCA / t-SNE</td>
      <td>태그 군집 결과 시각화</td>
    </tr>
  </tbody>
</table>

예를 들어 `에너자이저`, `산책이 제일 좋아`, `밖이 좋아요`와 같은 태그가 임베딩 공간에서 가까운 군집으로 묶이면,  
이 태그들을 `dog_a: 활동성·탐험` 축에 배치한 근거로 활용할 수 있습니다.

성향 검증은 태그 이름과 설명 문장을 임베딩한 뒤 KMeans 군집화를 수행하고, 그 결과를 PCA / t-SNE로 2차원 시각화하는 방식으로 진행했습니다.  
이 분석의 목적은 추천 성능을 직접 높이는 것이 아니라, `DogScorer` / `OwnerScorer`의 5축 정의가 임의적인 수기 분류가 아니라 태그 의미 구조와도 어느 정도 일치하는지를 확인하는 데 있습니다.

Silhouette score만 보면 dog / owner 모두 `k=4`에서 가장 높게 나왔지만, 최종 문서화와 성향 축 해석의 일관성을 위해 `FINAL_K = 5` 기준 결과도 함께 검토했습니다.

> #### KMeans 시각화 결과

**Dog tag t-SNE (3rd test)**

![Dog tag t-SNE](assets/kmeans/K-Means_3rd_test/dog/dog_tag_3rd_tsne_scatter.png)

반려견 태그는 활동형, 사회성 중심, 신중·예민 성향처럼 의미가 가까운 항목들이 서로 인접한 군집으로 모이는 경향을 보였습니다.  
이는 `DogScorer`의 5축이 실제 태그 의미 분포와 완전히 무관하게 정의된 것이 아님을 보여주는 보조 근거로 해석할 수 있습니다.

**Owner tag t-SNE (3rd test)**

![Owner tag t-SNE](assets/kmeans/K-Means_3rd_test/owner/owner_tag_3rd_tsne_scatter.png)

보호자 태그 역시 자연 선호, 도시 탐방, 감성·휴식, 먹거리 중심 취향처럼 유사 의미 태그들이 가까운 위치에 배치되는 패턴을 보였습니다.  
따라서 `OwnerScorer`의 축 정의 역시 온보딩 태그의 의미 구조와 일정 부분 정합성이 있다고 설명할 수 있습니다.

**Silhouette score**

![Dog tag silhouette](assets/kmeans/K-Means_3rd_test/dog/dog_tag_3rd_silhouette_score.png)

정량 지표 측면에서는 군집 수에 따라 분리도가 어떻게 변하는지 함께 확인했으며, 시각화 결과와 축 해석 가능성을 함께 고려해 최종 군집 구성을 해석했습니다.

<br />

## 4.3. AI 장소 추천

AI 장소 추천은 사용자 검색어, 반려견 성향, 보호자 취향, 장소 메타데이터를 함께 반영해 반려견 동반 가능 장소를 추천하는 기능입니다.

사용자 입력은 먼저 KoELECTRA 의도분류 모델을 거쳐 `장소추천` 의도로 분류되며, 이후 `chat_response_service._handle_places()` 경로에서 하이브리드 장소 검색과 성향 기반 재정렬을 수행합니다. `PlacesChain`의 재정렬 규칙은 이 경로에서 공통으로 재사용됩니다.

> #### 장소추천 파이프라인

```text
사용자 자유 입력
    ↓
KoELECTRA 의도분류
    ↓
장소추천 intent
    ↓
chat_response_service._handle_places()
    ↓
QueryParser 조건 파싱
    ↓
RDB 후보 필터링 / 위치 기반 반경 후보 생성
    ↓
ChromaDB 의미 검색
일반 질문: 자유 검색
근처·GPS 질문: 반경 후보 안 재순위
    ↓
rule_score + rag_score 결합
    ↓
후보 최대 20개 확보
    ↓
반려견/보호자 성향 기반 재순위
    ↓
상위 5개 선택
    ↓
GPT-4.1-mini 추천 메시지 생성
    ↓
장소 메타데이터 병합
    ↓
프론트 반환
```

> #### Step 1 — 성향 타입 분류

장소 추천 요청이 들어오면 사용자의 온보딩 태그를 기반으로 반려견 타입과 보호자 타입을 분류합니다.

```text
dog_tags
  → DogScorer.classify_type()
  → dog_type
  → a ~ e 축 점수 중 최고점 축을 타입 ID로 매핑

owner_tags
  → OwnerScorer.classify_type()
  → owner_type
  → a ~ e 축 점수 중 최고점 축을 타입 ID로 매핑
```

태그가 없는 경우에는 타입 분류 없이 `None`으로 처리하고 추천을 진행합니다.

> #### Step 2 — 쿼리 파싱 및 RDB 후보 필터링

```text
사용자 입력
  → QueryParser
  → objective 조건 추출
      - 지역 / 장소유형 / 실내외 / 주차 / 시간 / GPS / landmark
  → subjective 조건 추출
      - 조용한 / 넓은 / 분위기 좋은 / 산책하기 좋은 등
  → RDB 후보 필터링
```

RDB 후보 필터링은 SQL 조건 기반으로 후보를 좁히는 단계입니다. 6차 평가 이후 기본 후보 상한을 500개로 확대했고, 장소 유형 텍스트 필터 결과가 5개 미만이면 원본 후보를 유지해 과도한 후보 손실을 방지합니다. `근처`, `주변`, `내 주변`처럼 위치가 핵심인 질문은 1km → 2km → 3km 순으로 반경을 넓혀 거리 후보를 먼저 만들고, 이후 검색도 이 후보 안에서 재정렬합니다.

> #### Step 3 — ChromaDB 의미 검색

사용자 검색 쿼리를 임베딩한 뒤 ChromaDB에서 의미적으로 가까운 장소를 검색합니다. `subjective` 조건이 있으면 이를 우선 사용하고, 비어 있으면 사용자 원문 전체를 사용합니다.

```text
subjective or raw_query
  → Embedder.embed()
  → query embedding
  → ChromaDB.query()
  → COLLECTION_PLACES 검색
  → 코사인 유사도 기반 places[] 반환
```

검색 시 필요한 경우 아래 조건을 함께 사용할 수 있습니다.

```text
category
city
district
```

6차 평가 이후 일반 combined 모드에서는 ChromaDB 후보를 RDB 후보 안으로 제한하지 않습니다. 따라서 객관 조건 기반 RDB 검색과 의미 기반 ChromaDB 검색이 각각 후보 품질을 보완하고, 이후 점수 계산에서 결합됩니다. 다만 `경복궁 근처`, `서울역 주변`, `내 주변`처럼 위치 의도가 핵심인 질문은 반경 후보 안에서만 ChromaDB 재순위를 수행해 거리 조건을 우선 보존합니다.

> #### Step 4 — RDB + ChromaDB 결합 정렬

ChromaDB 검색 결과는 RDB의 장소 상세 정보와 `content_id`로 조인한 뒤, 의미 유사도와 반려견 친화도 규칙 점수를 결합해 기본 순위를 계산합니다.

```text
rule_score =
  전구역 동반 가능        +0.4
  제한사항 없음          +0.3
  실외 이용 가능         +0.2
  주차 가능              +0.1

base_score = rag_score * 0.5 + rule_score * 0.5 + category_bias
```

`rag_score`는 사용자 쿼리와 장소 `description` 간 의미 유사도이고, `rule_score`는 반려견 동반 친화도입니다. 명시적 장소 유형이 있는 경우 `category_bias`를 추가해 사용자의 직접 조건을 보존합니다.

> #### Step 5 — 반려견/보호자 성향 기반 재순위

하이브리드 검색으로 가져온 장소 후보에 대해 반려견 성향과 보호자 성향을 함께 반영해 재정렬합니다. 현재 실서비스는 최종 5개를 바로 고르지 않고, 검색 단계에서 최대 20개 후보를 확보한 뒤 프로필 점수를 더해 상위 5개를 반환합니다.

```text
dog_score_vector = DogScorer.calculate_vector(dog_tags)
owner_score_vector = OwnerScorer.calculate_vector(owner_tags)

활동성 a > 3 + category=공원/놀이터  → +0.10 bonus
사회성 b > 3 + category=카페/관광지  → +0.05 bonus
예민도 e > 3 + outdoor=Y            → -0.15 penalty
예민도 e > 3 + 반려견놀이터/레포츠  → -0.15 penalty

자연 선호 a > 3 + outdoor=Y         → +0.08 bonus
도시 탐험 b > 3 + category=카페/관광지 → +0.05 bonus
여유 휴식 d > 3 + indoor=Y / 카페    → +0.05 bonus
먹거리 선호 e > 3 + category=카페/식당 → +0.08 bonus
```

```python
base_score = rag_score * 0.5 + rule_score * 0.5 + category_bias
final_score = base_score + profile_bonus
```

`dog_tags`와 `owner_tags`가 모두 없는 경우에는 이 재정렬 단계를 생략합니다.

> #### Step 6 — 추천 이유 생성

검색 및 재정렬된 최종 장소 5개를 기반으로 `chat_response_service.generate_place_reasons()` 가 GPT-4.1-mini를 호출해 장소별 추천 이유만 생성합니다. 현재 실서비스 응답 조립은 `chat_response_service` 에서 수행하고, `PlacesChain` 은 성향 재정렬 규칙을 재사용하는 역할로 남아 있습니다.

```text
최종 places[5]
  → generate_place_reasons()
  → 사용자 질문 + 후보 장소 메타데이터 전달
  → GPT-4.1-mini
  → JSON: { places[{ name, reason }] }
```

> #### Step 7 — 결과 병합 및 반환

GPT가 생성한 추천 이유와 ChromaDB/RDB 장소 메타데이터를 병합해 프론트로 반환합니다.

```json
{
  "places": [
    {
      "name": "장소명",
      "address": "주소",
      "lat": 37.0,
      "lng": 127.0,
      "category": "카페",
      "conditions": "반려견 동반 가능 조건",
      "reason": "추천 이유"
    }
  ]
}
```

> #### 추천 점수 구조

현재 장소 추천은 하이브리드 검색 단계에서 `rag_score`, `rule_score`, `category_bias`를 합산해 기본 점수를 만들고, 그 위에 반려견/보호자 성향 기반 보너스와 패널티를 더해 재정렬합니다.

```python
base_score = rag_score * 0.5 + rule_score * 0.5 + category_bias
final_score = base_score + profile_bonus
```

현재 구현은 축별 가중합을 직접 계산하기보다, 태그 점수 벡터를 규칙 기반 bonus/penalty로 반영하는 방식입니다. 필요하다면 향후에는 아래와 같이 각 요소를 명시적 가중치 구조로 확장할 수 있습니다.

```python
final_score = (
    rag_score   * 0.45  # 검색어 ↔ 장소 설명 의미 유사도
  + dog_score   * 0.25  # 반려견 성향 ↔ 장소 반려견 적합도
  + owner_score * 0.20  # 보호자 취향 ↔ 장소 보호자 적합도
  + rule_score  * 0.10  # 동반 가능 여부, 실내외 조건 등 명시 규칙
)
```

> #### 장소 카테고리 분류

<table width="100%">
  <thead>
    <tr>
      <th>추천 유형</th>
      <th>포함 카테고리</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>공원·산책</td>
      <td>공원, 관광지, 여행지</td>
    </tr>
    <tr>
      <td>반려견놀이터</td>
      <td>반려견놀이터</td>
    </tr>
    <tr>
      <td>카페·식당</td>
      <td>카페, 식당</td>
    </tr>
    <tr>
      <td>숙소</td>
      <td>펜션, 호텔</td>
    </tr>
    <tr>
      <td>문화공간</td>
      <td>문예회관, 미술관, 박물관</td>
    </tr>
    <tr>
      <td>목적 기반 검색</td>
      <td>동물병원, 동물약국, 미용, 위탁관리, 반려동물용품</td>
    </tr>
  </tbody>
</table>

목적 기반 카테고리는 성향 추천 대상에서 제외하고, 사용자의 명시적 검색 의도가 있을 때 별도 처리합니다.

> #### 전체 흐름 요약

```text
사용자 입력
  → KoELECTRA 의도분류
  → 장소추천 intent
  → QueryParser (쿼리 → 객관 조건 분리) 
  → DogScorer / OwnerScorer 성향 타입 분류
  → RDB 후보 필터링
  → ChromaDB 의미 검색
  → rag_score / rule_score / category_bias 결합
  → 후보 최대 20개 확보
  → 반려견/보호자 성향 기반 bonus/penalty 재정렬
  → 상위 5개 선택
  → GPT-4.1-mini reason 생성
  → 장소 메타데이터 병합
  → 프론트 반환
```

<br />

## 4.4. AI 그림일기

AI 그림일기는 챗봇 대화를 바탕으로 하루의 에피소드를 텍스트 일기와 동화책 스타일 이미지로 생성하는 기능입니다.  
강아지 1인칭 시점으로 일기를 작성하고, 반려견의 견종·나이·감정·성격을 반영한 이미지 프롬프트를 자동 구성합니다.

> #### 대화 수집 및 생성 흐름

```mermaid
flowchart TD
    A["사용자 자유 입력"] --> B["대화 수집 및 정보 충분성 판단<br>_handle_diary_mini_flow"]

    B --> C{"정보 충분 여부"}

    C -->|정보 부족| D["GPT 추가 질문"]
    D --> B

    C -->|정보 충분| E["텍스트 일기 생성<br>그림일기로 만들어드릴까요?"]

    E --> F{"사용자 응답"}

    F -->|수정 요청| G["수정 반영 후 재생성"]
    G --> B

    F -->|응 / 만들어줘| H["DiaryChain.run()"]

    H --> I["견종 정보<br>RDB breeds 테이블 조회"]
    H --> J["과거 일기 RAG<br>DiaryRetriever → ChromaDB (n=3)"]

    I --> K["DiaryPromptBuilder<br>프롬프트 구성"]
    J --> K

    K --> L["GPT-4.1-mini<br>일기 텍스트 생성<br>max_tokens=1500 / temp=0.85"]

    L --> M["이미지 프롬프트 완성<br>build_final_image_prompt()"]
    M --> N["gpt-image-1<br>1024x1024 이미지 생성"]
    N --> O["S3 업로드 / DB 저장"]
    O --> P["최종 그림일기 반환<br>제목 + 본문 + 요약 + 이미지"]
```

> #### DiaryChain 파이프라인 (6단계)

<table width="100%">
  <thead>
    <tr>
      <th>단계</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Step 1</td>
      <td>견종 정보 조회 — RDB `breeds` 테이블에서 직접 조회 (단일 출처화)</td>
    </tr>
    <tr>
      <td>Step 2</td>
      <td>`DiaryRetriever.search(query, user_id, n_results=3)` — 유사 과거 일기 검색</td>
    </tr>
    <tr>
      <td>Step 3</td>
      <td>`DiaryPromptBuilder.build_diary_prompt()` — 일기 생성 프롬프트 구성</td>
    </tr>
    <tr>
      <td>Step 4</td>
      <td>GPT-4.1-mini 호출 — JSON 형식 일기 생성 (제목·본문·요약·이미지 힌트)</td>
    </tr>
    <tr>
      <td>Step 5</td>
      <td>JSON 파싱</td>
    </tr>
    <tr>
      <td>Step 6</td>
      <td>`build_final_image_prompt()` — 견종·나이·감정·구도 규칙을 결합해 최종 이미지 프롬프트 완성</td>
    </tr>
  </tbody>
</table>

> #### GPT 출력 형식

```json
{
  "title": "귀엽고 짧은 제목 (15자 이내, 강아지 말투)",
  "content": "일기 본문 (400자 이상, 강아지 1인칭)",
  "summary": "한줄요약 (30자 이내, 귀엽게)",
  "image_prompt_base": "English only. One single storybook scene within 90 words."
}
```

> #### DiaryPromptBuilder — 감정·유형·견종 반영

강아지의 감정과 일기 유형, 견종 특성을 프롬프트에 자동으로 반영합니다.

**감정 이모지 → 문체 톤 (12종)**

<table width="100%">
  <thead>
    <tr>
      <th>감정</th>
      <th>라벨</th>
      <th>문체 톤</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>😊</td>
      <td>신나고 행복해요</td>
      <td>밝고 신나고 경쾌한 톤. 짧고 통통 튀는 문장.</td>
    </tr>
    <tr>
      <td>😄</td>
      <td>기분이 너무 좋아요</td>
      <td>밝고 환한 톤. 활기차고 기분 좋은 하루.</td>
    </tr>
    <tr>
      <td>😂</td>
      <td>너무 웃겨요</td>
      <td>신나고 과장되게 즐거운 톤. 참을 수 없이 웃긴 상황.</td>
    </tr>
    <tr>
      <td>😅</td>
      <td>살짝 민망했어요</td>
      <td>살짝 민망하고 쑥스러운 톤. 귀엽게 당황한 느낌.</td>
    </tr>
    <tr>
      <td>🥰</td>
      <td>너무 사랑스러워요</td>
      <td>두근두근 설레고 사랑스러운 톤. 달달한 문장.</td>
    </tr>
    <tr>
      <td>🤍</td>
      <td>사랑스럽고 애틋해요</td>
      <td>다정하고 애틋한 톤. 보호자에 대한 사랑이 묻어남.</td>
    </tr>
    <tr>
      <td>😌</td>
      <td>평온하고 여유로워요</td>
      <td>잔잔하고 평온한 톤. 느긋하고 부드럽게 흘러가는 문장.</td>
    </tr>
    <tr>
      <td>🙂</td>
      <td>그냥 만족스러워요</td>
      <td>잔잔하고 만족스러운 톤. 충분히 행복한 느낌.</td>
    </tr>
    <tr>
      <td>🥹</td>
      <td>뭉클하고 감동적이에요</td>
      <td>감성적이고 뭉클한 톤. 여운이 남는 문장.</td>
    </tr>
    <tr>
      <td>😴</td>
      <td>나른하고 피곤해요</td>
      <td>나른하고 졸린 톤. 담백하고 느릿한 문장.</td>
    </tr>
    <tr>
      <td>😟</td>
      <td>조금 걱정되거나 불안해요</td>
      <td>살짝 걱정되고 세심한 톤. 조심스럽지만 부드럽게 마무리.</td>
    </tr>
    <tr>
      <td>😢</td>
      <td>슬프고 쓸쓸해요</td>
      <td>슬프고 쓸쓸한 톤. 잔잔하게 울컥하는 느낌.</td>
    </tr>
  </tbody>
</table>

**일기 유형 → 강조 포인트 (4종)**

<table width="100%">
  <thead>
    <tr>
      <th>유형</th>
      <th>집중 포인트</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>dog</td>
      <td>반려견의 행동, 컨디션, 먹은 것, 뛰어논 것</td>
    </tr>
    <tr>
      <td>owner</td>
      <td>보호자와의 교감, 유대감</td>
    </tr>
    <tr>
      <td>memory</td>
      <td>특별한 장면, 처음 경험, 여행</td>
    </tr>
    <tr>
      <td>daily</td>
      <td>평범하지만 소중한 일상의 안정감</td>
    </tr>
  </tbody>
</table>

> #### 이미지 프롬프트 완성 (`build_final_image_prompt`)

GPT가 생성한 `image_prompt_base`에 아래 요소를 결합해 최종 이미지 프롬프트를 구성합니다.

<table width="100%">
  <thead>
    <tr>
      <th>요소</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>견종 시각 힌트</td>
      <td>`BREED_VISUAL_HINTS` — 견종별 외형 특징 명시 (30종)</td>
    </tr>
    <tr>
      <td>나이 기반 스타일</td>
      <td>개월 수 기준으로 퍼피·성견·노령견 외형·비율 자동 조정</td>
    </tr>
    <tr>
      <td>감정 무드</td>
      <td>감정 이모지 → 이미지 표정·에너지 규칙으로 변환</td>
    </tr>
    <tr>
      <td>야간 감지</td>
      <td>대화 키워드 기반으로 야간 조명·분위기 자동 반영</td>
    </tr>
    <tr>
      <td>해외 배경 감지</td>
      <td>해외 지명 키워드 감지 시 현지 배경 스타일 반영</td>
    </tr>
    <tr>
      <td>구도 규칙</td>
      <td>단일 장면, 단 한 마리, 분할·패널·콜라주 금지</td>
    </tr>
    <tr>
      <td>인물 규칙</td>
      <td>동화책 스타일 얼굴, 사실적 인물 금지, 동아시아 외형</td>
    </tr>
    <tr>
      <td>품질 규칙</td>
      <td>한국·일본풍 그림책 일러스트, 구아슈+색연필 질감</td>
    </tr>
  </tbody>
</table>

> #### 이미지 생성 및 저장

```text
gpt-image-1
  - size    : 1024x1024
  - quality : low / medium / high (설정 가능)
  - format  : base64 (b64_json)
  → S3 업로드
  → DB 저장 (image_saved_path, diary_title, diary_content, diary_summary)
  → 앨범·캘린더에서 날짜별 조회
```

<br />

## 4.5. 사진 → 그림 변환 (Photo Illustration)

사용자가 촬영한 반려견 사진을 동화책 스타일 일러스트로 변환하는 기능입니다.
사진 속 피사체를 분석한 뒤, 분석 결과를 바탕으로 gpt-image-1 이미지 생성 프롬프트를 자동 구성합니다.

> #### 전체 파이프라인 흐름

```mermaid
flowchart TD
    A["사용자 사진 업로드"] --> B["S3 업로드 + Image 저장"]
    B --> C{"분석 파이프라인 선택<br>USE_YOLO_PIPELINE"}

    C -->|Cloud| D["GPT-4o Vision 단독 분석<br>피사체·장면·외형 묘사"]

    C -->|Local| E["YOLOv8n 객체 탐지<br>dog_count / person 감지"]
    E --> F["Qwen2.5-VL-3B 시각 언어 모델<br>장면·외형 상세 묘사"]
    F --> G["YOLO + VLM 결과 병합<br>PhotoValidationResult"]

    D --> H["프롬프트 빌더<br>build_photo_illustration_prompt()"]
    G --> H

    H --> I["gpt-image-1<br>1024×1024 일러스트 생성"]
    I --> J["S3 업로드 + DB 저장"]
    J --> K["그림일기 만들기 플로우 연결"]
```

> #### 이중 분석 파이프라인

사진 **분석** 단계에서 Cloud / Local 두 가지 파이프라인을 환경 변수로 전환할 수 있습니다.
이미지 생성은 두 경로 모두 gpt-image-1 을 사용합니다.

<table width="100%">
  <thead>
    <tr>
      <th>구분</th>
      <th>Cloud (기본)</th>
      <th>Local</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>환경 변수</td>
      <td><code>USE_YOLO_PIPELINE=false</code></td>
      <td><code>USE_YOLO_PIPELINE=true</code></td>
    </tr>
    <tr>
      <td>사진 분석</td>
      <td>GPT-4o Vision 단독</td>
      <td>YOLOv8n 탐지 + Qwen2.5-VL-3B 묘사</td>
    </tr>
    <tr>
      <td>장점</td>
      <td>추가 인프라 불필요, 높은 묘사 정확도</td>
      <td>GPU 서버 활용 시 API 비용 절감, 오프라인 분석 가능</td>
    </tr>
    <tr>
      <td>이미지 생성</td>
      <td>gpt-image-1</td>
      <td>gpt-image-1 (동일)</td>
    </tr>
  </tbody>
</table>

> #### 분석 결과 → 프롬프트 구성

분석 결과는 `PhotoValidationResult` 로 통일되며, 아래 정보를 포함합니다.

<table width="100%">
  <thead>
    <tr>
      <th>필드</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>dog_count</code></td>
      <td>감지된 강아지 수 (0~N)</td>
    </tr>
    <tr>
      <td><code>has_person</code></td>
      <td>사람 존재 여부</td>
    </tr>
    <tr>
      <td><code>scene_description</code></td>
      <td>장면 묘사 (배경, 상황)</td>
    </tr>
    <tr>
      <td><code>dog_visual_descriptions</code></td>
      <td>강아지별 외형 묘사 리스트</td>
    </tr>
    <tr>
      <td><code>person_visual_description</code></td>
      <td>사람 외형 묘사</td>
    </tr>
  </tbody>
</table>

프롬프트 빌더(`build_photo_illustration_prompt`)는 강아지 수·사람 유무 조합에 따라 주어·구도·얼굴 규칙을 자동으로 분기하며, 한국-일본풍 동화책 스타일(구아슈+색연필 질감, 파스텔 팔레트) 규칙을 공통으로 적용합니다.

<br />

## 4.6. 반려견 프로필 Vision 분석

온보딩 시 등록한 반려견 프로필 사진을 GPT-4o Vision 으로 분석하여, 사진에서만 파악 가능한 시각적 외형 정보를 구조화된 JSON 으로 추출합니다.
이 분석 결과는 이후 모든 그림일기 이미지 생성 시 **반려견 외형 일관성 유지**에 활용됩니다.

> #### Vision 분석이 추출하는 보조 정보

<table width="100%">
  <thead>
    <tr>
      <th>카테고리</th>
      <th>추출 항목</th>
      <th>예시</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>fur</code> (털)</td>
      <td>주 색상, 부 색상, 패턴, 길이, 질감</td>
      <td>"크림 베이지", "곱슬", "미디엄"</td>
    </tr>
    <tr>
      <td><code>face</code> (얼굴)</td>
      <td>눈 색상·형태, 코 색상, 입 특이사항</td>
      <td>"진한 갈색 둥근 눈", "검정 코"</td>
    </tr>
    <tr>
      <td><code>ears</code> (귀)</td>
      <td>형태, 크기</td>
      <td>"반쫑긋", "medium"</td>
    </tr>
    <tr>
      <td><code>distinctive_markings</code></td>
      <td>동일 외형 재현에 필수적인 시각 단서</td>
      <td>"가슴에 V자 흰털", "네 발 끝 흰 양말"</td>
    </tr>
    <tr>
      <td><code>character_sheet</code></td>
      <td><code>english_prompt</code> + <code>must_include_keywords</code></td>
      <td>이미지 생성 모델에 직접 주입할 영문 외형 프롬프트</td>
    </tr>
  </tbody>
</table>

> #### 그림일기 이미지 생성으로의 전달 경로

```text
프로필 사진 등록
  → GPT-4o Vision 분석
  → pet_profiles.profile_json 저장
      ├── character_sheet.english_prompt
      └── character_sheet.must_include_keywords

그림일기 생성 시:
  diary_response_service
  → pet.profile.profile_json 에서 english_prompt 추출
  → DiaryPromptBuilder.build_final_image_prompt() 에 주입
  → 견종 기본 묘사 대신 실제 외형 프롬프트 사용
  → gpt-image-1 이미지 생성
```

`english_prompt` 가 존재하면 견종명 기반의 일반 묘사(`one adorable poodle`) 대신 실제 분석된 외형(`cream-colored curly medium-length fur, round dark brown eyes, floppy ears, V-shaped white patch on chest`) 이 프롬프트에 들어가므로, 같은 반려견의 일기 이미지가 매번 일관된 외형으로 생성됩니다.

---

<div align="center">

  # 5. 화면흐름도

  ![image](./assets/화면흐름도.png)

</div>

> #### 페이지 구성

<table width="100%">
  <thead>
    <tr>
      <th>경로</th>
      <th>페이지</th>
      <th>인증 필요</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`/login`</td>
      <td>로그인 (카카오·구글·네이버 소셜)</td>
      <td>X</td>
    </tr>
    <tr>
      <td>`/oauth/callback`</td>
      <td>OAuth 콜백 처리</td>
      <td>X</td>
    </tr>
    <tr>
      <td>`/step`</td>
      <td>온보딩 (보호자·반려견 프로필 등록)</td>
      <td>O</td>
    </tr>
    <tr>
      <td>`/home`</td>
      <td>홈 (인트로·일기장·지도 탭)</td>
      <td>일부</td>
    </tr>
    <tr>
      <td>`/calendar`</td>
      <td>멍캘린더 (날짜별 일기 조회)</td>
      <td>O</td>
    </tr>
    <tr>
      <td>`/mypage`</td>
      <td>마이페이지 (프로필·반려견 정보 관리)</td>
      <td>O</td>
    </tr>
  </tbody>
</table>

> #### 전체 화면 흐름

```mermaid
flowchart TD
    ENTRY["서비스 첫 진입"] --> LOGIN["/login 로그인 페이지"]

    LOGIN -->|카카오 / 구글 / 네이버| OAUTH["/oauth/callback OAuth 콜백 처리"]

    OAUTH -->|신규 유저 is_new_user=true| STEP["/step 온보딩 보호자+반려견 정보 성격 태그 선택"]
    OAUTH -->|기존 유저 펫 없음| STEP
    OAUTH -->|기존 유저 펫 있음| HOME

    STEP -->|프로필 등록 완료| HOME["/home 홈 화면"]

    HOME -->|탭: 기본| INTRO["홈 인트로 서비스 소개"]
    HOME -->|tab=diary| DIARY["강아지 일기장 DiaryView + ChatBot"]
    HOME -->|tab=map| MAP["지도 MapView + ChatBot"]

    DIARY -->|album=true| ALBUM["앨범 그림일기 이미지 목록"]
    DIARY -->|챗봇 대화| CHATBOT["ChatBot 의도분류"]
    MAP -->|챗봇 대화| CHATBOT

    CHATBOT -->|그림일기 intent| DIARYGEN["AI 그림일기 생성 DiaryChain"]
    CHATBOT -->|장소추천 intent| PLACEREC["AI 장소 추천 PlacesChain"]

    DIARYGEN --> SAVE["S3 업로드 / DB 저장"]
    SAVE --> DIARY

    HOME -->|네비: 캘린더| CALENDAR["/calendar 멍캘린더 날짜별 일기 조회"]
    HOME -->|네비: 마이페이지| MYPAGE["/mypage 마이페이지"]
    MYPAGE -->|반려견 추가| STEP
```

> #### 내비게이션 구조

```text
Navbar
├── 홈
│   ├── 강아지 일기장  →  /home?tab=diary
│   └── 지도           →  /home?tab=map
├── 다이어리
│   ├── 앨범           →  /home?tab=diary&album=true  (로그인 필요)
│   └── 캘린더         →  /calendar                   (로그인 필요)
├── 마이페이지         →  /mypage                     (로그인 필요)
└── 프로필 아바타 (로그인 시)
    ├── 위드독 구독 패스  →  구독 안내 모달 (티어별 플랜 + 결제 버튼)
    ├── 튜토리얼 다시보기
    ├── 알림 설정
    └── 로그아웃       →  /login

    로그인 버튼 (비로그인 시)  →  /login
```

> #### 비로그인 접근 처리

로그인이 필요한 메뉴(앨범·캘린더·마이페이지)에 비로그인 상태로 접근하면
로그인 유도 모달이 표시되고 소셜 로그인 페이지로 이동합니다.

<div align="center">

  ```text
  비로그인 상태 → 보호 메뉴 클릭
      ↓
  로그인 유도 모달 표시
  (앨범 모아보기 / 멍캘린더 / AI 그림일기 / AI 맞춤 추천 기능 안내)
      ↓
  로그인 하러 가기 클릭  →  /login
  ```

</div>

> #### 서비스 기능 연결 구조

<div align="center">

  ```text
  챗봇 사용자 입력
          ↓
  KoELECTRA 의도분류
          ↓
  다이어리 작성 / 장소추천 / 시설정보 / 기타 라우팅
          ↓
  온보딩 성향 분석
          ↓
  반려견·보호자 성향 점수화
          ↓
  장소 특성 점수화
          ↓
  반려견 적합도 + 보호자 취향 유사도 계산
          ↓
  개인화 장소 추천
          ↓
  방문 경험 기록
          ↓
  AI 그림일기 생성
          ↓
  앨범·캘린더 저장 및 조회
  ```

</div>

> #### Flutter 모바일 앱 (Android)

웹 서비스의 핵심 기능을 Android 네이티브 앱으로 포팅한 모바일 클라이언트입니다.
운영 API (`https://withdog.kro.kr/api`) 를 그대로 재사용하며, Flutter 3.41 + Riverpod 상태 관리 기반으로 구현했습니다.

> #### 기술 스택

<table width="100%">
  <thead>
    <tr>
      <th>분류</th>
      <th>기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Framework</td>
      <td>Flutter 3.41 / Dart</td>
    </tr>
    <tr>
      <td>상태 관리</td>
      <td>Riverpod (StateNotifier + Provider)</td>
    </tr>
    <tr>
      <td>네트워크</td>
      <td>Dio (토큰 자동 갱신 인터셉터)</td>
    </tr>
    <tr>
      <td>OAuth</td>
      <td>flutter_appauth (구글) / flutter_inappwebview (카카오·네이버)</td>
    </tr>
    <tr>
      <td>이미지</td>
      <td>image_picker (카메라·갤러리) / cached_network_image</td>
    </tr>
    <tr>
      <td>지도</td>
      <td>InAppWebView 기반 카카오 지도 연동</td>
    </tr>
  </tbody>
</table>

> #### 포팅된 주요 기능

<table width="100%">
  <thead>
    <tr>
      <th>기능</th>
      <th>설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>소셜 로그인</td>
      <td>카카오·구글·네이버 3사 OAuth (구글: 시스템 브라우저, 카카오·네이버: WebView)</td>
    </tr>
    <tr>
      <td>온보딩</td>
      <td>보호자 프로필 + 반려견 정보 + 성격 태그 등록</td>
    </tr>
    <tr>
      <td>홈 미니 챗봇</td>
      <td>홈 탭 하단 간소화 입력 바 → 텍스트 입력 후 챗봇 탭으로 자동 이동하여 대화 시작</td>
    </tr>
    <tr>
      <td>AI 챗봇</td>
      <td>의도분류 기반 대화 (그림일기·장소추천·시설정보·일상대화)</td>
    </tr>
    <tr>
      <td>그림일기</td>
      <td>챗봇 대화 → 텍스트 일기 + 이미지 생성 → 앨범·캘린더 조회</td>
    </tr>
    <tr>
      <td>사진 → 그림</td>
      <td>사진 촬영/선택 → 동화책 스타일 변환 → 그림일기 만들기 연결</td>
    </tr>
    <tr>
      <td>장소 추천</td>
      <td>AI 기반 반려견 동반 장소 추천 + 카카오 지도</td>
    </tr>
    <tr>
      <td>경로 찾기</td>
      <td>현재 위치 → 장소까지 경로 조회 + 지도 Polyline 표시, 카카오맵·네이버지도 앱 연동</td>
    </tr>
    <tr>
      <td>다이어리</td>
      <td>즐겨찾기 일기 캘린더 조회 + 날짜별 감정 이모지 표시 + 월별 감정 통계</td>
    </tr>
    <tr>
      <td>마이페이지</td>
      <td>보호자·반려견 프로필 관리, 반려견 추가 등록</td>
    </tr>
  </tbody>
</table>

> #### 인앱 알림

모바일 앱에서는 그림일기 생성 완료, 사진 변환 완료, 일기 작성 리마인더 등의 인앱 알림을 지원합니다.
알림은 SharedPreferences 기반 로컬 저장이며, 7일 경과 시 자동 삭제됩니다.

<table width="100%">
  <thead>
    <tr>
      <th>알림 유형</th>
      <th>트리거</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>diaryReminder</code></td>
      <td>하루 한 번 일기 작성 리마인더</td>
    </tr>
    <tr>
      <td><code>diarySaved</code></td>
      <td>그림일기 저장 완료</td>
    </tr>
    <tr>
      <td><code>imageGenerated</code></td>
      <td>AI 이미지 생성 완료</td>
    </tr>
    <tr>
      <td><code>photoStyleDone</code></td>
      <td>사진 → 그림 변환 완료</td>
    </tr>
    <tr>
      <td><code>favoriteAdded</code></td>
      <td>즐겨찾기 등록</td>
    </tr>
  </tbody>
</table>

---

<div align="center">

  # 6. 빠른 시작

</div>

> #### 사전 준비

```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN23-FINAL-3Team.git
cd SKN23-FINAL-3Team
```

`.env` 파일을 저장소 root 에 배치합니다. 키 목록 권위는 §10.2 환경 설정 참조 (`.gitignore` 처리, 팀 내부 디스코드로 공유).

> #### 백엔드 + 프론트엔드 (Docker Compose, 권장)

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

- Nginx: `http://localhost` (80 → 443 리다이렉트), 운영 도메인 `https://withdog.kro.kr`
- FastAPI: 내부 네트워크 (`withdog-net`), Nginx `/api/*` 프록시 경유
- Swagger UI: `/api/docs`

> #### 백엔드 (로컬)

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS / Linux

pip install -r requirements.txt
uvicorn back.api.main:app --reload --port 8000
```

`.env` 의 `SERVER=local` 이면 sshtunnel + paramiko 로 EC2 → RDS MySQL 자동 터널링.

> #### 프론트엔드 (로컬)

```bash
cd front
pnpm install
pnpm dev
```

Vite Dev Server 3000 → FastAPI 8000 자동 프록시 (`/api/*`).

> #### 모바일 (Flutter Android)

```bash
cd mobile
flutter pub get
flutter run        # 연결된 Android 디바이스 또는 에뮬레이터
```

운영 API (`https://withdog.kro.kr/api`) 를 그대로 재사용합니다. OAuth 분기: 구글 = 시스템 브라우저 (`flutter_appauth`) / 카카오·네이버 = WebView (`flutter_inappwebview`).

---

<div align="center">

  # 7. QA 검증 및 평가

</div>

## 7.1. 성향분석

`DogScorer` / `OwnerScorer` 의 5축 점수 정의가 임의적이지 않음을 검증하기 위해, 온보딩 태그 이름과 설명 문장을 임베딩한 뒤 KMeans 군집화를 수행했습니다.

3차 실험 결과는 `assets/kmeans/K-Means_3rd_test/` 에 정리되어 있으며, dog / owner 모두 의미가 유사한 태그들이 인접한 군집으로 모이는 경향을 확인했습니다.

정량 지표상 silhouette 최고값은 `k=4`에서 관찰되었지만, 최종 해석과 문서화는 성향 축 설명의 일관성을 고려해 `k=5` 결과도 함께 검토했습니다.

<br />

#### 성향 점수 최적화 라운드 결과

<div align="center">

  <img src="./assets/성향점수 평가 그래프.png" alt="성향점수 평가 추이" width="92%" />

</div>

> #### 성향 점수 평가셋 및 추천 영향 평가

성향 점수가 실제 장소 추천 순위에 반영되는지 확인하기 위해 별도 평가셋과 자동 평가 스크립트(`ai/evaluation/run_trait_score_evaluation.py`)를 구성했습니다.

| 항목 | 값 |
| --- | --- |
| 평가 파일 | `data/eval/성향 점수 평가셋_50문항.xlsx` |
| 원본 질문 | 50문항 |
| 평가 row | 1,750건 (50문항 × 35개 성향 프로필 조합) |
| 프로필 구성 | DOG_ONLY 250건 / OWNER_ONLY 250건 / MIXED 1,250건 |
| 주요 입력 컬럼 | `profile_category`, `tag_or_tags`, `primary_axis`, `expected_type`, `preferred_categories`, `avoid_categories`, `정답` |
| 평가 지표 | Hit@5, Recall@5, NDCG@5, 선호 카테고리 비율, 회피 카테고리 위반율, 카테고리 통과율 |

최신 실행 결과(`ai/evaluation/results/성향 점수 평가셋_50문항_20260515_014623.xlsx`) 기준, 성향 기반 재정렬은 선호 카테고리 노출과 회피 카테고리 억제에 안정적으로 기여했습니다.

| 지표 | 결과 |
| --- | ---: |
| 평균 Hit@5 | 72.1% |
| 평균 Recall@5 | 37.0% |
| 평균 NDCG@5 | 38.8% |
| 선호 카테고리 비율 | 95.9% |
| 회피 카테고리 위반율 | 0.1% |
| 카테고리 통과율 | 97.5% |

프로필 유형별로는 MIXED 성향 조합이 Hit@5 73.7%로 가장 높았고, DOG_ONLY와 OWNER_ONLY는 각각 68.0%를 기록했습니다. 이는 반려견 성향과 보호자 취향을 함께 사용할 때 추천 후보 재정렬 효과가 더 커지는 경향을 보여줍니다.


<br />

> Round 1~3 성향 점수 가중치 보정 라운드 결과:
> - **NDCG@5**: 23.75% → 38.81% (추천 품질 64% 향상)
> - **선호 카테고리 비율**: 70.75% → 95.86% (카테고리 정합성 강화)
> - **회피 카테고리 비율**: 4.01% → 0.11% (사용자 불호 영역 거의 소멸)

<br />

라운드 흐름:
- **Round 1**: 초기 가중치 (서비스 기획 기반)
- **Round 2**: NDCG@5 결과 보고 가중치 조정
- **Round 3**: 회피 카테고리 비율 보고 최종 안정화

핵심 인사이트: 추천 품질 상승 + 카테고리 정합성 동시 개선. 평가 메트릭 기반 반복 라운드로 가중치 보정 효과 검증.

## 7.2. AI 장소 추천

장소추천 검색 품질을 정량 측정하기 위해 자동화 평가 시스템 (`ai/evaluation/`) 을 구축하고, `run_ablation.py` 로 Combined / RDB only / RAG only 성능을 비교했습니다.

> #### 평가셋 구성

<table width="100%">
  <thead>
    <tr>
      <th>항목</th>
      <th>값</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>평가 파일</td>
      <td>`data/eval/장소추천 평가셋 NEW.xlsx`</td>
    </tr>
    <tr>
      <td>평가 건수</td>
      <td>131건</td>
    </tr>
    <tr>
      <td>평가 모드</td>
      <td>Combined / RDB only / RAG only</td>
    </tr>
    <tr>
      <td>카테고리</td>
      <td>9종</td>
    </tr>
  </tbody>
</table>

카테고리 9종 — GPS 사용자 현재 위치 / 실내·실외 / 동반 조건 특수 / 편의시설(주차) / 시간 조건 / 복합 조건 / 위치 기반 근처 / 지역 × 장소유형 / 주관 형용사.

<br />

> #### 메트릭

<table width="100%">
  <thead>
    <tr>
      <th>메트릭</th>
      <th>정의</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>**Hit@k**</td>
      <td>Top-k 안에 정답이 하나라도 있는 비율 (이진 0 / 1)</td>
    </tr>
    <tr>
      <td>**Recall@k**</td>
      <td>정답이 여러 개일 때 Top-k 안에 포함된 정답 비율 (0.0 ~ 1.0)</td>
    </tr>
  </tbody>
</table>

<br />

> #### 5차 Baseline → 6차 Final → 7차 Stabilized 결과

5차 baseline에서는 Combined와 RDB only가 전 구간 동일하게 나타났습니다. 이는 오류가 아니라, `subjective` 가 비어 있을 때 ChromaDB 재순위를 생략하고 RDB fallback으로 조기 반환하던 로직 때문이었습니다. 6차 final에서는 후보 수 확대, Chroma 후보 제한 완화, `subjective` empty fallback 제거, 장소 유형 필터 완화를 반영했습니다. 7차 stabilized에서는 같은 평가셋 기준으로 GPS·지역 조건 보존과 후처리 필터를 안정화해 Combined Hit@5가 63.4%까지 개선되었습니다.

<div align="center">

  <img src="./assets/장소추천 평가 그래프.png" alt="장소 검색 평가 Hit@5 개선 추이" width="92%" />

</div>

<br />

> #### 회차별 Hit@5 추이

<table width="100%">
  <thead>
    <tr>
      <th>회차</th>
      <th>핵심 변경</th>
      <th align="right">Combined</th>
      <th align="right">RDB only</th>
      <th align="right">RAG only</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>5차 Baseline</td>
      <td>신규 평가셋 기준 baseline</td>
      <td align="right">29.0%</td>
      <td align="right">29.0%</td>
      <td align="right">61.1%</td>
    </tr>
    <tr>
      <td>6차 Final</td>
      <td>후보 수 확대 + Chroma/RDB 결합 개선 + subjective empty fallback 제거 + 장소 유형 필터 완화</td>
      <td align="right">62.6%</td>
      <td align="right">34.4%</td>
      <td align="right">61.1%</td>
    </tr>
    <tr>
      <td>7차 Stabilized</td>
      <td>GPS·지역 조건 보존 + 후처리 필터 안정화</td>
      <td align="right">63.4%</td>
      <td align="right">40.5%</td>
      <td align="right">61.8%</td>
    </tr>
  </tbody>
</table>

<br />

> #### Combined 최신 지표

<table width="100%">
  <thead>
    <tr>
      <th>지표</th>
      <th align="right">5차 Baseline</th>
      <th align="right">6차 Final</th>
      <th align="right">7차 Stabilized</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Combined Hit@1</td>
      <td align="right">26.0%</td>
      <td align="right">37.4%</td>
      <td align="right">38.2%</td>
    </tr>
    <tr>
      <td>Combined Hit@3</td>
      <td align="right">26.7%</td>
      <td align="right">55.0%</td>
      <td align="right">55.7%</td>
    </tr>
    <tr>
      <td>Combined Hit@5</td>
      <td align="right">29.0%</td>
      <td align="right">62.6%</td>
      <td align="right">63.4%</td>
    </tr>
    <tr>
      <td>Combined Hit@10</td>
      <td align="right">34.4%</td>
      <td align="right">77.1%</td>
      <td align="right">77.1%</td>
    </tr>
    <tr>
      <td>Combined Hit@20</td>
      <td align="right">55.7%</td>
      <td align="right">84.0%</td>
      <td align="right">82.4%</td>
    </tr>
    <tr>
      <td>Combined Recall@5</td>
      <td align="right">2.6%</td>
      <td align="right">11.5%</td>
      <td align="right">10.2%</td>
    </tr>
    <tr>
      <td>Combined Recall@20</td>
      <td align="right">8.6%</td>
      <td align="right">35.9%</td>
      <td align="right">34.2%</td>
    </tr>
  </tbody>
</table>

> #### 카테고리별 주요 변화 (Combined, Hit@5)

<table width="100%">
  <thead>
    <tr>
      <th>카테고리</th>
      <th align="right">5차 Baseline</th>
      <th align="right">7차 Stabilized</th>
      <th align="right">변화</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>주관 형용사</td>
      <td align="right">4.2%</td>
      <td align="right">87.5%</td>
      <td align="right">+83.3%p</td>
    </tr>
    <tr>
      <td>지역 × 장소유형</td>
      <td align="right">12.5%</td>
      <td align="right">62.5%</td>
      <td align="right">+50.0%p</td>
    </tr>
    <tr>
      <td>위치 기반 근처</td>
      <td align="right">20.0%</td>
      <td align="right">53.3%</td>
      <td align="right">+33.3%p</td>
    </tr>
    <tr>
      <td>시간 조건</td>
      <td align="right">27.3%</td>
      <td align="right">63.6%</td>
      <td align="right">+36.3%p</td>
    </tr>
    <tr>
      <td>복합 조건</td>
      <td align="right">20.7%</td>
      <td align="right">41.4%</td>
      <td align="right">+20.7%p</td>
    </tr>
    <tr>
      <td>편의시설 (주차)</td>
      <td align="right">44.4%</td>
      <td align="right">55.6%</td>
      <td align="right">+11.2%p</td>
    </tr>
    <tr>
      <td>GPS 사용자 현재 위치</td>
      <td align="right">75.0%</td>
      <td align="right">75.0%</td>
      <td align="right">유지</td>
    </tr>
    <tr>
      <td>실내·실외</td>
      <td align="right">70.0%</td>
      <td align="right">70.0%</td>
      <td align="right">유지</td>
    </tr>
    <tr>
      <td>동반 조건 특수</td>
      <td align="right">60.0%</td>
      <td align="right">80.0%</td>
      <td align="right">+20.0%p</td>
    </tr>
  </tbody>
</table>

핵심 개선 요인은 `subjective` 가 비어 있어도 원문 query로 ChromaDB 의미 검색을 수행하도록 바꾼 점입니다. 이를 통해 Combined가 RDB fallback에 머무르지 않고 RAG only 수준 이상의 성능을 보였으며, 이후 RDB 정렬 보강과 실서비스 오류 수정으로 7차 stabilized 기준 RDB only도 29.0% → 40.5%까지 개선되었습니다.

```bash
python ai/evaluation/run_ablation.py
```

<br />

> #### 평가 관점

<table width="100%">
  <thead>
    <tr>
      <th>평가 관점</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>검색 의도 적합성</td>
      <td>사용자 쿼리와 추천 장소가 의미적으로 관련 있는지 확인</td>
    </tr>
    <tr>
      <td>반려견 성향 적합성</td>
      <td>반려견의 활동성, 사회성, 예민함 등과 장소 특성이 맞는지 확인</td>
    </tr>
    <tr>
      <td>보호자 취향 적합성</td>
      <td>보호자의 자연 선호, 도시 선호, 먹거리 선호 등과 장소가 맞는지 확인</td>
    </tr>
    <tr>
      <td>장소 조건 적합성</td>
      <td>반려견 동반 가능 여부, 실내외 정보, 카테고리 정보가 적절한지 확인</td>
    </tr>
    <tr>
      <td>추천 이유 품질</td>
      <td>추천 사유가 사용자가 이해할 수 있게 설명되는지 확인</td>
    </tr>
  </tbody>
</table>

<br />

> #### 자동화 평가 흐름

평가 시스템은 외부 의존 없이 자체 인프라 (`ai/evaluation/`) 로 구축되어, 검색 로직 변경 후 즉시 회귀 테스트가 가능합니다.

```bash
# 전체 평가셋 단건 평가
python ai/evaluation/run_evaluation.py

# Combined / RDB only / RAG only Ablation
python ai/evaluation/run_ablation.py

# 개선 전·후 비교 (run_id 컬럼으로 다회 실행 구분)
python ai/evaluation/run_evaluation.py --output evaluation/results/before.xlsx
# (검색 로직 개선 작업)
python ai/evaluation/run_evaluation.py --output evaluation/results/after.xlsx
```

> #### 산출물

<table width="100%">
  <thead>
    <tr>
      <th>산출물</th>
      <th>경로 / 컬럼</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>결과 엑셀</td>
      <td>`evaluation/results/eval_results_YYYYMMDD_HHMMSS.xlsx`</td>
    </tr>
    <tr>
      <td>실행 로그</td>
      <td>`evaluation/logs/run_YYYYMMDD_HHMMSS.log` (쿼리별 상세 기록)</td>
    </tr>
    <tr>
      <td>주요 컬럼</td>
      <td>`카테고리`, `사용자질문`, `정답`, `mode`, `k`, `top1~top20`, `hit_at_k`, `recall_at_k`, `failure_type`, `rdb_debug_top_names`</td>
    </tr>
  </tbody>
</table>

CLI 옵션은 `--limit N` (빠른 확인), `--category "..."` (카테고리 필터), `--verbose` (각 쿼리 top5 출력), `--input` (외부 평가셋 지정) 등을 지원합니다.

<br />

## 7.3. AI 그림일기

생성 이미지의 품질을 자동으로 측정하고, 저품질 결과를 사전 필터링하기 위한 CV + LLM 하이브리드 평가 시스템입니다.
139장의 사람 평가 정답(Ground Truth)을 기준으로 7차에 걸쳐 개선하였습니다.

<br />

> #### 품질 등급 (L0~L5)

생성된 이미지는 품질 상태에 따라 `L0~L5` 등급으로 분류합니다.

<table width="100%">
  <thead>
    <tr>
      <th>등급</th>
      <th>점수</th>
      <th>의미</th>
      <th>설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>L0</td>
      <td>0~2점</td>
      <td>생성 실패</td>
      <td>이미지 생성 실패, 저장 실패, 이미지 손상, 형태 식별 불가</td>
    </tr>
    <tr>
      <td>L1</td>
      <td>3~6점</td>
      <td>사용 불가</td>
      <td>강아지 미검출, 강아지 수 오류, 심한 왜곡, 멀티패널, 텍스트 삽입 등 치명 오류</td>
    </tr>
    <tr>
      <td>L2</td>
      <td>7~10점</td>
      <td>매우 미흡</td>
      <td>강아지는 보이나 얼굴/다리/배경/스타일 오류가 많아 그림일기로 쓰기 어려움</td>
    </tr>
    <tr>
      <td>L3</td>
      <td>11~13점</td>
      <td>미흡</td>
      <td>기본 장면은 보이나 프롬프트 반영, 배경, 선명도, 스타일 완성도가 부족함</td>
    </tr>
    <tr>
      <td>L4</td>
      <td>14~16점</td>
      <td>보통</td>
      <td>강아지와 장면이 대체로 자연스럽고, 그림일기 스타일로 활용 가능</td>
    </tr>
    <tr>
      <td>L5</td>
      <td>17~18점</td>
      <td>우수</td>
      <td>강아지 외형, 장면, 스타일, 배경, 프롬프트 반영이 모두 우수하고 치명 오류 없음</td>
    </tr>
  </tbody>
</table>

<br />

> #### 캡 규칙 (치명 오류 → 최대 레벨 강제)

총점과 무관하게 치명 오류가 있으면 해당 등급 이하로 강제 분류합니다.

<table width="100%">
  <thead>
    <tr>
      <th>치명 오류</th>
      <th>최대 레벨</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>이미지 생성 실패 / 강아지 없음</td>
      <td>L0</td>
    </tr>
    <tr>
      <td>강아지 1마리 아님 / 멀티패널·분할 화면</td>
      <td>L1</td>
    </tr>
    <tr>
      <td>심한 얼굴·다리 왜곡</td>
      <td>L2</td>
    </tr>
    <tr>
      <td>텍스트 삽입 / 프롬프트 핵심 장면 불일치</td>
      <td>L3 이하</td>
    </tr>
  </tbody>
</table>

<br />

> #### 평가 항목 18종 — 평가기별 실제 모델 적용

<table width="100%">
  <thead>
    <tr>
      <th>카테고리</th>
      <th>item_key</th>
      <th>체크 항목</th>
      <th>CV7</th>
      <th>LLM4</th>
      <th>Hybrid</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>피사체</td>
      <td><code>dog_visible</code></td>
      <td>강아지가 명확히 검출되는가</td>
      <td>CLIP cosine diff (θ=0.020)</td>
      <td>GPT-4o</td>
      <td><b>CV</b></td>
    </tr>
    <tr>
      <td>피사체</td>
      <td><code>face_clear</code></td>
      <td>강아지 얼굴이 왜곡 없이 선명한가</td>
      <td>CLIP ¹</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>피사체</td>
      <td><code>no_duplicate_face_parts</code></td>
      <td>눈·코·귀가 중복 생성되지 않았는가</td>
      <td>기본값 1 ²</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>피사체</td>
      <td><code>no_extra_legs</code></td>
      <td>다리가 추가 생성되지 않았는가</td>
      <td>기본값 1 ²</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>피사체</td>
      <td><code>one_dog</code></td>
      <td>강아지가 정확히 1마리인가</td>
      <td>YOLOv8 ³</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>구도</td>
      <td><code>no_mirror</code></td>
      <td>반사/거울 이미지가 없는가</td>
      <td>기본값 1 ²</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>구도</td>
      <td><code>no_multi_panel</code></td>
      <td>단일 장면인가</td>
      <td>OpenCV Hough Lines</td>
      <td>GPT-4o</td>
      <td><b>CV</b></td>
    </tr>
    <tr>
      <td>스타일</td>
      <td><code>pastel_style</code></td>
      <td>파스텔 그림책 스타일인가</td>
      <td>CLIP ⁴</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>스타일</td>
      <td><code>no_realistic_rendering</code></td>
      <td>사실적 렌더링이 혼입되지 않았는가</td>
      <td>CLIP ⁴</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>사람</td>
      <td><code>human_prompt_consistency</code></td>
      <td>사람 표현이 보호자 설명과 일치하는가</td>
      <td>— (null)</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>사람</td>
      <td><code>human_face_clear</code></td>
      <td>사람 얼굴이 왜곡되지 않았는가</td>
      <td>— (null)</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>프롬프트</td>
      <td><code>prompt_reflected</code></td>
      <td>프롬프트 장면이 반영되었는가</td>
      <td>CLIP 활동 키워드 (18종)</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>배경</td>
      <td><code>brightness_ok</code></td>
      <td>밝기가 적절한가</td>
      <td>OpenCV 평균 밝기 (55~215)</td>
      <td>GPT-4o</td>
      <td><b>CV</b></td>
    </tr>
    <tr>
      <td>배경</td>
      <td><code>sharpness_ok</code></td>
      <td>충분히 선명한가</td>
      <td>OpenCV Laplacian (≥80)</td>
      <td>GPT-4o</td>
      <td><b>CV</b></td>
    </tr>
    <tr>
      <td>배경</td>
      <td><code>pastel_color_ok</code></td>
      <td>파스텔 색감 범위 내인가</td>
      <td>OpenCV HSV 채도 (20~165) ⁴</td>
      <td>GPT-4o</td>
      <td><b>CV</b></td>
    </tr>
    <tr>
      <td>배경</td>
      <td><code>time_palette_ok</code></td>
      <td>주간/야간 팔레트가 일치하는가</td>
      <td>OpenCV 밝기 + 시간 키워드</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>배경</td>
      <td><code>place_context_ok</code></td>
      <td>배경 장소가 활동과 일치하는가</td>
      <td>CLIP 장소 키워드 (13종)</td>
      <td>GPT-4o</td>
      <td><b>LLM</b></td>
    </tr>
    <tr>
      <td>기타</td>
      <td><code>no_text</code></td>
      <td>텍스트가 삽입되지 않았는가</td>
      <td>EasyOCR</td>
      <td>GPT-4o</td>
      <td><b>CV</b></td>
    </tr>
  </tbody>
</table>

> ¹ CLIP face_clear는 정밀도가 낮아 Hybrid에서 LLM으로 대체
> ² GT 139장에서 전수 통과 확인 → 평가 미수행, 기본값 1 처리
> ³ YOLOv8은 파스텔 일러스트에서 인식률이 낮아 Hybrid에서 LLM으로 대체
> ⁴ 139장 전체에서 동일 점수 → 현재 데이터셋 내 변별력 없음, 데이터 확장 시 재평가 필요
> Hybrid: `dog_visible=0` 시 LLM 호출 스킵 (비용 최적화)
> Hybrid 구성: CV 6개 항목 (객관 측정) + LLM 12개 항목 (주관 판단)

<br />

> #### 평가기 성능 비교 (139장 기준)

<table width="100%">
  <thead>
    <tr>
      <th>평가기</th>
      <th>평가 항목 수</th>
      <th align="right">정확 일치율</th>
      <th align="right">±1 등급 정확도</th>
      <th align="right">평균 오차 (MAE)</th>
      <th>편향</th>
      <th align="right">API 비용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>CV7 단독</td>
      <td>16개</td>
      <td align="right">28.1%</td>
      <td align="right"><b>79.1%</b></td>
      <td align="right"><b>0.99</b></td>
      <td>-0.18 (약간 과소평가)</td>
      <td align="right"><b>$0</b></td>
    </tr>
    <tr>
      <td>LLM4 단독 (GPT-4o)</td>
      <td>18개</td>
      <td align="right">34.5%</td>
      <td align="right">71.2%</td>
      <td align="right">1.08</td>
      <td>+0.68 (과대평가)</td>
      <td align="right">$1.58</td>
    </tr>
    <tr>
      <td><b>Hybrid (CV7 + LLM4)</b></td>
      <td><b>18개</b> (CV 6 + LLM 12)</td>
      <td align="right"><b>37.4%</b></td>
      <td align="right">72.7%</td>
      <td align="right">1.07</td>
      <td>+0.53 (과대평가)</td>
      <td align="right">$1.10</td>
    </tr>
  </tbody>
</table>

> Hybrid는 LLM의 과대평가 경향이 유입되면서 ±1 정확도는 CV7보다 하락하지만, 정확 일치율은 세 평가기 중 최고. CV7의 과소평가와 LLM4의 과대평가가 상호 보정되어 정확 일치에서 이점을 가짐.

<br />

> #### 사용 모델

<table width="100%">
  <thead>
    <tr>
      <th>모델</th>
      <th>용도</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>CLIP (ViT-B-32)</td>
      <td>강아지 검출, 스타일 분류, 프롬프트·장소 키워드 매칭</td>
    </tr>
    <tr>
      <td>YOLOv8-nano</td>
      <td>강아지 수 카운팅 (보조)</td>
    </tr>
    <tr>
      <td>GPT-4o Vision</td>
      <td>주관적 항목 12종 평가 (LLM / Hybrid)</td>
    </tr>
    <tr>
      <td>EasyOCR</td>
      <td>이미지 내 텍스트 검출</td>
    </tr>
    <tr>
      <td>OpenCV</td>
      <td>밝기, 선명도(Laplacian), 색감(HSV), 분할선(Hough Lines)</td>
    </tr>
  </tbody>
</table>

<br />

> #### GT 점수 분포 (139장)

<table width="100%">
  <thead>
    <tr>
      <th>등급</th>
      <th align="right">이미지 수</th>
      <th align="right">비율</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>L0</td>
      <td align="right">0장</td>
      <td align="right">0%</td>
    </tr>
    <tr>
      <td>L1</td>
      <td align="right">6장</td>
      <td align="right">4.3%</td>
    </tr>
    <tr>
      <td>L2</td>
      <td align="right">26장</td>
      <td align="right">18.7%</td>
    </tr>
    <tr>
      <td>L3</td>
      <td align="right">21장</td>
      <td align="right">15.1%</td>
    </tr>
    <tr>
      <td>L4</td>
      <td align="right">42장</td>
      <td align="right">30.2%</td>
    </tr>
    <tr>
      <td>L5</td>
      <td align="right">44장</td>
      <td align="right">31.7%</td>
    </tr>
  </tbody>
</table>

> 평균 총점: 13.81 / 18점. L0이 0장인 이유는 평가셋이 생성 성공 이미지만 수집한 결과.

<br />

> #### 사용자 가치

<table width="100%">
  <thead>
    <tr>
      <th>구분</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>저품질 필터링</td>
      <td>L0~L2 이미지를 자동 감지하여 서비스 노출 전 차단</td>
    </tr>
    <tr>
      <td>품질 모니터링</td>
      <td>수동 QA 없이 생성 품질을 정량적으로 추적</td>
    </tr>
    <tr>
      <td>비용 효율</td>
      <td>Hybrid 평가기로 비용 30% 절감 ($1.58 → $1.10) 하면서 최고 정확 일치율 달성</td>
    </tr>
  </tbody>
</table>

<br />

> #### 향후 개선 방향

현재 Hybrid는 18개 항목 중 CV 6개 / LLM 12개로 구성되어 LLM 의존도가 높습니다.
비전 모델을 단계적으로 도입하여 CV 커버리지를 확대하고, LLM 호출량과 비용을 줄이는 방향입니다.

<table width="100%">
  <thead>
    <tr>
      <th>도입 모델</th>
      <th>대상 항목</th>
      <th>기대 효과</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>동물 자세 추정 (AnimalPose 등) + 커스텀 keypoint 학습</td>
      <td><code>no_duplicate_face_parts</code>, <code>no_extra_legs</code></td>
      <td>기본값 1 → 실측 평가 전환</td>
    </tr>
    <tr>
      <td>경량 VLM (Qwen2.5-VL 등)</td>
      <td><code>no_mirror</code>, <code>human_prompt_consistency</code>, <code>pastel_style</code>, <code>time_palette_ok</code>, <code>place_context_ok</code></td>
      <td>LLM 전용 5개 항목 → CV로 이관</td>
    </tr>
    <tr>
      <td>얼굴 검출 (MediaPipe 등)</td>
      <td><code>human_face_clear</code></td>
      <td>null → 사람 얼굴 왜곡 실탐지</td>
    </tr>
    <tr>
      <td>CLIP ViT-L-14</td>
      <td><code>no_realistic_rendering</code>, <code>prompt_reflected</code></td>
      <td>비전형 견종·스타일 인식 정밀도 향상</td>
    </tr>
    <tr>
      <td>PaddleOCR</td>
      <td><code>no_text</code></td>
      <td>EasyOCR 대비 인식률 개선 검토</td>
    </tr>
  </tbody>
</table>

<table width="100%">
  <thead>
    <tr>
      <th>과제</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>CV 항목 확대</td>
      <td>현재 6 / 18 → 단계적으로 CV 커버리지 확대, LLM 호출량 절감</td>
    </tr>
    <tr>
      <td>저품질 변별력 강화</td>
      <td>GT=L1~L2 이미지를 과대평가하는 문제(13건)가 주요 오차 원인, 해당 영역 우선 개선</td>
    </tr>
    <tr>
      <td>등급 경계 보정</td>
      <td>총점 → 등급 변환 함수를 데이터 기반으로 세밀화하여 정확 일치율 향상</td>
    </tr>
  </tbody>
</table>

<br />

---

<br />

<div align="center">

  # 8. 서비스 아키텍처

  ![시스템아키텍처](./assets/시스템아키텍처.png)

</div>

<br />

> #### 요청 흐름

<table width="100%">
  <thead>
    <tr>
      <th>요청 유형</th>
      <th>경로</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>페이지 접근</td>
      <td>브라우저 → Nginx → React SPA (index.html) → 클라이언트 라우팅</td>
    </tr>
    <tr>
      <td>API 호출</td>
      <td>브라우저 → Nginx (`/api/*`) → FastAPI 백엔드 (internal)</td>
    </tr>
    <tr>
      <td>정적 파일</td>
      <td>브라우저 → Nginx (직접 서빙, 1년 캐시)</td>
    </tr>
    <tr>
      <td>이미지 업로드</td>
      <td>프론트 → FastAPI → AWS S3 (aioboto3 비동기)</td>
    </tr>
    <tr>
      <td>그림일기 생성</td>
      <td>FastAPI → ChromaDB(RAG) → OpenAI GPT → gpt-image-1 → S3 저장</td>
    </tr>
  </tbody>
</table>

<br />

> #### 로컬 개발 환경

```
로컬 머신
    │
    ├─ FastAPI (uvicorn --reload, port 8000)
    │       │
    │       └─ SSH 터널 (sshtunnel + paramiko)
    │               │
    │               └─ AWS EC2 → AWS RDS MySQL (port 3306)
    │
    ├─ Vite Dev Server (port 3000)
    │       └─ /api/* → proxy → localhost:8000
    │
    └─ .env  SERVER=local  (EC2 환경에서는 SERVER=ec2)
```

- **도메인**: `https://withdog.kro.kr` (HTTPS, Let's Encrypt 인증서) → EC2 퍼블릭 IP 연결 (무료 도메인, kro.kr)  
- **컨테이너 포트**: Nginx만 `80:80` / `443:443` 외부 노출 (80 → 443 리다이렉트), 백엔드는 내부 네트워크(`withdog-net`)로만 통신

<br />

---

<div align="center">

  # 9. 데이터베이스 설계

</div>

- DBMS: AWS RDS MySQL 8.0, charset `utf8mb4_unicode_ci`, 엔진 `InnoDB`.  
- DDL 원본: `back/db/withDOG.sql`, `back/db/migrations/`, `back/db/migrate_add_pet_profiles.sql`.
- ORM 매핑: `back/api/models/`.
- 런타임 생성 테이블: `api_costs` (`ai/infrastructure/cost_tracker.py`).

> #### ERD 다이어그램

<div align="center">

  ![ERD](./assets/ERD.png)

</div>

> #### 테이블 목록 (총 12개)

<details>
<summary><b>테이블 목록 펼쳐 보기 (총 12개)</b></summary>

<br />

<table width="100%">
  <thead>
    <tr>
      <th>테이블</th>
      <th>용도</th>
      <th>Soft Delete</th>
      <th>비고</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>`users`</td>
      <td>소셜 로그인 사용자</td>
      <td>✓ (`deleted_at`)</td>
      <td>UNIQUE(provider, provider_id)</td>
    </tr>
    <tr>
      <td>`pets`</td>
      <td>반려견</td>
      <td>✓</td>
      <td>breed_id RESTRICT, type_id RESTRICT</td>
    </tr>
    <tr>
      <td>`breeds`</td>
      <td>견종 마스터 (173종)</td>
      <td>—</td>
      <td>시드 1회성</td>
    </tr>
    <tr>
      <td>`keywords`</td>
      <td>성향 태그 (PET / USER)</td>
      <td>—</td>
      <td>description = JSON 점수 벡터</td>
    </tr>
    <tr>
      <td>`chat_rooms`</td>
      <td>챗봇 대화 세션</td>
      <td>✓</td>
      <td>룸 삭제해도 메시지 보존</td>
    </tr>
    <tr>
      <td>`chat_messages`</td>
      <td>대화 메시지</td>
      <td>✗ (영구 보존)</td>
      <td>role: user / assistant / system</td>
    </tr>
    <tr>
      <td>`diaries`</td>
      <td>그림일기 (6하원칙)</td>
      <td>✓</td>
      <td>diary_date, is_favorite, image_id nullable</td>
    </tr>
    <tr>
      <td>`images`</td>
      <td>S3 이미지 메타</td>
      <td>✓</td>
      <td>file_url, file_name</td>
    </tr>
    <tr>
      <td>`places`</td>
      <td>반려견 동반 장소 (약 22,102건)</td>
      <td>—</td>
      <td>content_id UNIQUE, 입장료/추가요금 컬럼 포함</td>
    </tr>
    <tr>
      <td>`favorite_places`</td>
      <td>사용자별 즐겨찾기 장소</td>
      <td>—</td>
      <td>UNIQUE(user_id, place_id)</td>
    </tr>
    <tr>
      <td>`pet_profiles`</td>
      <td>반려견 이미지 분석 프로필</td>
      <td>—</td>
      <td>pet_id UNIQUE, profile_json 저장</td>
    </tr>
    <tr>
      <td>`api_costs`</td>
      <td>OpenAI API 호출 비용 추적</td>
      <td>—</td>
      <td>런타임 자동 생성, FK 없음</td>
    </tr>
  </tbody>
</table>

</details>

<br />

> #### 관계 (ER)

<details>
<summary><b>ER 관계 펼쳐 보기</b></summary>

```text
users 1 ─── N pets
users 1 ─── N chat_rooms ── N chat_messages
users 1 ─── N diaries N ─── 1 pets
users.profile_id      ── 1 images   (nullable)
users.type_id         ── 1 keywords (nullable, USER 카테고리)
users.primary_pet_id  ── 1 pets     (nullable)
pets.breed_id         ── 1 breeds
pets.type_id          ── 1 keywords (nullable, PET 카테고리)
pets.image_id         ── 1 images   (nullable)
diaries.image_id      ── 1 images   (nullable)
pet_profiles.pet_id   ── 1 pets     (UNIQUE)
pet_profiles.image_id ── 1 images   (nullable)
users N ─── M places      via favorite_places
api_costs                 독립 비용 추적 테이블
```

</details>

<br />

> #### 설계 원칙

- **Soft Delete + 10일 후 Hard Delete** — `users` / `pets` / `chat_rooms` / `diaries` / `images` 는 `deleted_at` 컬럼으로 soft delete. 모든 조회 쿼리는 `WHERE deleted_at IS NULL` 자동 추가하며, `users` 만 APScheduler 가 매일 03:00 `deleted_at < now() - 10 days` 사용자를 물리 삭제합니다.
- **2-phase 다이어리 저장** — `diaries.image_id = NULL` 로 일기 행 먼저 생성 → 이미지 생성·S3 업로드 완료 후 `PATCH` 로 바인딩. 이미지 생성 실패가 일기 본문 저장을 막지 않도록 분리.
- **반려견 이미지 분석 프로필** — `pet_profiles` 는 반려견 1마리당 1개 프로필을 `profile_json` 으로 저장하며, `pet_id` 에 UNIQUE 제약을 둡니다.
- **chat_messages 영구 보존** — `chat_rooms` 가 soft delete 되어도 메시지는 보존됩니다 (룸 복구·학습 데이터 활용 목적).
- **이미지 참조 분리** — `users.profile_id`, `pets.image_id`, `diaries.image_id`, `pet_profiles.image_id` 가 `images` 를 참조하며, 사용자/반려견/일기/분석 프로필 이미지 메타를 공통 테이블로 관리합니다.
- **인덱스 전략** — 사용자 식별 `(provider, provider_id)` UNIQUE, 룸 정렬 `(user_id, updated_at)`, 메시지 정렬 `(room_id, created_at)`, 일기 필터 `(user_id, diary_date, deleted_at)` / `(user_id, is_favorite, deleted_at)`, 장소 위치 `(latitude, longitude)`, 장소 요금 타입 `(entrance_fee_type)` / `(extra_fee_type)`, 즐겨찾기 `(user_id, place_id)` UNIQUE.
- **API 비용 추적** — `api_costs` 는 `OpenAICostTracker` 가 생성하는 독립 테이블로, 모델명·호출 유형·토큰 수·비용을 기록합니다.

---

<div align="center">

  #  10. 디렉토리 구조

</div>

<details>
<summary><b>디렉토리 구조 펼쳐 보기</b></summary>

```
SKN23-FINAL-3Team/
├── front/                      # React 프론트엔드
│   └── src/app/
│       ├── pages/              # HomePage, MyPage, CalendarPage, LoginPage, Step2Page, OAuthCallbackPage
│       ├── components/         # ChatBot, ChatHistory, Navbar, MapView, DiaryView, DogProfileCard ...
│       ├── services/           # API 클라이언트 (userService, diaryService, chatService ...)
│       ├── hooks/              # useChatbot
│       └── types/              # 공통 타입 정의
│
├── back/
│   ├── main.py                 # 진입점 (back/api/main.py 로더)
│   ├── api/                    # FastAPI 백엔드
│   │   ├── main.py             # FastAPI 앱 (lifespan, 라우터 등록)
│   │   ├── routers/            # 14개 등록 라우터 (auth, users, pets, diaries, chat-rooms, chat-messages, images, places, breeds, keywords, admin, diary_photo, directions, eval) + intent_router.py 보관
│   │   ├── services/           # 23종 (chat_response, diary_response, chat_message, place, user, pet, diary, chat_room, image, breed, keyword, intent, auth, admin, common, scheduler, favorite_place, pet_profile, photo_detector, photo_illustration, photo_validation, photo_vlm, place_image)
│   │   ├── models/             # 11개 SQLAlchemy 모델
│   │   ├── schemas/            # 10개 Pydantic 스키마
│   │   └── core/               # config, database, deps, location, type
│   ├── data/scripts/           # breeds / keywords / places 시드 (2026-04-27 back/db/seeds/ 에서 이동)
│   └── db/
│       └── withDOG.sql         # MySQL DDL 덤프
│
├── ai/
│   ├── chains/                 # DiaryChain (RAG + GPT 일기 생성 파이프라인)
│   ├── prompts/                # DiaryPromptBuilder (일기·이미지 프롬프트 빌더)
│   ├── retrievers/             # BreedRetriever, DiaryRetriever, PlacesRetriever
│   ├── scorers/                # DogScorer, OwnerScorer (성향 태그 점수화)
│   ├── intent/                 # KoELECTRA 의도 분류 모델 학습·추론
│   ├── infrastructure/         # AIContainer, OpenAICostTracker, Embedder, VectorStore
│   ├── eval/                   # 이미지 품질 자동 평가 (피사체순도·배경품질·스타일일관성)
│   ├── core/                   # ChromaDB 클라이언트, 인터페이스
│   └── utils/                  # 공통 유틸리티
│
├── mobile/                     # Flutter 모바일 (Android 풀 포팅, 5/20 시연 데모)
│   ├── lib/
│   │   ├── features/           # auth, calendar, chat, diary, home, inquiry,
│   │   │                       #   intro, mypage, notification, onboarding, places
│   │   ├── shared/             # 공통 위젯·모델·서비스
│   │   └── core/               # theme, network, env helper
│   ├── pubspec.yaml            # Flutter 3.41 / Riverpod / Dio / image_picker / InAppWebView
│   └── android/                # Android 빌드 설정 (mipmap, Adaptive Icon)
│
├── data/                       # 장소·견종 데이터 및 임베딩 스크립트
├── infra/docker/               # Dockerfile, docker-compose
└── requirements.txt
```

</details>

<br />

## 10.1. 주요 API 엔드포인트

<details>
<summary><b>주요 API 엔드포인트 펼쳐 보기</b></summary>

<br />

<table width="100%">
  <thead>
    <tr>
      <th>메서드</th>
      <th>경로</th>
      <th>설명</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GET</td>
      <td>`/api/health`</td>
      <td>헬스체크 (server / db 상태)</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/auth/{provider}`</td>
      <td>소셜 로그인 (kakao / google / naver)</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/admin/token`</td>
      <td>개발용 무기한 JWT (`X-Admin-Key` 헤더)</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/users/me`</td>
      <td>내 정보 조회</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/users/me/agreements`</td>
      <td>약관·개인정보처리방침 동의 저장</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/users/{id}`</td>
      <td>사용자 조회</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td>`/api/users/{id}`</td>
      <td>유저 정보 수정</td>
    </tr>
    <tr>
      <td>DELETE</td>
      <td>`/api/users/{id}`</td>
      <td>유저 soft delete (10일 후 hard delete)</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/pets`</td>
      <td>반려견 등록</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/pets?user_id={id}`</td>
      <td>반려견 목록 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/pets/{id}`</td>
      <td>반려견 상세</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td>`/api/pets/{id}`</td>
      <td>반려견 수정</td>
    </tr>
    <tr>
      <td>DELETE</td>
      <td>`/api/pets/{id}`</td>
      <td>반려견 soft delete</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/diaries?user_id={id}`</td>
      <td>사용자별 일기 목록 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/diaries?user_id={id}&pet_id={id}`</td>
      <td>반려견별 일기 목록 조회</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/diaries`</td>
      <td>일기 생성 (image_id 없이도 생성 가능)</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/diaries/calendar?year=&month=`</td>
      <td>즐겨찾기 일기 캘린더 조회</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td>`/api/diaries/{id}`</td>
      <td>일기 수정 (image_id 바인딩 포함)</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td>`/api/diaries/{id}/favorite`</td>
      <td>일기 즐겨찾기 토글</td>
    </tr>
    <tr>
      <td>DELETE</td>
      <td>`/api/diaries/{id}`</td>
      <td>일기 soft delete</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/diary/generate`</td>
      <td>AI 일기 텍스트 생성 (GPT-4.1-mini)</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/diary/generate-image`</td>
      <td>AI 일기 이미지 생성 (gpt-image-1)</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/diary/photo-style`</td>
      <td>사진 업로드 기반 그림체 변환</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/images`</td>
      <td>이미지 S3 업로드</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/images/{id}`</td>
      <td>이미지 메타 조회</td>
    </tr>
    <tr>
      <td>DELETE</td>
      <td>`/api/images/{id}`</td>
      <td>이미지 soft delete (FK RESTRICT 검증)</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/chat-rooms`</td>
      <td>채팅방 생성 (title NULL이면 첫 메시지로 자동)</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/chat-rooms?user_id={id}`</td>
      <td>채팅방 목록 (updated_at DESC)</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/chat-rooms/{id}`</td>
      <td>채팅방 상세</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td>`/api/chat-rooms/{id}/title`</td>
      <td>채팅방 제목 변경</td>
    </tr>
    <tr>
      <td>DELETE</td>
      <td>`/api/chat-rooms/{id}`</td>
      <td>채팅방 soft delete (메시지는 보존)</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/chat-rooms/{id}/messages`</td>
      <td>채팅 메시지 전송 (챗봇 한 턴 처리)</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/chat-rooms/{id}/messages/save`</td>
      <td>AI 응답 없이 채팅 메시지 직접 저장</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td>`/api/chat-rooms/{id}/messages/{message_id}`</td>
      <td>채팅 메시지 내용 수정</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/chat-rooms/{id}/messages`</td>
      <td>채팅 메시지 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/places/search?query=&pet_id=&user_lat=&user_lng=`</td>
      <td>장소 추천 검색 (RAG + LLM reason)</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/places/by-name?name=`</td>
      <td>장소명 기반 시설 상세 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/places/favorites`</td>
      <td>즐겨찾기 장소 목록 조회</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td>`/api/places/{content_id}/favorite`</td>
      <td>장소 즐겨찾기 토글</td>
    </tr>
    <tr>
      <td>POST</td>
      <td>`/api/directions/route`</td>
      <td>카카오 Mobility 경로 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/eval/parse?query=`</td>
      <td>평가용 쿼리 파싱 결과 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/eval/places/search?query=&mode=&n=`</td>
      <td>평가용 장소 검색 (combined / rdb_only / rag_only)</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/breeds`</td>
      <td>견종 목록 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/breeds/{id}`</td>
      <td>견종 상세 조회</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/keywords?category=PET`</td>
      <td>강아지 성향 태그</td>
    </tr>
    <tr>
      <td>GET</td>
      <td>`/api/keywords?category=USER`</td>
      <td>사용자 여행 성향 태그</td>
    </tr>
  </tbody>
</table>

</details>

<br />

- API 명세서 (Postman): https://documenter.getpostman.com/view/53095517/2sBXqCPipg
- 전체 API 문서 (Swagger UI): `https://withdog.kro.kr/api/docs`

<br />

## 10.2. 환경 설정

> ### 환경변수 (.env)

카테고리별로 정리한 주요 환경변수 템플릿입니다. 값은 환경별로 직접 채워 사용하세요 (`.env`는 `.gitignore` 처리됨).

<details>
<summary><b>환경변수 템플릿 펼쳐 보기</b></summary>

  ```env
  # ── 서버 환경 ───────────────────────────────────────────────
  SERVER=               # local | ec2
  APP_ENV=
  DEBUG=
  FRONTEND_BASE_URL=
  VITE_API_URL=

  # ── 데이터베이스 (AWS RDS MySQL) ────────────────────────────
  DB_HOST=
  DB_PORT=
  DB_USER=
  DB_PASSWORD=
  DB_NAME=

  # ── SSH 터널 (local 환경 전용) ──────────────────────────────
  SSH_HOST=
  SSH_PORT=
  SSH_USER=
  SSH_PKEY=

  # ── 외부 API ────────────────────────────────────────────────
  OPENAI_API_KEY=
  DOG_API_KEY=          # The Dog API
  TOUR_API_KEY=         # 한국관광공사 OpenAPI
  KAKAO_REST_API_KEY=   # 카카오 REST API (랜드마크 좌표 조회)

  # ── OAuth 2.0 (백엔드) ──────────────────────────────────────
  GOOGLE_CLIENT_ID=
  GOOGLE_CLIENT_SECRET=
  GOOGLE_REDIRECT_URI=
  GOOGLE_ANDROID_CLIENT_ID=
  KAKAO_CLIENT_ID=
  KAKAO_CLIENT_SECRET=
  KAKAO_REDIRECT_URI=
  NAVER_CLIENT_ID=
  NAVER_CLIENT_SECRET=
  NAVER_REDIRECT_URI=

  # ── OAuth 2.0 (프론트, Vite 노출) ───────────────────────────
  VITE_GOOGLE_CLIENT_ID=
  VITE_KAKAO_CLIENT_ID=
  VITE_KAKAO_JAVASCRIPT_API_KEY=    # 카카오 지도 SDK
  VITE_NAVER_CLIENT_ID=

  # ── AWS S3 ──────────────────────────────────────────────────
  AWS_ACCESS_KEY_ID=
  AWS_SECRET_ACCESS_KEY=
  AWS_REGION=
  AWS_S3_BUCKET_NAME=

  # ── 보안 ────────────────────────────────────────────────────
  SECRET_KEY=           # JWT 서명 + 관리자 토큰 발급 (이중 용도)
  ACCESS_TOKEN_EXPIRE_MINUTES=

  # ── LLM / 임베딩 모델 ───────────────────────────────────────
  GPT_MODEL=            # 기본 모델 ID (예: gpt-4.1-mini)
  GPT_IMAGE_MODEL=      # 이미지 생성 모델 (현재 gpt-image-1)
  EMBED_MODEL_NAME=     # sentence-transformers 모델

  # ── Hugging Face / Transformers ────────────────────────────
  HF_HUB_OFFLINE=       # 0 | 1
  TRANSFORMERS_OFFLINE= # 0 | 1

  # ── 사진 분석 / 그림체 변환 ─────────────────────────────────
  USE_YOLO_PIPELINE=    # true: YOLO+VLM, false: GPT-4o Vision
  USE_YOLO_DETECTOR=
  USE_LOCAL_VLM=
  PHOTO_UPLOAD_MAX_MB=
  PHOTO_STYLE_MOCK_MODE=

  # ── 기타 ────────────────────────────────────────────────────
  ANONYMIZED_TELEMETRY= # ChromaDB 텔레메트리 무력화
  USE_DUMMY_PLACES=     # 장소 검색 디버깅용 더미 데이터 플래그
  ```

</details>

<br />

---

<div align="center">

  #  11. 비즈니스 전략

</div>

Freemium 기반으로 앱 유입 → 구독 전환 → 데이터 수익까지 확장되는 다층 수익 구조입니다.

<table width="100%">
  <thead>
    <tr>
      <th>단계</th>
      <th>모델</th>
      <th>내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>①</td>
      <td>Freemium</td>
      <td>무료 체험으로 서비스 진입 장벽 최소화</td>
    </tr>
    <tr>
      <td>②</td>
      <td>유료 구독 1단계</td>
      <td>월 10,000원 — 핵심 기능 확장</td>
    </tr>
    <tr>
      <td>③</td>
      <td>유료 구독 2단계</td>
      <td>월 25,000원 — 프리미엄 전체 개방</td>
    </tr>
    <tr>
      <td>④</td>
      <td>광고/제휴</td>
      <td>펫 친화 카페·숙소·용품 노출 기반 PPL, 예약 연계 패키지</td>
    </tr>
    <tr>
      <td>⑤</td>
      <td>B2B 데이터</td>
      <td>지역별 수요·소비 패턴 트렌드 리포트 판매 (관광사·지자체·숙박)</td>
    </tr>
  </tbody>
</table>

---

> #### 구독 티어 상세 *(고도화 시 추가 예정)*

<table width="100%">
  <thead>
    <tr>
      <th>기능</th>
      <th align="center">무료</th>
      <th align="center">1단계 (10,000원/월)</th>
      <th align="center">2단계 (25,000원/월)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>그림일기 생성</td>
      <td align="center">하루 3회</td>
      <td align="center">하루 10회</td>
      <td align="center">무제한</td>
    </tr>
    <tr>
      <td>일기 본문 길이</td>
      <td align="center">300자</td>
      <td align="center">450자</td>
      <td align="center">500자+ 세밀한 묘사</td>
    </tr>
    <tr>
      <td>감정 선택</td>
      <td align="center">6종</td>
      <td align="center">12종</td>
      <td align="center">12종</td>
    </tr>
    <tr>
      <td>그림 스타일</td>
      <td align="center">기본 1종</td>
      <td align="center">3종</td>
      <td align="center">전체 5종+</td>
    </tr>
    <tr>
      <td>그림일기 수정</td>
      <td align="center">불가</td>
      <td align="center">앱 내 일 5회</td>
      <td align="center">앱 내 일 10회</td>
    </tr>
    <tr>
      <td>등록 반려견 수</td>
      <td align="center">2마리</td>
      <td align="center">3마리</td>
      <td align="center">무제한</td>
    </tr>
    <tr>
      <td>월별 감정 리포트</td>
      <td align="center">✕</td>
      <td align="center">O</td>
      <td align="center">O</td>
    </tr>
    <tr>
      <td>클라우드 백업</td>
      <td align="center">✕</td>
      <td align="center">✕</td>
      <td align="center">O</td>
    </tr>
    <tr>
      <td>광고</td>
      <td align="center">있음</td>
      <td align="center">제거</td>
      <td align="center">제거</td>
    </tr>
  </tbody>
</table>

> 현재 MVP 단계에서는 구독 구분 없이 전체 기능을 제공합니다. 구독 시스템 및 플랜별 기능 제한은 Phase 2 모바일 앱 출시와 함께 적용될 예정입니다.

**단위 경제성**: `gpt-4.1-mini` 기반 텍스트 생성과 일일 횟수 제한으로 API 비용을 통제하며, 구독 단계가 올라갈수록 프롬프트 품질·스타일 다양성을 함께 높여 자연스러운 업그레이드 동기를 부여합니다. 향후 최신 이미지 모델 전환 시 토큰 기반 과금으로 비용 최적화가 가능합니다.

<br />

> ### 시장 기회

한국 반려동물 시장은 2023년 기준 약 **4조 5천억 원** 규모로, 2027년까지 **6조 원** 돌파가 전망됩니다. 반려동물을 가족 구성원으로 여기는 **펫팸족(Pet + Family)** 이 전체 가구의 30%를 넘어섰으며, 이들은 반려동물 관련 콘텐츠·기록·공간 탐색에 높은 지출 의향을 보입니다.

<table width="100%">
  <thead>
    <tr>
      <th>지표</th>
      <th>수치</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>국내 반려동물 양육 가구</td>
      <td>약 552만 가구 (2023, 농림축산식품부)</td>
    </tr>
    <tr>
      <td>1인당 월평균 반려동물 지출</td>
      <td>약 15만 원</td>
    </tr>
    <tr>
      <td>반려동물 앱 월간 활성 사용자(MAU) 성장률</td>
      <td>연 30%↑</td>
    </tr>
    <tr>
      <td>펫 친화 장소 등록 수요 (카카오맵 기준)</td>
      <td>연 40%↑</td>
    </tr>
  </tbody>
</table>

<br />

> ### 핵심 경쟁 우위

withDog은 단순 일기 앱이나 단순 장소 추천 앱이 아닙니다. **"기록 × 장소 × AI 개인화"** 가 결합된 점이 차별점입니다.

<table width="100%">
  <thead>
    <tr>
      <th>경쟁 요소</th>
      <th>일반 일기 앱</th>
      <th>일반 장소 앱</th>
      <th>**withDog**</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>AI 그림일기 자동 생성</td>
      <td>✕</td>
      <td>✕</td>
      <td>✅ 12가지 감정 반영</td>
    </tr>
    <tr>
      <td>반려견 성향 기반 장소 추천</td>
      <td>✕</td>
      <td>✕</td>
      <td>✅ 개성향 태그 매칭</td>
    </tr>
    <tr>
      <td>장소 → 일기 자동 연동</td>
      <td>✕</td>
      <td>✕</td>
      <td>✅ where_text 저장</td>
    </tr>
    <tr>
      <td>견종·나이별 이미지 자동 생성</td>
      <td>✕</td>
      <td>✕</td>
      <td>✅ 30종 시각 힌트</td>
    </tr>
    <tr>
      <td>감정 기반 캘린더 시각화</td>
      <td>✕</td>
      <td>✕</td>
      <td>✅ 이모지 달력</td>
    </tr>
    <tr>
      <td>반려동물 성향 데이터 누적</td>
      <td>✕</td>
      <td>✕</td>
      <td>✅ 행동·선호 패턴</td>
    </tr>
  </tbody>
</table>

> 경쟁 앱(포동이·강쥐일기·펫로그 등)은 단순 텍스트 기록 또는 커뮤니티 중심이며, **AI 생성 그림일기 + 개인화 장소 추천의 결합**은 국내 시장에서 유일한 포지셔닝입니다.

<br />

> ### 성장 플라이휠

사용자가 늘수록 데이터 품질이 올라가고, 데이터 품질이 올라갈수록 추천 정확도가 높아져 사용자가 더 모이는 **자기 강화 구조**입니다.


```
그림일기 기록 증가
      ↓
반려견 감정·행동 데이터 누적
      ↓
장소 추천 개인화 정확도 향상
      ↓
장소 방문 → 일기 기록 → 재방문 유도
      ↓
유저 Lock-in (기록이 쌓일수록 이탈 어려움)
      ↓
구독 전환율 상승 & 입소문 확산
```

<br />

> ### 파트너십 & 제휴 전략

withDog의 **장소 추천 + 방문 기록 연동** 기능은 오프라인 비즈니스와의 직접 연결 고리가 됩니다.

<table width="100%">
  <thead>
    <tr>
      <th>파트너 유형</th>
      <th>제휴 방식</th>
      <th>기대 효과</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>펫 친화 카페·레스토랑</td>
      <td>앱 내 장소 우선 노출 + 방문 기록 뱃지</td>
      <td>신규 고객 유입, 재방문 동기</td>
    </tr>
    <tr>
      <td>애견 동반 숙소·호텔</td>
      <td>여행 일기 패키지 + 예약 연계</td>
      <td>예약 수수료 수익</td>
    </tr>
    <tr>
      <td>동물병원·펫샵</td>
      <td>건강 기록 연동 + 쿠폰 발행</td>
      <td>B2B SaaS 구독</td>
    </tr>
    <tr>
      <td>지자체·관광공사</td>
      <td>펫 친화 여행 코스 공동 개발</td>
      <td>공공 데이터 제휴</td>
    </tr>
  </tbody>
</table>

<br />

> ### 장기 확장 로드맵

<table width="100%">
  <thead>
    <tr>
      <th>시기</th>
      <th>목표</th>
      <th>핵심 기능</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>**Phase 1** (현재)</td>
      <td>MVP 검증 · 초기 유저 확보</td>
      <td>AI 그림일기, 장소 추천, 감정 캘린더</td>
    </tr>
    <tr>
      <td>**Phase 2** (6개월)</td>
      <td>사용자 확장</td>
      <td>MAU 1만, 푸시 알림, 소셜 공유, 오프라인 파트너 연동</td>
    </tr>
    <tr>
      <td>**Phase 3** (1년)</td>
      <td>구독 전환 가속 · B2B 진입</td>
      <td>건강 기록 연동, 트렌드 리포트 판매, API 제공</td>
    </tr>
  </tbody>
</table>

<br />

<div align="center">

  #  12. 기술 스택

</div>

> ### Backend

<table width="100%">
  <thead>
    <tr>
      <th>분류</th>
      <th>기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Framework</td>
      <td><img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" /></td>
    </tr>
    <tr>
      <td>ORM</td>
      <td><img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" /> <img src="https://img.shields.io/badge/AsyncIO-3776AB?style=flat-square&logo=python&logoColor=white" alt="AsyncIO" /></td>
    </tr>
    <tr>
      <td>Database</td>
      <td><img src="https://img.shields.io/badge/AWS_RDS-527FFF?style=flat-square&logo=amazonrds&logoColor=white" alt="AWS RDS" /> <img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white" alt="MySQL" /></td>
    </tr>
    <tr>
      <td>Auth</td>
      <td><img src="https://img.shields.io/badge/JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white" alt="JWT" /> <img src="https://img.shields.io/badge/OAuth_2.0-EB5424?style=flat-square&logo=auth0&logoColor=white" alt="OAuth 2.0" /></td>
    </tr>
    <tr>
      <td>Storage</td>
      <td><img src="https://img.shields.io/badge/AWS_S3-569A31?style=flat-square&logo=amazons3&logoColor=white" alt="AWS S3" /> <img src="https://img.shields.io/badge/aioboto3-3776AB?style=flat-square&logo=python&logoColor=white" alt="aioboto3" /></td>
    </tr>
    <tr>
      <td>Scheduler</td>
      <td><img src="https://img.shields.io/badge/APScheduler-333333?style=flat-square&logo=python&logoColor=white" alt="APScheduler" /></td>
    </tr>
  </tbody>
</table>

> ### AI / ML

<table width="100%">
  <thead>
    <tr>
      <th>분류</th>
      <th>기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>텍스트 일기 생성</td>
      <td><img src="https://img.shields.io/badge/GPT--4.1--mini-412991?style=flat-square&logo=openai&logoColor=white" alt="GPT-4.1-mini" /></td>
    </tr>
    <tr>
      <td>이미지 생성</td>
      <td><img src="https://img.shields.io/badge/gpt--image--1-412991?style=flat-square&logo=openai&logoColor=white" alt="gpt-image-1" /></td>
    </tr>
    <tr>
      <td>의도 분류</td>
      <td><img src="https://img.shields.io/badge/KoELECTRA-FF6F00?style=flat-square&logo=huggingface&logoColor=white" alt="KoELECTRA" /> <img src="https://img.shields.io/badge/Fine--tuned-FFB000?style=flat-square" alt="Fine-tuned" /></td>
    </tr>
    <tr>
      <td>임베딩</td>
      <td><img src="https://img.shields.io/badge/ko--sroberta--multitask-FF6F00?style=flat-square&logo=huggingface&logoColor=white" alt="ko-sroberta-multitask" /> <img src="https://img.shields.io/badge/sentence--transformers-FFB000?style=flat-square" alt="sentence-transformers" /></td>
    </tr>
    <tr>
      <td>Vector DB</td>
      <td><img src="https://img.shields.io/badge/ChromaDB-FF6B35?style=flat-square" alt="ChromaDB" /> <img src="https://img.shields.io/badge/RAG_x3-6A5ACD?style=flat-square" alt="RAG" /></td>
    </tr>
    <tr>
      <td>군집·시각화</td>
      <td><img src="https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white" alt="scikit-learn" /> <img src="https://img.shields.io/badge/KMeans-3776AB?style=flat-square" alt="KMeans" /> <img src="https://img.shields.io/badge/matplotlib-11557C?style=flat-square" alt="matplotlib" /> <img src="https://img.shields.io/badge/PCA·t--SNE-6A5ACD?style=flat-square" alt="PCA·t--SNE" /></td>
    </tr>
    <tr>
      <td>이미지 평가</td>
      <td><img src="https://img.shields.io/badge/CLIP-412991?style=flat-square&logo=openai&logoColor=white" alt="CLIP" /> <img src="https://img.shields.io/badge/YOLOv8n-00FFFF?style=flat-square" alt="YOLOv8n" /></td>
    </tr>
  </tbody>
</table>

> ### Frontend

<table width="100%">
  <thead>
    <tr>
      <th>분류</th>
      <th>기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Framework</td>
      <td><img src="https://img.shields.io/badge/React_18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" /> <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" /></td>
    </tr>
    <tr>
      <td>Build</td>
      <td><img src="https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite" /></td>
    </tr>
    <tr>
      <td>Styling</td>
      <td><img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="TailwindCSS" /></td>
    </tr>
    <tr>
      <td>Router</td>
      <td><img src="https://img.shields.io/badge/React_Router_v7-CA4245?style=flat-square&logo=reactrouter&logoColor=white" alt="React Router" /></td>
    </tr>
    <tr>
      <td>Animation</td>
      <td><img src="https://img.shields.io/badge/Motion-0055FF?style=flat-square&logo=framer&logoColor=white" alt="Motion" /></td>
    </tr>
    <tr>
      <td>UI</td>
      <td><img src="https://img.shields.io/badge/Lucide_React-F56565?style=flat-square&logo=lucide&logoColor=white" alt="Lucide React" /></td>
    </tr>
    <tr>
      <td>Map</td>
      <td><img src="https://img.shields.io/badge/Kakao_Maps_SDK-FFCD00?style=flat-square&logo=kakao&logoColor=black" alt="Kakao Maps SDK" /></td>
    </tr>
    <tr>
      <td>Design</td>
      <td><img src="https://img.shields.io/badge/Figma-F24E1E?style=flat-square&logo=figma&logoColor=white" alt="Figma" /> <img src="https://img.shields.io/badge/Photoshop-31A8FF?style=flat-square&logo=adobephotoshop&logoColor=white" alt="Adobe Photoshop" /> <img src="https://img.shields.io/badge/Illustrator-FF9A00?style=flat-square&logo=adobeillustrator&logoColor=white" alt="Adobe Illustrator" /></td>
    </tr>
  </tbody>
</table>

> ### Mobile

<table width="100%">
  <thead>
    <tr>
      <th>분류</th>
      <th>기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Framework</td>
      <td><img src="https://img.shields.io/badge/Flutter_3.41-02569B?style=flat-square&logo=flutter&logoColor=white" alt="Flutter" /> <img src="https://img.shields.io/badge/Dart-0175C2?style=flat-square&logo=dart&logoColor=white" alt="Dart" /></td>
    </tr>
    <tr>
      <td>State</td>
      <td><img src="https://img.shields.io/badge/Riverpod-0553B1?style=flat-square&logo=flutter&logoColor=white" alt="Riverpod" /></td>
    </tr>
    <tr>
      <td>Network</td>
      <td><img src="https://img.shields.io/badge/Dio-0175C2?style=flat-square&logo=dart&logoColor=white" alt="Dio" /></td>
    </tr>
    <tr>
      <td>Routing</td>
      <td><img src="https://img.shields.io/badge/go__router-02569B?style=flat-square&logo=flutter&logoColor=white" alt="go_router" /></td>
    </tr>
    <tr>
      <td>OAuth</td>
      <td><img src="https://img.shields.io/badge/flutter__appauth-02569B?style=flat-square" alt="flutter_appauth" /> <img src="https://img.shields.io/badge/flutter__inappwebview-02569B?style=flat-square" alt="flutter_inappwebview" /></td>
    </tr>
    <tr>
      <td>Storage</td>
      <td><img src="https://img.shields.io/badge/flutter__secure__storage-02569B?style=flat-square" alt="flutter_secure_storage" /></td>
    </tr>
    <tr>
      <td>Platform</td>
      <td><img src="https://img.shields.io/badge/Android-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Android" /></td>
    </tr>
  </tbody>
</table>

> ### Infra

<table width="100%">
  <thead>
    <tr>
      <th>분류</th>
      <th>기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Cloud</td>
      <td><img src="https://img.shields.io/badge/AWS_EC2-FF9900?style=flat-square&logo=amazonec2&logoColor=white" alt="AWS EC2" /> <img src="https://img.shields.io/badge/AWS_RDS-527FFF?style=flat-square&logo=amazonrds&logoColor=white" alt="AWS RDS" /> <img src="https://img.shields.io/badge/AWS_S3-569A31?style=flat-square&logo=amazons3&logoColor=white" alt="AWS S3" /></td>
    </tr>
    <tr>
      <td>Container</td>
      <td><img src="https://img.shields.io/badge/Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker Compose" /></td>
    </tr>
    <tr>
      <td>Web Server</td>
      <td><img src="https://img.shields.io/badge/Nginx_1.25-009639?style=flat-square&logo=nginx&logoColor=white" alt="Nginx" /></td>
    </tr>
    <tr>
      <td>Domain</td>
      <td><img src="https://img.shields.io/badge/withdog.kro.kr-000000?style=flat-square&logo=googlechrome&logoColor=white" alt="withdog.kro.kr" /></td>
    </tr>
    <tr>
      <td>터널링</td>
      <td><img src="https://img.shields.io/badge/SSH_Tunnel-4D4D4D?style=flat-square&logo=openssh&logoColor=white" alt="SSH Tunnel" /> <img src="https://img.shields.io/badge/sshtunnel-3776AB?style=flat-square&logo=python&logoColor=white" alt="sshtunnel" /> <img src="https://img.shields.io/badge/paramiko-3776AB?style=flat-square&logo=python&logoColor=white" alt="paramiko" /></td>
    </tr>
  </tbody>
</table>

> ### External API

<table width="100%">
  <thead>
    <tr>
      <th>분류</th>
      <th>기술</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>LLM / 이미지</td>
      <td><img src="https://img.shields.io/badge/OpenAI_API-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI" /></td>
    </tr>
    <tr>
      <td>견종 데이터</td>
      <td><img src="https://img.shields.io/badge/The_Dog_API-FFA500?style=flat-square" alt="The Dog API" /></td>
    </tr>
    <tr>
      <td>관광 데이터</td>
      <td><img src="https://img.shields.io/badge/한국관광공사_OpenAPI-0064FF?style=flat-square" alt="한국관광공사 OpenAPI" /></td>
    </tr>
    <tr>
      <td>지도·좌표</td>
      <td><img src="https://img.shields.io/badge/Kakao_Maps-FFCD00?style=flat-square&logo=kakao&logoColor=black" alt="Kakao Maps" /> <img src="https://img.shields.io/badge/Kakao_REST_API-FFCD00?style=flat-square&logo=kakao&logoColor=black" alt="Kakao REST API" /></td>
    </tr>
    <tr>
      <td>소셜 로그인</td>
      <td><img src="https://img.shields.io/badge/Kakao_OAuth-FFCD00?style=flat-square&logo=kakao&logoColor=black" alt="Kakao OAuth" /> <img src="https://img.shields.io/badge/Google_OAuth-4285F4?style=flat-square&logo=google&logoColor=white" alt="Google OAuth" /> <img src="https://img.shields.io/badge/Naver_OAuth-03C75A?style=flat-square&logo=naver&logoColor=white" alt="Naver OAuth" /></td>
    </tr>
  </tbody>
</table>

<br />
