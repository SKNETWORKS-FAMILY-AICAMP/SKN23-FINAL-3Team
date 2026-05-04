import { useState, useEffect } from 'react';
import { Star, MapPin, Navigation, Phone, ArrowLeft } from 'lucide-react';
import { getPlaceFavorites, togglePlaceFavorite, type FavoritePlace } from '../services/placeService';
import { getPlaceByName, type FacilityCard } from '../services/chatService';

export default function PlaceFavoritesPage() {
  const [favorites, setFavorites] = useState<FavoritePlace[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<FacilityCard | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [togglingIds, setTogglingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    getPlaceFavorites()
      .then(setFavorites)
      .catch(() => {})
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
          <h1 className="text-xl font-bold text-[#3D2B1F]">⭐ 장소 즐겨찾기</h1>
          {!loading && (
            <span className="ml-auto text-sm text-[#B08B7A]">{favorites.length}곳</span>
          )}
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
                  className={`relative flex cursor-pointer items-center gap-4 rounded-2xl border bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${
                    selected?.content_id === item.content_id
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
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-black/20 transition hover:bg-black/35 disabled:opacity-50"
                  >
                    <Star className="h-4 w-4" fill="white" stroke="white" />
                  </button>
                </div>
              ))}
            </div>

            {/* 상세 패널 */}
            {(selected || detailLoading) && (
              <div className="overflow-hidden rounded-[28px] border border-[#F2E7DD] bg-white shadow-sm self-start">
                {detailLoading ? (
                  <div className="flex h-60 items-center justify-center">
                    <span className="text-sm text-[#B08B7A]">불러오는 중...</span>
                  </div>
                ) : selected && (
                  <>
                    <div className="flex h-[180px] w-full items-center justify-center bg-[#F6EFE8] text-5xl">
                      🐾
                    </div>
                    <div className="border-b border-[#F5EAE1] p-5">
                      <p className="text-xl font-bold text-[#2F241D]">{selected.name}</p>
                      <div className="mt-1 flex items-center gap-2 text-sm text-gray-500">
                        <MapPin className="h-4 w-4 shrink-0" />
                        <span>{selected.address}</span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {selected.category && (
                          <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">{selected.category}</span>
                        )}
                        {selected.sub_category && (
                          <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">{selected.sub_category}</span>
                        )}
                        {selected.indoor === 'Y' && (
                          <span className="rounded-md bg-[#EFF6FF] px-2.5 py-1 text-xs font-medium text-blue-600">실내 가능</span>
                        )}
                        {selected.outdoor === 'Y' && (
                          <span className="rounded-md bg-[#F0FDF4] px-2.5 py-1 text-xs font-medium text-green-600">실외 가능</span>
                        )}
                      </div>
                    </div>
                    <div className="space-y-4 px-5 py-5">
                      {selected.operation && (
                        <div>
                          <p className="mb-1 text-sm font-bold text-[#2F241D]">운영시간</p>
                          <p className="text-sm text-gray-700">{selected.operation}</p>
                        </div>
                      )}
                      {selected.conditions && (
                        <div>
                          <p className="mb-1 text-sm font-bold text-[#2F241D]">이용조건</p>
                          <p className="text-sm text-gray-700">{selected.conditions}</p>
                        </div>
                      )}
                      {selected.tel && (
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="mb-1 text-sm font-bold text-[#2F241D]">연락처</p>
                            <p className="text-sm text-gray-700">{selected.tel}</p>
                          </div>
                          <a
                            href={`tel:${selected.tel}`}
                            className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-3 py-1.5 text-sm font-medium text-pink-500 hover:bg-pink-50"
                          >
                            <Phone className="h-4 w-4" />
                            전화
                          </a>
                        </div>
                      )}
                      <a
                        href={`https://map.kakao.com/link/search/${encodeURIComponent(selected.name)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="flex w-full items-center justify-center gap-2 rounded-2xl border border-[#F5D6C8] py-2.5 text-sm font-semibold text-[#F4845F] transition hover:bg-[#FFF0E6]"
                      >
                        <Navigation className="h-4 w-4" />
                        길찾기
                      </a>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
