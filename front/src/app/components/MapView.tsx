import { useState } from 'react';
import { Search } from 'lucide-react';

const MAP_TAGS = ['#공원', '#산책', '#애견카페', '#카페', '#반려견 친화'];

const RECOMMENDED_PLACES = [
  {
    name: '한강공원 반포지구',
    desc: '서울 서초구 반포동',
    tags: ['#비포장로', '#반려견과 여유'],
  },
  {
    name: '서울숲 공원',
    desc: '서울 성동구 뚝섬로',
    tags: ['#숲속 산책', '#넓은 산책'],
  },
  {
    name: '월드컵공원',
    desc: '서울 마포구 상암동',
    tags: ['#반려견 산책', '#넓은 공간'],
  },
];

interface Props {
  onUsePlace: (place: string) => void;
}

export default function MapView({ onUsePlace }: Props) {
  const [keyword, setKeyword] = useState('');

  return (
    <div className="p-6">
      <div className="space-y-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="지역 / 장소 검색"
            className="w-full rounded-xl border border-gray-300 py-3 pl-10 pr-4 text-sm outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-200"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {MAP_TAGS.map((tag, idx) => (
            <button
              key={tag}
              type="button"
              className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                idx === 0
                  ? 'bg-pink-500 text-white'
                  : 'border border-gray-200 bg-white text-gray-600'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>

        <div className="flex h-[280px] items-center justify-center rounded-xl bg-blue-100 text-sm text-gray-600">
          <div className="text-center">
            <div className="mb-2 text-3xl">📍</div>
            카카오맵 API 연결 영역
          </div>
        </div>

        <div>
          <div className="mb-2 text-sm font-semibold text-gray-700">추천 장소</div>
          <div className="space-y-3">
            {RECOMMENDED_PLACES.map((item) => (
              <div key={item.name} className="rounded-xl bg-amber-50 p-4">
                <div className="text-base font-semibold text-gray-800">📍 {item.name}</div>
                <div className="mt-1 text-sm text-gray-600">{item.desc}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                  {item.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => onUsePlace(item.name)}
                  className="mt-3 text-sm font-semibold text-orange-600 hover:text-orange-700"
                >
                  이 장소로 일기 쓰기 →
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
