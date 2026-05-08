import { useState, useEffect } from 'react';
import { Star, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router';
import { getPlaceFavorites, togglePlaceFavorite, type FavoritePlace, type PlaceResult } from '../services/placeService';
import { getPlaceByName, type FacilityCard } from '../services/chatService';
import PlaceDetailCard from '../components/PlaceDetailCard';

/** FacilityCard → PlaceResult 변환. HomePage 의 autoPlace state 가 PlaceResult 타입이라 매핑 필요. */
function facilityToPlaceResult(f: FacilityCard): PlaceResult {
  return {
    name: f.name,
    address: f.address,
    category: f.category,
    sub_category: f.sub_category,
    content_id: f.content_id,
    lat: f.lat,
    lng: f.lng,
    tel: f.tel,
    conditions: f.conditions,
    pet_zone: '',
    pet_size: '',
    has_parking: f.has_parking,
    operation: f.operation,
    indoor: f.indoor,
    outdoor: f.outdoor,
    description: f.description,
    firstimage: '',
    similarity: f.match_confidence ?? 0,
    final_score: f.match_confidence ?? 0,
  };
}

export default function PlaceFavoritesPage() {
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState<FavoritePlace[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<FacilityCard | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [togglingIds, setTogglingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    getPlaceFavorites()
      .then(setFavorites)
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  const handleCardClick = async (item: FavoritePlace) => {
    setDetailLoading(true);
    setSelected(null);
    try {
      const facility = await getPlaceByName(item.name);
      setSelected(facility);
    } catch {
      alert('시설 정보를 불러올 수 없어요.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleToggle = async (e: React.MouseEvent, contentId: string) => {
    e.stopPropagation();
    if (togglingIds.has(contentId)) return;
    setTogglingIds((prev) => new Set(prev).add(contentId));
    try {
      const res = await togglePlaceFavorite(contentId);
      if (!res.is_favorite) {
        setFavorites((prev) => prev.filter((f) => f.content_id !== contentId));
        if (selected?.content_id === contentId) setSelected(null);
      }
    } catch {
    } finally {
      setTogglingIds((prev) => { const next = new Set(prev); next.delete(contentId); return next; });
    }
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });

  return (
    <div className="min-h-screen bg-[#FFF8F3] pt-20 px-4 pb-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center gap-3">
          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-1.5 rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            뒤로
          </button>
          <h1 className="flex items-center gap-1.5 text-xl font-bold text-[#3D2B1F]">
            ⭐ 장소 즐겨찾기
            {!loading && (
              <span className="text-sm text-[#B08B7A]">({favorites.length})</span>)}
          </h1>
        </div>

        {loading ? (
          <div className="flex h-60 items-center justify-center">
            <span className="text-sm text-[#B08B7A]">불러오는 중...</span>
          </div>
        ) : favorites.length === 0 ? (
          <div className="flex h-60 flex-col items-center justify-center gap-3 text-center">
            <span className="text-5xl">⭐</span>
            <p className="text-base font-bold text-[#3D2B1F]">즐겨찾기한 장소가 없어요</p>
            <p className="text-sm text-[#8B6355]">지도에서 장소 카드의 별 버튼을 눌러 추가해보세요</p>
          </div>
        ) : (
          <div className={`grid gap-6 ${selected || detailLoading ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1'}`}>
            {/* 즐겨찾기 목록 */}
            <div className="space-y-3">
              {favorites.map((item) => (
                <div
                  key={item.content_id}
                  onClick={() => handleCardClick(item)}
                  className={`relative flex cursor-pointer items-center gap-4 rounded-2xl border bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${selected?.content_id === item.content_id
                    ? 'border-[#F4845F] bg-[#FFF0E6]'
                    : 'border-[#F5D6C8]'
                    }`}
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#FFF0E6] text-2xl">
                    📍
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-[#3D2B1F]">{item.name}</p>
                    {item.sub_category && (
                      <p className="mt-0.5 text-xs text-[#8B6355]">{item.sub_category}</p>
                    )}
                    <p className="mt-0.5 text-[11px] text-[#B08B7A]">{formatDate(item.favorited_at)} 추가</p>
                  </div>
                  <button
                    onClick={(e) => handleToggle(e, item.content_id)}
                    disabled={togglingIds.has(item.content_id)}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#F4845F] transition hover:bg-[#e8764f] active:scale-95 disabled:opacity-50"
                  >
                    <Star className="h-4 w-4" fill="white" stroke="white" />
                  </button>
                </div>
              ))}
            </div>

            {/* 상세 패널 */}
            {(selected || detailLoading) && (
              <div className="self-start">
                {detailLoading ? (
                  <div className="overflow-hidden rounded-2xl border border-[#F2E7DD] bg-white shadow-sm">
                    <div className="flex h-60 items-center justify-center">
                      <span className="text-sm text-[#B08B7A]">불러오는 중...</span>
                    </div>
                  </div>
                ) : selected && (
                  <PlaceDetailCard
                    place={selected}
                    variant="panel"
                    showImage
                    showPetInfo
                    showDescription
                    showLocationSection
                    isFavorite
                    onToggleFavorite={async () => {
                      // 즐겨찾기 페이지의 카드 = 모두 즐겨찾기 상태. 별 클릭 = 해제 = 카드 + 상세 패널 모두 닫힘.
                      const cid = selected.content_id;
                      if (!cid || togglingIds.has(cid)) return;
                      setTogglingIds((prev) => new Set(prev).add(cid));
                      try {
                        const res = await togglePlaceFavorite(cid);
                        if (!res.is_favorite) {
                          setFavorites((prev) => prev.filter((f) => f.content_id !== cid));
                          setSelected(null);
                        }
                      } finally {
                        setTogglingIds((prev) => {
                          const next = new Set(prev);
                          next.delete(cid);
                          return next;
                        });
                      }
                    }}
                    favoriteToggling={togglingIds.has(selected.content_id)}
                    onSelectForDiary={() =>
                      navigate('/home?tab=diary', {
                        state: { autoPlace: facilityToPlaceResult(selected) },
                      })
                    }
                  />
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
