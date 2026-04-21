import { useState, useEffect, useRef, useMemo } from 'react';
import { Search, MapPin, Phone, Navigation } from 'lucide-react';

declare global {
  interface Window {
    kakao: any;
  }
}

const MAP_TAGS = ['#공원', '#산책', '#애견카페', '#카페', '#반려견 친화'];

interface Props {
  onUsePlace: (place: string) => void;
}

export default function MapView({ onUsePlace }: Props) {
  const [keyword, setKeyword] = useState('');
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const [places, setPlaces] = useState<any[]>([]);
  const mapRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<any[]>([]);
  const mapInstanceRef = useRef<any>(null);

  useEffect(() => {
    const waitForKakao = () => {
      if (!window.kakao || !window.kakao.maps) {
        setTimeout(waitForKakao, 100);
        return;
      }

      window.kakao.maps.load(() => {
        const options = {
          center: new window.kakao.maps.LatLng(37.5665, 126.9780),
          level: 3,
        };

        mapInstanceRef.current = new window.kakao.maps.Map(
          mapRef.current,
          options
        );

        const marker = new window.kakao.maps.Marker({
          map: mapInstanceRef.current,
          position: new window.kakao.maps.LatLng(37.5665, 126.9780),
        });

        markersRef.current.push(marker);
      });
    };

    waitForKakao();
  }, []);

  const searchPlaces = async (query: string) => {
    if (!query.trim()) return;
    const res = await fetch(`/api/places/search?query=${encodeURIComponent(query)}`);
    const data = await res.json();
    setPlaces(data.places);
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];
    if (data.places.length === 0) return;
    const bounds = new window.kakao.maps.LatLngBounds();
    data.places.forEach((place: any) => {
      const position = new window.kakao.maps.LatLng(place.lat, place.lng);
      const marker = new window.kakao.maps.Marker({
        map: mapInstanceRef.current,
        position,
      });
      markersRef.current.push(marker);
      bounds.extend(position);
    });
    mapInstanceRef.current.setBounds(bounds);
  };

  const selectedPlace = useMemo(
    () => places.find((place) => place.name === selectedPlaceId) ?? null,
    [selectedPlaceId, places]
  );

  const filteredPlaces = useMemo(() => {
    if (!keyword.trim()) return places;
    return places.filter((item) => {
      const target = `${item.name} ${item.address} ${item.category}`.toLowerCase();
      return target.includes(keyword.toLowerCase());
    });
  }, [keyword, places]);

  const handleSelectPlace = (placeName: string) => {
    setSelectedPlaceId(placeName);
    const place = places.find((p) => p.name === placeName);
    if (place && mapInstanceRef.current) {
      const moveLatLon = new window.kakao.maps.LatLng(place.lat, place.lng);
      mapInstanceRef.current.setCenter(moveLatLon);
      markersRef.current.forEach((m) => m.setMap(null));
      markersRef.current = [];
      const marker = new window.kakao.maps.Marker({
        map: mapInstanceRef.current,
        position: moveLatLon,
      });
      markersRef.current.push(marker);
    }
  };

  return (
    <div className="h-full bg-[#FCFAF7] p-4 md:p-6">
      <div
        className={`grid gap-5 transition-all duration-300 ${
          selectedPlace ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1'
        }`}
      >
        {/* 왼쪽: 검색 + 태그 + 지도 + 추천장소 */}
        <div className="min-w-0">
          <div className="space-y-4 rounded-[24px] border border-[#F2E7DD] bg-white p-4 shadow-sm md:p-5">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchPlaces(keyword)}
                placeholder="지역 / 장소 검색"
                className="w-full rounded-xl border border-[#E7DDD3] bg-white py-3 pl-10 pr-4 text-sm outline-none transition focus:border-[#F08A4B] focus:ring-2 focus:ring-[#FCE2CF]"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              {MAP_TAGS.map((tag, idx) => (
                <button
                  key={tag}
                  type="button"
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                    idx === 0
                      ? 'bg-pink-500 text-white'
                      : 'border border-[#E8DED5] bg-white text-gray-600 hover:bg-[#FFF7F1]'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>

            <div
              className={`overflow-hidden rounded-2xl border border-[#EDE3DA] transition-all duration-300 ${
                selectedPlace ? 'h-[480px]' : 'h-[640px]'
              }`}
            >
              <div ref={mapRef} className="h-full w-full" />
            </div>

            <div>
              <div className="mb-3 flex items-center justify-between">
                <div className="text-sm font-semibold text-gray-700">추천 장소</div>
                {selectedPlace && (
                  <button
                    type="button"
                    onClick={() => setSelectedPlaceId(null)}
                    className="text-xs font-medium text-gray-500 hover:text-gray-700"
                  >
                    상세 닫기
                  </button>
                )}
              </div>

              <div className="space-y-3">
                {places.map((item) => {
                  const isActive = selectedPlace?.name === item.name;
                  return (
                    <div
                      key={item.name}
                      className={`rounded-2xl border p-4 transition ${
                        isActive
                          ? 'border-[#F4B183] bg-[#FFF7F1] shadow-sm'
                          : 'border-[#F4E8DE] bg-[#FFFDF9]'
                      }`}
                    >
                      <div className="text-base font-semibold text-gray-800">📍 {item.name}</div>
                      <div className="mt-1 text-sm text-gray-600">{item.address}</div>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                        <span>{item.category}</span>
                        <span>{item.city}</span>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => isActive ? setSelectedPlaceId(null) : handleSelectPlace(item.name)}
                          className={`rounded-full px-3 py-2 text-sm font-semibold transition ${
                            isActive
                              ? 'bg-[#F08A4B] text-white hover:bg-[#E67D3C]'
                              : 'border border-[#F3C8A8] bg-white text-[#E57A3A] hover:bg-[#FFF2E9]'
                          }`}
                        >
                          {isActive ? '장소 정보 닫기' : '장소 보기'}
                        </button>
                        <button
                          type="button"
                          onClick={() => onUsePlace(item.name)}
                          className="text-sm font-semibold text-orange-600 hover:text-orange-700"
                        >
                          이 장소로 일기 쓰기 →
                        </button>
                      </div>
                    </div>
                  );
                })}

                {filteredPlaces.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-[#E8DED5] bg-[#FFFCF8] px-4 py-8 text-center text-sm text-gray-500">
                    검색 결과가 없어요.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 오른쪽: 장소 상세 패널 */}
        {selectedPlace && (
          <div className="min-w-0">
            <div className="overflow-hidden rounded-[28px] border border-[#F2E7DD] bg-white shadow-sm">
              {/* 이미지 */}
              <img
                src={selectedPlace.image || '../assets/default-place.png'}
                alt={selectedPlace.name}
                className="h-[200px] w-full object-cover"
                onError={(e) => {
                  e.currentTarget.src = '../assets/default-place.png';
                }}
              />

              {/* 헤더 */}
              <div className="p-5 border-b border-[#F5EAE1]">
                <div className="text-2xl font-bold text-[#2F241D]">{selectedPlace.name}</div>
                <div className="mt-1 flex items-center gap-2 text-sm text-gray-500">
                  <MapPin className="h-4 w-4" />
                  <span>{selectedPlace.address}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">
                    {selectedPlace.category}
                  </span>
                  <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">
                    {selectedPlace.city}
                  </span>
                </div>
              </div>

              <div className="space-y-6 px-5 py-5">
                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">이용조건</div>
                  <p className="text-sm leading-7 text-gray-700">
                    {selectedPlace.conditions || '제한사항 없음'}
                  </p>
                </section>

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">영업시간</div>
                  <p className="text-sm text-gray-700">{selectedPlace.open_hours || '정보 없음'}</p>
                </section>

                {selectedPlace.closed_days && (
                  <section>
                    <div className="mb-3 text-base font-bold text-[#2F241D]">휴무일</div>
                    <p className="text-sm text-gray-700">{selectedPlace.closed_days}</p>
                  </section>
                )}

                {selectedPlace.tel && (
                  <section>
                    <div className="mb-3 text-base font-bold text-[#2F241D]">매장 연락처</div>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm text-gray-700">{selectedPlace.tel}</p>
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
                      >
                        <Phone className="h-4 w-4" />
                        전화하기
                      </button>
                    </div>
                  </section>
                )}

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">매장 위치</div>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-gray-700">{selectedPlace.address}</p>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
                    >
                      <Navigation className="h-4 w-4" />
                      길찾기
                    </button>
                  </div>
                </section>

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">입장료</div>
                  <p className="text-sm text-gray-700">{selectedPlace.entrance_fee || '무료'}</p>
                </section>

                {selectedPlace.parking && (
                  <section>
                    <div className="mb-3 text-base font-bold text-[#2F241D]">주차</div>
                    <p className="text-sm text-gray-700">{selectedPlace.parking}</p>
                  </section>
                )}

                {selectedPlace.homepage && selectedPlace.homepage !== '정보없음' && (
                  <section>
                    <div className="mb-3 text-base font-bold text-[#2F241D]">홈페이지</div>
                    <a
                      href={selectedPlace.homepage}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-blue-500 underline"
                    >
                      {selectedPlace.homepage}
                    </a>
                  </section>
                )}

                <section className="rounded-2xl bg-[#FAF7F3] px-4 py-8 text-center">
                  <div className="text-4xl font-bold text-gray-400">0.0</div>
                  <div className="mt-2 text-sm text-gray-500">작성된 리뷰가 없어요</div>
                  <button
                    type="button"
                    className="mt-5 rounded-full border border-pink-200 px-5 py-2 text-sm font-semibold text-pink-500 hover:bg-pink-50"
                  >
                    리뷰 작성하기
                  </button>
                </section>

                <button
                  type="button"
                  onClick={() => onUsePlace(selectedPlace.name)}
                  className="w-full rounded-2xl bg-[#F08A4B] py-3 text-sm font-bold text-white hover:bg-[#E67D3C]"
                >
                  이 장소로 일기 쓰기 →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}