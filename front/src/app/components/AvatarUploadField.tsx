import { useRef } from 'react';
import { User } from 'lucide-react';
import { validateImageSize } from '../utils/validation';

interface Props {
  /**
   * 현재 이미지 (data: URL 또는 백엔드에서 받은 image_url).
   * 백엔드 응답 url 은 그대로 표시, data: URL 은 신규 업로드 (handleStart 분기에서 base64 → 업로드).
   */
  value?: string | null;
  /**
   * 파일 선택 후 호출 — 부모는 받은 base64 dataURL 을 form state 에 세팅.
   * 5MB 검증은 본 컴포넌트 내부에서 선처리.
   */
  onChange: (dataUrl: string) => void;
  /** placeholder 아이콘 — 보호자=User (디폴트) / 반려견=Camera 등 lucide 아이콘 컴포넌트. */
  placeholderIcon?: React.ComponentType<{ className?: string }>;
  /** 원형 컨테이너 톤 — 보호자=slate, 반려견=오렌지. */
  tone?: 'slate' | 'orange';
  /** 안내 라벨 — 디폴트 = "클릭하여 사진 추가". */
  helperText?: string;
  /** 형식 안내 — 디폴트 = "PNG · JPEG · 5MB 이하". */
  formatText?: string;
  /** 접근성용 alt 라벨. */
  alt?: string;
}

const TONE_CLASS: Record<'slate' | 'orange', string> = {
  slate: 'bg-[#E8EAF0] text-[#7B859F]',
  orange: 'bg-[#F6E5D4] text-[#C27A37]',
};

/**
 * 원형 아바타 사진 업로드 필드.
 *
 * Step2Page 의 보호자 사진(`handleGuardianImageChange`) + 반려견 사진(`handleImageChange`) 두 핸들러가
 * 동일한 5MB 검증 + FileReader → base64 → form state 패턴이었던 것을 단일 컴포넌트로 통합.
 * tone / placeholderIcon prop 으로 외관만 분기.
 *
 * 정책 #72-A — 5MB 사전 검증 (Nginx·백엔드 매직바이트 검증보다 먼저 차단) 을 본 필드에서 일괄 처리한다.
 */
export default function AvatarUploadField({
  value,
  onChange,
  placeholderIcon: PlaceholderIcon = User,
  tone = 'slate',
  helperText = '클릭하여 사진 추가',
  formatText = '5MB 이하의 PNG, JPEG 이미지를 업로드해 주세요.',
  alt = '프로필',
}: Props) {
  const fileRef = useRef<HTMLInputElement | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const sizeError = validateImageSize(file);
    if (sizeError) {
      alert(sizeError);
      e.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result === 'string') {
        onChange(reader.result);
      }
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  return (
    <>
      <div className="flex justify-center">
        <input
          ref={fileRef}
          type="file"
          accept="image/png,image/jpeg"
          className="hidden"
          onChange={handleChange}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="flex flex-col items-center"
        >
          <div
            className={`flex h-[100px] w-[100px] items-center justify-center overflow-hidden rounded-full shadow-sm ${TONE_CLASS[tone]}`}
          >
            {value ? (
              <img src={value} alt={alt} className="h-full w-full object-cover" />
            ) : (
              <PlaceholderIcon className="h-10 w-10" />
            )}
          </div>
          <span className="mt-3 text-[11px] text-[#A19A92]">{helperText}</span>
        </button>
      </div>
      <p className="mt-1 text-[10px] text-[#B5ADA4] text-center">{formatText}</p>
    </>
  );
}
