/**
 * 회원가입 약관·개인정보처리방침 동의 단계 (Step2Page 진입 전 첫 단계).
 *
 * 외부팀 QA #76 / 정보통신망법 제22조 — 회원가입 시 약관 명시 동의 의무.
 *
 * 흐름:
 *   1. 헤더 안내 + 전체 동의 체크박스 1개 (개별 2개 토글)
 *   2. 필수 체크박스 2개 (이용약관 / 개인정보처리방침) + "보기" 버튼
 *   3. "다음" 버튼 — 두 체크박스 모두 체크해야 활성화
 *   4. 클릭 시 POST /users/me/agreements → 성공 시 onComplete() 호출
 *
 * 모달 dismiss = X / 배경 클릭 / ESC (LoginPromptModal 패턴 정합).
 */
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Check, ChevronRight, X } from 'lucide-react';
import { submitAgreements } from '../services/userService';
import { PrivacyContent } from './PrivacyContent';
import { TermsContent } from './TermsContent';

interface Props {
  /** 동의 완료 시 호출 — Step2Page 의 기존 폼 진입. */
  onComplete: () => void;
}

type ModalKind = null | 'terms' | 'privacy';

export default function AgreementsStep({ onComplete }: Props) {
  const [termsAgreed, setTermsAgreed] = useState(false);
  const [privacyAgreed, setPrivacyAgreed] = useState(false);
  const [modal, setModal] = useState<ModalKind>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allAgreed = termsAgreed && privacyAgreed;

  const handleAllAgree = () => {
    const next = !allAgreed;
    setTermsAgreed(next);
    setPrivacyAgreed(next);
  };

  const handleNext = async () => {
    if (!allAgreed || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitAgreements({ terms_agreed: true, privacy_agreed: true });
      onComplete();
    } catch (e) {
      const msg = e instanceof Error ? e.message : '동의 처리에 실패했어요. 잠시 후 다시 시도해주세요.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFF8F0] px-4 pb-16 pt-24">
      <div className="mx-auto max-w-md rounded-2xl bg-white p-6 shadow-sm md:p-8">
        <h1 className="text-xl font-bold text-[#3D2B1F] md:text-2xl">
          서비스 이용을 위해 동의가 필요합니다
        </h1>
        <p className="mt-2 text-sm text-[#8B6355]">
          아래 두 항목 모두 동의해야 가입을 완료할 수 있어요.
        </p>

        <div className="mt-6 space-y-3">
          {/* 전체 동의 */}
          <button
            type="button"
            onClick={handleAllAgree}
            className="flex w-full items-center gap-3 rounded-2xl border border-[#F0C7B0] bg-[#FFF3EA] px-4 py-3.5 text-left transition active:scale-[0.99]"
          >
            <CheckboxBox checked={allAgreed} />
            <span className="text-[15px] font-bold text-[#3D2B1F]">
              전체 동의
            </span>
          </button>

          {/* 개별 — 이용약관 */}
          <AgreementRow
            checked={termsAgreed}
            onToggle={() => setTermsAgreed((v) => !v)}
            label="(필수) 서비스 이용약관 동의"
            onView={() => setModal('terms')}
          />

          {/* 개별 — 개인정보처리방침 */}
          <AgreementRow
            checked={privacyAgreed}
            onToggle={() => setPrivacyAgreed((v) => !v)}
            label="(필수) 개인정보처리방침 동의"
            onView={() => setModal('privacy')}
          />
        </div>

        {error && (
          <p className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          type="button"
          onClick={handleNext}
          disabled={!allAgreed || submitting}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-[15px] font-bold text-white transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: allAgreed
              ? 'linear-gradient(135deg, #F4845F 0%, #F06030 100%)'
              : '#D9CFC6',
          }}
        >
          {submitting ? '처리 중...' : '다음'}
          {!submitting && <ChevronRight className="h-4 w-4" />}
        </button>
      </div>

      <AgreementModal
        open={modal !== null}
        kind={modal}
        onClose={() => setModal(null)}
      />
    </div>
  );
}


function CheckboxBox({ checked }: { checked: boolean }) {
  return (
    <span
      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition ${
        checked ? 'border-[#F06030] bg-[#F06030]' : 'border-[#D9CFC6] bg-white'
      }`}
    >
      {checked && <Check className="h-3.5 w-3.5 text-white" strokeWidth={3} />}
    </span>
  );
}


function AgreementRow({
  checked,
  onToggle,
  label,
  onView,
}: {
  checked: boolean;
  onToggle: () => void;
  label: string;
  onView: () => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-[#E3DDD7] bg-white px-4 py-3.5">
      <button
        type="button"
        onClick={onToggle}
        className="flex flex-1 items-center gap-3 text-left"
      >
        <CheckboxBox checked={checked} />
        <span className="text-sm text-[#3D2B1F]">{label}</span>
      </button>
      <button
        type="button"
        onClick={onView}
        className="ml-3 shrink-0 rounded-full border border-[#E3DDD7] px-3 py-1 text-xs text-[#8B6355] transition hover:bg-[#FFF8F3]"
      >
        보기
      </button>
    </div>
  );
}


function AgreementModal({
  open,
  kind,
  onClose,
}: {
  open: boolean;
  kind: ModalKind;
  onClose: () => void;
}) {
  // ESC 키로 닫기 — LoginPromptModal 패턴 정합.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const title = kind === 'terms' ? '서비스 이용약관' : '개인정보처리방침';

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-100 flex items-center justify-center px-4 py-8"
          style={{ background: 'rgba(61,43,31,0.45)', backdropFilter: 'blur(6px)' }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="flex w-full max-w-2xl flex-col overflow-hidden rounded-[24px] bg-white shadow-[0_24px_64px_rgba(61,43,31,0.18)]"
            style={{ maxHeight: '85vh' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#F0E6DC] px-6 py-4">
              <h2 className="text-lg font-bold text-[#3D2B1F]">{title}</h2>
              <button
                type="button"
                onClick={onClose}
                aria-label="닫기"
                className="flex h-8 w-8 items-center justify-center rounded-full text-[#8B6355] transition hover:bg-[#FFF8F3]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="overflow-y-auto px-6 py-5">
              {kind === 'terms' && <TermsContent />}
              {kind === 'privacy' && <PrivacyContent />}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
