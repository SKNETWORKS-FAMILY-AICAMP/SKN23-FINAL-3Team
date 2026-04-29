import { ImageWithFallback } from './figma/ImageWithFallback';
import { TrendingUp } from 'lucide-react';

interface DogProfileCardProps {
  name: string;
  age: string;
  status: 'overweight' | 'normal';
  insight: string;
  imageUrl: string;
}

export function DogProfileCard({ name, age, status, insight, imageUrl }: DogProfileCardProps) {
  const statusConfig = {
    overweight: {
      label: '과체중',
      className: 'bg-red-50 text-red-700 border-red-200'
    },
    normal: {
      label: '정상',
      className: 'bg-green-50 text-green-700 border-green-200'
    }
  };

  const currentStatus = statusConfig[status];

  return (
    null
  );
}
