import { useMemo, useState } from 'react';
import {
  Search,
  MapPin,
  Star,
  Phone,
  Navigation,
  Heart,
  Share2,
} from 'lucide-react';

const MAP_TAGS = ['#공원', '#산책', '#애견카페', '#카페', '#반려견 친화'];

const RECOMMENDED_PLACES = [
  {
    id: 1,
    name: '한강공원 반포지구',
    shortName: '한강',
    desc: '서울 서초구 반포동',
    fullAddress: '서울특별시 서초구 반포동',
    rating: 0.0,
    likes: 4,
    tags: ['#비포장로', '#반려견과 여유'],
    badgeTags: ['적적한', '반듯한', '풍부한'],
    intro:
      '서울시민의 가장 대표적인 휴식공원으로 주변에 편의점, 다이닝이 잘 되어 있어 많은 사람들이 찾는 곳',
    hours: '운영시간 정보 없음',
    phone: '02-3780-0777',
    price: '입장료 0원',
    image:
      'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 2,
    name: '서울숲 공원',
    shortName: '서울숲',
    desc: '서울 성동구 뚝섬로',
    fullAddress: '서울특별시 성동구 뚝섬로 273',
    rating: 4.7,
    likes: 18,
    tags: ['#숲속 산책', '#넓은 산책'],
    badgeTags: ['산책좋은', '조용한', '넓은'],
    intro:
      '넓은 녹지와 산책로가 잘 조성되어 있어 반려견과 함께 여유롭게 걷기 좋은 장소예요.',
    hours: '매일 24시간',
    phone: '02-460-2905',
    price: '입장료 0원',
    image:
      'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 3,
    name: '월드컵공원',
    shortName: '월드컵공원',
    desc: '서울 마포구 상암동',
    fullAddress: '서울특별시 마포구 하늘공원로 95',
    rating: 4.5,
    likes: 12,
    tags: ['#반려견 산책', '#넓은 공간'],
    badgeTags: ['탁트인', '산책좋은', '자연친화'],
    intro:
      '넓은 공간과 탁 트인 뷰가 특징이며, 반려견과 가볍게 산책하거나 쉬어가기 좋은 장소입니다.',
    hours: '매일 09:00 - 18:00',
    phone: '02-300-5500',
    price: '입장료 0원',
    image:
      'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80',
  },
];

interface Props {
  onUsePlace: (place: string) => void;
}

