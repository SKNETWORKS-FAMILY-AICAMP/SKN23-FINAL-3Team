import { useMemo, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { PenSquare, FolderOpen, CalendarDays, MapPinned, SquarePen, UserRound, NotebookPen, Map, Star } from 'lucide-react';
import type { Pet, DiaryEntry, User } from '../types';
import DiaryView from '../components/DiaryView';
import MapView from '../components/MapView';
import ChatBot from '../components/ChatBot';
import ChatHistory from '../components/ChatHistory';
import type { GeneratedDiary } from '../services/diaryService';
import type { PlaceResult } from '../services/placeService';
import { createDiary, updateDiary, deleteDiary } from '../services/dbDiaryService';
import { uploadImage } from '../services/imageService';
import { getMe } from '../services/userService';
import { getPets } from '../services/petService';
import { getBreed } from '../services/breedService';
import { getDiariesByUser } from '../services/dbDiaryService';
import { getImage } from '../services/imageService';

type Tab = 'diary' | 'map' | null;

interface Props {
  pet?: Pet;
  pets?: Pet[];
  selectedPet?: Pet;
  user: User;
  diaries: DiaryEntry[];
  onSaveDiary: (entry: DiaryEntry) => void;
  onGoMypage: () => void;
  onSelectPet?: (pet: Pet) => void;
}

function HomeIntro({
  onOpenMap,
  onOpenDiary,
  onGoMypage,
}: {
  onOpenMap: () => void;
  onOpenDiary: () => void;
  onGoMypage: () => void;
}) {
  return (
    <div className="h-full w-full overflow-hidden bg-gradient-to-b from-[#F1F1F3] to-[#ECEDEA]">
      <div className="relative h-full overflow-hidden">
        {/* 오른쪽 영상 */}
        <div className="absolute inset-y-0 right-0 w-[58%] overflow-hidden">
          <video
            src="/intro.mp4"
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '100%',
              height: '70%',
              objectFit: 'cover',
            }}
          />
        </div>

        {/* 왼쪽 오버레이 카드 */}
        <div className="absolute left-8 top-1/2 z-10 w-[46%] min-w-[420px] max-w-[600px] -translate-y-1/2 rounded-[40px] border border-white/40 bg-white/65 px-10 py-12 shadow-[0_24px_80px_rgba(61,43,31,0.12)] backdrop-blur-[16px]">
          <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full bg-[#ffffff] px-4 py-1.5 text-sm font-semibold text-[#B86A2E]">
            <span className="text-[#f54900]">AI 맞춤 반려견 도우미</span>
          </div>

          <h2 className="mb-5 text-[36px] font-bold leading-[1.18] tracking-[-0.02em] text-[#3D2B1F] xl:text-[48px]">
            반려견과
            <br />
            추억을 남겨요
          </h2>

          <p className="mb-7 text-[16px] leading-8 text-[#7A5C4D]">
            산책로, 카페, 실내 장소, 여행지까지
            <br />
            우리 아이의 성향과 상황에 맞춰 AI가 추천해드려요.
          </p>

          <div className="mb-6 flex flex-wrap gap-2">
            <span className="rounded-full border border-[#EEDFD3] bg-white/90 px-4 py-1.5 text-sm text-[#8B6355] shadow-sm">
              #실내추천
            </span>
            <span className="rounded-full border border-[#EEDFD3] bg-white/90 px-4 py-1.5 text-sm text-[#8B6355] shadow-sm">
              #산책코스
            </span>
            <span className="rounded-full border border-[#EEDFD3] bg-white/90 px-4 py-1.5 text-sm text-[#8B6355] shadow-sm">
              #AI그림일기
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <button
              type="button"
              onClick={onOpenMap}
              className="group flex flex-col rounded-2xl border border-[#EEDFD3] bg-white px-4 py-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#F4845F] hover:bg-[#FFF0E6] hover:shadow-md"
            >
              <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#FFF0E6] transition group-hover:bg-[#F4845F]">
                <MapPinned className="h-6 w-6 text-[#F4845F] transition group-hover:text-white" />
              </div>
              <p className="mb-1 text-[13px] font-bold text-[#3D2B1F]">AI 장소 추천</p>
              <p className="text-[11px] leading-[18px] text-[#8B6355]">
                산책로, 카페, 실내 장소를 AI가 추천해줘요.
              </p>
            </button>

            <button
              type="button"
              onClick={onOpenDiary}
              className="group flex flex-col rounded-2xl border border-[#EEDFD3] bg-white px-4 py-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#F4845F] hover:bg-[#FFF0E6] hover:shadow-md"
            >
              <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#FFF0E6] transition group-hover:bg-[#F4845F]">
                <SquarePen className="h-6 w-6 text-[#F4845F] transition group-hover:text-white" />
              </div>
              <p className="mb-1 text-[13px] font-bold text-[#3D2B1F]">오늘 일기 쓰기</p>
              <p className="text-[11px] leading-[18px] text-[#8B6355]">
                오늘 있었던 일을 기록하고 우리 아이의 하루를 남겨보세요.
              </p>
            </button>

            <button
              type="button"
              onClick={onGoMypage}
              className="group flex flex-col rounded-2xl border border-[#EEDFD3] bg-white px-4 py-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#F4845F] hover:bg-[#FFF0E6] hover:shadow-md"
            >
              <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#FFF0E6] transition group-hover:bg-[#F4845F]">
                <UserRound className="h-6 w-6 text-[#F4845F] transition group-hover:text-white" />
              </div>
              <p className="mb-1 text-[13px] font-bold text-[#3D2B1F]">마이페이지 보기</p>
              <p className="text-[11px] leading-[18px] text-[#8B6355]">
                반려견 정보와 기록을 한눈에 확인해보세요.
              </p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MapIntro({ onStartMap }: { onStartMap: () => void }) {
  return (
    <div className="h-full w-full overflow-hidden bg-gradient-to-b from-[#EEF3F1] to-[#E8EFED]">
      <div className="relative h-full overflow-hidden">
        {/* 오른쪽 영상 */}
        <div className="absolute inset-y-0 right-0 w-[58%] overflow-hidden">
          <video
            src="/intro3.mp4"
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '100%',
              height: '70%',
              objectFit: 'cover',
            }}
          />
        </div>

        {/* 왼쪽 안내 카드 */}
        <div className="absolute left-8 top-1/2 z-10 w-[46%] min-w-[420px] max-w-[560px] -translate-y-1/2 rounded-[40px] border border-white/40 bg-white/65 px-10 py-12 shadow-[0_24px_80px_rgba(30,60,40,0.12)] backdrop-blur-[16px]">
          <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full bg-white px-4 py-1.5 text-sm font-semibold">
            <span className="text-[#4CAF50]">📍 반려견 장소 추천</span>
          </div>

          <h2 className="mb-5 text-[36px] font-bold leading-[1.18] tracking-[-0.02em] text-[#1E3A2A] xl:text-[48px]">
            반려견과 함께할
            <br />
            특별한 장소를 찾아요
          </h2>

          <p className="mb-7 text-[16px] leading-8 text-[#4A6B54]">
            산책로, 애견카페, 실내 놀이터, 여행지까지
            <br />
            우리 아이가 행복할 수 있는 장소를 AI가 추천해드려요.
          </p>

          <div className="mb-8 flex flex-wrap gap-2">
            {['#반려견동반', '#실내추천', '#산책코스', '#여행지'].map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-[#C8E6C9] bg-white/90 px-4 py-1.5 text-sm text-[#3A7A4A] shadow-sm"
              >
                {tag}
              </span>
            ))}
          </div>

          <button
            type="button"
            onClick={onStartMap}
            className="group w-full rounded-2xl border-2 border-transparent bg-[#0F6E56] px-6 py-4 text-left shadow-md transition hover:-translate-y-0.5 hover:border-[#0F6E56] hover:bg-white hover:shadow-lg"
          >
            <p className="flex items-center gap-2 text-lg font-black text-white transition group-hover:text-[#0F6E56]">
              <MapPinned className="h-5 w-5" />
              지도 검색하기
            </p>
            <p className="mt-0.5 text-sm text-[#D7F1EA] transition group-hover:text-[#0F6E56]/70">
              우리 아이에게 맞는 반려견 동반 장소를 지금 바로 찾아보세요
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}

