import { useState, useEffect, useCallback, useRef } from 'react';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';

interface TourStep {
  target: string;          // data-tour 값
  title: string;
  description: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

const STEPS: TourStep[] = [
  {
    target: 'diary-button',
    title: '그림일기 쓰기',
    description: '이 버튼을 누르면 챗봇과 대화가 시작되고, AI가 자동으로 그림일기를 만들어줘요.',
    position: 'top',
  },
  {
    target: 'place-button',
    title: '장소 추천',
    description: '이 버튼을 누르면 챗봇과 자유롭게 대화하며 반려견 동반 장소를 추천받을 수 있어요.',
    position: 'top',
  },
  {
    target: 'chatbot',
    title: '장소 → 그림일기',
    description: '지도에서 장소를 찾은 뒤 "이 장소로 일기 쓰기"를 누르면 그 장소를 배경으로 그림일기가 만들어져요.',
    position: 'left',
  },
  {
    target: 'pet-picker',
    title: '반려견 전환',
    description: '마이페이지에서 반려견을 추가하면 여기서 전환할 수 있어요. 선택한 반려견의 모습으로 그림이 만들어져요.',
    position: 'bottom',
  },
  {
    target: 'photo-upload',
    title: '사진 → 그림 변환',
    description: '챗봇에 사진을 올리면 AI가 그림으로 변환해줘요.',
    position: 'top',
  },
  {
    target: 'new-chat',
    title: '새 채팅 / 최근 채팅 기록',
    description: '"새 채팅"으로 새로운 일기를 시작하고, "최근 채팅 기록"에서 이전 대화를 이어갈 수 있어요.',
    position: 'bottom',
  },
  {
    target: 'diary-menu',
    title: '다이어리',
    description: '다이어리 메뉴에서 지금까지 저장된 그림일기를 모아볼 수 있어요.',
    position: 'bottom',
  },
];

interface Props {
  open: boolean;
  onComplete: () => void;
}

interface SpotlightRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

export default function FeatureTour({ open, onComplete }: Props) {
  const [step, setStep] = useState(0);
  const [rect, setRect] = useState<SpotlightRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const isLast = step === STEPS.length - 1;

  const updateRect = useCallback(() => {
    const current = STEPS[step];
    if (!current) return;
    const el = document.querySelector(`[data-tour="${current.target}"]`);
    if (el) {
      const r = el.getBoundingClientRect();
      setRect({
        top: r.top - 4,
        left: r.left - 4,
        width: r.width + 8,
        height: r.height + 8,
      });
    } else {
      setRect(null);
    }
  }, [step]);

  useEffect(() => {
    if (!open) return;
    updateRect();
    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);
    return () => {
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('scroll', updateRect, true);
    };
  }, [open, updateRect]);

  const handleNext = () => {
    if (isLast) {
      onComplete();
      setStep(0);
    } else {
      setStep((s) => s + 1);
    }
  };

  const handlePrev = () => {
    if (step > 0) setStep((s) => s - 1);
  };

  const handleSkip = () => {
    onComplete();
    setStep(0);
  };

  if (!open) return null;

  const current = STEPS[step];

  // 툴팁 위치 계산 (뷰포트 밖으로 나가지 않도록 클램핑)
  const TOOLTIP_WIDTH = 320;
  const EDGE_MARGIN = 12;

  const getTooltipStyle = (): React.CSSProperties => {
    if (!rect) return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };

    const gap = 16;
    const pos = current.position ?? 'bottom';
    const vw = window.innerWidth;

    const clampLeft = (centerX: number) => {
      const half = TOOLTIP_WIDTH / 2;
      const minLeft = EDGE_MARGIN + half;
      const maxLeft = vw - EDGE_MARGIN - half;
      return Math.max(minLeft, Math.min(maxLeft, centerX));
    };

    switch (pos) {
      case 'bottom':
        return {
          top: rect.top + rect.height + gap,
          left: clampLeft(rect.left + rect.width / 2),
          transform: 'translateX(-50%)',
        };
      case 'top':
        return {
          top: rect.top - gap,
          left: clampLeft(rect.left + rect.width / 2),
          transform: 'translate(-50%, -100%)',
        };
      case 'left':
        return {
          top: rect.top + rect.height / 2,
          left: rect.left - gap,
          transform: 'translate(-100%, -50%)',
        };
      case 'right':
        return {
          top: rect.top + rect.height / 2,
          left: rect.left + rect.width + gap,
          transform: 'translateY(-50%)',
        };
    }
  };

  return (
    <div className="fixed inset-0 z-[9998]">
      {/* 어두운 오버레이 (스포트라이트 구멍 제외) */}
      <svg className="absolute inset-0 h-full w-full" style={{ pointerEvents: 'none' }}>
        <defs>
          <mask id="spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {rect && (
              <rect
                x={rect.left}
                y={rect.top}
                width={rect.width}
                height={rect.height}
                rx="12"
                fill="black"
              />
            )}
          </mask>
        </defs>
        <rect
          x="0" y="0" width="100%" height="100%"
          fill="rgba(0,0,0,0.55)"
          mask="url(#spotlight-mask)"
        />
      </svg>

      {/* 스포트라이트 테두리 */}
      {rect && (
        <div
          className="absolute rounded-xl border-2 border-[#F4845F] transition-all duration-300"
          style={{
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
            boxShadow: '0 0 0 4px rgba(244,132,95,0.25)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* 클릭 차단 오버레이 */}
      <div className="absolute inset-0" onClick={handleSkip} />

      {/* 툴팁 카드 */}
      <div
        ref={tooltipRef}
        className="absolute z-10 w-[320px] rounded-2xl border border-[#F5D6C8] bg-white p-5 shadow-xl"
        style={getTooltipStyle()}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 스텝 카운터 + 닫기 */}
        <div className="mb-3 flex items-center justify-between">
          <span className="rounded-full bg-[#FFF0E6] px-3 py-1 text-xs font-bold text-[#F4845F]">
            {step + 1} / {STEPS.length}
          </span>
          <button
            onClick={handleSkip}
            className="rounded-full p-1 text-[#B08B7A] transition hover:bg-[#FFF0E6] hover:text-[#F4845F]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <h3 className="mb-2 text-base font-bold text-[#3D2B1F]">{current.title}</h3>
        <p className="mb-4 text-sm leading-relaxed text-[#7A5C4D]">{current.description}</p>

        {/* 네비게이션 */}
        <div className="flex items-center justify-between">
          {step > 0 ? (
            <button
              onClick={handlePrev}
              className="flex items-center gap-1 rounded-full border border-[#E9D9C9] px-4 py-2 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              이전
            </button>
          ) : (
            <button
              onClick={handleSkip}
              className="rounded-full px-4 py-2 text-xs text-[#B08B7A] transition hover:text-[#8B6355]"
            >
              건너뛰기
            </button>
          )}

          <button
            onClick={handleNext}
            className="flex items-center gap-1 rounded-full bg-[#F4845F] px-5 py-2 text-xs font-bold text-white shadow transition hover:-translate-y-0.5 hover:bg-[#e0724e]"
          >
            {isLast ? '완료' : '다음'}
            {!isLast && <ChevronRight className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
