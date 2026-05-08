import type { PlaceLike } from './PlaceDetailCard';

type PlaceBadgesVariant = 'panel' | 'compact' | 'simple';

interface Props {
  /** 배지로 변환할 장소 데이터 (`category` / `sub_category` / `indoor` / `outdoor` / `has_parking`). */
  place: PlaceLike;
  /**
   * 배지 외관 모드.
   * - `panel` (default): MapView 상세 패널·PlaceFavoritesPage 의 표준 배지 (rounded-md, 큰 배경).
   * - `compact`: PlaceDetailCard 의 sidebar/modal variant 에서 쓰는 작은 배지 (rounded-full).
   * - `simple`: MapView 카드 목록의 텍스트만 (배경 없음).
   */
  variant?: PlaceBadgesVariant;
  /** simple 모드에서 주차 배지 노출 여부. 디폴트 false. */
  showParking?: boolean;
}

/**
 * 장소 카드의 카테고리 / 실내 / 야외 / 주차 배지 묶음.
 *
 * 보고서 #5 5곳 (PlaceDetailCard 패널·sidebar·modal + MapView 카드 목록 + 기타) 에서 거의 동일한
 * 조건부 span 마크업이 박혀있던 것을 단일 컴포넌트로 통합. variant 로 톤만 분기.
 */
export default function PlaceBadges({ place, variant = 'panel', showParking = false }: Props) {
  if (variant === 'simple') {
    return (
      <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
        {place.category && <span>{place.category}</span>}
        {place.sub_category && <span>{place.sub_category}</span>}
        {place.indoor === 'Y' && <span>실내</span>}
        {place.outdoor === 'Y' && <span>실외</span>}
        {showParking && place.has_parking === 'Y' && <span>주차</span>}
      </div>
    );
  }

  if (variant === 'compact') {
    return (
      <div className="flex flex-wrap gap-1 mt-1.5">
        {place.category && (
          <span className="rounded-full bg-[#FFF0E6] px-2.5 py-0.5 text-xs text-[#F4845F] font-medium">{place.category}</span>
        )}
        {place.sub_category && (
          <span className="rounded-full bg-[#FFF0E6] px-2.5 py-0.5 text-xs text-[#F4845F] font-medium">{place.sub_category}</span>
        )}
        {place.indoor === 'Y' && (
          <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs text-blue-500 font-medium">실내 가능</span>
        )}
        {place.outdoor === 'Y' && (
          <span className="rounded-full bg-[#E8F5E9] px-2.5 py-0.5 text-xs text-[#4CAF50] font-medium">야외 가능</span>
        )}
        {place.has_parking === 'Y' && (
          <span className="rounded-full bg-[#F3E5F5] px-2.5 py-0.5 text-xs text-[#9C27B0] font-medium">주차 가능</span>
        )}
      </div>
    );
  }

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {place.category && (
        <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">{place.category}</span>
      )}
      {place.sub_category && (
        <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">{place.sub_category}</span>
      )}
      {place.indoor === 'Y' && (
        <span className="rounded-md bg-[#EFF6FF] px-2.5 py-1 text-xs font-medium text-blue-600">실내 가능</span>
      )}
      {place.outdoor === 'Y' && (
        <span className="rounded-md bg-[#F0FDF4] px-2.5 py-1 text-xs font-medium text-green-600">실외 가능</span>
      )}
    </div>
  );
}
