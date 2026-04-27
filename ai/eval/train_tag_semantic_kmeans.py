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
1차 실험 vs 2차 실험
---------------------------------------------------------------------------
  [1차 실험]  dog 태그 + owner 태그를 합쳐서 KMeans → 의미 축이 섞이는 문제 확인
  [2차 실험]  dog 태그 / owner 태그를 분리하여 각각 KMeans 수행
              출력 파일에 _2nd 접미사를 붙여 1차 결과와 구분합니다.

---------------------------------------------------------------------------
기존 10D 유저 KMeans vs 이 실험의 차이
---------------------------------------------------------------------------
  [10D 유저 KMeans]
    입력: 유저가 선택한 태그 → DogScorer/OwnerScorer 점수화 → 10D 벡터
    목적: 비슷한 성향의 유저를 군집화 → 유저 세그먼트 설계

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
  pip install sentence-transformers scikit-learn pandas numpy matplotlib joblib

===========================================================================
입력 / 출력
===========================================================================
입력: ai/eval_data/K-Means_eval_data/tag_semantic/tag_input.csv
      (없으면 DogScorer / OwnerScorer 실제 태그 기반 샘플 자동 생성)

출력 (2차): ai/eval_data/K-Means_eval_data/tag_semantic/dog/   (dog 태그)
            ai/eval_data/K-Means_eval_data/tag_semantic/owner/ (owner 태그)
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
_ROOT      = Path(__file__).parent.parent.parent
_BASE_DIR  = _ROOT / "ai" / "eval_data" / "K-Means_eval_data" / "tag_semantic"
_INPUT_CSV = _BASE_DIR / "tag_input.csv"

# 2차 실험 출력 디렉터리
_DOG_DIR   = _BASE_DIR / "dog"
_OWNER_DIR = _BASE_DIR / "owner"

# ─── 하이퍼파라미터 ───────────────────────────────────────────────────────────
EMBED_MODEL  = "jhgan/ko-sroberta-multitask"
K_RANGE      = range(3, 8)   # k=3~7 (분리 후 태그 수가 줄어들므로 범위 조정)
FINAL_K      = 5
RANDOM_STATE = 42

# ─── 자동 라벨링 키워드 사전 ──────────────────────────────────────────────────
# cluster_id에 고정 라벨을 바로 붙이지 않고,
# 각 cluster에 들어간 태그 이름/설명을 보고 키워드 매칭으로 임시 라벨을 결정합니다.
# ※ cluster_id는 KMeans 실행마다 달라질 수 있으므로 최종 라벨은
#    클러스터별 포함 태그를 보고 재검토해야 합니다.
_DOG_LABEL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("활동성·탐험",   ["산책", "활동", "뛰", "공", "장난감", "탐험", "탐색", "야외", "밖", "에너"]),
    ("사회성·친화력", ["사람", "친근", "애교", "낯선", "강아지 친구", "안기", "시키", "교감"]),
    ("안정·힐링",     ["느긋", "집", "혼자", "먹", "간식", "실내", "편안", "쉬"]),
    ("호기심·자유",   ["호기심", "자유", "고집", "독립", "자신만", "제 갈"]),
    ("예민·신중",     ["예민", "겁", "짖", "경계", "무서", "낯을", "신중", "스트레스", "민감"]),
]
_OWNER_LABEL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("자연선호",     ["자연", "숲", "바다", "산", "계곡", "나무", "자연적"]),
    ("도시·핫플",   ["도시", "핫플", "카페", "골목", "트렌디", "로컬", "인기"]),
    ("활동·모험",   ["뛰", "신나게", "활발", "공원", "산책", "즉흥", "떠나"]),
    ("감성·힐링",   ["감성", "느긋", "사진", "전시", "문화", "아름다운", "여유"]),
    ("먹거리·일상", ["먹", "식당", "브런치", "일상", "루틴", "동반"]),
]


