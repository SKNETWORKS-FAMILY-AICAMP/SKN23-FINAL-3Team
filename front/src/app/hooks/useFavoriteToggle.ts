import { useEffect, useState } from 'react';
import { getPlaceFavorites, togglePlaceFavorite } from '../services/placeService';

interface Options {
  /**
   * 마운트 시 즐겨찾기 목록 자동 로드 여부. 디폴트 true.
   * 비로그인 상태에서도 호출은 안전하지만 (token 없으면 skip), false 로 두면 호출조차 안 함.
   */
  enabled?: boolean;
}

/**
 * 장소 즐겨찾기 토글 훅 — 낙관적 업데이트 + 백엔드 호출 + 실패 롤백.
 *
 * HomePage 다이어리 결과 / DiaryAlbum 상세 / CalendarPage 상세 3 호출처에서
 * 동일하게 박혀있던 `placeFavoriteIds` Set + `favoriteToggling` Set + 토글 함수
 * 묶음을 단일 훅으로 응집한다.
 *
 * Returns:
 *   - `isFavorite(contentId)`: 현재 즐겨찾기 여부
 *   - `isToggling(contentId)`: 토글 진행 중 여부 (중복 호출 차단용)
 *   - `toggle(contentId)`: 토글 — 낙관적 업데이트 후 togglePlaceFavorite 호출, 실패 시 롤백
 */
export function useFavoriteToggle({ enabled = true }: Options = {}) {
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());
  const [togglingIds, setTogglingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!enabled) return;
    const token = localStorage.getItem('access_token');
    if (!token) return;
    getPlaceFavorites()
      .then((items) => setFavoriteIds(new Set(items.map((i) => i.content_id))))
      .catch(() => { });
  }, [enabled]);

  const toggle = async (contentId: string) => {
    if (!contentId || togglingIds.has(contentId)) return;
    setTogglingIds((prev) => new Set(prev).add(contentId));
    const wasFavorite = favoriteIds.has(contentId);
    setFavoriteIds((prev) => {
      const next = new Set(prev);
      wasFavorite ? next.delete(contentId) : next.add(contentId);
      return next;
    });
    try {
      await togglePlaceFavorite(contentId);
    } catch {
      setFavoriteIds((prev) => {
        const next = new Set(prev);
        wasFavorite ? next.add(contentId) : next.delete(contentId);
        return next;
      });
    } finally {
      setTogglingIds((prev) => {
        const next = new Set(prev);
        next.delete(contentId);
        return next;
      });
    }
  };

  const isFavorite = (contentId: string) => favoriteIds.has(contentId);
  const isToggling = (contentId: string) => togglingIds.has(contentId);

  return { isFavorite, isToggling, toggle };
}
