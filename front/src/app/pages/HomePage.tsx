import { useMemo, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { PenSquare, FolderOpen, CalendarDays, MapPinned, SquarePen, UserRound, NotebookPen, Map } from 'lucide-react';
import type { Pet, DiaryEntry, User } from '../types';
import DiaryView from '../components/DiaryView';
import MapView from '../components/MapView';
import ChatBot from '../components/ChatBot';
import ChatHistory from '../components/ChatHistory';
import type { GeneratedDiary } from '../services/diaryService';
import { createDiary, updateDiary } from '../services/dbDiaryService';
import { uploadImage } from '../services/imageService';
import { getMe } from '../services/userService';
import { getPets } from '../services/petService';

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
}: {
  diaries: DiaryEntry[];
  onBack: () => void;
}) {
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

        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          {[...diaries].reverse().map((entry) => (
            <div
              key={entry.id}
              className="overflow-hidden rounded-[20px] border border-[#E9D9C9] bg-[#FFFDF8] shadow-[0_4px_16px_rgba(61,43,31,0.07)] transition hover:-translate-y-0.5 hover:shadow-md"
            >
              {entry.imageUrl ? (
                <img
                  src={entry.imageUrl}
                  alt={entry.title}
                  className="h-36 w-full object-cover"
                />
              ) : (
                <div className="flex h-36 w-full items-center justify-center bg-[#FFF0E6] text-4xl">
                  🐾
                </div>
              )}
              <div className="p-3">
                <p className="truncate text-sm font-bold text-[#3D2B1F]">{entry.title}</p>
                <p className="mt-0.5 truncate text-[11px] text-[#B08B7A]">{entry.date}</p>
                {entry.summary && (
                  <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-[#8B6355]">{entry.summary}</p>
                )}
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
  const [diaryResult, setDiaryResult] = useState<{ diary: GeneratedDiary; imageUrl: string } | null>(null);
  const [diaryTrigger, setDiaryTrigger] = useState(0);
  const [showAlbum, setShowAlbum] = useState(false);
  const [albumDiaries, setAlbumDiaries] = useState<DiaryEntry[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [fetchedPetId, setFetchedPetId] = useState<number | null>(null);
  const [showChatHistory, setShowChatHistory] = useState(false);

  // 로그인된 유저의 첫 번째 반려견 ID를 백엔드에서 가져옴
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    getMe()
      .then((me) => getPets(me.id))
      .then((pets) => { if (pets.length > 0) setFetchedPetId(pets[0].id); })
      .catch(() => {/* 로그인 안 된 경우 무시 */});
  }, []);

  // URL ?tab= 파라미터 변경 시 탭 동기화
  useEffect(() => {
    const t = new URLSearchParams(location.search).get('tab');
    if (t === 'diary' || t === 'map') {
      setTab(t);
      setShowDiaryEditor(false);
      setShowMapSearch(false);
      setShowAlbum(false);
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
  const currentPet = selectedPet ?? safePets[0] ?? pet;

  const handleOpenDiaryTab = () => {
    setTab('diary');
    setShowDiaryEditor(false);
    setShowAlbum(false);
  };

  const handleOpenMapTab = () => {
    setTab('map');
    setShowMapSearch(false);
  };

  const handleUsePlace = (place: string) => {
    setAutoPlace(place);
    setTab('diary');
    setDiaryResult(null);
    setDiaryTrigger((prev) => prev + 1);
  };

  const handleGoMypage = () => {
    if (onGoMypage) {
      onGoMypage();
    } else {
      navigate('/mypage');
    }
  };

  const handleSaveDiary = (entry: DiaryEntry) => {
    if (onSaveDiary) {
      onSaveDiary(entry);
    }
    setAlbumDiaries((prev) => [...prev, entry]);
  };

  const handleDiaryReady = (diary: GeneratedDiary, imageUrl: string) => {
    setDiaryResult({ diary, imageUrl });
    setTab('diary');
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
          }}
          className="flex items-center gap-1.5 rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
        >
          ← 뒤로
        </button>
        <h2 className="text-lg font-bold text-[#3D2B1F]">🐾 그림일기</h2>
      </div>

      {/* 스케치북/일기장 본문 */}
      <div className="relative rounded-[28px] border border-[#E9D9C9] bg-[#FFFDF8] p-6 shadow-[0_8px_24px_rgba(61,43,31,0.08)] md:p-8">
        {/* 마스킹 테이프 느낌 */}
        <div className="absolute -top-3 left-10 h-6 w-20 rotate-[-8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />
        <div className="absolute -top-3 right-10 h-6 w-20 rotate-[8deg] rounded-sm bg-[#F7D9A6]/80 shadow-sm" />

        {/* 제목/요약 */}
        <div className="mb-6 text-center">
          <p className="text-xs tracking-[0.2em] text-[#B08B7A]">오늘의 그림일기</p>
          <h3 className="mt-2 text-2xl font-bold text-[#F4845F]">
            {diaryResult.diary.title}
          </h3>
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
        <div
          className="rounded-[20px] border border-[#F1E4D8] bg-[#FFFCF8] px-5 py-5"
          style={{
            backgroundImage:
              'repeating-linear-gradient(to bottom, transparent 0px, transparent 30px, #F3E7DA 31px)',
          }}
        >
          <p className="whitespace-pre-wrap text-[15px] leading-[31px] text-[#3D2B1F]">
            {diaryResult.diary.content}
          </p>
        </div>

        {/* 저장 버튼 */}
        <button
          disabled={isSaving}
          onClick={async () => {
            const petId = currentPet?.id ?? fetchedPetId ?? undefined;
            if (!petId) {
              alert('반려견 정보를 찾을 수 없어요.');
              return;
            }
            setIsSaving(true);
            try {
              // 1단계: 일기 텍스트 먼저 저장
              const saved = await createDiary({
                pet_id: petId,
                title: diaryResult.diary.title,
                content: diaryResult.diary.content,
                summary: diaryResult.diary.summary ?? '',
                emotion: diaryResult.diary.emotion ?? '',
              });

              // 2단계: base64 이미지 → File → S3 업로드 → image_id 바인딩
              try {
                const blob = await fetch(diaryResult.imageUrl).then((r) => r.blob());
                const file = new File([blob], 'diary.png', { type: 'image/png' });
                const imgRecord = await uploadImage(file);
                await updateDiary(saved.id, { image_id: imgRecord.id });
              } catch {
                // 이미지 업로드 실패해도 일기 텍스트는 저장됨
              }

              // 로컬 앨범에도 추가
              handleSaveDiary({
                id: saved.id.toString(),
                title: diaryResult.diary.title,
                body: diaryResult.diary.content,
                summary: diaryResult.diary.summary ?? '',
                date: new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }),
                place: autoPlace || '',
                imageUrl: diaryResult.imageUrl,
              });
              alert('그림일기가 저장되었어요 🐾');
            } catch {
              alert('저장에 실패했어요. 다시 시도해주세요.');
            } finally {
              setIsSaving(false);
            }
          }}
          className="mt-6 w-full rounded-2xl bg-[#F4845F] py-4 text-sm font-bold text-white transition hover:bg-[#e8764f] disabled:opacity-60"
        >
          {isSaving ? '저장 중...' : '💾 저장하기'}
        </button>
      </div>
    </div>
  </div>
)}

              {tab === 'map' && !showMapSearch && (
                <MapIntro onStartMap={() => setShowMapSearch(true)} />
              )}

              {tab === 'map' && showMapSearch && (
                <MapView onUsePlace={handleUsePlace} />
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

                  <button
                    onClick={() => setShowChatHistory((prev) => !prev)}
                    className="rounded-full px-2.5 py-1 text-[10px] font-semibold transition hover:opacity-80"
                    style={{ background: showChatHistory ? '#3D2B1F' : '#F4845F', color: '#FFFFFF' }}
                  >
                    {showChatHistory ? '← 챗봇' : '최근 대화 기록'}
                  </button>
                </div>
              </div>

              <div className="min-h-0 flex-1" style={{ background: '#FFF8F3' }}>
                {showChatHistory ? (
                  <ChatHistory onBack={() => setShowChatHistory(false)} />
                ) : (
                  <div className="h-full p-3">
                    <ChatBot
                      pet={currentPet}
                      onSelectPlace={handleUsePlace}
                      onNavigateToDiary={handleOpenDiaryTab}
                      onNavigateToMap={handleOpenMapTab}
                      onDiaryReady={handleDiaryReady}
                      diaryTrigger={diaryTrigger}
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