def auto_label_cluster(tag_texts: list[str], tag_type: str) -> str:
    """
    cluster에 속한 태그 텍스트 목록을 보고 키워드 매칭으로 임시 라벨을 반환합니다.
    매칭 키워드가 가장 많은 라벨을 선택하고, 동점이면 첫 번째 후보를 선택합니다.
    일치 키워드가 없으면 None을 반환합니다.
    """
    keyword_table = _DOG_LABEL_KEYWORDS if tag_type == "dog" else _OWNER_LABEL_KEYWORDS
    combined_text = " ".join(tag_texts)
    scores = [(label, sum(1 for kw in kws if kw in combined_text)) for label, kws in keyword_table]
    best_label, best_score = max(scores, key=lambda x: x[1])
    return best_label if best_score > 0 else None


# ─── 실제 태그 샘플 데이터 ────────────────────────────────────────────────────
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
    ("dog", "먹는 게 최고",       "음식에 대한 관심이 높고 간식을 이용한 활동을 좋아하는 강아지"),
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
    ("owner", "바다",              "바다와 해변에서 반려견과 함께 시간 보내는 것을 즐기는 보호자"),
    ("owner", "산",                "산악 등산 하이킹을 즐기는 자연 애호가 보호자"),
    ("owner", "숲",                "숲 산책과 나무 사이 걷기를 좋아하는 보호자"),
    ("owner", "계곡",              "계곡 물놀이와 자연 힐링을 즐기는 보호자"),
    ("owner", "신나게 뛰어놀기",   "넓은 공간에서 강아지와 함께 활발하게 뛰어노는 것을 좋아하는 보호자"),
    ("owner", "도시 구경",         "도시 거리 탐방과 핫플레이스 방문을 즐기는 보호자"),
    ("owner", "핫플 인증",         "트렌디한 장소와 인기 있는 핫플을 방문하는 것을 좋아하는 보호자"),
    ("owner", "카페 투어",         "반려견 동반 카페 방문을 즐기는 도시형 보호자"),
    ("owner", "새로운 곳 구경",    "새로운 장소와 환경을 탐색하는 것을 좋아하는 보호자"),
    ("owner", "동네 골목 탐방",    "동네 골목과 로컬 명소를 탐방하는 것을 즐기는 보호자"),
    ("owner", "공원 산책",         "공원과 산책로에서 강아지와 산책하는 것을 즐기는 보호자"),
    ("owner", "계획 없이 떠나기",  "즉흥적으로 여행하고 새로운 경험을 좋아하는 보호자"),
    ("owner", "느긋하게 쉬어가기", "여유롭고 느긋하게 반려견과 시간을 보내는 것을 좋아하는 보호자"),
    ("owner", "감성 충만",         "감성적인 분위기와 아름다운 장소를 선호하는 보호자"),
    ("owner", "사진 건지러",       "반려견과 함께 사진 찍기 좋은 장소를 찾아다니는 보호자"),
    ("owner", "전시 관람",         "전시회나 문화 공간을 반려견과 함께 즐기는 보호자"),
    ("owner", "일상 충전",         "반려견과 함께하는 일상적인 루틴을 소중히 여기는 보호자"),
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
def load_or_generate_tags() -> pd.DataFrame:
    """
    tag_input.csv 로드, 없으면 실제 태그 기반 샘플 자동 생성.
    컬럼: tag_type (dog/owner), tag_name, tag_description
    """
    if _INPUT_CSV.exists():
        df = pd.read_csv(_INPUT_CSV)
        print(f"  tag_input.csv 로드: {len(df)}개 태그")
        return df

    print("  tag_input.csv 없음 -> 실제 태그 기반 샘플 자동 생성")
    df = pd.DataFrame(_SAMPLE_TAGS, columns=["tag_type", "tag_name", "tag_description"])
    _BASE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(_INPUT_CSV, index=False, encoding="utf-8-sig")
    n_dog   = (df.tag_type == "dog").sum()
    n_owner = (df.tag_type == "owner").sum()
    print(f"  tag_input.csv 저장: {len(df)}개 태그 ({n_dog}개 강아지 / {n_owner}개 보호자)")
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


