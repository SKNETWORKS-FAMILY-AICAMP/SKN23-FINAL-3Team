import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface DayEmotion {
  date: string;
  emotion: string;
}

const EMOTIONS_LIST = ['😊', '😆', '😌', '😴', '😢', '😠', '🤔', '😨'];

const SAMPLE_EMOTIONS: DayEmotion[] = [
  { date: '2026-01-01', emotion: '😊' },
  { date: '2026-01-02', emotion: '😆' },
  { date: '2026-01-03', emotion: '😊' },
  { date: '2026-01-04', emotion: '😌' },
  { date: '2026-01-05', emotion: '😠' },
  { date: '2026-01-06', emotion: '😊' },
  { date: '2026-01-07', emotion: '😴' },
  { date: '2026-01-08', emotion: '😊' },
  { date: '2026-01-09', emotion: '😆' },
  { date: '2026-01-10', emotion: '😴' },
  { date: '2026-01-11', emotion: '😊' },
  { date: '2026-01-12', emotion: '😆' },
  { date: '2026-01-13', emotion: '😌' },
  { date: '2026-01-14', emotion: '😊' },
  { date: '2026-01-15', emotion: '😊' },
  { date: '2026-01-16', emotion: '😢' },
  { date: '2026-01-17', emotion: '😊' },
  { date: '2026-01-18', emotion: '😌' },
  { date: '2026-01-19', emotion: '😆' },
  { date: '2026-01-20', emotion: '😊' },
  { date: '2026-01-21', emotion: '😴' },
  { date: '2026-01-22', emotion: '😢' },
  { date: '2026-01-23', emotion: '😊' },
  { date: '2026-01-24', emotion: '😆' },
  { date: '2026-01-25', emotion: '😊' },
  { date: '2026-01-26', emotion: '😌' },
  { date: '2026-01-27', emotion: '😊' },
  { date: '2026-01-28', emotion: '😆' },
  { date: '2026-01-29', emotion: '😊' },
  { date: '2026-01-30', emotion: '😴' },
  { date: '2026-01-31', emotion: '😊' },
];

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
  const [currentDate, setCurrentDate] = useState(new Date(2026, 0, 1)); // January 2026

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

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
    const emotion = SAMPLE_EMOTIONS.find((e) => e.date === dateStr);
    return emotion?.emotion || null;
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-pink-50 pt-20 px-4 pb-8">
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
                  className={`aspect-square flex items-center justify-center rounded-2xl transition-all relative ${
                    day
                      ? isToday
                        ? 'bg-orange-100 border-2 border-orange-400'
                        : 'bg-gray-50 hover:bg-orange-50 cursor-pointer'
                      : ''
                  }`}
                >
                  {day && (
                    <>
                      {/* 날짜 - 왼쪽 상단에 작게 */}
                      <div
                        className={`absolute top-2 left-2 text-sm font-medium ${
                          isToday ? 'text-orange-600 font-bold' : 'text-gray-700'
                        }`}
                      >
                        {day}
                      </div>
                      {/* 감정 이모지 - 중앙에 매우 크게 */}
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
