import { motion, AnimatePresence } from "motion/react";
import { X, Check, Crown, Star, Sparkles } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

const TIERS = [
  {
    key: "free",
    name: "무료",
    price: "₩0",
    period: "",
    icon: Star,
    color: "from-gray-100 to-gray-200",
    iconColor: "text-gray-500",
    badgeColor: "bg-gray-100 text-gray-600",
    btnClass: "bg-gray-200 text-gray-500 cursor-default",
    btnLabel: "현재 플랜",
    features: [
      "그림일기 하루 3회",
      "일기 내용 300자",
      "감정 6종",
      "그림 스타일 1종",
      "반려견 2마리 등록",
      "일기 수정 불가",
    ],
    disabled: true,
  },
  {
    key: "basic",
    name: "1단계",
    price: "₩10,000",
    period: "/ 월",
    icon: Crown,
    color: "from-orange-50 to-orange-100",
    iconColor: "text-orange-500",
    badgeColor: "bg-orange-100 text-orange-600",
    btnClass:
      "bg-gradient-to-r from-orange-400 to-orange-500 hover:from-orange-500 hover:to-orange-600 text-white shadow-md hover:shadow-lg active:scale-95",
    btnLabel: "구독 시작하기",
    features: [
      "그림일기 하루 10회",
      "일기 내용 450자",
      "감정 12종",
      "그림 스타일 3종",
      "반려견 3마리 등록",
      "일기 수정 하루 5회",
      "월별 감정 리포트",
    ],
    disabled: false,
  },
  {
    key: "premium",
    name: "2단계",
    price: "₩25,000",
    period: "/ 월",
    icon: Sparkles,
    color: "from-amber-50 to-yellow-100",
    iconColor: "text-yellow-500",
    badgeColor: "bg-yellow-100 text-yellow-700",
    btnClass:
      "bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-white shadow-md hover:shadow-lg active:scale-95",
    btnLabel: "프리미엄 시작하기",
    features: [
      "그림일기 무제한",
      "일기 내용 500자+",
      "전체 감정 & 스타일",
      "반려견 무제한 등록",
      "일기 수정 하루 10회",
      "월별 감정 리포트",
      "클라우드 백업",
      "gpt-image-2 고품질 이미지",
    ],
    disabled: false,
  },
];

export function SubscriptionModal({ open, onClose }: Props) {
  const handlePayment = (tierName: string) => {
    alert(`${tierName} 결제 기능은 준비 중이에요! 곧 만나요 🐾`);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[200] flex items-center justify-center px-4 py-8"
          style={{ background: "rgba(61,43,31,0.5)", backdropFilter: "blur(8px)" }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 28, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.96 }}
            transition={{ duration: 0.24, ease: "easeOut" }}
            className="w-full max-w-2xl overflow-hidden rounded-[28px] bg-white shadow-[0_32px_80px_rgba(61,43,31,0.22)]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 헤더 */}
            <div
              className="relative flex flex-col items-center px-8 pt-10 pb-7"
              style={{ background: "linear-gradient(145deg, #FFF3EA 0%, #FFE8D6 100%)" }}
            >
              <button
                onClick={onClose}
                className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-full bg-white/60 text-[#8B6355] transition hover:bg-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-[0_4px_16px_rgba(244,132,95,0.25)]">
                <span className="text-3xl">🐾</span>
              </div>
              <h2 className="mt-4 text-[22px] font-black tracking-tight text-[#3D2B1F]">
                구독 패스
              </h2>
              <p className="mt-1.5 text-center text-sm text-[#8B6355]">
                반려견과의 소중한 순간을 더 풍성하게 기록해보세요
              </p>
            </div>

            {/* 플랜 카드 */}
            <div className="grid grid-cols-3 gap-4 px-6 py-6">
              {TIERS.map((tier) => {
                const Icon = tier.icon;
                return (
                  <div
                    key={tier.key}
                    className={`flex flex-col rounded-2xl bg-gradient-to-b ${tier.color} p-4`}
                  >
                    {/* 티어 헤더 */}
                    <div className="flex items-center gap-2 mb-3">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/70">
                        <Icon className={`h-4 w-4 ${tier.iconColor}`} />
                      </div>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${tier.badgeColor}`}>
                        {tier.name}
                      </span>
                    </div>

                    {/* 가격 */}
                    <div className="mb-4">
                      <span className="text-xl font-black text-[#3D2B1F]">{tier.price}</span>
                      {tier.period && (
                        <span className="text-xs text-gray-500 ml-1">{tier.period}</span>
                      )}
                    </div>

                    {/* 기능 목록 */}
                    <ul className="flex flex-col gap-1.5 mb-5 flex-1">
                      {tier.features.map((f) => (
                        <li key={f} className="flex items-start gap-1.5">
                          <Check className="mt-0.5 h-3 w-3 shrink-0 text-green-500" />
                          <span className="text-xs text-gray-700 leading-tight">{f}</span>
                        </li>
                      ))}
                    </ul>

                    {/* 버튼 */}
                    <button
                      disabled={tier.disabled}
                      onClick={() => !tier.disabled && handlePayment(tier.name)}
                      className={`w-full rounded-xl py-2.5 text-xs font-bold transition-all ${tier.btnClass}`}
                    >
                      {tier.btnLabel}
                    </button>
                  </div>
                );
              })}
            </div>

            {/* 안내 문구 */}
            <div className="px-6 pb-6 text-center">
              <p className="text-xs text-[#B08B7A]">
                구독은 언제든 해지할 수 있어요 · 결제 기능은 출시 준비 중입니다
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