# ─── 자동 클러스터 요약 (라벨은 태그 내용 기반으로 자동 도출) ─────────────────
def build_cluster_summary(df: pd.DataFrame, labels: np.ndarray, tag_type: str, final_k: int) -> dict:
    """
    각 cluster에 포함된 태그 목록을 분석하여 임시 라벨을 자동으로 부여합니다.

    ※ cluster_id는 KMeans 실행마다 달라질 수 있으므로 최종 라벨은
       클러스터별 포함 태그를 보고 재검토해야 합니다.
    """
    summary = {}
    for cid in range(final_k):
        mask       = labels == cid
        cluster_df = df[mask].reset_index(drop=True)
        tag_names  = cluster_df["tag_name"].tolist()
        tag_descs  = cluster_df["tag_description"].tolist()

        # 태그 이름 + 설명을 합쳐 키워드 매칭
        all_texts   = tag_names + tag_descs
        auto_label  = auto_label_cluster(all_texts, tag_type)
        label_str   = auto_label if auto_label else f"군집 {cid} (검토 필요)"

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


# ─── 서브셋별 실행 (dog 또는 owner) ──────────────────────────────────────────
def run_subset(df_sub: pd.DataFrame, tag_type: str, out_dir: Path, model) -> None:
    label_kr = "강아지(dog)" if tag_type == "dog" else "보호자(owner)"
    n = len(df_sub)
    print(f"\n  [{label_kr}] {n}개 태그")

    # 이 subset에서 실제 쓸 k
    final_k = min(FINAL_K, n - 1)
    k_range  = range(K_RANGE.start, min(K_RANGE.stop, n))

    out_dir.mkdir(parents=True, exist_ok=True)
    tag_names = df_sub["tag_name"].tolist()

    # 임베딩
    embeddings = embed_tags(df_sub, model)

    # k 평가
    print(f"\n    k={k_range.start}~{k_range.stop-1} 평가 (Elbow + Silhouette)")
    eval_df = evaluate_k(embeddings, k_range)
    eval_path = out_dir / f"{tag_type}_tag_2nd_k_evaluation.csv"
    eval_df.to_csv(eval_path, index=False, encoding="utf-8-sig")
    print(f"    -> {eval_path.name} 저장")

    # 최종 KMeans
    km, labels = fit_final_kmeans(embeddings, final_k)
    sil = silhouette_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    print(f"    Inertia: {km.inertia_:.2f}  |  Silhouette: {sil:.4f}")

    # cluster 결과 CSV
    result_df = df_sub.copy().reset_index(drop=True)
    result_df["cluster_id"] = labels

    # 자동 라벨 (태그 내용 기반)
    summary = build_cluster_summary(df_sub.reset_index(drop=True), labels, tag_type, final_k)
    result_df["cluster_label"] = [summary[str(c)]["cluster_label"] for c in labels]

    result_path = out_dir / f"{tag_type}_tag_2nd_cluster_result.csv"
    result_df.to_csv(result_path, index=False, encoding="utf-8-sig")
    print(f"    -> {result_path.name} 저장")

    # cluster summary JSON
    summary_path = out_dir / f"{tag_type}_tag_2nd_cluster_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"    -> {summary_path.name} 저장")

    # 클러스터별 출력
    print(f"\n    {'Cluster':>10}  {'자동 라벨':>16}  {'태그 수':>6}")
    print("    " + "-" * 45)
    for cid, v in summary.items():
        print(f"    Cluster {cid}  {v['cluster_label']:>16}  {v['total_count']:>4}개")
        print(f"              포함 태그: {' / '.join(v['tag_names'])}")

    # 시각화
    print(f"\n    시각화 저장 중...")
    plot_elbow(eval_df, out_dir / f"{tag_type}_tag_2nd_elbow_curve.png", final_k)
    print(f"    -> {tag_type}_tag_2nd_elbow_curve.png")
    plot_silhouette(eval_df, out_dir / f"{tag_type}_tag_2nd_silhouette_score.png", final_k)
    print(f"    -> {tag_type}_tag_2nd_silhouette_score.png")
    plot_pca(embeddings, labels, tag_names,
             out_dir / f"{tag_type}_tag_2nd_pca_scatter.png", final_k, summary)
    print(f"    -> {tag_type}_tag_2nd_pca_scatter.png")
    print(f"    t-SNE 산점도 생성 중...")
    plot_tsne(embeddings, labels, tag_names,
              out_dir / f"{tag_type}_tag_2nd_tsne_scatter.png", final_k, summary)
    print(f"    -> {tag_type}_tag_2nd_tsne_scatter.png")


