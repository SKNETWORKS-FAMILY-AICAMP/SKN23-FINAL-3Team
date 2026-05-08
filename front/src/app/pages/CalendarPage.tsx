import { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { getDiary, getDiaryCalendar, updateDiary, type DiaryRecord } from '../services/dbDiaryService';
import { getImage } from '../services/imageService';
import DiaryDetailView, { type DiaryViewModel } from '../components/DiaryDetailView';

interface DayEmotion {
  date: string;   // 'YYYY-MM-DD'
  emotion: string;
  diaryId: number;
}


const MONTHS = [
  { num: 1, name: '1월' },
  { num: 2, name: '2월' },
  { num: 3, name: '3월' },
  { num: 4, name: '4월' },
  { num: 5, name: '5월' },
  { num: 6, name: '6월' },
  { num: 7, name: '7월' },
  { num: 8, name: '8월' },
  { num: 9, name: '9월' },
  { num: 10, name: '10월' },
  { num: 11, name: '11월' },
  { num: 12, name: '12월' },
];

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [emotions, setEmotions] = useState<DayEmotion[]>([]);
  const [selectedDiary, setSelectedDiary] = useState<DiaryRecord | null>(null);
  const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(null);
  const [diaryLoading, setDiaryLoading] = useState(false);
  // 활성 월 카드 ref — 좌측 사이드바에서 현재 선택된 월이 화면에 보이도록 자동 스크롤.
  const activeMonthRef = useRef<HTMLDivElement | null>(null);

  const handleDayClick = (day: number) => {
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const found = emotions.find((e) => e.date === dateStr);
    if (!found) return;
    setDiaryLoading(true);
    setSelectedImageUrl(null);
    getDiary(found.diaryId)
      .then(async (diary) => {
        setSelectedDiary(diary);
        if (diary.image_id) {
          try {
            const img = await getImage(diary.image_id);
            setSelectedImageUrl(img.url);
          } catch { /* 이미지 없으면 무시 */ }
        }
      })
      .catch(() => {})
      .finally(() => setDiaryLoading(false));
  };

  // 월이 바뀔 때마다 캘린더 API 재조회
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    const y = currentDate.getFullYear();
    const m = currentDate.getMonth() + 1; // API는 1-indexed
    getDiaryCalendar(y, m)
      .then((res) => {
        const mapped: DayEmotion[] = res.items.map((item) => ({
          date: item.date,
          emotion: item.emotion,
          diaryId: item.diary_id,
        }));
        setEmotions(mapped);
      })
      .catch(() => {});
  }, [currentDate]);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // 활성 월(month) 변경 시 좌측 사이드바에서 해당 카드를 화면 중앙으로 스크롤.
  // mount 시 자동 적용 + 우측 ◀ ▶ 로 월 이동 시에도 좌측 동기화.
  useEffect(() => {
    activeMonthRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [month]);

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  const daysInMonth = lastDayOfMonth.getDate();
  const startingDayOfWeek = firstDayOfMonth.getDay();

  const days = [];
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push(null);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    days.push(day);
  }

  const getEmotionForDate = (day: number | null) => {
    if (!day) return null;
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return emotions.find((e) => e.date === dateStr)?.emotion ?? null;
  };

  const goToPreviousMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const goToPreviousYear = () => {
    setCurrentDate(new Date(year - 1, month, 1));
  };

  const goToNextYear = () => {
    setCurrentDate(new Date(year + 1, month, 1));
  };

  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  const handleMonthClick = (monthNum: number) => {
    setCurrentDate(new Date(year, monthNum - 1, 1));
  };

  // 미니 달력 그리드 생성 함수
  const getMiniCalendarDays = (monthNum: number) => {
    const firstDay = new Date(year, monthNum - 1, 1);
    const lastDay = new Date(year, monthNum, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();

    const days = [];
    for (let i = 0; i < startingDay; i++) {
      days.push(null);
    }
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }
    return days;
  };

  /* ── 일기 상세 뷰 ─────────────────────────────────── */
  if (selectedDiary || diaryLoading) {
    return (
      <div className="min-h-screen bg-[#F6F1EA] pt-20 px-4 pb-8">
        <div className="mx-auto w-full max-w-[720px]">
          {diaryLoading ? (
            <>
              <div className="mb-4 flex items-center gap-3">
                <button
                  onClick={() => { setSelectedDiary(null); setSelectedImageUrl(null); }}
                  className="flex items-center gap-1.5 rounded-full border border-[#F5D6C8] bg-white px-3 py-1.5 text-xs font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
                >
                  ← 캘린더로 돌아가기
                </button>
                <h2 className="text-lg font-bold text-[#3D2B1F]">🐾 그림일기</h2>
              </div>
              <div className="flex h-60 items-center justify-center rounded-[28px] bg-[#FFFDF8] border border-[#E9D9C9] shadow-[0_8px_24px_rgba(61,43,31,0.08)]">
                <span className="text-sm text-[#B08B7A]">불러오는 중...</span>
              </div>
            </>
          ) : selectedDiary && (
            <DiaryDetailView
              diary={{
                title: selectedDiary.title ?? '오늘의 일기',
                body: selectedDiary.content ?? '',
                summary: selectedDiary.summary ?? undefined,
                imageUrl: selectedImageUrl ?? undefined,
                placeName: selectedDiary.where_text ?? undefined,
              } satisfies DiaryViewModel}
              backLabel="← 캘린더로 돌아가기"
              onBack={() => { setSelectedDiary(null); setSelectedImageUrl(null); }}
              onUpdate={async (title, body) => {
                await updateDiary(selectedDiary.id, { title, content: body });
                setSelectedDiary({ ...selectedDiary, title, content: body });
              }}
            />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-orange-50 via-white to-pink-50 pt-20 px-4 pb-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex gap-6">
          {/* Left Sidebar - Month List */}
          <div className="w-1/4 bg-white rounded-[32px] shadow-lg border border-orange-100 p-6 overflow-y-auto max-h-[calc(100vh-120px)]">
            {/* Year selector */}
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={goToPreviousYear}
                className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600" />
              </button>
              <h3 className="text-lg font-bold text-gray-900">{year}년</h3>
              <button
                onClick={goToNextYear}
                className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <ChevronRight className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            {/* Mini calendars for each month */}
            <div className="space-y-4">
              {MONTHS.map((m) => {
                const miniDays = getMiniCalendarDays(m.num);
                const isSelected = month === m.num - 1;

                return (
                  <div
                    key={m.num}
                    ref={isSelected ? activeMonthRef : null}
                    className={`rounded-xl p-3 cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-orange-500 text-white shadow-md'
                        : 'bg-gray-50 text-gray-700 hover:bg-orange-50'
                    }`}
                    onClick={() => handleMonthClick(m.num)}
                  >
                    <div className={`text-sm font-semibold mb-2 ${isSelected ? 'text-white' : 'text-gray-900'}`}>
                      {m.name}
                    </div>

                    {/* Mini calendar grid */}
                    <div className="grid grid-cols-7 gap-0.5">
                      {miniDays.slice(0, 35).map((day, idx) => (
                        <div
                          key={idx}
                          className={`text-center text-[10px] py-0.5 ${
                            day
                              ? isSelected
                                ? 'text-white/90'
                                : 'text-gray-600'
                              : ''
                          }`}
                        >
                          {day || ''}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Content - Calendar */}
          <div className="flex-1 bg-white rounded-[32px] shadow-lg border border-orange-100 p-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <button
                onClick={goToPreviousMonth}
                className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <ChevronLeft className="w-6 h-6 text-gray-600" />
              </button>

              <h2 className="text-2xl font-bold text-gray-900">
                {year}년 {MONTHS[month].name}
              </h2>

              <button
                onClick={goToNextMonth}
                className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <ChevronRight className="w-6 h-6 text-gray-600" />
              </button>
            </div>

          {/* Week days */}
          <div className="grid grid-cols-7 gap-2 mb-4">
            {weekDays.map((day, idx) => (
              <div
                key={day}
                className={`text-center py-3 text-sm font-semibold ${
                  idx === 0 ? 'text-red-500' : idx === 6 ? 'text-blue-500' : 'text-gray-600'
                }`}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-2">
            {days.map((day, idx) => {
              const emotion = getEmotionForDate(day);
              const isToday =
                day === new Date().getDate() &&
                month === new Date().getMonth() &&
                year === new Date().getFullYear();

              return (
                <div
                  key={idx}
                  onClick={() => day && emotion && handleDayClick(day)}
                  className={`aspect-square flex items-center justify-center rounded-2xl transition-all relative ${
                    day
                      ? isToday
                        ? 'bg-orange-100 border-2 border-orange-400'
                        : emotion
                          ? 'bg-gray-50 hover:bg-orange-50 cursor-pointer'
                          : 'bg-gray-50'
                      : ''
                  }`}
                >
                  {day && (
                    <>
                      <div
                        className={`absolute top-2 left-2 text-sm font-medium ${
                          isToday ? 'text-orange-600 font-bold' : 'text-gray-700'
                        }`}
                      >
                        {day}
                      </div>
                      {emotion && (
                        <div className="text-7xl leading-none">{emotion}</div>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>

            {/* Legend */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">감정 기록</h3>
              <div className="flex flex-wrap gap-3">
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                  <span className="text-xl">😊</span>
                  <span className="text-xs text-gray-600">행복</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                  <span className="text-xl">😆</span>
                  <span className="text-xs text-gray-600">신남</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                  <span className="text-xl">😌</span>
                  <span className="text-xs text-gray-600">평온</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                  <span className="text-xl">😴</span>
                  <span className="text-xs text-gray-600">졸림</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                  <span className="text-xl">😢</span>
                  <span className="text-xs text-gray-600">슬픔</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                  <span className="text-xl">😠</span>
                  <span className="text-xs text-gray-600">화남</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
