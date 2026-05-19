import { PrivacyContent } from '../components/PrivacyContent';

export function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#FFF8F0] px-4 pb-16 pt-24">
      <div className="mx-auto max-w-4xl rounded-2xl bg-white p-6 shadow-sm md:p-8">
        <h1 className="text-2xl font-bold text-gray-900 md:text-3xl">
          개인정보처리방침
        </h1>
        <p className="mt-2 text-sm text-gray-500">시행일: 2026.05.14.</p>

        <div className="mt-8">
          <PrivacyContent />
        </div>
      </div>
    </div>
  );
}
