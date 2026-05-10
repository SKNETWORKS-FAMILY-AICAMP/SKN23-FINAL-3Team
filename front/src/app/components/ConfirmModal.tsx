import { motion, AnimatePresence } from "motion/react";

export type ConfirmVariant = "default" | "danger";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
  loading?: boolean;
}

/**
 * yes/no 확인 모달.
 *
 * Destructive 액션 (회원탈퇴·반려견 삭제·다이어리 삭제 등) 의 사용자 확인용 재사용 컴포넌트.
 * variant="danger" 시 confirm 버튼이 빨간 톤. cancel 디폴트 강조 패턴.
 * loading 중에는 backdrop 클릭·ESC 무시 + 버튼 disabled.
 */
export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "확인",
  cancelLabel = "취소",
  variant = "default",
  loading = false,
}: ConfirmModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="confirm-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 bg-black/40 px-4 py-10"
          onClick={loading ? undefined : onClose}
        >
          <motion.div
            key="confirm-card"
            initial={{ opacity: 0, scale: 0.94, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            className="mx-auto mt-24 max-w-md rounded-[28px] bg-white p-7 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="break-keep text-xl font-bold text-slate-900">{title}</h3>
            {description && (
              <p className="mt-3 whitespace-pre-line break-keep text-sm leading-6 text-slate-600">
                {description}
              </p>
            )}
            <div className="mt-7 flex gap-3">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
              >
                {cancelLabel}
              </button>
              <button
                type="button"
                onClick={onConfirm}
                disabled={loading}
                className={`flex-1 rounded-2xl px-4 py-3 text-sm font-semibold text-white shadow-sm transition disabled:opacity-60 ${
                  variant === "danger"
                    ? "bg-red-500 hover:bg-red-600"
                    : "bg-slate-900 hover:bg-slate-800"
                }`}
              >
                {loading ? "처리 중..." : confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
