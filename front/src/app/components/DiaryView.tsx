import { useState, useRef } from 'react';
import type { Pet, DiaryEntry, DiaryResult, User } from '../types';

interface Props {
  pet: Pet;
  user: User;
  diaries: DiaryEntry[];
  autoPlace: string;
  onClearAutoPlace: () => void;
  onSave: (entry: DiaryEntry) => void;
}

export default function DiaryView({
  pet,
  user,
  diaries,
  autoPlace,
  onClearAutoPlace,
  onSave,
}: Props) {
  const [memo, setMemo] = useState('');
  const [place, setPlace] = useState(autoPlace || '');
  const [emotion, setEmotion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiaryResult | null>(null);
  const [saved, setSaved] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  const today = new Date().toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  });

  const generate = async () => {
    setLoading(true);
    setSaved(false);

    setTimeout(() => {
      const mockResult: DiaryResult = {
        title: `${pet.name}의 즐거운 하루`,
        body: `오늘은 ${place || '산책로'}에서 ${user.name || '주인님'}과 함께 산책을 했어요. 신나게 뛰어놀았더니 기분이 정말 ${emotion || '좋았'}어요!`,
        summary: `${place || '산책'} · ${emotion || '행복'}`,
      };
      setResult(mockResult);
      setLoading(false);
      setTimeout(
        () => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
        100
      );
    }, 1200);
  };

  const handleSave = () => {
    if (!result) return;

    onSave({
      ...result,
      id: Date.now().toString(),
      date: today,
      place: place || '장소 미입력',
    } as DiaryEntry);

    setSaved(true);
  };

  return (
    <div className="p-6">
      

      {result && (
        <div
          className="mt-5 rounded-2xl border border-amber-300 bg-amber-50 p-4"
          ref={resultRef}
        >
          <div className="mb-4 flex aspect-[16/6] items-center justify-center rounded-xl bg-gray-200 text-5xl">
            🐕
          </div>

          <h3 className="text-xl font-bold text-gray-800">{result.title}</h3>
          <p className="mt-3 text-sm leading-7 text-gray-600">{result.body}</p>

          <div className="mt-3 inline-flex rounded-full bg-amber-200 px-3 py-1 text-xs font-semibold text-amber-800">
            ✨ {result.summary}
          </div>

          <button
            type="button"
            className="mt-4 w-full rounded-xl bg-amber-500 py-3 text-sm font-semibold text-white hover:bg-amber-600 disabled:bg-gray-300"
            onClick={handleSave}
            disabled={saved}
          >
            {saved ? '✅ 저장됨' : '💾 저장하기'}
          </button>
        </div>
      )}

      
    </div>
  );
}
