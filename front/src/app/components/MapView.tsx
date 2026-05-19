import { useEffect, useMemo, useRef, useState } from 'react';
import { LocateFixed, Star } from 'lucide-react';
import type { PlaceResult } from '../services/placeService';
import { togglePlaceFavorite, getPlaceFavorites } from '../services/placeService';
import PlaceDetailCard from './PlaceDetailCard';
import PlaceBadges from './PlaceBadges';

declare global {
  interface Window {
    kakao: any;
  }
}


interface Props {
  places: PlaceResult[];
  onUsePlace: (place: PlaceResult) => void;
  initialSelectedId?: string;
  userLocation?: { lat: number; lng: number };
}

const DEFAULT_CENTER = { lat: 37.5665, lng: 126.9780 };

export default function MapView({ places, onUsePlace, initialSelectedId, userLocation }: Props) {
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(initialSelectedId ?? null);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());
  const [togglingIds, setTogglingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    getPlaceFavorites()
      .then((items) => setFavoriteIds(new Set(items.map((i) => i.content_id))))
      .catch(() => {});
  }, []);

  const handleToggleFavorite = async (contentId: string) => {
    console.log('[Star] clicked, content_id:', contentId);
    if (!contentId) {
      alert('content_id가 없습니다: ' + String(contentId));
      return;
    }
    if (togglingIds.has(contentId)) return;
    setTogglingIds((prev) => new Set(prev).add(contentId));
    const wasFavorite = favoriteIds.has(contentId);
    setFavoriteIds((prev) => {
      const next = new Set(prev);
      wasFavorite ? next.delete(contentId) : next.add(contentId);
      return next;
    });
    try {
      await togglePlaceFavorite(contentId);
    } catch (err) {
      alert('즐겨찾기 오류: ' + String(err));
      setFavoriteIds((prev) => {
        const next = new Set(prev);
        wasFavorite ? next.add(contentId) : next.delete(contentId);
        return next;
      });
    } finally {
      setTogglingIds((prev) => { const next = new Set(prev); next.delete(contentId); return next; });
    }
  };
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const infoWindowRef = useRef<any>(null);
  const relayoutTimerRef = useRef<number | null>(null);
  const userOverlayRef = useRef<any>(null);
  const defaultMarkerRef = useRef<any>(null);
  const hasInitialCenteredRef = useRef(false);
  const userLocationRef = useRef(userLocation);

  const clearMarkers = () => {
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];
  };

  const clearDefaultMarker = () => {
    if (defaultMarkerRef.current) {
      defaultMarkerRef.current.setMap(null);
      defaultMarkerRef.current = null;
    }
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

  const renderUserOverlay = (loc: { lat: number; lng: number }) => {
    if (!mapInstanceRef.current || !window.kakao?.maps) return;

    if (userOverlayRef.current) {
      userOverlayRef.current.setMap(null);
    }

    const position = new window.kakao.maps.LatLng(loc.lat, loc.lng);
    const content = `
      <div style="
        width:16px;height:16px;border-radius:50%;
        background:#4285F4;border:3px solid white;
        box-shadow:0 0 0 4px rgba(66,133,244,0.25);
      "></div>`;
    userOverlayRef.current = new window.kakao.maps.CustomOverlay({
      position,
      content,
      map: mapInstanceRef.current,
      zIndex: 10,
    });
  };

  useEffect(() => {
    userLocationRef.current = userLocation;
  }, [userLocation]);

  const handleGpsClick = () => {
    if (!userLocation) {
      setGpsError('위치 권한을 허용해주세요.');
      setTimeout(() => setGpsError(null), 3000);
      return;
    }
    if (mapInstanceRef.current && window.kakao?.maps) {
      renderUserOverlay(userLocation);
      mapInstanceRef.current.setCenter(new window.kakao.maps.LatLng(userLocation.lat, userLocation.lng));
      mapInstanceRef.current.setLevel(5);
    }
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
      // GPS 미허용일 때만 서울시청 마커 표시
      if (!userLocationRef.current) {
        const defaultPosition = new window.kakao.maps.LatLng(DEFAULT_CENTER.lat, DEFAULT_CENTER.lng);
        mapInstanceRef.current.setCenter(defaultPosition);
        mapInstanceRef.current.setLevel(7);
        defaultMarkerRef.current = new window.kakao.maps.Marker({
          map: mapInstanceRef.current,
          position: defaultPosition,
          title: '서울시청',
        });
      }
      return;
    }

    clearDefaultMarker();

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
        const initLoc = userLocationRef.current;
        const initCenter = initLoc
          ? new window.kakao.maps.LatLng(initLoc.lat, initLoc.lng)
          : new window.kakao.maps.LatLng(DEFAULT_CENTER.lat, DEFAULT_CENTER.lng);
        const initLevel = initLoc ? 5 : 7;

        mapInstanceRef.current = new window.kakao.maps.Map(mapRef.current, {
          center: initCenter,
          level: initLevel,
        });

        infoWindowRef.current = new window.kakao.maps.InfoWindow({
          removable: false,
        });

        renderMarkers();

        // GPS가 이미 있으면 즉시 파란 점 그리기 + 초기 센터링 완료 표시
        const loc = userLocationRef.current;
        if (loc) {
          const pos = new window.kakao.maps.LatLng(loc.lat, loc.lng);
          const content = `<div style="width:16px;height:16px;border-radius:50%;background:#4285F4;border:3px solid white;box-shadow:0 0 0 4px rgba(66,133,244,0.25);"></div>`;
          userOverlayRef.current = new window.kakao.maps.CustomOverlay({ position: pos, content, map: mapInstanceRef.current, zIndex: 10 });
          hasInitialCenteredRef.current = true;
        }

        setMapReady(true);
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
    if (!userLocation || !mapInstanceRef.current) return;
    renderUserOverlay(userLocation);

    // 처음 위치가 잡히는 순간 서울시청 마커 제거 + 지도 중심 이동
    if (!hasInitialCenteredRef.current && window.kakao?.maps) {
      clearDefaultMarker();
      mapInstanceRef.current.setCenter(
        new window.kakao.maps.LatLng(userLocation.lat, userLocation.lng),
      );
      mapInstanceRef.current.setLevel(5);
      hasInitialCenteredRef.current = true;
    }
  }, [userLocation, mapReady]);

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
              className={`relative overflow-hidden rounded-2xl border border-[#EDE3DA] transition-all duration-300 ${
                selectedPlace ? 'h-[480px]' : 'h-[640px]'
              }`}
            >
              <div ref={mapRef} className="h-full w-full" />
              <button
                type="button"
                onClick={handleGpsClick}
                title="현재 위치로 이동"
                className="absolute bottom-4 right-4 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-md hover:bg-gray-50"
              >
                <LocateFixed className={`h-5 w-5 ${userLocation ? 'text-blue-500' : 'text-gray-400'}`} />
              </button>
              {gpsError && (
                <div className="absolute bottom-16 right-4 z-10 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600 shadow">
                  {gpsError}
                </div>
              )}
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
                        <PlaceBadges place={item} variant="simple" />
                        <div className="mt-3 flex flex-wrap items-center gap-2">
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
                          <button
                            type="button"
                            onClick={() => handleToggleFavorite(item.content_id)}
                            disabled={togglingIds.has(item.content_id)}
                            className="ml-auto flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#F4845F] transition hover:bg-[#e8764f] active:scale-95 disabled:opacity-50"
                          >
                            <Star
                              className="h-5 w-5"
                              fill={favoriteIds.has(item.content_id) ? 'white' : 'none'}
                              stroke="white"
                            />
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
            <PlaceDetailCard
              place={selectedPlace}
              variant="panel"
              showImage
              showPetInfo
              showDescription
              showLocationSection
              isFavorite={favoriteIds.has(selectedPlace.content_id)}
              onToggleFavorite={() => handleToggleFavorite(selectedPlace.content_id)}
              favoriteToggling={togglingIds.has(selectedPlace.content_id)}
              onSelectForDiary={() => onUsePlace(selectedPlace)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
