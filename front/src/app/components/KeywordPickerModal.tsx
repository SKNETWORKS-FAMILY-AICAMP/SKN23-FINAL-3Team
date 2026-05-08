import { X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  /** 선택 가능한 옵션 목록 (label = value 가정). */
  options: string[];
  /** 현재 선택된 값들. */
  selectedItems: string[];
  /** 단일 항목 토글. */
  onToggle: (item: string) => void;
  /** 모달 헤더 타이틀. */
  title: string;
  /** 부제 (예: "원하는 성격을 자유롭게 선택해 주세요 (최대 5개)"). */
  description?: string;
}

/**
 * 다중 선택 칩 모달.
 *
 * Step2Page 의 PersonalityModal (반려견 성격) + OwnerPersonalityModal (보호자 라이프스타일)
 * 두 컴포넌트가 거의 100% 동일한 마크업이었던 것을 단일 컴포넌트로 통합.
 * title/description/options 만 prop 으로 분기.
 */
export default function KeywordPickerModal({
  isOpen,
  onClose,
  options,
  selectedItems,
  onToggle,
  title,
  description,
}: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/25 px-4 py-10" onClick={onClose}>
      <div
        className="mx-auto flex max-h-[82vh] w-full max-w-3xl flex-col overflow-hidden rounded-[32px] bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 px-6 pb-4 pt-6 md:px-8">
          <div>
            <h2 className="text-[28px] font-bold tracking-tight text-[#3F3A35]">{title}</h2>
            {description && (
              <p className="mt-2 text-sm text-[#8D867E]">{description}</p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="grid h-12 w-12 place-items-center rounded-full bg-[#F4F1EE] text-[#8A837B]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="overflow-y-auto px-6 pb-8 md:px-8">
          <div className="flex flex-wrap gap-3">
            {options.map((item) => (
              <KeywordChip
                key={item}
                active={selectedItems.includes(item)}
                onClick={() => onToggle(item)}
              >
                {item}
              </KeywordChip>
            ))}
          </div>
        </div>

        <div className="border-t border-[#F0ECE7] px-6 py-4 md:px-8">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-[16px] bg-[#DB5F2E] px-6 py-4 text-base font-bold text-white transition hover:bg-[#D05523]"
          >
            선택 완료
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * 키워드 칩 (라운드 + 토글). KeywordPickerModal·KeywordChipsField 양쪽에서 재사용.
 */
export function KeywordChip({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
        active
          ? 'border-[#E86A2C] bg-[#FFF2EA] text-[#D45E23]'
          : 'border-[#E6E1DB] bg-white text-[#7B746B] hover:border-[#F1B18C] hover:text-[#D45E23]'
      }`}
    >
      {children}
    </button>
  );
}
