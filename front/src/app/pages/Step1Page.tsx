import { useNavigate } from 'react-router';
import { DogPhotoUpload } from '../components/DogPhotoUpload';

interface Step1Props {
  onNext: () => void;
  onSkipToAdditional: () => void;
}

function Step1QuickSignup({ onNext, onSkipToAdditional }: Step1Props) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext();
  };

  const handleAdditionalInfo = (e: React.MouseEvent) => {
    e.preventDefault();
    onSkipToAdditional();
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="text-center mb-8">
        <div className="inline-block mb-4">
          <span className="px-4 py-1.5 bg-orange-100 text-primary rounded-full text-sm">
            빠른 시작
          </span>
        </div>
        <h1 className="mb-3 text-gray-800">빠르게 시작하기</h1>
        <p className="text-gray-600 mb-2">
          우리 강아지를 위한 맞춤 건강 코칭을 시작해보세요
        </p>
        <p className="text-sm text-muted-foreground">
          가입 후 추가 정보는 천천히 입력할 수 있어요
        </p>
      </div>

      <div className="bg-white rounded-3xl shadow-lg shadow-orange-100/50 p-8 border border-gray-100">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="pb-2">
            <DogPhotoUpload />
          </div>

          <div>
            <input
              type="text"
              placeholder="닉네임 입력"
              className="w-full px-5 py-4 rounded-2xl bg-input-background border-0 focus:ring-2 focus:ring-primary/30 transition-all"
              required
            />
          </div>

          <div>
            <input
              type="text"
              placeholder="강아지 이름 (예: 초코)"
              className="w-full px-5 py-4 rounded-2xl bg-input-background border-0 focus:ring-2 focus:ring-primary/30 transition-all"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full py-4 bg-gradient-to-r from-orange-400 to-orange-500 text-white rounded-2xl hover:from-orange-500 hover:to-orange-600 transition-all shadow-lg shadow-orange-200/50"
          >
            바로 시작하기
          </button>

          <button
            type="button"
            onClick={handleAdditionalInfo}
            className="w-full py-4 bg-white text-gray-600 border-2 border-gray-300 rounded-2xl hover:border-primary hover:text-primary hover:bg-orange-50 transition-all"
          >
            추가 정보 입력하기
          </button>

          <p className="text-center text-sm text-muted-foreground">
            추가 정보는 설정에서 다시 입력할 수 있어요
          </p>
        </form>
      </div>
    </div>
  );
}

export function Step1Page() {
  const navigate = useNavigate();

  const handleNext = () => {
    navigate('/');
  };

  const handleSkipToAdditional = () => {
    navigate('/step2');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-orange-100 flex items-center justify-center px-6 py-12">
      <Step1QuickSignup onNext={handleNext} onSkipToAdditional={handleSkipToAdditional} />
    </div>
  );
}
