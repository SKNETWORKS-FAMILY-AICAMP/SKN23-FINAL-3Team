interface Props {
  /** 일기 제목 (편집 모드에서는 input 의 값으로 분리). */
  title: string;
  /** 일기 본문. */
  body: string;
  /** 한 줄 요약 (있으면 ✨ 배지로 표시). */
  summary?: string;
  /** 일러스트 이미지 URL. 없으면 🐾 placeholder. */
  imageUrl?: string;
  /** 장소명 (있으면 📍 핀 버튼으로 표시). */
  placeName?: string;
  /** 핀 클릭 핸들러. 미전달 시 핀은 단순 표시. */
  onPlaceClick?: () => void;
  /** 핀 버튼 활성 상태 (modal 열려있을 때 색상 반전). */
  placePinActive?: boolean;
  /** 핀 버튼 비활성화 (loading 중). */
  placePinDisabled?: boolean;

  /** 편집 모드 — title/body 가 input/textarea 로 표시되고 변경 콜백 호출. */
  isEditing?: boolean;
  editTitle?: string;
  editBody?: string;
  onTitleChange?: (value: string) => void;
  onBodyChange?: (value: string) => void;
}

/**
 * 다이어리 본문 코어 카드 — 마스킹 테이프 + 제목 + 요약 + 핀 + 이미지 + 줄노트.
 *
 * HomePage diaryResult / DiaryAlbum selected / CalendarPage selectedDiary 3 곳에서
 * 거의 100% 동일한 마크업이 인라인으로 박혀있던 부분을 단일 컴포넌트로 통합.
 * 편집 모드 prop 흡수로 (a) 의 인라인 toggle 흐름도 함께 사용.
 */
export default function DiaryNoteCard({
  title,
  body,
  summary,
  imageUrl,
  placeName,
  onPlaceClick,
  placePinActive = false,
  placePinDisabled = false,
  isEditing = false,
  editTitle,
  editBody,
  onTitleChange,
  onBodyChange,
}: Props) {
  return (
    <div className="relative rounded-[28px] border border-[#E9D9C9] bg-[#FFFDF8] p-6 shadow-[0_8px_24px_rgba(61,43,31,0.08)] md:p-8">
      {/* 마스킹 테이프 */}
      <div className="absolute -top-3 left-10 h-6 w-20 rotate-[-8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />
      <div className="absolute -top-3 right-10 h-6 w-20 rotate-[8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />

      {/* 제목 / 요약 / 핀 */}
      <div className="mb-6 text-center">
        <p className="text-xs tracking-[0.2em] text-[#B08B7A]">오늘의 그림일기</p>
        {isEditing ? (
          <input
            value={editTitle ?? ''}
            onChange={(e) => onTitleChange?.(e.target.value)}
            className="mt-2 w-full rounded-xl border border-[#F4845F] bg-[#FFF8F3] px-3 py-2 text-center text-xl font-bold text-[#F4845F] outline-none"
          />
        ) : (
          <h3 className="mt-2 text-2xl font-bold text-[#F4845F] font-diary">{title}</h3>
        )}
        {summary && (
          <div className="mt-3 inline-flex rounded-full bg-[#FFF0E6] px-3 py-1 text-xs font-medium text-[#F4845F] font-diary">
            ✨ {summary}
          </div>
        )}
        {placeName && (
          onPlaceClick ? (
            <button
              type="button"
              onClick={onPlaceClick}
              disabled={placePinDisabled}
              className={`mt-2 inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition ${
                placePinActive ? 'bg-[#5B8DB8] text-white' : 'bg-[#F0F7FF] text-[#5B8DB8] hover:bg-[#ddeeff]'
              } disabled:opacity-60`}
            >
              📍 {placeName}
            </button>
          ) : (
            <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-[#F0F7FF] px-3 py-1 text-xs font-medium text-[#5B8DB8]">
              📍 {placeName}
            </div>
          )
        )}
      </div>

      {/* 이미지 — key={imageUrl} 로 URL 변경 시 강제 재마운트 (304 캐시 본문 부재 회피) */}
      <div className="mx-auto mb-6 w-full max-w-[520px] rounded-[22px] border border-[#E8D9CC] bg-white p-3 shadow-[0_6px_18px_rgba(61,43,31,0.06)]">
        {imageUrl ? (
          <img key={imageUrl} src={imageUrl} alt={title} className="w-full h-auto rounded-[16px] object-contain" />
        ) : (
          <div className="flex h-48 items-center justify-center text-5xl">🐾</div>
        )}
      </div>

      {/* 본문 — 줄노트 */}
      {isEditing ? (
        <textarea
          value={editBody ?? ''}
          onChange={(e) => onBodyChange?.(e.target.value)}
          rows={10}
          className="w-full rounded-[20px] border border-[#F4845F] bg-[#FFFCF8] px-5 py-5 text-[15px] leading-[31px] text-[#3D2B1F] outline-none resize-none"
          style={{ backgroundImage: 'repeating-linear-gradient(to bottom, transparent 0px, transparent 30px, #F3E7DA 31px)' }}
        />
      ) : (
        <div
          className="rounded-[20px] border border-[#F1E4D8] bg-[#FFFCF8] px-5 py-5"
          style={{ backgroundImage: 'repeating-linear-gradient(to bottom, transparent 0px, transparent 30px, #F3E7DA 31px)' }}
        >
          <p className="whitespace-pre-wrap text-[17px] leading-[31px] text-[#3D2B1F] font-diary">
            {body || '내용이 없어요.'}
          </p>
        </div>
      )}
    </div>
  );
}
