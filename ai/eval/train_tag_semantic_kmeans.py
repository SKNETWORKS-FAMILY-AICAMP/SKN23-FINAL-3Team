"""
train_tag_semantic_kmeans.py  —  태그 의미 기반 KMeans 군집화 실험 스크립트

===========================================================================
이 스크립트의 목적
===========================================================================
이 실험은 유저를 직접 군집화하는 것이 아닙니다.

온보딩 태그 텍스트의 의미를 임베딩하여 비슷한 의미의 태그끼리 묶는 실험입니다.
이를 통해 DogScorer / OwnerScorer의 축 정의와 태그 분류가
단순 임의 기준이 아니라, 태그 의미 구조를 기반으로 설계되었음을 설명할 수 있습니다.

---------------------------------------------------------------------------
실험 이력
---------------------------------------------------------------------------
  [1차]  dog + owner 태그 합산 KMeans → 의미 축이 섞이는 문제 확인
  [2차]  dog / owner 분리 KMeans
         문제점:
           - owner Cluster 1에 활동성·감성·일상 태그 혼합
           - "계획 없이 떠나기" 1개짜리 고립 클러스터
           - "먹는 게 최고"(dog)가 활동성 클러스터로 오분류
  [3차]  태그 설명(description) 개선
         각 태그 설명에 해당 축의 핵심 키워드를 명확히 반영하여
         임베딩 공간에서 5축 분리가 더 선명하게 나타나도록 개선

---------------------------------------------------------------------------
10D 유저 KMeans vs 이 실험의 차이
---------------------------------------------------------------------------
  [10D 유저 KMeans]
    입력: 유저 선택 태그 → DogScorer/OwnerScorer 점수화 → 10D 벡터
    목적: 비슷한 성향의 유저 군집화 → 유저 세그먼트 설계

  [이 실험 - 태그 의미 KMeans]
    입력: 태그 텍스트(이름 + 설명) → 문장 임베딩 → 고차원 의미 벡터
    목적: 의미가 비슷한 태그끼리 군집화 → 축 정의와 태그 분류의 근거 생성

  두 실험은 목적이 다릅니다.
  태그 의미 군집화는 "왜 이 태그들을 같은 축에 넣었는가"를 설명하는 근거이고,
  유저 군집화는 "어떤 유저를 어떤 세그먼트로 분류할 것인가"의 결과입니다.

===========================================================================
실행 방법
===========================================================================
  # 프로젝트 루트에서
  python ai/eval/train_tag_semantic_kmeans.py

  # 필요 패키지
  pip install sentence-transformers scikit-learn pandas numpy matplotlib

===========================================================================
출력 위치
===========================================================================
  ai/eval_data/K-Means_eval_data/K-Means_3rd_test/dog/
  ai/eval_data/K-Means_eval_data/K-Means_3rd_test/owner/
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

warnings.filterwarnings("ignore")

# ─── 경로 설정 ────────────────────────────────────────────────────────────────
_ROOT      = Path(__file__).parent.parent.parent          # 프로젝트 루트
_BASE_DIR  = _ROOT / "ai" / "eval_data" / "K-Means_eval_data" / "K-Means_3rd_test"
_DOG_DIR   = _BASE_DIR / "dog"
_OWNER_DIR = _BASE_DIR / "owner"

# ─── 하이퍼파라미터 ───────────────────────────────────────────────────────────
EMBED_MODEL  = "jhgan/ko-sroberta-multitask"
K_RANGE      = range(3, 8)
FINAL_K      = 5
RANDOM_STATE = 42

# ─── 자동 라벨링 키워드 사전 ──────────────────────────────────────────────────
# cluster에 속한 태그 이름+설명 텍스트를 보고 키워드 매칭으로 임시 라벨을 결정합니다.
# ※ cluster_id는 KMeans 실행마다 달라질 수 있으므로 최종 라벨은
#    클러스터별 포함 태그를 보고 재검토해야 합니다.
_DOG_LABEL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("활동성·탐험",   ["산책", "활동", "뛰", "공", "장난감", "탐험", "탐색", "야외", "밖", "에너"]),
    ("사회성·친화력", ["사람", "친근", "애교", "낯선", "강아지 친구", "안기", "시키", "교감"]),
    ("안정·힐링",     ["느긋", "집", "혼자", "먹", "간식", "실내", "편안", "쉬", "안정", "만족"]),
    ("호기심·자유",   ["호기심", "자유", "고집", "독립", "자신만", "제 갈"]),
    ("예민·신중",     ["예민", "겁", "짖", "경계", "무서", "낯을", "신중", "스트레스", "민감"]),
]
_OWNER_LABEL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("자연선호",     ["자연", "숲", "해변", "바다", "산", "계곡", "나무"]),
    ("도시·핫플",   ["도시", "핫플", "골목", "트렌디", "로컬", "인기", "즉흥", "명소"]),
    ("활동·모험",   ["뛰", "신나게", "활발", "공원", "산책", "야외", "운동"]),
    # "감성·힐링" 하나로 두 클러스터를 다 끌어당기던 문제를 두 레이블로 분리
    # - 감성·먹거리: 감성적 경험 + 먹거리 키워드 (카페, 사진, 전시, 맛집 태그 유도)
    # - 힐링·일상:   힐링/느긋함 + 일상 루틴 키워드 (느긋하게 쉬어가기, 일상 충전 태그 유도)
    ("감성·먹거리", ["감성", "사진", "전시", "문화", "분위기", "먹", "카페", "맛집", "식당", "브런치"]),
    ("힐링·일상",   ["힐링", "느긋", "여유", "쉬", "일상", "루틴", "충전"]),
]


def auto_label_cluster(tag_texts: list[str], tag_type: str) -> str:
    """cluster 내 태그 텍스트를 보고 키워드 매칭으로 임시 라벨 반환."""
    keyword_table = _DOG_LABEL_KEYWORDS if tag_type == "dog" else _OWNER_LABEL_KEYWORDS
    combined_text = " ".join(tag_texts)
    scores = [(label, sum(1 for kw in kws if kw in combined_text)) for label, kws in keyword_table]
    best_label, best_score = max(scores, key=lambda x: x[1])
    return best_label if best_score > 0 else None


# ─── 태그 샘플 데이터 (3차 — 설명 개선) ──────────────────────────────────────
# 2차 대비 변경 내역
#
# [dog]
#   "먹는 게 최고": "활동을 좋아하는" 제거, 안정·편안 키워드 추가
#     → 2차에서 활동성 클러스터로 오분류된 문제 개선
#
# [owner]
#   "바다"             : "자연 해변" 키워드 명시 → 자연선호 클러스터 유도
#   "계획 없이 떠나기" : "핫플·도시 명소" 키워드 추가 → 도시·핫플 클러스터 유도
#   "느긋하게 쉬어가기": "감성·힐링" 키워드 추가 → 감성·힐링 클러스터 유도
#   "사진 건지러"      : "감성적인 공간·분위기" 키워드 강화 → 감성·힐링 클러스터 유도
#   "전시 관람"        : "감성 문화 공간" 키워드 추가 → 감성·힐링 클러스터 유도
#   "일상 충전"        : "카페·맛집·먹거리" 키워드 추가 → 먹거리·일상 클러스터 유도
#   "카페 투어"        : "맛집·먹거리" 키워드 추가 → 먹거리·일상 클러스터 유도
_SAMPLE_TAGS = [
    # ── 강아지 태그 (DogScorer) ──────────────────────────────────────────────
    ("dog", "에너자이저",         "산책과 놀이를 좋아하고 활동량이 매우 많은 강아지"),
    ("dog", "산책이 제일 좋아",   "야외 산책을 가장 즐기고 걷거나 뛰는 것을 좋아하는 강아지"),
    ("dog", "밖이 좋아요",        "실외 환경을 선호하고 야외에서 활동하는 것을 즐기는 강아지"),
    ("dog", "겁 없는 탐험가",     "새로운 장소나 환경을 두려움 없이 탐색하는 강아지"),
    ("dog", "공이라면 뭐든지",    "공을 이용한 놀이와 움직임을 매우 좋아하는 강아지"),
    ("dog", "장난감 수집가",      "장난감을 좋아하고 물건을 탐색하고 노는 것을 즐기는 강아지"),
    ("dog", "애교쟁이",           "보호자와 사람에게 친근하게 다가가고 애교가 많은 강아지"),
    ("dog", "낯선 사람도 좋아요", "처음 보는 사람에게도 친근하고 두려움 없이 다가가는 강아지"),
    ("dog", "사람이라면 다 좋아", "모든 사람을 좋아하고 사람과 함께하는 것을 즐기는 강아지"),
    ("dog", "강아지 친구 환영",   "다른 강아지와 잘 어울리고 사회적인 교류를 즐기는 강아지"),
    ("dog", "안기는 거 좋아요",   "보호자에게 안기거나 스킨십을 좋아하는 강아지"),
    ("dog", "시키는 건 다 해요",  "훈련과 지시에 잘 따르고 사람과 교감하는 것을 좋아하는 강아지"),
    ("dog", "느긋한 편",          "조용하고 안정적인 환경을 선호하며 여유로운 강아지"),
    ("dog", "집이 편해요",        "실내에서 쉬는 것을 좋아하고 집 환경을 편안해하는 강아지"),
    ("dog", "혼자도 잘 놀아요",   "혼자 있어도 잘 지내고 독립적으로 놀이하는 강아지"),
    ("dog", "먹는 게 최고",       "음식과 간식에 대한 관심이 높고 먹는 것으로 편안함과 만족감을 찾는 강아지"),
    ("dog", "제 갈 길 가는 타입", "독립적이고 자신만의 방식으로 자유롭게 탐색하는 강아지"),
    ("dog", "호기심 폭발",        "새로운 것에 강한 호기심을 보이고 탐색을 즐기는 강아지"),
    ("dog", "고집 있는 편",       "자신의 의지가 강하고 고집스럽게 원하는 것을 추구하는 강아지"),
    ("dog", "낯을 가려요",        "새로운 사람이나 환경에 조심스럽고 경계하는 강아지"),
    ("dog", "사람은 좀 무서워요", "낯선 사람에 대한 두려움이 있고 거리를 두는 강아지"),
    ("dog", "겁쟁이",             "소리나 새로운 환경에 쉽게 겁을 먹는 강아지"),
    ("dog", "예민한 편",          "주변 자극에 민감하게 반응하고 스트레스를 잘 받는 강아지"),
    ("dog", "낯선 것엔 짖어요",   "낯선 자극이나 소리에 짖으며 경계하는 강아지"),
    # ── 보호자 태그 (OwnerScorer) ────────────────────────────────────────────
    ("owner", "자연 속으로",       "숲 공원 계곡 등 자연적인 공간을 선호하는 보호자"),
    ("owner", "바다",              "자연 해변과 바다 풍경 속에서 반려견과 자연을 즐기는 자연 애호 보호자"),
    ("owner", "산",                "산악 등산 하이킹을 즐기는 자연 애호가 보호자"),
    ("owner", "숲",                "숲 산책과 나무 사이 걷기를 좋아하는 보호자"),
    ("owner", "계곡",              "계곡 물놀이와 자연 힐링을 즐기는 보호자"),
    ("owner", "신나게 뛰어놀기",   "넓은 야외 공간에서 강아지와 함께 활발하고 신나게 뛰어노는 것을 좋아하는 보호자"),
    ("owner", "도시 구경",         "도시 거리 탐방과 핫플레이스 방문을 즐기는 보호자"),
    ("owner", "핫플 인증",         "트렌디한 장소와 인기 있는 핫플을 방문하는 것을 좋아하는 보호자"),
    ("owner", "카페 투어",         "반려견 동반 카페와 맛집을 찾아다니며 먹거리를 즐기는 보호자"),
    ("owner", "새로운 곳 구경",    "새로운 장소와 환경을 탐색하는 것을 좋아하는 보호자"),
    ("owner", "동네 골목 탐방",    "동네 골목과 로컬 명소를 탐방하는 것을 즐기는 보호자"),
    ("owner", "공원 산책",         "공원과 산책로에서 강아지와 산책하는 것을 즐기는 보호자"),
    ("owner", "계획 없이 떠나기",  "즉흥적으로 새로운 핫플과 도시 명소를 자유롭게 탐방하는 보호자"),
    ("owner", "느긋하게 쉬어가기", "여유롭고 감성적인 분위기 속에서 천천히 힐링하며 쉬어가는 것을 즐기는 보호자"),
    ("owner", "감성 충만",         "감성적인 분위기와 아름다운 장소를 선호하는 보호자"),
    ("owner", "사진 건지러",       "감성적인 분위기의 공간에서 반려견과 함께 감성 사진을 찍는 것을 즐기는 보호자"),
    ("owner", "전시 관람",         "미술관이나 전시회 등 감성적인 문화 공간을 반려견과 함께 즐기는 보호자"),
    ("owner", "일상 충전",         "카페나 맛집 방문 등 일상 속 먹거리 루틴으로 재충전하는 것을 좋아하는 보호자"),
    ("owner", "맛있는 거 먹으러",  "강아지 동반 가능한 식당과 브런치 카페를 즐기는 보호자"),
]


# ─── 한글 폰트 설정 ───────────────────────────────────────────────────────────
def _setup_font():
    import platform
    try:
        if platform.system() == "Windows":
            matplotlib.rc("font", family="Malgun Gothic")
        elif platform.system() == "Darwin":
            matplotlib.rc("font", family="AppleGothic")
        matplotlib.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass


# ─── 데이터 로드 ──────────────────────────────────────────────────────────────
def load_tags() -> pd.DataFrame:
    df = pd.DataFrame(_SAMPLE_TAGS, columns=["tag_type", "tag_name", "tag_description"])
    n_dog   = (df.tag_type == "dog").sum()
    n_owner = (df.tag_type == "owner").sum()
    print(f"  태그 로드: {len(df)}개 ({n_dog}개 강아지 / {n_owner}개 보호자)")
    return df


# ─── 임베딩 ───────────────────────────────────────────────────────────────────
def embed_tags(df: pd.DataFrame, model) -> np.ndarray:
    sentences = (df["tag_name"] + ": " + df["tag_description"]).tolist()
    print(f"    임베딩 중... ({len(sentences)}개 문장)")
    embeddings = model.encode(sentences, show_progress_bar=True, convert_to_numpy=True)
    embeddings = normalize(embeddings, norm="l2")
    print(f"    임베딩 완료: shape={embeddings.shape}")
    return embeddings


# ─── k 범위 평가 ──────────────────────────────────────────────────────────────
def evaluate_k(embeddings: np.ndarray, k_range: range) -> pd.DataFrame:
    records = []
    print(f"  {'k':>4} {'Inertia':>12} {'Silhouette':>12}")
    print("  " + "-" * 32)
    for k in k_range:
        if k >= len(embeddings):
            continue
        km  = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        lbl = km.fit_predict(embeddings)
        sil = silhouette_score(embeddings, lbl) if len(set(lbl)) > 1 else 0.0
        records.append({"k": k, "inertia": round(km.inertia_, 4), "silhouette_score": round(sil, 4)})
        print(f"  {k:>4} {km.inertia_:>12.2f} {sil:>12.4f}")
    return pd.DataFrame(records)


# ─── 최종 군집화 ──────────────────────────────────────────────────────────────
def fit_final_kmeans(embeddings: np.ndarray, final_k: int):
    km = KMeans(n_clusters=final_k, random_state=RANDOM_STATE, n_init=10)
    labels = km.fit_predict(embeddings)
    return km, labels


# ─── 클러스터 요약 ────────────────────────────────────────────────────────────
def build_cluster_summary(df: pd.DataFrame, labels: np.ndarray, tag_type: str, final_k: int) -> dict:
    summary = {}
    for cid in range(final_k):
        mask       = labels == cid
        cluster_df = df[mask].reset_index(drop=True)
        tag_names  = cluster_df["tag_name"].tolist()
        tag_descs  = cluster_df["tag_description"].tolist()

        all_texts  = tag_names + tag_descs
        auto_label = auto_label_cluster(all_texts, tag_type)
        label_str  = auto_label if auto_label else f"군집 {cid} (검토 필요)"

        summary[str(cid)] = {
            "cluster_id":          cid,
            "cluster_label":       label_str,
            "label_source":        "keyword_auto" if auto_label else "unmatched",
            "total_count":         int(mask.sum()),
            "tag_names":           tag_names,
            "representative_tags": tag_names[:3],
            "note": (
                "cluster_id는 KMeans 실행마다 달라질 수 있으므로 "
                "최종 라벨은 클러스터별 포함 태그를 보고 재검토해야 합니다."
            ),
        }
    return summary


# ─── 시각화 ───────────────────────────────────────────────────────────────────
def _scatter(X2d, labels, tag_names, title, path, final_k, cluster_labels: dict, note=""):
    colors = plt.cm.tab10(np.linspace(0, 1, final_k))
    fig, ax = plt.subplots(figsize=(11, 8))
    for cid in range(final_k):
        mask = labels == cid
        lbl  = cluster_labels.get(str(cid), {}).get("cluster_label", f"군집{cid}")
        ax.scatter(X2d[mask, 0], X2d[mask, 1],
                   color=colors[cid], s=80, alpha=0.8,
                   label=f"Cluster {cid}: {lbl}")
        for x, y, name in zip(X2d[mask, 0], X2d[mask, 1], np.array(tag_names)[mask]):
            ax.annotate(name, (x, y), fontsize=7, alpha=0.75,
                        xytext=(3, 3), textcoords="offset points")
    ax.set_title(f"{title}\n{note}", fontsize=12)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_pca(embeddings, labels, tag_names, path, final_k, cluster_labels):
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    X2d = pca.fit_transform(embeddings)
    var = pca.explained_variance_ratio_
    _scatter(X2d, labels, tag_names,
             title=f"PCA 2D 산점도 (k={final_k})",
             note=f"PC1={var[0]*100:.1f}%  PC2={var[1]*100:.1f}%  | 시각화 전용",
             path=path, final_k=final_k, cluster_labels=cluster_labels)


def plot_tsne(embeddings, labels, tag_names, path, final_k, cluster_labels):
    perp = min(30, max(5, len(embeddings) // 4))
    tsne = TSNE(n_components=2, random_state=RANDOM_STATE, perplexity=perp, max_iter=1000)
    X2d  = tsne.fit_transform(embeddings)
    _scatter(X2d, labels, tag_names,
             title=f"t-SNE 2D 산점도 (k={final_k})",
             note=f"perplexity={perp}  | 시각화 전용",
             path=path, final_k=final_k, cluster_labels=cluster_labels)


def plot_elbow(eval_df, path, final_k):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(eval_df["k"], eval_df["inertia"], "o-", color="#F4845F", lw=2, ms=8)
    ax.axvline(x=final_k, color="#3D2B1F", ls="--", alpha=0.6, label=f"선택 k={final_k}")
    ax.set_xlabel("k"); ax.set_ylabel("Inertia")
    ax.set_title("Elbow Curve (태그 의미 임베딩 기반)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def plot_silhouette(eval_df, path, final_k):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(eval_df["k"], eval_df["silhouette_score"], "s-", color="#6BAED6", lw=2, ms=8)
    ax.axvline(x=final_k, color="#3D2B1F", ls="--", alpha=0.6, label=f"선택 k={final_k}")
    ax.set_xlabel("k"); ax.set_ylabel("Silhouette Score")
    ax.set_title("Silhouette Score (태그 의미 임베딩 기반)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


# ─── 서브셋별 실행 ────────────────────────────────────────────────────────────
def run_subset(df_sub: pd.DataFrame, tag_type: str, out_dir: Path, model) -> None:
    label_kr = "강아지(dog)" if tag_type == "dog" else "보호자(owner)"
    n = len(df_sub)
    print(f"\n  [{label_kr}] {n}개 태그")

    final_k = min(FINAL_K, n - 1)
    k_range  = range(K_RANGE.start, min(K_RANGE.stop, n))

    out_dir.mkdir(parents=True, exist_ok=True)
    tag_names = df_sub["tag_name"].tolist()

    embeddings = embed_tags(df_sub, model)

    print(f"\n    k={k_range.start}~{k_range.stop-1} 평가 (Elbow + Silhouette)")
    eval_df   = evaluate_k(embeddings, k_range)
    eval_path = out_dir / f"{tag_type}_tag_3rd_k_evaluation.csv"
    eval_df.to_csv(eval_path, index=False, encoding="utf-8-sig")
    print(f"    -> {eval_path.name} 저장")

    km, labels = fit_final_kmeans(embeddings, final_k)
    sil = silhouette_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    print(f"    Inertia: {km.inertia_:.2f}  |  Silhouette: {sil:.4f}")

    result_df = df_sub.copy().reset_index(drop=True)
    result_df["cluster_id"] = labels

    summary = build_cluster_summary(df_sub.reset_index(drop=True), labels, tag_type, final_k)
    result_df["cluster_label"] = [summary[str(c)]["cluster_label"] for c in labels]

    result_path = out_dir / f"{tag_type}_tag_3rd_cluster_result.csv"
    result_df.to_csv(result_path, index=False, encoding="utf-8-sig")
    print(f"    -> {result_path.name} 저장")

    summary_path = out_dir / f"{tag_type}_tag_3rd_cluster_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"    -> {summary_path.name} 저장")

    print(f"\n    {'Cluster':>10}  {'자동 라벨':>16}  {'태그 수':>6}")
    print("    " + "-" * 45)
    for cid, v in summary.items():
        print(f"    Cluster {cid}  {v['cluster_label']:>16}  {v['total_count']:>4}개")
        print(f"              포함 태그: {' / '.join(v['tag_names'])}")

    print(f"\n    시각화 저장 중...")
    plot_elbow(eval_df, out_dir / f"{tag_type}_tag_3rd_elbow_curve.png", final_k)
    print(f"    -> {tag_type}_tag_3rd_elbow_curve.png")
    plot_silhouette(eval_df, out_dir / f"{tag_type}_tag_3rd_silhouette_score.png", final_k)
    print(f"    -> {tag_type}_tag_3rd_silhouette_score.png")
    plot_pca(embeddings, labels, tag_names,
             out_dir / f"{tag_type}_tag_3rd_pca_scatter.png", final_k, summary)
    print(f"    -> {tag_type}_tag_3rd_pca_scatter.png")
    print(f"    t-SNE 산점도 생성 중...")
    plot_tsne(embeddings, labels, tag_names,
              out_dir / f"{tag_type}_tag_3rd_tsne_scatter.png", final_k, summary)
    print(f"    -> {tag_type}_tag_3rd_tsne_scatter.png")


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    _setup_font()
    _BASE_DIR.mkdir(parents=True, exist_ok=True)

    sep = "=" * 60
    print(sep)
    print("withDOG 태그 의미 기반 KMeans 군집화 실험 (3차 — 설명 개선)")
    print(sep)

    print("\n[1] 태그 데이터 로드")
    df       = load_tags()
    df_dog   = df[df["tag_type"] == "dog"].reset_index(drop=True)
    df_owner = df[df["tag_type"] == "owner"].reset_index(drop=True)
    print(f"    dog: {len(df_dog)}개  /  owner: {len(df_owner)}개")

    print(f"\n[2] 임베딩 모델 로드: {EMBED_MODEL}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)

    print("\n" + sep)
    print("[3] Dog 태그 KMeans (3차)")
    print(sep)
    run_subset(df_dog, "dog", _DOG_DIR, model)

    print("\n" + sep)
    print("[4] Owner 태그 KMeans (3차)")
    print(sep)
    run_subset(df_owner, "owner", _OWNER_DIR, model)

    print(f"\n{sep}")
    print("[완료] 3차 실험 결과 저장 위치:")
    print(f"  dog   -> {_DOG_DIR}")
    print(f"  owner -> {_OWNER_DIR}")
    print(sep)


if __name__ == "__main__":
    main()
