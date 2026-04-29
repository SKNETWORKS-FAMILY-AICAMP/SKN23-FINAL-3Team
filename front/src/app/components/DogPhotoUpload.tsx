import { useState } from 'react';
import { Upload, X } from 'lucide-react';

interface DogPhotoUploadProps {
  value?: File | null;
  onChange?: (file: File | null) => void;
}

export function DogPhotoUpload({ value, onChange }: DogPhotoUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      onChange?.(file);
    }
  };

  const handleRemove = () => {
    setPreview(null);
    onChange?.(null);
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-40 h-40">
        {preview ? (
          <>
            <img
              src={preview}
              alt="강아지 사진"
              className="w-full h-full rounded-full object-cover border-4 border-orange-200"
            />
            <button
              onClick={handleRemove}
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
              type="button"
            >
              <X className="w-4 h-4" />
            </button>
          </>
        ) : (
          <label className="w-full h-full rounded-full border-4 border-dashed border-orange-200 flex flex-col items-center justify-center cursor-pointer hover:border-orange-300 transition-colors bg-orange-50">
            <Upload className="w-4 h-4 text-orange-400 mb-1" />
            <span className="text-xs text-gray-600">사진 업로드</span>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        )}
      </div>
    </div>
  );
}
