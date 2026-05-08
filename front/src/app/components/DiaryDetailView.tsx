import { useEffect, useState } from 'react';
import { Trash2 } from 'lucide-react';
import { getPlaceByName, type FacilityCard } from '../services/chatService';
import { useFavoriteToggle } from '../hooks/useFavoriteToggle';
import DiaryNoteCard from './DiaryNoteCard';
import PlaceDetailCard from './PlaceDetailCard';
import ConfirmModal from './ConfirmModal';

/**
 * DiaryDetailView 가 받는 정규형 일기 데이터.
 *
 * 호출처별 raw 타입(DiaryEntry / DiaryRecord / GeneratedDiary) 이 다르므로
 * 호출 시점에 본 인터페이스로 매핑한다. 핀(`placeName`) 은 이름 string 으로,
 * 실제 시설 정보는 클릭 시 `getPlaceByName` 호출로 lazy 조회.
 */
export interface DiaryViewModel {
  title: string;
  body: string;
  summary?: string;
  imageUrl?: string;
  placeName?: string;
}

interface Props {
  /** 정규형 일기. */
  diary: DiaryViewModel;
  /** 헤더 좌측 뒤로가기 버튼 라벨. 디폴트 "← 뒤로". */
  backLabel?: string;
  /** 뒤로가기 콜백. */
  onBack: () => void;
  /** 헤더 타이틀. 디폴트 "🐾 그림일기". */
  headerTitle?: string;
  /**
   * 편집 저장 콜백. 미전달 시 ✏️ 수정 버튼이 표시되지 않음 (캘린더 = 단순 보기 모드).
   * 호출처는 `(title, body) => Promise<void>` 형태로 백엔드 업데이트 + 부모 state 갱신을 처리.
   */
  onUpdate?: (title: string, body: string) => Promise<void>;
  /**
   * 삭제 콜백. 미전달 시 🗑 버튼이 표시되지 않음.
   * 호출처는 백엔드 deleteDiary + 부모 state 갱신 + 화면 복귀(onBack 호출)를 처리.
   * 호출 시점에는 본 컴포넌트가 ConfirmModal 로 사용자 확인을 이미 받은 후.
   */
  onDelete?: () => Promise<void>;
}

/**
 * 다이어리 상세 보기 통합 뷰 ((b) 앨범 → 상세 + (c) 캘린더 → 상세).
 *
 * 응집 영역:
 *   1. 헤더 — 뒤로가기 + 타이틀 + (옵션) 편집/저장/취소 액션
 *   2. 본문 — DiaryNoteCard (편집 모드 prop 흡수)
 *   3. 핀 클릭 → PlaceDetailCard variant="modal" 호출 (state 자체 관리)
 *   4. 즐겨찾기 별 → useFavoriteToggle 훅 (3 호출처에서 중복되던 패턴 응집)
 *
 * (a) 다이어리 결과 화면(자동저장 + 인라인 편집) 은 본 컴포넌트 영역 외 — DiaryNoteCard 만 사용.
 */