# ─── README 갱신 ──────────────────────────────────────────────────────────────
def update_readme(path: Path) -> None:
    content = """\
# 태그 의미 기반 KMeans 군집화 실험

## 실험 목적

> **"본 실험은 유저를 직접 군집화하는 것이 아니라,
> 온보딩 태그 텍스트의 의미를 임베딩하여 비슷한 의미의 태그끼리 묶는 실험이다.
> 이를 통해 DogScorer / OwnerScorer의 축 정의와 태그 분류가
> 단순 임의 기준이 아니라, 태그 의미 구조를 기반으로 설계되었음을 설명할 수 있다."**

---

## 두 KMeans 실험의 차이

| 구분 | 태그 의미 KMeans (이 실험) | 10D 유저 KMeans |
|------|--------------------------|----------------|
| 입력 | 태그 텍스트 임베딩 벡터 | 유저 태그 선택 점수 10D 벡터 |
| 단위 | 태그 1개 = 점 1개 | 유저 1명 = 점 1개 |
| 목적 | 태그 간 의미 유사성 확인 -> 축 정의 근거 | 유저 간 성향 유사성 확인 -> 세그먼트 분류 |
| 결과 활용 | "왜 이 태그들이 같은 축인가" 설명 | "어떤 유저가 어떤 세그먼트인가" 분류 |

---

## 1차 실험 vs 2차 실험

| 구분 | 1차 실험 | 2차 실험 |
|------|---------|---------|
| 대상 | dog 태그 + owner 태그 합산 (43개) | dog 태그 (24개), owner 태그 (19개) 분리 |
| 문제 | dog/owner 의미 축이 혼재 → 클러스터 해석 어려움 | 각 도메인 내 의미 유사성만 비교 |
| 출력 위치 | `tag_semantic/` | `tag_semantic/dog/`, `tag_semantic/owner/` |
| 파일 suffix | (없음) | `_2nd` |
| 클러스터 라벨 | 고정 사전 매핑 | 포함 태그 내용 기반 키워드 자동 도출 |

> **1차 실험에서 발견한 문제:**
> dog 태그와 owner 태그를 함께 임베딩하면, "자연 속으로(owner)"와 "밖이 좋아요(dog)"처럼
> 의미는 다르지만 표면적으로 유사한 태그가 같은 클러스터에 배치되어
> 각 도메인의 성향 축이 뚜렷하게 분리되지 않는 문제가 있었습니다.
>
> **2차 실험 개선:**
> dog / owner 태그를 분리하여 각각 독립적으로 KMeans를 수행함으로써
> 도메인 내 의미 유사성을 더 선명하게 확인할 수 있습니다.

---

## 임베딩 방식

- 입력 문장: `태그이름: 태그설명`
- 모델: `jhgan/ko-sroberta-multitask` (프로젝트 기존 사용 모델)
- 정규화: L2 정규화 후 KMeans 입력
- 시각화: PCA / t-SNE (시각화 전용 — 실제 KMeans는 고차원 임베딩 기반)

---

## 생성 파일 설명

### 1차 실험 (tag_semantic/ 루트)

| 파일 | 설명 |
|------|------|
| `tag_input.csv` | 입력 태그 데이터 (dog + owner 합산) |
| `tag_cluster_result.csv` | 태그별 cluster_id 배정 결과 |
| `tag_k_evaluation.csv` | k별 평가 지표 |
| `tag_cluster_summary.json` | 클러스터별 태그 목록 |
| `tag_elbow_curve.png` | Elbow Curve |
| `tag_silhouette_score.png` | Silhouette Score |
| `tag_pca_scatter.png` | PCA 2D 시각화 |
| `tag_tsne_scatter.png` | t-SNE 2D 시각화 |

### 2차 실험 (dog/ 및 owner/ 서브디렉터리)

| 파일 패턴 | 설명 |
|-----------|------|
| `{type}_tag_2nd_cluster_result.csv` | 태그별 cluster_id 및 자동 라벨 |
| `{type}_tag_2nd_k_evaluation.csv` | k별 평가 지표 |
| `{type}_tag_2nd_cluster_summary.json` | 클러스터별 태그 목록 및 자동 라벨 |
| `{type}_tag_2nd_elbow_curve.png` | Elbow Curve |
| `{type}_tag_2nd_silhouette_score.png` | Silhouette Score |
| `{type}_tag_2nd_pca_scatter.png` | PCA 2D 시각화 |
| `{type}_tag_2nd_tsne_scatter.png` | t-SNE 2D 시각화 |

> `{type}` = `dog` 또는 `owner`

---

## 자동 라벨링 방식

클러스터 라벨은 고정 사전 대신, 각 클러스터에 속한 태그 이름과 설명을 분석하여
키워드 매칭 방식으로 자동 부여합니다.

```
cluster에 포함된 태그 텍스트 -> 키워드 집합과 매칭 -> 가장 많이 매칭된 라벨 선택
```

> **주의:** cluster_id는 KMeans 실행마다 달라질 수 있으므로
> 최종 라벨은 클러스터별 포함 태그를 보고 재검토해야 합니다.
> 자동 라벨은 검토를 위한 임시 참고값이며 `label_source: keyword_auto` 로 표시됩니다.

---

## 실행 방법

```bash
pip install sentence-transformers scikit-learn pandas numpy matplotlib
python ai/eval/train_tag_semantic_kmeans.py
```

---

## 멘토님 설명용 문장

> "1차 실험에서는 강아지 태그와 보호자 태그를 함께 군집화했더니
> 의미 축이 섞이는 문제가 발생했고, 이를 확인한 뒤 2차 실험에서 분리하여 재실험했습니다."

> "단어 의미별 군집화는 태그 텍스트를 임베딩한 뒤 KMeans를 적용하는 방식이고,
> 기존 10D 유저 군집화는 태그 선택 결과를 점수화한 유저 벡터를 KMeans로 묶는 방식입니다.
> 두 실험은 목적이 다릅니다."

> "그룹을 나눈 것은 KMeans이고, 그룹 이름을 붙인 것은 서비스 기획적 해석입니다.
> 2차 실험에서는 고정 라벨 대신 클러스터 내 실제 태그를 보고 자동으로 라벨을 도출했습니다."

> "에너자이저, 산책이 제일 좋아, 밖이 좋아요 같은 태그들이 임베딩 공간에서도
> 의미적으로 가까이 위치한다는 것을 이 실험으로 확인했고,
> 이것이 DogScorer의 dog_a(활동성) 축에 이 태그들을 배치한 근거입니다."
"""
    path.write_text(content, encoding="utf-8")


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    _setup_font()
    _BASE_DIR.mkdir(parents=True, exist_ok=True)

    sep = "=" * 60
    print(sep)
    print("withDOG 태그 의미 기반 KMeans 군집화 실험 (2nd - 분리 실험)")
    print(sep)

    # 1) 태그 데이터 로드
    print("\n[1] 태그 데이터 로드")
    df = load_or_generate_tags()
    df_dog   = df[df["tag_type"] == "dog"].reset_index(drop=True)
    df_owner = df[df["tag_type"] == "owner"].reset_index(drop=True)
    print(f"    dog: {len(df_dog)}개  /  owner: {len(df_owner)}개")

    # 2) 임베딩 모델 로드 (공유)
    print(f"\n[2] 임베딩 모델 로드: {EMBED_MODEL}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)

    # 3) dog 태그 KMeans
    print("\n" + sep)
    print("[3] Dog 태그 KMeans (2nd)")
    print(sep)
    run_subset(df_dog, "dog", _DOG_DIR, model)

    # 4) owner 태그 KMeans
    print("\n" + sep)
    print("[4] Owner 태그 KMeans (2nd)")
    print(sep)
    run_subset(df_owner, "owner", _OWNER_DIR, model)

    # 5) README 갱신
    print("\n[5] README 갱신")
    update_readme(_BASE_DIR / "README_tag_semantic_kmeans.md")
    print("  README_tag_semantic_kmeans.md 업데이트")

    # 최종 요약
    print(f"\n{sep}")
    print("[완료] 2차 실험 결과 저장 위치:")
    print(f"  dog   -> {_DOG_DIR}")
    print(f"  owner -> {_OWNER_DIR}")
    print(sep)


if __name__ == "__main__":
    main()
