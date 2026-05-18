import { useState, useCallback } from 'react';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import FeatureTour from './FeatureTour';

const ONBOARDING_KEY_PREFIX = 'onboarding_completed_';

function getOnboardingKey(userId?: number): string {
  return userId ? `${ONBOARDING_KEY_PREFIX}${userId}` : 'onboarding_completed';
}

const SLIDES = [
  '/onboarding/onboarding_01_welcome.png',
  '/onboarding/onboarding_02_map.png',
  '/onboarding/onboarding_03_diary.png',
  '/onboarding/onboarding_04_diary_graph.png',
  '/onboarding/onboarding_05_profile_image.png',
];

interface Props {
  open: boolean;
  onComplete: () => void;
  /** true면 localStorage 업데이트 안 함 (수동 실행용) */
  manual?: boolean;
  /** 계정별 온보딩 구분용 유저 ID */
  userId?: number;
}

/** localStorage에 온보딩 완료 여부 저장 (계정별) */
export function markOnboardingComplete(userId?: number) {
  localStorage.setItem(getOnboardingKey(userId), new Date().toISOString());
}

/** 온보딩을 아직 완료하지 않았는지 확인 (계정별) */
export function isOnboardingPending(userId?: number): boolean {
  return !localStorage.getItem(getOnboardingKey(userId));
}

type Phase = 'slides' | 'feature-tour';

export default function OnboardingTour({ open, onComplete, manual, userId }: Props) {
  const [phase, setPhase] = useState<Phase>('slides');
  const [page, setPage] = useState(0);
  const isLast = page === SLIDES.length - 1;

  // 전체 종료 (건너뛰기 or 최종 완료)
  const finishAll = useCallback(() => {
    if (!manual) markOnboardingComplete(userId);
    setPage(0);
    setPhase('slides');
    onComplete();
  }, [manual, onComplete, userId]);

  // 슬라이드 완료 → 인터랙티브 투어로 전환
  const handleSlidesComplete = useCallback(() => {
    setPage(0);
    setPhase('feature-tour');
  }, []);

  if (!open) return null;

  // Phase 2: 인터랙티브 기능 투어
  if (phase === 'feature-tour') {
    return <FeatureTour open onComplete={finishAll} />;
  }

  // Phase 1: 이미지 슬라이드
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative mx-4 flex w-full max-w-[820px] flex-col overflow-hidden rounded-[28px] bg-white shadow-2xl">
        {/* 건너뛰기 / 닫기 */}
        <div className="flex items-center justify-end px-4 pt-3">
          {isLast ? (
            <div className="h-9" />
          ) : (
            <button
              onClick={finishAll}
              className="flex items-center gap-1 rounded-full px-3 py-1.5 text-sm text-[#8B6355] transition hover:bg-[#FFF0E6]"
            >
              건너뛰기
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* 이미지 슬라이드 */}
        <div className="relative flex-1 overflow-hidden px-2">
          <div
            className="flex transition-transform duration-300 ease-in-out"
            style={{ transform: `translateX(-${page * 100}%)` }}
          >
            {SLIDES.map((src, i) => (
              <div key={i} className="w-full flex-shrink-0 px-2">
                <img
                  src={src}
                  alt={`온보딩 ${i + 1}`}
                  className="mx-auto h-auto max-h-[85vh] w-full object-contain"
                  draggable={false}
                />
              </div>
            ))}
          </div>

          {/* 좌우 화살표 */}
          {page > 0 && (
            <button
              onClick={() => setPage((p) => p - 1)}
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-1.5 shadow-md transition hover:bg-white"
            >
              <ChevronLeft className="h-5 w-5 text-[#3D2B1F]" />
            </button>
          )}
          {!isLast && (
            <button
              onClick={() => setPage((p) => p + 1)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-1.5 shadow-md transition hover:bg-white"
            >
              <ChevronRight className="h-5 w-5 text-[#3D2B1F]" />
            </button>
          )}
        </div>

        {/* 도트 인디케이터 */}
        <div className="flex items-center justify-center gap-2 py-3">
          {SLIDES.map((_, i) => (
            <button
              key={i}
              onClick={() => setPage(i)}
              className="h-2 rounded-full transition-all duration-300"
              style={{
                width: i === page ? 20 : 8,
                backgroundColor: i === page ? '#F4845F' : '#E9D9C9',
              }}
            />
          ))}
        </div>

        {/* 하단 버튼 */}
        <div className="px-5 pb-5">
          <button
            onClick={isLast ? handleSlidesComplete : () => setPage((p) => p + 1)}
            className="w-full rounded-2xl bg-[#F4845F] py-3.5 text-sm font-bold text-white shadow-md transition hover:-translate-y-0.5 hover:bg-[#e0724e] hover:shadow-lg"
          >
            {isLast ? '기능 둘러보기' : '다음'}
          </button>
        </div>
      </div>
    </div>
  );
}
