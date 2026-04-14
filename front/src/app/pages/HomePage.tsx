import { useMemo, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router';
import type { Pet, DiaryEntry, User } from '../types';
import DiaryView from '../components/DiaryView';
import MapView from '../components/MapView';
import ChatBot from '../components/ChatBot';

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
        <div className="absolute left-8 top-1/2 z-10 w-[46%] min-w-[420px] max-w-[560px] -translate-y-1/2 rounded-[40px] border border-white/35 bg-white/25 px-10 py-12 shadow-[0_24px_80px_rgba(61,43,31,0.12)] backdrop-blur-[16px]">
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

          <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
            <button
              type="button"
              onClick={onOpenMap}
              className="rounded-2xl border border-[#EEDFD3] bg-white/92 px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <p className="mb-1 text-sm font-bold text-[#3D2B1F]">
                📍 장소 추천 받기
              </p>
              <p className="text-xs leading-5 text-[#8B6355]">
                산책로, 카페, 실내 장소를 AI에게 추천받아보세요.
              </p>
            </button>

            <button
              type="button"
              onClick={onOpenDiary}
              className="rounded-2xl border border-[#EEDFD3] bg-white/92 px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <p className="mb-1 text-sm font-bold text-[#3D2B1F]">
                📝 오늘 일기 쓰기
              </p>
              <p className="text-xs leading-5 text-[#8B6355]">
                오늘 있었던 일을 기록하고 우리 아이의 하루를 남겨보세요.
              </p>
            </button>

            <button
              type="button"
              onClick={onGoMypage}
              className="rounded-2xl border border-[#EEDFD3] bg-white/92 px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <p className="mb-1 text-sm font-bold text-[#3D2B1F]">
                🐶 마이페이지 보기
              </p>
              <p className="text-xs leading-5 text-[#8B6355]">
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
            {['#반려견동반', '#펫프렌들리', '#실내추천', '#산책코스', '#여행지'].map((tag) => (
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
            className="w-full rounded-2xl bg-orange-500 px-6 py-4 text-left shadow-md transition hover:-translate-y-0.5 hover:bg-orange-600 hover:shadow-lg"
          >
            <p className="text-lg font-black text-white">🗺 지도 검색하기</p>
            <p className="mt-0.5 text-sm text-orange-100">
              우리 아이에게 맞는 반려견 동반 장소를 지금 바로 찾아보세요
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}

function DiaryIntro({
  onStartDiary,
  onGoMypage,
}: {
  onStartDiary: () => void;
  onGoMypage: () => void;
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
        <div className="absolute left-8 top-1/2 z-10 w-[46%] min-w-[420px] max-w-[560px] -translate-y-1/2 rounded-[40px] border border-white/40 bg-white/65 px-10 py-12 shadow-[0_24px_80px_rgba(61,43,31,0.12)] backdrop-blur-[16px]">
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

          <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
            <button
              type="button"
              onClick={onStartDiary}
              className="rounded-2xl border border-[#EEDFD3] bg-white/92 px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <p className="mb-1 text-sm font-bold text-[#3D2B1F]">
                ✍️ 일기 쓰기
              </p>
              <p className="text-xs leading-5 text-[#8B6355]">
                오늘의 하루를 바로 기록해보세요.
              </p>
            </button>

            <button
              type="button"
              className="rounded-2xl border border-[#EEDFD3] bg-white/92 px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <p className="mb-1 text-sm font-bold text-[#3D2B1F]">
                🖼️ 그림일기 안내
              </p>
              <p className="text-xs leading-5 text-[#8B6355]">
                기록한 내용을 AI 그림일기로 남길 수 있어요.
              </p>
            </button>

            <button
              type="button"
              onClick={onGoMypage}
              className="rounded-2xl border border-[#EEDFD3] bg-white/92 px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <p className="mb-1 text-sm font-bold text-[#3D2B1F]">
                🐶 마이페이지
              </p>
              <p className="text-xs leading-5 text-[#8B6355]">
                반려견 정보와 기존 기록을 확인해보세요.
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

  const [tab, setTab] = useState<Tab>(null);
  const [autoPlace, setAutoPlace] = useState('');
  const [showDiaryEditor, setShowDiaryEditor] = useState(false);
  const [showMapSearch, setShowMapSearch] = useState(false);

  // 로고·홈 버튼 클릭 시 항상 인트로로 리셋
  useEffect(() => {
    setTab(null);
    setShowDiaryEditor(false);
    setShowMapSearch(false);
    setAutoPlace('');
  }, [location.key]);

  const safePets = useMemo(() => {
    if (Array.isArray(pets) && pets.length > 0) return pets;
    if (pet) return [pet];
    return [{ name: '콩이', breed: '말티즈' } as Pet];
  }, [pets, pet]);

  const safeUser = user ?? ({ name: '테스트유저' } as User);
  const safeDiaries = diaries ?? [];
  const currentPet = selectedPet ?? safePets[0] ?? pet;

  const handleOpenDiaryTab = () => {
    setTab('diary');
    setShowDiaryEditor(false);
  };

  const handleOpenMapTab = () => {
    setTab('map');
    setShowMapSearch(false);
  };

  const handleUsePlace = (place: string) => {
    setAutoPlace(place);
    setTab('diary');
    setShowDiaryEditor(true);
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
  };

  return (
    <div className="h-screen bg-[#f8f8f6] pt-16">
      <div className="flex h-full overflow-hidden">
        <div className="flex flex-1 overflow-hidden">
          {/* 왼쪽 메인 영역 */}
          <div className="flex min-w-0 flex-[2] flex-col border-r border-gray-200 bg-white">
            <div className="flex border-b border-gray-200">
              <button
                className={`flex-1 px-6 py-3 font-medium transition-colors ${
                  tab === 'diary'
                    ? 'border-b-2 border-amber-600 bg-white text-amber-600'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                }`}
                onClick={handleOpenDiaryTab}
              >
                📝 강아지 일기장
              </button>

              <button
                className={`flex-1 px-6 py-3 font-medium transition-colors ${
                  tab === 'map'
                    ? 'border-b-2 border-amber-600 bg-white text-amber-600'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                }`}
                onClick={handleOpenMapTab}
              >
                🗺 지도
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

              {tab === 'diary' && !showDiaryEditor && (
                <DiaryIntro
                  onStartDiary={() => setShowDiaryEditor(true)}
                  onGoMypage={handleGoMypage}
                />
              )}

              {tab === 'diary' && showDiaryEditor && currentPet && (
                <DiaryView
                  pet={currentPet}
                  user={safeUser}
                  diaries={safeDiaries}
                  autoPlace={autoPlace}
                  onClearAutoPlace={() => setAutoPlace('')}
                  onSave={handleSaveDiary}
                />
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
          <div className="flex-1 bg-[#FFF8F3] p-4">
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
                      일기, 산책 장소, 여행지를 도와줄게!
                    </p>
                  </div>

                  <div
                    className="rounded-full px-2.5 py-1 text-[10px] font-semibold"
                    style={{ background: '#F4845F', color: '#FFFFFF' }}
                  >
                    AI
                  </div>
                </div>
              </div>

              <div className="min-h-0 flex-1" style={{ background: '#FFF8F3' }}>
                <div className="h-full p-3">
                  <ChatBot pet={currentPet} onSelectPlace={handleUsePlace} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}