export default function DiaryDetailView({
  diary,
  backLabel = '← 뒤로',
  onBack,
  headerTitle = '🐾 그림일기',
  onUpdate,
  onDelete,
}: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [editSaving, setEditSaving] = useState(false);

  // 핀 modal — getPlaceByName 으로 lazy 조회
  const [placeDetail, setPlaceDetail] = useState<FacilityCard | null>(null);
  const [placeDetailLoading, setPlaceDetailLoading] = useState(false);
  const [placeError, setPlaceError] = useState<string | null>(null);

  // 삭제 확인 — ConfirmModal 재사용
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const favorite = useFavoriteToggle();

  // 일기 변경 시 modal 닫기 + 편집 모드 리셋
  useEffect(() => {
    setPlaceDetail(null);
    setPlaceDetailLoading(false);
    setIsEditing(false);
  }, [diary.title, diary.body]);

  const handleClickPlace = async (placeName: string) => {
    if (placeDetail && placeDetail.name === placeName) {
      setPlaceDetail(null);
      return;
    }
    setPlaceDetailLoading(true);
    setPlaceDetail(null);
    setPlaceError(null);
    try {
      const facility = await getPlaceByName(placeName);
      setPlaceDetail(facility);
    } catch {
      setPlaceError('장소 정보를 불러올 수 없어요');
      setTimeout(() => setPlaceError(null), 3000);
    } finally {
      setPlaceDetailLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!onUpdate) return;
    setEditSaving(true);
    try {
      await onUpdate(editTitle, editBody);
      setIsEditing(false);
    } catch {
      alert('수정에 실패했어요. 다시 시도해주세요.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!onDelete || deleting) return;
    setDeleting(true);
    try {
      await onDelete();
      setDeleteOpen(false);
      // 호출처가 onBack / state 갱신 처리. 본 컴포넌트는 모달만 닫음.
    } catch (err) {
      alert(err instanceof Error ? err.message : '삭제에 실패했어요. 다시 시도해주세요.');
    } finally {
      setDeleting(false);
    }
  };

  const showModal = placeDetail !== null;

  return (
    <>
      {/* 헤더 */}
      <div className="mb-4 flex items-center gap-3">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
        >
          {backLabel}
        </button>
        <h2 className="text-lg font-bold text-[#3D2B1F]">{headerTitle}</h2>
        <div className="ml-auto flex items-center gap-2">
          {!isEditing && onUpdate && (
            <button
              onClick={() => {
                setEditTitle(diary.title);
                setEditBody(diary.body);
                setIsEditing(true);
              }}
              className="rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
            >
              ✏️ 수정
            </button>
          )}
          {!isEditing && onDelete && (
            <button
              type="button"
              onClick={() => setDeleteOpen(true)}
              aria-label="다이어리 삭제"
              className="grid h-7 w-7 place-items-center rounded-full border border-[#F5D6C8] bg-white text-[#8B6355] transition hover:border-red-200 hover:bg-red-50 hover:text-red-500"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
          {isEditing && (
            <>
              <button
                onClick={() => setIsEditing(false)}
                className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-400 transition hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={editSaving}
                className="rounded-full bg-[#F4845F] px-3 py-1.5 text-xs text-white transition hover:bg-[#e0724e] disabled:opacity-50"
              >
                {editSaving ? '저장 중...' : '저장'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* 본문 + 에러 */}
      <DiaryNoteCard
        title={diary.title}
        body={diary.body}
        summary={diary.summary}
        imageUrl={diary.imageUrl}
        placeName={diary.placeName}
        onPlaceClick={diary.placeName ? () => handleClickPlace(diary.placeName!) : undefined}
        placePinActive={showModal}
        placePinDisabled={placeDetailLoading}
        isEditing={isEditing}
        editTitle={editTitle}
        editBody={editBody}
        onTitleChange={setEditTitle}
        onBodyChange={setEditBody}
      />
      {placeError && (
        <p className="mt-2 text-center text-xs text-red-500">{placeError}</p>
      )}

      {/* 핀 modal */}
      {showModal && placeDetail && (
        <PlaceDetailCard
          place={placeDetail}
          variant="modal"
          showImage
          showPetInfo
          showDescription
          showLocationSection
          onClose={() => setPlaceDetail(null)}
          isFavorite={favorite.isFavorite(placeDetail.content_id)}
          onToggleFavorite={() => favorite.toggle(placeDetail.content_id)}
          favoriteToggling={favorite.isToggling(placeDetail.content_id)}
        />
      )}

      <ConfirmModal
        isOpen={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleConfirmDelete}
        title="다이어리를 삭제하시겠습니까?"
        description="삭제된 다이어리는 복구할 수 없습니다."
        confirmLabel="삭제"
        cancelLabel="취소"
        variant="danger"
        loading={deleting}
      />
    </>
  );
}