export default function MapView({ onUsePlace }: Props) {
  const [keyword, setKeyword] = useState('');
  const [selectedPlaceId, setSelectedPlaceId] = useState<number | null>(null);

  const selectedPlace = useMemo(
    () =>
      RECOMMENDED_PLACES.find((place) => place.id === selectedPlaceId) ?? null,
    [selectedPlaceId]
  );

  const filteredPlaces = useMemo(() => {
    if (!keyword.trim()) return RECOMMENDED_PLACES;

    return RECOMMENDED_PLACES.filter((item) => {
      const target = `${item.name} ${item.desc} ${item.tags.join(' ')}`.toLowerCase();
      return target.includes(keyword.toLowerCase());
    });
  }, [keyword]);

  const handleSelectPlace = (placeId: number) => {
    setSelectedPlaceId(placeId);
  };

  const handleUsePlace = (placeName: string) => {
    onUsePlace(placeName);
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
              className={`overflow-hidden rounded-2xl border border-[#EDE3DA] bg-[#DCEAFE] transition-all duration-300 ${
                selectedPlace ? 'h-[480px]' : 'h-[640px]'
              }`}
            >
              <div className="flex h-full items-center justify-center text-sm text-gray-600">
                <div className="text-center">
                  <div className="mb-2 text-3xl">📍</div>
                  카카오맵 API 연결 영역
                  {selectedPlace && (
                    <div className="mt-2 text-xs text-[#F08A4B]">
                      선택 장소: {selectedPlace.name}
                    </div>
                  )}
                </div>
              </div>
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
                {filteredPlaces.map((item) => {
                  const isActive = selectedPlace?.id === item.id;

                  return (
                    <div
                      key={item.id}
                      className={`rounded-2xl border p-4 transition ${
                        isActive
                          ? 'border-[#F4B183] bg-[#FFF7F1] shadow-sm'
                          : 'border-[#F4E8DE] bg-[#FFFDF9]'
                      }`}
                    >
                      <div className="text-base font-semibold text-gray-800">
                        📍 {item.name}
                      </div>
                      <div className="mt-1 text-sm text-gray-600">{item.desc}</div>

                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                        {item.tags.map((tag) => (
                          <span key={tag}>{tag}</span>
                        ))}
                      </div>

                      <div className="mt-3 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            isActive ? setSelectedPlaceId(null) : handleSelectPlace(item.id)
                          }
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
                          onClick={() => handleUsePlace(item.name)}
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
              <div className="relative h-[240px] w-full overflow-hidden bg-gray-100 md:h-[300px]">
                <img
                  src={selectedPlace.image}
                  alt={selectedPlace.name}
                  className="h-full w-full object-cover"
                />

                <div className="absolute inset-0 bg-gradient-to-t from-black/35 via-black/5 to-transparent" />

                <div className="absolute bottom-0 left-0 right-0 flex items-end justify-between p-5 text-white">
                  <div>
                    <div className="mb-2 text-2xl font-bold">{selectedPlace.shortName}</div>
                    <div className="flex items-center gap-2 text-sm text-white/90">
                      <Star className="h-4 w-4 fill-current" />
                      <span>{selectedPlace.rating.toFixed(1)}</span>
                      <span>·</span>
                      <MapPin className="h-4 w-4" />
                      <span>{selectedPlace.fullAddress}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 rounded-full bg-white/15 px-3 py-2 backdrop-blur">
                    <button type="button" className="flex items-center gap-1 text-sm">
                      <Share2 className="h-4 w-4" />
                      <span>공유</span>
                    </button>
                    <button type="button" className="flex items-center gap-1 text-sm">
                      <Heart className="h-4 w-4" />
                      <span>{selectedPlace.likes}</span>
                    </button>
                  </div>
                </div>
              </div>

              <div className="border-b border-[#F5EAE1] px-5 pt-4">
                <div className="flex flex-wrap gap-2 pb-4">
                  {selectedPlace.badgeTags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="flex gap-8 text-sm font-semibold">
                  <button className="border-b-2 border-[#F08A4B] pb-3 text-[#F08A4B]">
                    장소정보
                  </button>
                  <button className="pb-3 text-gray-400">가격정보</button>
                  <button className="pb-3 text-gray-400">리뷰(0)</button>
                </div>
              </div>

              <div className="space-y-6 px-5 py-5">
                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">소개글</div>
                  <p className="text-sm leading-7 text-gray-700">{selectedPlace.intro}</p>
                </section>

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">영업시간</div>
                  <p className="text-sm text-gray-700">{selectedPlace.hours}</p>
                </section>

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">매장 연락처</div>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-gray-700">{selectedPlace.phone}</p>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
                    >
                      <Phone className="h-4 w-4" />
                      전화하기
                    </button>
                  </div>
                </section>

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">매장 위치</div>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-gray-700">{selectedPlace.fullAddress}</p>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
                    >
                      <Navigation className="h-4 w-4" />
                      길찾기
                    </button>
                  </div>

                  <div className="mt-4 overflow-hidden rounded-2xl border border-[#EFE5DC] bg-[#EEF5EA]">
                    <div className="flex h-[220px] items-center justify-center text-sm text-gray-500">
                      지도 미리보기 영역
                    </div>
                  </div>
                </section>

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">가격정보</div>
                  <p className="text-sm text-gray-700">{selectedPlace.price}</p>
                </section>

                <section className="rounded-2xl bg-[#FAF7F3] px-4 py-8 text-center">
                  <div className="text-4xl font-bold text-gray-400">
                    {selectedPlace.rating.toFixed(1)}
                  </div>
                  <div className="mt-2 text-sm text-gray-500">작성된 리뷰가 없어요</div>
                  <button
                    type="button"
                    className="mt-5 rounded-full border border-pink-200 px-5 py-2 text-sm font-semibold text-pink-500 hover:bg-pink-50"
                  >
                    리뷰 작성하기
                  </button>
                </section>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}