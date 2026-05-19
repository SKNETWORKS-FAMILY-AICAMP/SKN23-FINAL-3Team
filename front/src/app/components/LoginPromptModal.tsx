import { useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { LogIn, X } from 'lucide-react';
import { useNavigate } from 'react-router';

const DEFAULT_FEATURES: { emoji: string; text: string }[] = [
  { emoji: '🐾', text: '반려견 프로필 등록 및 관리' },
  { emoji: '🗺️', text: 'AI 맞춤 여행지 추천' },
  { emoji: '📔', text: 'AI 그림일기 생성' },
  { emoji: '📅', text: '멍캘린더 일정 관리' },
];

interface Props {
  /** 표시 여부 (modal variant 에서만 의미). */
  open: boolean;
  /** 닫기 콜백 (X / 배경 클릭 / ESC). */
  onClose: () => void;
  /** 안내 기능 4개 — 호출처별 메시지가 약간 다르므로 override 가능. */
  features?: { emoji: string; text: string }[];
  /** 헤더 안내 문구. */
  title?: string;
  /** 부제 (줄바꿈 포함 가능). */
  subtitle?: string;
}

/**
 * 비로그인 사용자에게 로그인을 유도하는 모달.
 *
 * 외부팀 QA #65 (X 버튼 부재 / UI 일관성) 해소: 닫기 버튼 + 배경 클릭 dismiss + ESC 키 dismiss
 * 동시 지원. 기존 Navbar 의 인라인 모달 + MyPage 비로그인 분기 양쪽에서 호출되던 마크업을 통합.
 */
export default function LoginPromptModal({
  open,
  onClose,
  features = DEFAULT_FEATURES,
  title = '로그인이 필요해요',
  subtitle = 'withDOG의 더 많은 기능을\n로그인 후 이용해보세요',
}: Props) {
  const navigate = useNavigate();

  // ESC 키로 닫기 — 외부팀 QA #65 dismissibility 보강
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-100 flex items-center justify-center px-4"
          style={{ background: 'rgba(61,43,31,0.45)', backdropFilter: 'blur(6px)' }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="w-full max-w-[360px] overflow-hidden rounded-[28px] bg-white shadow-[0_24px_64px_rgba(61,43,31,0.18)]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 상단 일러스트 영역 */}
            <div
              className="relative flex flex-col items-center px-8 pb-6 pt-10"
              style={{ background: 'linear-gradient(145deg, #FFF3EA 0%, #FFE8D6 100%)' }}
            >
              <button
                onClick={onClose}
                aria-label="닫기"
                className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-full bg-white/60 text-[#8B6355] transition hover:bg-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-[0_4px_16px_rgba(244,132,95,0.2)]">
                <span className="text-4xl">🐾</span>
              </div>
              <h2 className="mt-4 text-[22px] font-black tracking-tight text-[#3D2B1F]">{title}</h2>
              <p className="mt-1.5 whitespace-pre-line text-center text-sm text-[#8B6355]">{subtitle}</p>
            </div>

            {/* 기능 안내 */}
            <div className="px-7 py-5">
              <div className="flex flex-col gap-2.5">
                {features.map(({ emoji, text }) => (
                  <div key={text} className="flex items-center gap-3 rounded-2xl bg-[#FFF8F3] px-4 py-2.5">
                    <span className="text-base">{emoji}</span>
                    <span className="text-sm font-medium text-[#5C3D2B]">{text}</span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={() => {
                  onClose();
                  navigate('/login');
                }}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-[15px] font-bold text-white transition active:scale-95"
                style={{ background: 'linear-gradient(135deg, #F4845F 0%, #F06030 100%)' }}
              >
                <LogIn className="h-4 w-4" />
                로그인 하러 가기
              </button>
              <p className="mt-3 text-center text-xs text-[#B08B7A]">
                카카오 · 구글 · 네이버로 간편 가입
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
