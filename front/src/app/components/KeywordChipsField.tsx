import { useState } from 'react';
import { MoreHorizontal } from 'lucide-react';
import KeywordPickerModal, { KeywordChip } from './KeywordPickerModal';

interface Props {
  /** 필드 라벨 (예: "성격 (중복 선택 가능)"). */
  label: string;
  /** 모달 헤더 타이틀 (예: "성격 더보기"). */
  modalTitle: string;
  /** 모달 부제. */
  modalDescription?: string;
  /** "선택된 N" 라벨 단어 (예: "성격" / "라이프스타일"). 디폴트 = "항목". */
  selectedNoun?: string;
  /** 전체 옵션 목록 (백엔드 keywords 테이블). */
  options: string[];
  /** 현재 선택값. */
  value: string[];
  /** 토글 — 부모가 max 검증·error 메시지 처리. */
  onToggle: (item: string) => void;
  /** 전체 지우기 — 부모가 value 를 빈 배열로 갱신. */
  onClear: () => void;
  /** 메인 영역 미리보기 칩 개수 (디폴트 10). */
  previewLimit?: number;
  /** 최대 선택 개수 (안내용 — 실제 검증은 부모 onToggle 에서). 디폴트 5. */
  maxSelect?: number;
  /** 부모가 max 초과 등 에러 메시지를 넘겨주면 하단 빨간 텍스트로 표시. */
  error?: string;
}

/**
 * 키워드 다중 선택 입력 필드.
 *
 * Step2Page 의 보호자 라이프스타일 + 반려견 성격 두 입력부가 ~55줄씩 동일하게 박혀있던 것을
 * 단일 필드 컴포넌트로 통합. 미리보기 칩 + 더보기 모달 + 선택된 항목 표시 + 전체지우기 + error
 * 한 묶음을 props 로 캡슐화한다.
 */
export default function KeywordChipsField({
  label,
  modalTitle,
  modalDescription,
  selectedNoun = '항목',
  options,
  value,
  onToggle,
  onClear,
  previewLimit = 10,
  maxSelect = 5,
  error,
}: Props) {
  const [pickerOpen, setPickerOpen] = useState(false);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label className="block text-xs font-medium text-[#8D867E]">{label}</label>
        <span className="text-xs font-semibold text-[#D45E23]">
          {value.length}/{maxSelect}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {options.slice(0, previewLimit).map((item) => (
          <KeywordChip
            key={item}
            active={value.includes(item)}
            onClick={() => onToggle(item)}
          >
            {item}
          </KeywordChip>
        ))}
        <button
          type="button"
          onClick={() => setPickerOpen(true)}
          className="inline-flex items-center gap-2 rounded-full border border-[#E6E1DB] bg-white px-4 py-2 text-sm font-medium text-[#7B746B] transition hover:border-[#F1B18C] hover:text-[#D45E23]"
        >
          <MoreHorizontal className="h-4 w-4" />
          더보기
        </button>
      </div>

      {value.length > 0 && (
        <div className="mt-3">
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-xs text-[#A29A91]">선택된 {selectedNoun}</span>
            <button
              type="button"
              onClick={onClear}
              className="text-xs text-[#B0A89F] transition-colors hover:text-red-400"
            >
              전체 지우기
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {value.map((item) => (
              <span
                key={item}
                className="rounded-full bg-[#FFF2EA] px-3 py-1 text-xs font-semibold text-[#D45E23] ring-1 ring-[#F3D3BF]"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-red-500">{error}</p>}

      <KeywordPickerModal
        isOpen={pickerOpen}
        onClose={() => setPickerOpen(false)}
        options={options}
        selectedItems={value}
        onToggle={onToggle}
        title={modalTitle}
        description={modalDescription}
      />
    </div>
  );
}