function DiaryAlbum({
  diaries,
  onBack,
  onDelete,
  onUpdate,
}: {
  diaries: DiaryEntry[];
  onBack: () => void;
  onDelete: (id: string) => void;
  onUpdate?: (id: string, title: string, body: string) => Promise<void>;
}) {
  const [selected, setSelected] = useState<DiaryEntry | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem('diary_favorites');
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch { return new Set(); }
  });

  const toggleFavorite = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setFavorites(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      localStorage.setItem('diary_favorites', JSON.stringify([...next]));
      return next;
    });
  };

  const handleSaveAlbumEdit = async () => {
    if (!selected || !onUpdate) return;
    setEditSaving(true);
    try {
      await onUpdate(selected.id, editTitle, editBody);
      setSelected({ ...selected, title: editTitle, body: editBody });
      setIsEditing(false);
    } catch {
      alert('수정에 실패했어요. 다시 시도해주세요.');
    } finally {
      setEditSaving(false);
    }
  };

  if (selected) {
    return (
      <div className="h-full overflow-y-auto bg-[#F6F1EA] p-6">
        <div className="mx-auto w-full max-w-[720px]">
          <div className="mb-4 flex items-center gap-3">
            <button
              onClick={() => { setSelected(null); setIsEditing(false); }}
              className="flex items-center gap-1.5 rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
            >
              ← 목록으로
            </button>
            <h2 className="text-lg font-bold text-[#3D2B1F]">🐾 그림일기</h2>
            <div className="ml-auto flex items-center gap-2">
              {!isEditing && onUpdate && (
                <button
                  onClick={() => { setEditTitle(selected.title); setEditBody(selected.body || ''); setIsEditing(true); }}
                  className="rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
                >
                  ✏️ 수정
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
                    onClick={handleSaveAlbumEdit}
                    disabled={editSaving}
                    className="rounded-full bg-[#F4845F] px-3 py-1.5 text-xs text-white transition hover:bg-[#e0724e] disabled:opacity-50"
                  >
                    {editSaving ? '저장 중...' : '저장'}
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="relative rounded-[28px] border border-[#E9D9C9] bg-[#FFFDF8] p-6 shadow-[0_8px_24px_rgba(61,43,31,0.08)] md:p-8">
            {/* 마스킹 테이프 */}
            <div className="absolute -top-3 left-10 h-6 w-20 rotate-[-8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />
            <div className="absolute -top-3 right-10 h-6 w-20 rotate-[8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />

            {/* 제목/요약 */}
            <div className="mb-6 text-center">
              <p className="text-xs tracking-[0.2em] text-[#B08B7A]">오늘의 그림일기</p>
              {isEditing ? (
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-[#F4845F] bg-[#FFF8F3] px-3 py-2 text-center text-xl font-bold text-[#F4845F] outline-none"
                />
              ) : (
                <h3 className="mt-2 text-2xl font-bold text-[#F4845F]">{selected.title}</h3>
              )}
              {selected.summary && (
                <div className="mt-3 inline-flex rounded-full bg-[#FFF0E6] px-3 py-1 text-xs font-medium text-[#F4845F]">
                  ✨ {selected.summary}
                </div>
              )}
            </div>

            {/* 이미지 */}
            <div className="mx-auto mb-6 w-full max-w-[520px] rounded-[22px] border border-[#E8D9CC] bg-white p-3 shadow-[0_6px_18px_rgba(61,43,31,0.06)]">
              {selected.imageUrl ? (
                <img src={selected.imageUrl} alt={selected.title} className="w-full h-auto rounded-[16px] object-contain" />
              ) : (
                <div className="flex h-48 items-center justify-center text-5xl">🐾</div>
              )}
            </div>

            {/* 일기 본문 - 줄 있는 노트 */}
            {isEditing ? (
              <textarea
                value={editBody}
                onChange={(e) => setEditBody(e.target.value)}
                rows={10}
                className="w-full rounded-[20px] border border-[#F4845F] bg-[#FFFCF8] px-5 py-5 text-[15px] leading-[31px] text-[#3D2B1F] outline-none resize-none"
                style={{ backgroundImage: 'repeating-linear-gradient(to bottom, transparent 0px, transparent 30px, #F3E7DA 31px)' }}
              />
            ) : (
              <div
                className="rounded-[20px] border border-[#F1E4D8] bg-[#FFFCF8] px-5 py-5"
                style={{ backgroundImage: 'repeating-linear-gradient(to bottom, transparent 0px, transparent 30px, #F3E7DA 31px)' }}
              >
                <p className="whitespace-pre-wrap text-[15px] leading-[31px] text-[#3D2B1F]">
                  {selected.body || '내용이 없어요.'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (diaries.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 bg-[#F6F1EA] p-8 text-center">
        <span className="text-6xl">🖼️</span>
        <p className="text-lg font-bold text-[#3D2B1F]">아직 저장된 그림일기가 없어요</p>
        <p className="text-sm text-[#8B6355]">챗봇과 함께 오늘의 하루를 기록하고 저장해보세요!</p>
        <button
          onClick={onBack}
          className="mt-2 rounded-full border border-[#F5D6C8] bg-white px-5 py-2 text-sm font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
        >
          ← 돌아가기
        </button>
      </div>
    );
  }

  // 날짜별 그룹핑 후 최신 날짜 먼저 정렬
  const grouped = [...diaries]
    .reduce<{ date: string; entries: DiaryEntry[] }[]>((acc, entry) => {
      const existing = acc.find((g) => g.date === entry.date);
      if (existing) {
        existing.entries.push(entry);
      } else {
        acc.push({ date: entry.date, entries: [entry] });
      }
      return acc;
    }, [])
    .sort((a, b) => b.date.localeCompare(a.date));

  const formatDateHeader = (dateStr: string) => {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' });
  };

  return (
    <div className="h-full overflow-y-auto bg-[#F6F1EA] p-6">
      <div className="mx-auto w-full max-w-[720px]">
        <div className="mb-5 flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
          >
            ← 뒤로
          </button>
          <h2 className="text-lg font-bold text-[#3D2B1F]">🖼️ 일기 모아보기</h2>
          <span className="ml-auto text-xs text-[#B08B7A]">{diaries.length}개의 일기</span>
        </div>

        <div className="flex flex-col gap-8">
          {grouped.map(({ date, entries }) => (
            <div key={date}>
              {/* 날짜 헤더 */}
              <div className="mb-3 flex items-center gap-3">
                <span className="text-sm font-bold text-[#3D2B1F]">{formatDateHeader(date)}</span>
                <div className="flex-1 border-t border-[#E9D9C9]" />
                <span className="text-xs text-[#B08B7A]">{entries.length}개</span>
              </div>

              {/* 해당 날짜 카드 그리드 */}
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                {entries.map((entry) => (
                  <div
                    key={entry.id}
                    className="group relative cursor-pointer overflow-hidden rounded-[20px] border border-[#E9D9C9] bg-[#FFFDF8] shadow-[0_4px_16px_rgba(61,43,31,0.07)] transition hover:-translate-y-0.5 hover:shadow-md"
                    onClick={() => setSelected(entry)}
                  >
                    {/* 즐겨찾기 버튼 (좌상단) */}
                    <button
                      onClick={(e) => toggleFavorite(e, entry.id)}
                      className="absolute left-2 top-2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-black/30 transition hover:bg-black/50"
                    >
                      <Star
                        className="h-4 w-4"
                        fill={favorites.has(entry.id) ? '#F4845F' : 'none'}
                        stroke={favorites.has(entry.id) ? '#F4845F' : 'white'}
                      />
                    </button>
                    {/* 삭제 버튼 (우상단, hover 시 표시) */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('이 일기를 삭제할까요?')) onDelete(entry.id);
                      }}
                      className="absolute right-2 top-2 z-10 hidden h-6 w-6 items-center justify-center rounded-full bg-black/50 text-white transition hover:bg-red-500 group-hover:flex"
                    >
                      ✕
                    </button>
                    {entry.imageUrl ? (
                      <img src={entry.imageUrl} alt={entry.title} className="h-36 w-full object-cover" />
                    ) : (
                      <div className="flex h-36 w-full items-center justify-center bg-[#FFF0E6] text-4xl">🐾</div>
                    )}
                    <div className="p-3">
                      <p className="truncate text-sm font-bold text-[#3D2B1F]">{entry.title}</p>
                      {entry.summary && (
                        <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-[#8B6355]">{entry.summary}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DiaryIntro({
  onStartDiary,
  onOpenAlbum,
  onGoCalendar,
}: {
  onStartDiary: () => void;
  onOpenAlbum: () => void;
  onGoCalendar: () => void;
}) {
  return (
    <div className="h-full w-full overflow-hidden" style={{ background: '#F0F3F2' }}>
      <div className="relative h-full overflow-hidden">
        {/* 오른쪽 영상 */}
        <div className="absolute inset-y-0 right-0 w-[58%] overflow-hidden">
          <video
            src="/intro2.mp4"
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '100%',
              height: '70%',
              objectFit: 'cover',
            }}
          />
        </div>

        {/* 왼쪽 안내 카드 */}
        <div className="absolute left-8 top-1/2 z-10 w-[46%] min-w-[420px] max-w-[590px] -translate-y-1/2 rounded-[40px] border border-white/40 bg-white/65 px-10 py-12 shadow-[0_24px_80px_rgba(61,43,31,0.12)] backdrop-blur-[16px]">
          <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full bg-white px-4 py-1.5 text-sm font-semibold text-[#B86A2E]">
            <span className="text-[#F57C3D]">강아지 일기장</span>
          </div>

          <h2 className="mb-5 text-[36px] font-bold leading-[1.18] tracking-[-0.02em] text-[#3D2B1F] xl:text-[48px]">
            우리 아이의 하루를
            <br />
            기록해요
          </h2>

          <p className="mb-7 text-[16px] leading-8 text-[#7A5C4D]">
            오늘 있었던 일, 기분, 다녀온 장소, 특별한 순간까지
            <br />
            쉽고 예쁘게 남길 수 있는 반려견 전용 일기장이에요.
          </p>

          <div className="mb-6 flex flex-wrap gap-2">
            <span className="rounded-full border border-[#EEDFD3] bg-white/90 px-4 py-1.5 text-sm text-[#8B6355] shadow-sm">
              #오늘의기록
            </span>
            <span className="rounded-full border border-[#EEDFD3] bg-white/90 px-4 py-1.5 text-sm text-[#8B6355] shadow-sm">
              #감정메모
            </span>
            <span className="rounded-full border border-[#EEDFD3] bg-white/90 px-4 py-1.5 text-sm text-[#8B6355] shadow-sm">
              #AI그림일기
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <button
              type="button"
              onClick={onStartDiary}
              className="group flex flex-col rounded-2xl border border-[#F4845F] bg-[#F4845F] px-4 py-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:bg-[#FFF0E6] hover:shadow-md"
            >
              <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-white/25 transition group-hover:bg-[#F4845F]">
                <PenSquare className="h-6 w-6 text-white" />
              </div>
              <p className="mb-1 text-[13px] font-bold text-white transition group-hover:text-[#3D2B1F]">새 그림일기 쓰기</p>
              <p className="text-[11px] leading-[18px] text-orange-100 transition group-hover:text-[#8B6355]">
                챗봇과 함께 오늘의 하루를 바로 기록해보세요.
              </p>
            </button>

            <button
              type="button"
              onClick={onOpenAlbum}
              className="group flex flex-col rounded-2xl border border-[#EEDFD3] bg-white px-4 py-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#F4845F] hover:bg-[#FFF0E6] hover:shadow-md"
            >
              <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#FFF0E6] transition group-hover:bg-[#F4845F]">
                <FolderOpen className="h-6 w-6 text-[#F4845F] transition group-hover:text-white" />
              </div>
              <p className="mb-1 text-[13px] font-bold text-[#3D2B1F]">일기 모아보기</p>
              <p className="text-[11px] leading-[18px] text-[#8B6355]">
                차곡차곡 쌓인 그림일기를 다시 꺼내보세요.
              </p>
            </button>

            <button
              type="button"
              onClick={onGoCalendar}
              className="group flex flex-col rounded-2xl border border-[#EEDFD3] bg-white px-4 py-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#F4845F] hover:bg-[#FFF0E6] hover:shadow-md"
            >
              <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#FFF0E6] transition group-hover:bg-[#F4845F]">
                <CalendarDays className="h-6 w-6 text-[#F4845F] transition group-hover:text-white" />
              </div>
              <p className="mb-1 text-[13px] font-bold text-[#3D2B1F]">멍캘린더</p>
              <p className="text-[11px] leading-[18px] text-[#8B6355]">
                캘린더로 한 달의 기록과 특별한 순간을 돌아보세요.
              </p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HomePage({
  pet,
  pets,
  selectedPet,
  user,
  diaries,
  onSaveDiary,
  onGoMypage,
}: Partial<Props>) {
  const navigate = useNavigate();
  const location = useLocation();
  const [tab, setTab] = useState<Tab>(() => {
    const t = new URLSearchParams(location.search).get('tab');
    return (t === 'diary' || t === 'map') ? t : null;
  });
  const [autoPlace, setAutoPlace] = useState('');
  const [showDiaryEditor, setShowDiaryEditor] = useState(false);
  const [showMapSearch, setShowMapSearch] = useState(false);
  const [mapPlaces, setMapPlaces] = useState<PlaceResult[]>([]);
  const [diaryResult, setDiaryResult] = useState<{ diary: GeneratedDiary; imageUrl: string } | null>(null);
  const [diaryTrigger, setDiaryTrigger] = useState(0);
  const [showAlbum, setShowAlbum] = useState(false);
  const [albumDiaries, setAlbumDiaries] = useState<DiaryEntry[]>([]);
  const [autoSaveState, setAutoSaveState] = useState<'idle' | 'saving' | 'done' | 'error'>('idle');
  const [fetchedPetId, setFetchedPetId] = useState<number | null>(null);
  const [fetchedPet, setFetchedPet] = useState<Pet | null>(null);
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [chatKey, setChatKey] = useState(0);
  const [savedDiaryId, setSavedDiaryId] = useState<number | null>(null);
  const [isEditingDiary, setIsEditingDiary] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [editSaving, setEditSaving] = useState(false);

  // 선택된 반려견 정보(이름 + 견종명)를 백엔드에서 가져옴 — pet-select-change 시 재실행
  useEffect(() => {
    const fetchPetData = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const me = await getMe();
        const allPets = await getPets(me.id);
        if (allPets.length === 0) return;
        const savedId = Number(localStorage.getItem('selected_pet_id')) || null;
        const p = (savedId ? allPets.find((pet) => pet.id === savedId) : null) ?? allPets[0];
        setFetchedPetId(p.id);
        let breedName = '강아지';
        try {
          const breed = await getBreed(p.breed_id);
          breedName = breed.name_ko;
        } catch { /* breed 조회 실패 시 기본값 유지 */ }
        setFetchedPet({
          id: p.id,
          name: p.name,
          breed: breedName,
          birthDate: p.birth_date ?? undefined,
          gender: p.gender ?? undefined,
          ownerName: me.nickname ?? undefined,
          ownerGender: me.gender ?? undefined,
          personality: Array.isArray(p.selected_tags) ? p.selected_tags : [],
        });
      } catch { /* 로그인 안 된 경우 무시 */ }
    };

    fetchPetData();
    window.addEventListener('pet-select-change', fetchPetData);
    return () => window.removeEventListener('pet-select-change', fetchPetData);
  }, []);

  // URL ?tab= 파라미터 변경 시 탭 동기화
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const t = params.get('tab');
    const album = params.get('album');
    if (t === 'diary' || t === 'map') {
      setTab(t);
      setShowDiaryEditor(false);
      setShowMapSearch(false);
      setShowAlbum(album === 'true');
    }
  }, [location.search]);

  // 로고·홈 버튼 클릭 시 항상 인트로로 리셋
  useEffect(() => {
    const t = new URLSearchParams(location.search).get('tab');
    if (t) return; // tab 파라미터 있으면 리셋 안 함
    setTab(null);
    setShowDiaryEditor(false);
    setShowMapSearch(false);
    setShowAlbum(false);
    setAutoPlace('');
  }, [location.key]);

  const safePets = useMemo(() => {
    if (Array.isArray(pets) && pets.length > 0) return pets;
    if (pet) return [pet];
    return [];
  }, [pets, pet]);

  const safeUser = user;
  const safeDiaries = diaries ?? [];
  const currentPet = selectedPet ?? fetchedPet ?? safePets[0] ?? pet;

  const handleOpenDiaryTab = () => {
    setTab('diary');
    setShowDiaryEditor(false);
    setShowAlbum(false);
  };

  const handleOpenMapTab = () => {
    setTab('map');
    setShowMapSearch(true);
  };

  const handleUsePlace = (place: string) => {
    setAutoPlace(place);
    setTab('diary');
    setDiaryResult(null);
    setDiaryTrigger((prev) => prev + 1);
  };

  const handlePlacesFound = (places: PlaceResult[]) => {
    setMapPlaces(places);
    setTab('map');
    setShowMapSearch(true);
  };

  const handleGoMypage = () => {
    if (onGoMypage) {
      onGoMypage();
    } else {
      navigate('/mypage');
    }
  };

  // 앨범 열릴 때 백엔드에서 일기 목록 불러오기
  useEffect(() => {
    if (!showAlbum) return;
    const token = localStorage.getItem('access_token');
    if (!token) return;
    getMe()
      .then((me) => getDiariesByUser(me.id))
      .then(async (records) => {
        const entries: DiaryEntry[] = await Promise.all(
          records.map(async (d) => {
            let imageUrl: string | undefined;
            if (d.image_id) {
              try { imageUrl = (await getImage(d.image_id)).url; } catch { /* 이미지 없으면 무시 */ }
            }
            return {
              id: String(d.id),
              title: d.title ?? '오늘의 일기',
              body: d.content ?? '',
              summary: d.summary ?? '',
              date: d.created_at.substring(0, 10),
              place: '',
              imageUrl,
            };
          })
        );
        setAlbumDiaries(entries.reverse());
      })
      .catch(() => {});
  }, [showAlbum]);

  const handleSaveDiary = (entry: DiaryEntry) => {
    if (onSaveDiary) {
      onSaveDiary(entry);
    }
    setAlbumDiaries((prev) => [entry, ...prev]);
  };

  const handleDiaryReady = (diary: GeneratedDiary, imageUrl: string) => {
    setDiaryResult({ diary, imageUrl });
    setAutoSaveState('idle');
    setTab('diary');
  };

  // 일기 생성 완료 시 자동저장
  useEffect(() => {
    if (!diaryResult || autoSaveState !== 'idle') return;
    const petId = currentPet?.id ?? fetchedPetId ?? undefined;
    if (!petId) return;

    setAutoSaveState('saving');
    setSavedDiaryId(null);
    setIsEditingDiary(false);
    (async () => {
      try {
        const saved = await createDiary({
          pet_id: petId,
          title: diaryResult.diary.title,
          content: diaryResult.diary.content,
          summary: diaryResult.diary.summary ?? '',
          emotion: diaryResult.diary.emotion ?? '',
        });
        setSavedDiaryId(saved.id);
        try {
          const blob = await fetch(diaryResult.imageUrl).then((r) => r.blob());
          const file = new File([blob], 'diary.png', { type: 'image/png' });
          const imgRecord = await uploadImage(file);
          await updateDiary(saved.id, { image_id: imgRecord.id });
        } catch (imgErr) {
          console.warn('[자동저장] 이미지 업로드 실패:', imgErr);
        }
        handleSaveDiary({
          id: saved.id.toString(),
          title: diaryResult.diary.title,
          body: diaryResult.diary.content,
          summary: diaryResult.diary.summary ?? '',
          date: new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }),
          place: autoPlace || '',
          imageUrl: diaryResult.imageUrl,
        });
        setAutoSaveState('done');
      } catch {
        setAutoSaveState('error');
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diaryResult]);

  const handleSaveEdit = async () => {
    if (!savedDiaryId) return;
    setEditSaving(true);
    try {
      await updateDiary(savedDiaryId, { title: editTitle, content: editBody });
      setDiaryResult((prev) =>
        prev ? { ...prev, diary: { ...prev.diary, title: editTitle, content: editBody } } : prev
      );
      setAlbumDiaries((prev) =>
        prev.map((d) => d.id === String(savedDiaryId) ? { ...d, title: editTitle, body: editBody } : d)
      );
      setIsEditingDiary(false);
    } catch {
      alert('수정에 실패했어요. 다시 시도해주세요.');
    } finally {
      setEditSaving(false);
    }
  };

  return (
    <div className="h-screen bg-[#f8f8f6] pt-16">
      <div className="flex h-full overflow-hidden">
        <div className="flex flex-1 overflow-hidden">
          {/* 왼쪽 메인 영역 */}
          <div className="flex min-w-0 flex-[2] flex-col border-r border-gray-200 bg-white">
            <div className="flex border-b border-gray-100 bg-white">
              <button
                className={`group flex flex-1 items-center justify-center gap-2 px-6 py-3.5 text-sm font-semibold transition-all ${
                  tab === 'diary'
                    ? 'border-b-2 border-[#F4845F] text-[#F4845F]'
                    : 'border-b-2 border-transparent text-gray-400 hover:text-[#F4845F]'
                }`}
                onClick={handleOpenDiaryTab}
              >
                <NotebookPen className="h-4 w-4" />
                강아지 일기장
              </button>

              <button
                className={`group flex flex-1 items-center justify-center gap-2 px-6 py-3.5 text-sm font-semibold transition-all ${
                  tab === 'map'
                    ? 'border-b-2 border-[#F4845F] text-[#F4845F]'
                    : 'border-b-2 border-transparent text-gray-400 hover:text-[#F4845F]'
                }`}
                onClick={handleOpenMapTab}
              >
                <Map className="h-4 w-4" />
                지도
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              {tab === null && (
                <HomeIntro
                  onOpenMap={handleOpenMapTab}
                  onOpenDiary={handleOpenDiaryTab}
                  onGoMypage={handleGoMypage}
                />
              )}

              {tab === 'diary' && !showDiaryEditor && !diaryResult && !showAlbum && (
                <DiaryIntro
                  onStartDiary={() => {
                    setDiaryTrigger((prev) => prev + 1);
                  }}
                  onOpenAlbum={() => setShowAlbum(true)}
                  onGoCalendar={() => navigate('/calendar')}
                />
              )}

              {tab === 'diary' && showAlbum && !diaryResult && (
                <DiaryAlbum
                  diaries={albumDiaries}
                  onBack={() => setShowAlbum(false)}
                  onDelete={async (id) => {
                    try {
                      await deleteDiary(Number(id));
                      setAlbumDiaries((prev) => prev.filter((d) => d.id !== id));
                    } catch {
                      alert('삭제에 실패했어요.');
                    }
                  }}
                  onUpdate={async (id, title, body) => {
                    await updateDiary(Number(id), { title, content: body });
                    setAlbumDiaries((prev) =>
                      prev.map((d) => d.id === id ? { ...d, title, body } : d)
                    );
                  }}
                />
              )}

              {tab === 'diary' && showDiaryEditor && !diaryResult && currentPet && (
                <DiaryView
                  pet={currentPet}
                  user={safeUser!}
                  diaries={safeDiaries}
                  autoPlace={autoPlace}
                  onClearAutoPlace={() => setAutoPlace('')}
                  onSave={handleSaveDiary}
                />
              )}

{tab === 'diary' && diaryResult && (
  <div className="h-full overflow-y-auto bg-[#F6F1EA] p-6">
    <div className="mx-auto w-full max-w-[720px]">
      {/* 상단 헤더 */}
      <div className="mb-4 flex items-center gap-3">
        <button
          onClick={() => {
            setDiaryResult(null);
            setShowDiaryEditor(false);
            setShowAlbum(true);
            setIsEditingDiary(false);
          }}
          className="flex items-center gap-1.5 rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
        >
          ← 뒤로
        </button>
        <h2 className="text-lg font-bold text-[#3D2B1F]">🐾 그림일기</h2>
        <div className="ml-auto flex items-center gap-2 text-xs font-medium">
          {autoSaveState === 'saving' && <span className="text-[#B08B7A]">저장 중...</span>}
          {autoSaveState === 'done' && !isEditingDiary && <span className="text-green-500">✓ 저장 완료</span>}
          {autoSaveState === 'error' && <span className="text-red-400">저장 실패</span>}
          {savedDiaryId && !isEditingDiary && autoSaveState === 'done' && (
            <button
              onClick={() => { setEditTitle(diaryResult.diary.title); setEditBody(diaryResult.diary.content); setIsEditingDiary(true); }}
              className="rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-[#8B6355] transition hover:bg-[#FFF0E6]"
            >
              ✏️ 수정
            </button>
          )}
          {isEditingDiary && (
            <>
              <button
                onClick={() => setIsEditingDiary(false)}
                className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-gray-400 transition hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={editSaving}
                className="rounded-full bg-[#F4845F] px-3 py-1.5 text-white transition hover:bg-[#e0724e] disabled:opacity-50"
              >
                {editSaving ? '저장 중...' : '저장'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* 스케치북/일기장 본문 */}
      <div className="relative rounded-[28px] border border-[#E9D9C9] bg-[#FFFDF8] p-6 shadow-[0_8px_24px_rgba(61,43,31,0.08)] md:p-8">
        {/* 마스킹 테이프 느낌 */}
        <div className="absolute -top-3 left-10 h-6 w-20 rotate-[-8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />
        <div className="absolute -top-3 right-10 h-6 w-20 rotate-[8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />

        {/* 제목/요약 */}
        <div className="mb-6 text-center">
          <p className="text-xs tracking-[0.2em] text-[#B08B7A]">오늘의 그림일기</p>
          {isEditingDiary ? (
            <input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="mt-2 w-full rounded-xl border border-[#F4845F] bg-[#FFF8F3] px-3 py-2 text-center text-xl font-bold text-[#F4845F] outline-none"
            />
          ) : (
            <h3 className="mt-2 text-2xl font-bold text-[#F4845F]">
              {diaryResult.diary.title}
            </h3>
          )}
          {diaryResult.diary.summary && (
            <div className="mt-3 inline-flex rounded-full bg-[#FFF0E6] px-3 py-1 text-xs font-medium text-[#F4845F]">
              ✨ {diaryResult.diary.summary}
            </div>
          )}
        </div>

        {/* 이미지 */}
        <div className="mx-auto mb-6 w-full max-w-[520px] rounded-[22px] border border-[#E8D9CC] bg-white p-3 shadow-[0_6px_18px_rgba(61,43,31,0.06)]">
          <img
            src={diaryResult.imageUrl}
            alt="그림일기"
            className="w-full h-auto rounded-[16px] object-contain"
          />
        </div>

        {/* 일기 본문 - 줄 있는 노트 느낌 */}
        {isEditingDiary ? (
          <textarea
            value={editBody}
            onChange={(e) => setEditBody(e.target.value)}
            rows={10}
            className="w-full rounded-[20px] border border-[#F4845F] bg-[#FFFCF8] px-5 py-5 text-[15px] leading-[31px] text-[#3D2B1F] outline-none resize-none"
            style={{ backgroundImage: 'repeating-linear-gradient(to bottom, transparent 0px, transparent 30px, #F3E7DA 31px)' }}
          />
        ) : (
          <div
            className="rounded-[20px] border border-[#F1E4D8] bg-[#FFFCF8] px-5 py-5"
            style={{ backgroundImage: 'repeating-linear-gradient(to bottom, transparent 0px, transparent 30px, #F3E7DA 31px)' }}
          >
            <p className="whitespace-pre-wrap text-[15px] leading-[31px] text-[#3D2B1F]">
              {diaryResult.diary.content}
            </p>
          </div>
        )}
      </div>
    </div>
  </div>
)}

              {tab === 'map' && !showMapSearch && (
                <MapIntro onStartMap={() => setShowMapSearch(true)} />
              )}

              {tab === 'map' && showMapSearch && (
                <MapView places={mapPlaces} onUsePlace={handleUsePlace} />
              )}
            </div>
          </div>

          {/* 오른쪽 챗봇 영역 */}
          <div className="w-[450px] shrink-0 bg-[#FFF8F3] p-4">
            <div
              className="flex h-full flex-col overflow-hidden rounded-[28px] border shadow-[0_0_40px_rgba(0,0,0,0.08)]"
              style={{ borderColor: '#F5D6C8', background: '#FFFFFF' }}
            >
              <div
                className="border-b px-4 py-3"
                style={{ borderColor: '#F5D6C8', background: '#FFFFFF' }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-11 w-11 items-center justify-center rounded-full"
                    style={{ background: '#FFE8D6' }}
                  >
                    <span className="text-2xl">🐾</span>
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold" style={{ color: '#3D2B1F' }}>
                      AI 멍봇
                    </p>
                    <p className="text-xs" style={{ color: '#8B6355' }}>
                      {currentPet ? `${currentPet.name} · ${currentPet.breed}` : '반려견 AI 도우미'}
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {!showChatHistory && (
                      <button
                        onClick={() => {
                          setShowChatHistory(false);
                          setChatKey((k) => k + 1);
                        }}
                        className="rounded-full border border-[#F4845F] bg-white px-3 py-1.5 text-xs font-semibold text-[#F4845F] transition hover:bg-[#FFF0E6]"
                      >
                        + 새 채팅
                      </button>
                    )}
                    <button
                      onClick={() => setShowChatHistory((prev) => !prev)}
                      className="rounded-full px-3 py-1.5 text-xs font-semibold transition hover:opacity-80"
                      style={{ background: showChatHistory ? '#3D2B1F' : '#F4845F', color: '#FFFFFF' }}
                    >
                      {showChatHistory ? '← 챗봇' : '최근 채팅 기록'}
                    </button>
                  </div>
                </div>
              </div>

              <div className="min-h-0 flex-1" style={{ background: '#FFF8F3' }}>
                {showChatHistory ? (
                  <ChatHistory onBack={() => setShowChatHistory(false)} />
                ) : (
                  <div className="h-full p-3">
                    <ChatBot
                      key={chatKey}
                      pet={currentPet}
                      onSelectPlace={handleUsePlace}
                      onPlacesFound={handlePlacesFound}
                      onNavigateToDiary={handleOpenDiaryTab}
                      onNavigateToMap={handleOpenMapTab}
                      onDiaryReady={handleDiaryReady}
                      diaryTrigger={diaryTrigger}
                      initialMessage={chatKey > 0 ? '새로운 이야기를 시작해볼까요? 🐾' : undefined}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
