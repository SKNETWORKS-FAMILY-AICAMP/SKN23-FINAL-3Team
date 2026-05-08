import { useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { MapPin, Navigation, Phone, Star, X } from 'lucide-react';
import PlaceBadges from './PlaceBadges';

/**
 * 장소 상세 카드의 입력 데이터 — `PlaceResult` (placeService) 와 `FacilityCard` (chatService) 의
 * 합집합 형태로 정의. 양쪽 호출자가 그대로 넘길 수 있도록 모든 필드를 optional 로 둠.
 */
export interface PlaceLike {
  name: string;
  address?: string;
  category?: string;
  sub_category?: string;
  indoor?: string;
  outdoor?: string;
  has_parking?: string;
  conditions?: string;
  operation?: string;
  tel?: string;
  description?: string;
  pet_zone?: string;
  pet_size?: string;
  image?: string;
  firstimage?: string;
  content_id?: string;
}

export type PlaceDetailVariant = 'panel' | 'modal';

interface Props {
  place: PlaceLike;
  /**
   * 카드 외관 모드.
   * - `panel` (default): MapView·PlaceFavoritesPage 의 표준 카드 (rounded-2xl).
   *   호출처가 자체 grid/flex 레이아웃 안에 직접 배치.
   * - `modal`: 다이어리 흐름 (HomePage diaryResult / DiaryAlbum / CalendarPage) 에서 사용.
   *   panel 과 동일한 카드 본문을 backdrop dim + 중앙 정렬 wrapper 안에 띄움.
   *   X 버튼 + ESC + 배경 클릭 3중 dismiss.
   */
  variant?: PlaceDetailVariant;
  /** 이미지/플레이스홀더 노출. 디폴트 true. */
  showImage?: boolean;
  /** 반려견 이용 정보 (구역·크기·주차) 섹션 표시. */
  showPetInfo?: boolean;
  /** 장소 설명 섹션 표시. */
  showDescription?: boolean;
  /** 매장 위치(주소+길찾기) 섹션 분리 표시. */
  showLocationSection?: boolean;
  /** 일기 쓰기 버튼 (하단 CTA). 미전달 시 버튼 숨김. */
  onSelectForDiary?: () => void;
  /** 닫기 (X) 버튼 — modal 에서 우상단 + ESC + 배경 클릭에서 호출. */
  onClose?: () => void;
  /** 즐겨찾기 별 버튼. */
  isFavorite?: boolean;
  onToggleFavorite?: () => void;
  favoriteToggling?: boolean;
}

/**
 * 반려견 동반 장소의 상세 정보를 표시하는 통합 카드.
 *
 * `panel` 과 `modal` 두 variant 모두 동일한 카드 본문(`PanelCardBody`)을 공유한다.
 * `modal` 은 panel 카드를 backdrop + 중앙 정렬 wrapper 로 감싼 형태이며,
 * 시각·구조·디자인 토큰은 panel 과 1:1 동일.
 *
 * 사용처:
 * - panel: MapView 우측 상세, PlaceFavoritesPage 우측 상세
 * - modal: HomePage 다이어리 결과/앨범 상세, CalendarPage 다이어리 상세 (핀 클릭 시)
 */
export default function PlaceDetailCard(props: Props) {
  const { variant = 'panel', onClose } = props;

  // ESC 키 dismiss — modal 전용 (외부팀 QA #65 dismissibility 패턴 정합)
  useEffect(() => {
    if (variant !== 'modal' || !onClose) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [variant, onClose]);

  if (variant === 'modal') {
    return (
      <AnimatePresence>
        <motion.div
          key="place-modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-100 flex items-start justify-center px-4 py-10 overflow-y-auto"
          style={{ background: 'rgba(61,43,31,0.45)', backdropFilter: 'blur(4px)' }}
          onClick={onClose}
        >
          <motion.div
            key="place-modal-card"
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="relative w-full max-w-[520px]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* X 닫기 — 카드 우상단에 absolute 배치 */}
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                aria-label="닫기"
                className="absolute right-4 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 text-[#8B6355] shadow-sm transition hover:bg-white hover:text-[#3D2B1F]"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <PanelCardBody {...props} />
          </motion.div>
        </motion.div>
      </AnimatePresence>
    );
  }

  // panel (default)
  return <PanelCardBody {...props} />;
}

/**
 * panel · modal 양쪽이 공유하는 카드 본문.
 * 이미지 + 헤더(이름·즐겨찾기) + 주소 + 배지 + 정보 섹션들 + 일기쓰기 CTA.
 */
function PanelCardBody({
  place,
  showImage = true,
  showPetInfo = false,
  showDescription = false,
  showLocationSection = false,
  onSelectForDiary,
  isFavorite,
  onToggleFavorite,
  favoriteToggling,
}: Props) {
  const imageSrc = place.image || place.firstimage;
  return (
    <div className="overflow-hidden rounded-2xl border border-[#F2E7DD] bg-white shadow-sm">
      {showImage && (
        imageSrc ? (
          // 네이버 thumb (dthumb-phinf.pstatic.net) 등은 referer 검사로 hotlink 차단 →
          // referrerPolicy=no-referrer 로 우회. 그래도 실패 시 🐾 placeholder 로 fallback.
          <img
            src={imageSrc}
            alt={place.name}
            referrerPolicy="no-referrer"
            className="h-[200px] w-full object-cover"
            onError={(e) => {
              const img = e.currentTarget;
              img.style.display = 'none';
              const fallback = img.nextElementSibling as HTMLElement | null;
              if (fallback) fallback.style.display = 'flex';
            }}
          />
        ) : null
      )}
      {showImage && (
        <div
          className="h-[200px] w-full items-center justify-center bg-[#F6EFE8] text-5xl"
          style={{ display: imageSrc ? 'none' : 'flex' }}
        >
          🐾
        </div>
      )}

      <div className="border-b border-[#F5EAE1] p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="text-2xl font-bold text-[#2F241D]">{place.name}</div>
          {onToggleFavorite && (
            <button
              type="button"
              onClick={onToggleFavorite}
              disabled={favoriteToggling}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#F4845F] transition hover:bg-[#e8764f] active:scale-95 disabled:opacity-50"
            >
              <Star
                className="h-5 w-5"
                fill={isFavorite ? 'white' : 'none'}
                stroke="white"
              />
            </button>
          )}
        </div>
        {place.address && (
          <div className="mt-1 flex items-center gap-2 text-sm text-gray-500">
            <MapPin className="h-4 w-4 shrink-0" />
            <span>{place.address}</span>
          </div>
        )}
        <PlaceBadges place={place} variant="panel" />
      </div>

      <div className="space-y-4 px-5 py-5">
        {place.conditions !== undefined && (
          <section>
            <p className="mb-1 text-base font-bold text-[#2F241D]">이용조건</p>
            <p className="text-sm leading-7 text-gray-700">
              {place.conditions || '제한사항 없음'}
            </p>
          </section>
        )}

        {place.operation !== undefined && (
          <section>
            <p className="mb-1 text-base font-bold text-[#2F241D]">운영시간</p>
            <p className="whitespace-pre-wrap text-sm text-gray-700">
              {place.operation || '정보 없음'}
            </p>
          </section>
        )}

        {showPetInfo && (
          <section>
            <p className="mb-1 text-base font-bold text-[#2F241D]">반려견 이용 정보</p>
            <div className="space-y-1 text-sm text-gray-700">
              <p>반려견 구역: {place.pet_zone || '정보 없음'}</p>
              <p>크기 제한: {place.pet_size || '정보 없음'}</p>
              <p>주차: {place.has_parking === 'Y' ? '가능' : '정보 없음'}</p>
            </div>
          </section>
        )}

        {place.tel && (
          <section>
            <p className="mb-1 text-base font-bold text-[#2F241D]">{showLocationSection ? '매장 연락처' : '연락처'}</p>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-gray-700">{place.tel}</p>
              <a
                href={`tel:${place.tel}`}
                className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
              >
                <Phone className="h-4 w-4" />
                {showLocationSection ? '전화하기' : '전화'}
              </a>
            </div>
          </section>
        )}

        {showLocationSection && place.address && (
          <section>
            <p className="mb-1 text-base font-bold text-[#2F241D]">매장 위치</p>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-gray-700">{place.address}</p>
              <a
                href={`https://map.kakao.com/link/search/${encodeURIComponent(place.name)}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
              >
                <Navigation className="h-4 w-4" />
                길찾기
              </a>
            </div>
          </section>
        )}

        {/* PlaceFavoritesPage: 매장위치 분리 섹션이 없으면 길찾기를 단독 풀폭 버튼으로 표시 */}
        {!showLocationSection && place.address && (
          <a
            href={`https://map.kakao.com/link/search/${encodeURIComponent(place.name)}`}
            target="_blank"
            rel="noreferrer"
            className="flex w-full items-center justify-center gap-2 rounded-2xl border border-[#F5D6C8] py-2.5 text-sm font-semibold text-[#F4845F] transition hover:bg-[#FFF0E6]"
          >
            <Navigation className="h-4 w-4" />
            길찾기
          </a>
        )}

        {showDescription && place.description && (
          <section>
            <p className="mb-1 text-base font-bold text-[#2F241D]">장소 설명</p>
            <p className="text-sm leading-7 text-gray-700">{place.description}</p>
          </section>
        )}

        {onSelectForDiary && (
          <button
            type="button"
            onClick={onSelectForDiary}
            className="w-full rounded-2xl bg-[#F08A4B] py-3 text-sm font-bold text-white hover:bg-[#E67D3C]"
          >
            이 장소로 일기 쓰기 →
          </button>
        )}
      </div>
    </div>
  );
}
