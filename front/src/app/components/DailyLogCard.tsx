import { useState } from 'react';
import { Check } from 'lucide-react';

interface LogItem {
  id: string;
  label: string;
  checked: boolean;
}

export function DailyLogCard() {
  const items: LogItem[] = [
  { id: '1', label: '권장 사료량 지켰어요', checked: true, weight: 25 },
  { id: '2', label: '추가 간식 안 먹었어요', checked: false, weight: 25 },
  { id: '3', label: '산책 목표 달성', checked: true, weight: 20 },
  { id: '4', label: '체중 기록 완료', checked: false, weight: 10 },
  { id: '5', label: '오늘 활동량 충분해요', checked: true, weight: 10 },
  { id: '6', label: 'AI 미션 완료', checked: false, weight: 10 },
];

  const toggleItem = (id: string) => {
    setItems(items.map(item =>
      item.id === id ? { ...item, checked: !item.checked } : item
    ));
  };

  return (
    null
  );
}
