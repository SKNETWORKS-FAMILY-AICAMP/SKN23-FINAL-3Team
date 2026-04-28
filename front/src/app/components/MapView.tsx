import { useEffect, useMemo, useRef, useState } from 'react';
import { MapPin, Navigation, Phone } from 'lucide-react';
import type { PlaceResult } from '../services/placeService';

declare global {
  interface Window {
    kakao: any;
  }
}


interface Props {
  places: PlaceResult[];
  onUsePlace: (place: PlaceResult) => void;
}

const DEFAULT_CENTER = { lat: 37.5665, lng: 126.9780 };

export default function MapView({ places, onUsePlace }: Props) {
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const infoWindowRef = useRef<any>(null);
  const relayoutTimerRef = useRef<number | null>(null);

  const clearMarkers = () => {
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];
  };

  const fitMapToPlaces = () => {
    if (!mapInstanceRef.current || places.length === 0) {
      return;
    }

    const bounds = new window.kakao.maps.LatLngBounds();
    let hasValidPosition = false;

    places.forEach((place) => {
      if (!place.lat || !place.lng) return;
      bounds.extend(new window.kakao.maps.LatLng(place.lat, place.lng));
      hasValidPosition = true;
    });

    if (hasValidPosition) {
      mapInstanceRef.current.setBounds(bounds);
    }
  };

  const relayoutMap = () => {
    if (!mapInstanceRef.current || !window.kakao?.maps) {
      return;
    }

    mapInstanceRef.current.relayout();
  };

  const renderMarkers = () => {
    if (!mapInstanceRef.current || !window.kakao?.maps) {
      return;
    }

    clearMarkers();

    if (infoWindowRef.current) {
      infoWindowRef.current.close();
    }

    if (places.length === 0) {
      const defaultPosition = new window.kakao.maps.LatLng(
        DEFAULT_CENTER.lat,
        DEFAULT_CENTER.lng,
      );

      mapInstanceRef.current.setCenter(defaultPosition);
      mapInstanceRef.current.setLevel(7);

      const defaultMarker = new window.kakao.maps.Marker({
        map: mapInstanceRef.current,
        position: defaultPosition,
        title: '기본 위치',
      });

      markersRef.current.push(defaultMarker);
      return;
    }

    places.forEach((place) => {
      if (!place.lat || !place.lng) return;

      const position = new window.kakao.maps.LatLng(place.lat, place.lng);
      const marker = new window.kakao.maps.Marker({
        map: mapInstanceRef.current,
        position,
        title: place.name,
      });

      window.kakao.maps.event.addListener(marker, 'click', () => {
        handleSelectPlace(place.name);
      });

      markersRef.current.push(marker);
    });

    fitMapToPlaces();
  };

  useEffect(() => {
    const waitForKakao = () => {
      if (!window.kakao?.maps || !mapRef.current) {
        setTimeout(waitForKakao, 100);
        return;
      }

      window.kakao.maps.load(() => {
        mapInstanceRef.current = new window.kakao.maps.Map(mapRef.current, {
          center: new window.kakao.maps.LatLng(DEFAULT_CENTER.lat, DEFAULT_CENTER.lng),
          level: 7,
        });

        infoWindowRef.current = new window.kakao.maps.InfoWindow({
          removable: false,
        });

        renderMarkers();
      });
    };
    waitForKakao();
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current) return;

    setSelectedPlaceId(null);
    renderMarkers();
  }, [places]);

  useEffect(() => {
    if (!mapInstanceRef.current) {
      return;
    }

    relayoutMap();

    if (!selectedPlaceId) {
      fitMapToPlaces();
      return;
    }

    const place = places.find((item) => item.content_id === selectedPlaceId || item.name === selectedPlaceId);
    if (!place || !place.lat || !place.lng || !window.kakao?.maps) {
      return;
    }

    const position = new window.kakao.maps.LatLng(place.lat, place.lng);
    mapInstanceRef.current.setLevel(4);
    mapInstanceRef.current.setCenter(position);

    if (infoWindowRef.current) {
      infoWindowRef.current.setContent(
        `<div style="padding:8px 12px;font-size:12px;font-weight:600;color:#3D2B1F;">${place.name}</div>`,
      );
      infoWindowRef.current.open(
        mapInstanceRef.current,
        markersRef.current.find((marker) => marker.getTitle?.() === place.name),
      );
    }
  }, [places, selectedPlaceId]);

  useEffect(() => {
    const handleResize = () => {
      if (relayoutTimerRef.current) {
        window.clearTimeout(relayoutTimerRef.current);
      }

      relayoutTimerRef.current = window.setTimeout(() => {
        relayoutMap();

        if (selectedPlaceId) {
          const place = places.find((item) => item.content_id === selectedPlaceId || item.name === selectedPlaceId);
          if (place?.lat && place?.lng && mapInstanceRef.current && window.kakao?.maps) {
            mapInstanceRef.current.setCenter(
              new window.kakao.maps.LatLng(place.lat, place.lng),
            );
            mapInstanceRef.current.setLevel(4);
            return;
          }
        }

        fitMapToPlaces();
      }, 120);
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (relayoutTimerRef.current) {
        window.clearTimeout(relayoutTimerRef.current);
      }
    };
  }, [places, selectedPlaceId]);

  const selectedPlace = useMemo(
    () => places.find((place) => place.content_id === selectedPlaceId || place.name === selectedPlaceId) ?? null,
    [places, selectedPlaceId],
  );

  const handleSelectPlace = (placeId: string) => {
    setSelectedPlaceId(placeId);
  };

  const handleCloseDetail = () => {
    setSelectedPlaceId(null);
    if (infoWindowRef.current) {
      infoWindowRef.current.close();
    }
    fitMapToPlaces();
  };

  return (
    <div className="h-full bg-[#FCFAF7] p-4 md:p-6">
      <div
        className={`grid gap-5 transition-all duration-300 ${
          selectedPlace ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1'
        }`}
      >
        <div className="min-w-0">
          <div className="space-y-4 rounded-[24px] border border-[#F2E7DD] bg-white p-4 shadow-sm md:p-5">
            <div
              className={`overflow-hidden rounded-2xl border border-[#EDE3DA] transition-all duration-300 ${
                selectedPlace ? 'h-[480px]' : 'h-[640px]'
              }`}
            >
              <div ref={mapRef} className="h-full w-full" />
            </div>

            <div>
              <div className="mb-3 flex items-center justify-between">
                <div className="text-sm font-semibold text-gray-700">
                  추천 장소
                  {places.length > 0 && (
                    <span className="ml-1 text-[#F08A4B]">({places.length}곳)</span>
                  )}
                </div>
                {selectedPlace && (
                  <button
                    type="button"
                    onClick={handleCloseDetail}
                    className="text-xs font-medium text-gray-500 hover:text-gray-700"
                  >
                    상세 닫기
                  </button>
                )}
              </div>

              <div className="space-y-3">
                {places.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-[#E8DED5] bg-[#FFFCF8] px-4 py-10 text-center">
                    <p className="mb-2 text-2xl">🐾</p>
                    <p className="text-sm font-medium text-gray-600">
                      챗봇에서 장소를 추천받아보세요
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      예: "잠실 강아지 카페 추천해줘"
                    </p>
                  </div>
                ) : (
                  places.map((item) => {
                    const itemId = item.content_id || item.name;
                    const isActive =
                      selectedPlace?.content_id === item.content_id || selectedPlace?.name === item.name;

                    return (
                      <div
                        key={itemId}
                        className={`rounded-2xl border p-4 transition ${
                          isActive
                            ? 'border-[#F4B183] bg-[#FFF7F1] shadow-sm'
                            : 'border-[#F4E8DE] bg-[#FFFDF9]'
                        }`}
                      >
                        <div className="text-base font-semibold text-gray-800">📍 {item.name}</div>
                        <div className="mt-1 text-sm text-gray-600">{item.address}</div>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                          {item.category && <span>{item.category}</span>}
                          {item.sub_category && <span>{item.sub_category}</span>}
                          {item.indoor === 'Y' && <span>실내</span>}
                          {item.outdoor === 'Y' && <span>실외</span>}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => (isActive ? handleCloseDetail() : handleSelectPlace(itemId))}
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
                            onClick={() => onUsePlace(item)}
                            className="text-sm font-semibold text-orange-600 hover:text-orange-700"
                          >
                            이 장소로 일기 쓰기 →
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        {selectedPlace && (
          <div className="min-w-0">
            <div className="overflow-hidden rounded-[28px] border border-[#F2E7DD] bg-white shadow-sm">
              {selectedPlace.image || selectedPlace.firstimage ? (
                <img
                  src={selectedPlace.image || selectedPlace.firstimage}
                  alt={selectedPlace.name}
                  className="h-[200px] w-full object-cover"
                />
              ) : (
                <div className="flex h-[200px] w-full items-center justify-center bg-[#F6EFE8] text-5xl">
                  🐾
                </div>
              )}

              <div className="border-b border-[#F5EAE1] p-5">
                <div className="text-2xl font-bold text-[#2F241D]">{selectedPlace.name}</div>
                <div className="mt-1 flex items-center gap-2 text-sm text-gray-500">
                  <MapPin className="h-4 w-4" />
                  <span>{selectedPlace.address}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedPlace.category && (
                    <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">
                      {selectedPlace.category}
                    </span>
                  )}
                  {selectedPlace.sub_category && (
                    <span className="rounded-md bg-[#F6EFE8] px-2.5 py-1 text-xs font-medium text-[#8A6A58]">
                      {selectedPlace.sub_category}
                    </span>
                  )}
                  {selectedPlace.indoor === 'Y' && (
                    <span className="rounded-md bg-[#EFF6FF] px-2.5 py-1 text-xs font-medium text-blue-600">
                      실내 가능
                    </span>
                  )}
                  {selectedPlace.outdoor === 'Y' && (
                    <span className="rounded-md bg-[#F0FDF4] px-2.5 py-1 text-xs font-medium text-green-600">
                      실외 가능
                    </span>
                  )}
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
                  <div className="mb-3 text-base font-bold text-[#2F241D]">운영시간</div>
                  <p className="whitespace-pre-wrap text-sm text-gray-700">
                    {selectedPlace.operation || '정보 없음'}
                  </p>
                </section>

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">반려견 이용 정보</div>
                  <div className="space-y-1 text-sm text-gray-700">
                    <p>반려견 구역: {selectedPlace.pet_zone || '정보 없음'}</p>
                    <p>크기 제한: {selectedPlace.pet_size || '정보 없음'}</p>
                    <p>주차: {selectedPlace.has_parking === 'Y' ? '가능' : '정보 없음'}</p>
                  </div>
                </section>

                {selectedPlace.tel && (
                  <section>
                    <div className="mb-3 text-base font-bold text-[#2F241D]">매장 연락처</div>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm text-gray-700">{selectedPlace.tel}</p>
                      <a
                        href={`tel:${selectedPlace.tel}`}
                        className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
                      >
                        <Phone className="h-4 w-4" />
                        전화하기
                      </a>
                    </div>
                  </section>
                )}

                <section>
                  <div className="mb-3 text-base font-bold text-[#2F241D]">매장 위치</div>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-gray-700">{selectedPlace.address}</p>
                    <a
                      href={`https://map.kakao.com/link/search/${encodeURIComponent(selectedPlace.name)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded-full border border-pink-200 px-4 py-2 text-sm font-medium text-pink-500 hover:bg-pink-50"
                    >
                      <Navigation className="h-4 w-4" />
                      길찾기
                    </a>
                  </div>
                </section>

                {selectedPlace.description && (
                  <section>
                    <div className="mb-3 text-base font-bold text-[#2F241D]">장소 설명</div>
                    <p className="text-sm leading-7 text-gray-700">{selectedPlace.description}</p>
                  </section>
                )}

                <button
                  type="button"
                  onClick={() => onUsePlace(selectedPlace)}
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
