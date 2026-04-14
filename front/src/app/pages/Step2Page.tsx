import { useEffect, useMemo, useRef, useState } from "react";
import {
  Camera,
  ChevronRight,
  MoreHorizontal,
  Search,
  X,
} from "lucide-react";

type GuardianGender = "male" | "female" | "other" | undefined;
type PetGender = "male" | "female" | undefined;
type Neutered = "yes" | "no" | undefined;

type ProfileSetupData = {
  guardianName: string;
  guardianBirth: string;
  guardianGender: GuardianGender;
  petName: string;
  birthDate: string;
  breed: string;
  petGender: PetGender;
  neutered: Neutered;
  personality: string[];
  image?: string;
};

const popularBreeds = [
  "말티즈",
  "포메라니안",
  "푸들",
  "비숑 프리제",
  "시추",
  "골든 리트리버",
  "라브라도 리트리버",
  "웰시코기",
  "프렌치 불독",
  "진돗개",
  "닥스훈트",
  "치와와",
  "믹스",
];

const allBreeds = [
  "골든 리트리버",
  "그레이하운드",
  "그레이트 데인",
  "그레이트 피레니즈",
  "닥스훈트",
  "달마시안",
  "도베르만",
  "라브라도 리트리버",
  "라사 압소",
  "말티즈",
  "맨체스터 테리어",
  "마스티프",
  "미니어처 슈나우저",
  "미니어처 핀셔",
  "바센지",
  "바셋 하운드",
  "버니즈 마운틴 독",
  "보더 콜리",
  "비숑 프리제",
  "사모예드",
  "시바 이누",
  "시추",
  "아메리칸 코커 스패니얼",
  "아키타",
  "요크셔 테리어",
  "웰시코기",
  "진돗개",
  "치와와",
  "코커 스패니얼",
  "콜리",
  "퍼그",
  "포메라니안",
  "푸들",
  "프렌치 불독",
  "믹스",
];

const personalityOptions = [
  "활발",
  "얌전",
  "애교",
  "독립적",
  "낯가림",
  "낯선사람 좋아함",
  "사람 좋아함",
  "사람 싫어함",
  "겁이 많음",
  "용감함",
  "호기심천국",
  "고집쟁이",
  "예민함",
  "음식 좋아함",
  "잘 짖음",
  "산책 좋아함",
  "야외 선호",
  "실내 선호",
  "장난감 좋아함",
  "공놀이 좋아함",
  "다른 강아지 좋아함",
  "혼자 있는 거 잘함",
  "안기는 거 좋아함",
  "훈련 잘 따라옴",
];

const previewPersonalityOptions = personalityOptions.slice(0, 10);

const defaultData: ProfileSetupData = {
  guardianName: "",
  guardianBirth: "",
  guardianGender: undefined,
  petName: "",
  birthDate: "",
  breed: "",
  petGender: undefined,
  neutered: undefined,
  personality: [],
  image: undefined,
};

function getPersonalitySummary(traits: string[] = []) {
  if (traits.includes("활발") && traits.includes("산책 좋아함")) {
    return "에너지 넘치고 바깥 활동을 좋아하는 타입";
  }
  if (traits.includes("얌전") && traits.includes("낯가림")) {
    return "조용하고 신중하게 친해지는 타입";
  }
  if (traits.includes("사람 좋아함") && traits.includes("애교")) {
    return "사람을 좋아하고 표현이 많은 타입";
  }
  if (traits.includes("독립적") && traits.includes("혼자 있는 거 잘함")) {
    return "혼자서도 안정감 있게 지내는 타입";
  }
  if (traits.includes("호기심천국") || traits.includes("장난감 좋아함")) {
    return "새로운 것에 관심이 많고 탐색을 즐기는 타입";
  }
  if (traits.includes("예민함") || traits.includes("겁이 많음")) {
    return "환경 변화에 민감하고 세심한 케어가 필요한 타입";
  }
  return traits.length
    ? `성격 키워드 ${traits.length}개가 등록된 반려견`
    : "아직 성격 정보가 없어요";
}

function getPersonalityBadges(traits: string[] = []) {
  const groups = [
    { label: "활동형", keywords: ["활발", "산책 좋아함", "공놀이 좋아함", "야외 선호"] },
    { label: "애교형", keywords: ["애교", "사람 좋아함", "안기는 거 좋아함", "낯선사람 좋아함"] },
    { label: "신중형", keywords: ["얌전", "낯가림", "겁이 많음", "예민함"] },
    { label: "독립형", keywords: ["독립적", "혼자 있는 거 잘함", "실내 선호"] },
    { label: "탐험형", keywords: ["호기심천국", "용감함", "장난감 좋아함", "훈련 잘 따라옴"] },
  ];

  return groups
    .filter((group) => group.keywords.some((keyword) => traits.includes(keyword)))
    .map((group) => group.label);
}

function SegButton({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex h-12 w-full items-center justify-center rounded-2xl border text-base font-semibold transition ${
        active
          ? "border-[#E86A2C] bg-[#FFF2EA] text-[#D45E23]"
          : "border-[#E6E1DB] bg-white text-[#9B948B] hover:border-[#F1B18C]"
      }`}
    >
      {children}
    </button>
  );
}

function Chip({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
        active
          ? "border-[#E86A2C] bg-[#FFF2EA] text-[#D45E23]"
          : "border-[#E6E1DB] bg-white text-[#7B746B] hover:border-[#F1B18C] hover:text-[#D45E23]"
      }`}
    >
      {children}
    </button>
  );
}

function BreedModal({
  isOpen,
  onClose,
  onSelect,
  selectedBreed,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (breed: string) => void;
  selectedBreed: string;
}) {
  const [keyword, setKeyword] = useState("");

  useEffect(() => {
    if (!isOpen) setKeyword("");
  }, [isOpen]);

  const filteredBreeds = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    if (!q) return allBreeds;
    return allBreeds.filter((breed) => breed.toLowerCase().includes(q));
  }, [keyword]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/25 px-4 py-10" onClick={onClose}>
      <div
        className="mx-auto flex max-h-[82vh] w-full max-w-3xl flex-col overflow-hidden rounded-[32px] bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 px-6 pb-4 pt-6 md:px-8">
          <div>
            <h2 className="text-[32px] font-bold tracking-tight text-[#3F3A35]">견종 선택</h2>
            <p className="mt-2 text-base text-[#8D867E]">
              이름으로 검색하거나 목록에서 선택하세요
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="grid h-12 w-12 place-items-center rounded-full bg-[#F4F1EE] text-[#8A837B]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="px-6 md:px-8">
          <div className="flex h-16 items-center gap-3 rounded-[24px] border-2 border-[#F0A777] bg-white px-5">
            <Search className="h-5 w-5 text-[#8D867E]" />
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="견종 이름 검색..."
              className="w-full bg-transparent text-lg outline-none placeholder:text-[#B5AFA8]"
            />
          </div>
        </div>

        <div className="mt-6 overflow-y-auto px-6 pb-8 md:px-8">
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 pr-2">
            {filteredBreeds.map((breed) => {
              const active = selectedBreed === breed;
              return (
                <button
                  key={breed}
                  type="button"
                  onClick={() => {
                    onSelect(breed);
                    onClose();
                  }}
                  className={`rounded-[16px] px-4 py-4 text-left text-[18px] font-medium transition ${
                    active
                      ? "bg-[#F7E8E1] text-[#C65B27]"
                      : "text-[#5F5A55] hover:bg-[#F7F4F1]"
                  }`}
                >
                  {breed}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function PersonalityModal({
  isOpen,
  onClose,
  selectedItems,
  onToggle,
}: {
  isOpen: boolean;
  onClose: () => void;
  selectedItems: string[];
  onToggle: (item: string) => void;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/25 px-4 py-10" onClick={onClose}>
      <div
        className="mx-auto flex max-h-[82vh] w-full max-w-3xl flex-col overflow-hidden rounded-[32px] bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 px-6 pb-4 pt-6 md:px-8">
          <div>
            <h2 className="text-[28px] font-bold tracking-tight text-[#3F3A35]">성격 더보기</h2>
            <p className="mt-2 text-sm text-[#8D867E]">
              원하는 성격을 자유롭게 선택해 주세요 (최대 5개)
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="grid h-12 w-12 place-items-center rounded-full bg-[#F4F1EE] text-[#8A837B]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="overflow-y-auto px-6 pb-8 md:px-8">
          <div className="flex flex-wrap gap-3">
            {personalityOptions.map((item) => (
              <Chip
                key={item}
                active={selectedItems.includes(item)}
                onClick={() => onToggle(item)}
              >
                {item}
              </Chip>
            ))}
          </div>
        </div>

        <div className="border-t border-[#F0ECE7] px-6 py-4 md:px-8">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-[16px] bg-[#DB5F2E] px-6 py-4 text-base font-bold text-white transition hover:bg-[#D05523]"
          >
            선택 완료
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ProfileSetupPage() {
  const [form, setForm] = useState<ProfileSetupData>({
    ...defaultData,
    guardianName: "",
    guardianBirth: "",
    guardianGender: "male",
    petName: "코코",
    breed: "말티즈",
    petGender: "female",
    neutered: "yes",
  });

  const [isBreedModalOpen, setIsBreedModalOpen] = useState(false);
  const [isPersonalityModalOpen, setIsPersonalityModalOpen] = useState(false);
  const [personalityError, setPersonalityError] = useState("");
  const fileRef = useRef<HTMLInputElement | null>(null);

  const formatDateInput = (value: string) => {
    const onlyNumbers = value.replace(/\D/g, "").slice(0, 8);
    let formatted = onlyNumbers;

    if (onlyNumbers.length > 4) {
      formatted = `${onlyNumbers.slice(0, 4)}-${onlyNumbers.slice(4, 6)}`;
    }
    if (onlyNumbers.length > 6) {
      formatted = `${onlyNumbers.slice(0, 4)}-${onlyNumbers.slice(4, 6)}-${onlyNumbers.slice(6, 8)}`;
    }

    return formatted;
  };

  const togglePersonality = (item: string) => {
    setPersonalityError("");

    setForm((prev) => {
      if (prev.personality.includes(item)) {
        return {
          ...prev,
          personality: prev.personality.filter((value) => value !== item),
        };
      }

      if (prev.personality.length >= 5) {
        setPersonalityError("성격은 최대 5개까지 선택할 수 있어요.");
        return prev;
      }

      return {
        ...prev,
        personality: [...prev.personality, item],
      };
    });
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result === "string") {
        const result = reader.result;
        setForm((prev) => ({ ...prev, image: result }));
      }
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  const handleStart = () => {
    console.log("프로필 설정 완료", form);
  };

  return (
    <div className="min-h-screen bg-[#F6F1EC]">
      <header className="border-b-[3px] border-[#3DA0FF] bg-[#F6F1EC] px-4 py-4 text-center">
        <h1 className="text-sm font-bold tracking-tight text-[#2F2B27]">프로필 설정</h1>
      </header>

      <main className="mx-auto max-w-[780px] px-4 py-10">
        <div className="mx-auto max-w-[520px] space-y-6">
          <section className="rounded-[18px] border border-[#DDD6CF] bg-white px-6 py-5 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
            <h2 className="text-[16px] font-bold text-[#37322D]">보호자 정보</h2>

            <div className="mt-4">
              <label className="mb-2 block text-xs font-medium text-[#8D867E]">닉네임</label>
              <input
                value={form.guardianName}
                onChange={(e) => setForm((prev) => ({ ...prev, guardianName: e.target.value }))}
                placeholder="보호자님"
                className="h-12 w-full rounded-[10px] border border-[#E3DDD7] px-4 text-sm outline-none placeholder:text-[#BBB3AB] focus:border-[#F0A777]"
              />
            </div>

            <div className="mt-4">
              <label className="mb-2 block text-xs font-medium text-[#8D867E]">생년월일</label>
              <input
                type="text"
                value={form.guardianBirth}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    guardianBirth: formatDateInput(e.target.value),
                  }))
                }
                inputMode="numeric"
                maxLength={10}
                placeholder="연도-월-일"
                className="h-12 w-full rounded-[10px] border border-[#E3DDD7] px-4 text-sm outline-none placeholder:text-[#BBB3AB] focus:border-[#F0A777]"
              />
            </div>

            <div className="mt-4">
              <label className="mb-2 block text-xs font-medium text-[#8D867E]">성별</label>
              <div className="flex justify-center gap-3">
                <div className="w-44">
                  <SegButton
                    active={form.guardianGender === "male"}
                    onClick={() => setForm((prev) => ({ ...prev, guardianGender: "male" }))}
                  >
                    남성
                  </SegButton>
                </div>
                <div className="w-44">
                  <SegButton
                    active={form.guardianGender === "female"}
                    onClick={() => setForm((prev) => ({ ...prev, guardianGender: "female" }))}
                  >
                    여성
                  </SegButton>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-[18px] border border-[#DDD6CF] bg-white px-6 py-5 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
            <h2 className="text-[16px] font-bold text-[#37322D]">반려견 정보</h2>

            <div className="mt-6 flex justify-center">
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleImageChange}
              />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="flex flex-col items-center"
              >
                <div className="flex h-[72px] w-[72px] items-center justify-center overflow-hidden rounded-full bg-[#F6E5D4] text-[#C27A37] shadow-sm">
                  {form.image ? (
                    <img src={form.image} alt="반려견" className="h-full w-full object-cover" />
                  ) : (
                    <Camera className="h-6 w-6" />
                  )}
                </div>
                <span className="mt-3 text-[11px] text-[#A19A92]">클릭하여 사진 추가</span>
              </button>
            </div>

            <div className="mt-6 space-y-5">
              <div>
                <label className="mb-2 block text-xs font-medium text-[#8D867E]">강아지 이름</label>
                <input
                  value={form.petName}
                  onChange={(e) => setForm((prev) => ({ ...prev, petName: e.target.value }))}
                  placeholder="예: 코코"
                  className="h-12 w-full rounded-[10px] border border-[#F0C7B0] px-4 text-sm outline-none placeholder:text-[#BBB3AB] focus:border-[#F0A777]"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium text-[#8D867E]">생년월일</label>
                <input
                  type="text"
                  value={form.birthDate}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      birthDate: formatDateInput(e.target.value),
                    }))
                  }
                  inputMode="numeric"
                  maxLength={10}
                  placeholder="연도-월-일"
                  className="h-12 w-full rounded-[14px] border border-[#F0C7B0] px-4 text-sm outline-none placeholder:text-[#BBB3AB] focus:border-[#F0A777]"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium text-[#8D867E]">견종</label>
                <button
                  type="button"
                  onClick={() => setIsBreedModalOpen(true)}
                  className="flex h-12 w-full items-center justify-between rounded-[14px] border border-[#F0C7B0] px-4 text-left"
                >
                  <span className={`text-sm ${form.breed ? "text-[#2F2B27]" : "text-[#BBB3AB]"}`}>
                    {form.breed || "견종을 선택해주세요"}
                  </span>
                  <ChevronRight className="h-4 w-4 text-[#C08A60]" />
                </button>

                <p className="mb-3 mt-4 text-xs font-medium text-[#C18A61]">인기 견종</p>
                <div className="flex flex-wrap gap-2">
                  {popularBreeds.map((breed) => (
                    <Chip
                      key={breed}
                      active={form.breed === breed}
                      onClick={() => setForm((prev) => ({ ...prev, breed }))}
                    >
                      {breed}
                    </Chip>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium text-[#8D867E]">성별</label>
                <div className="grid grid-cols-2 gap-3">
                  <SegButton
                    active={form.petGender === "male"}
                    onClick={() => setForm((prev) => ({ ...prev, petGender: "male" }))}
                  >
                    남아
                  </SegButton>
                  <SegButton
                    active={form.petGender === "female"}
                    onClick={() => setForm((prev) => ({ ...prev, petGender: "female" }))}
                  >
                    여아
                  </SegButton>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium text-[#8D867E]">중성화 여부</label>
                <div className="grid grid-cols-2 gap-3">
                  <SegButton
                    active={form.neutered === "yes"}
                    onClick={() => setForm((prev) => ({ ...prev, neutered: "yes" }))}
                  >
                    O
                  </SegButton>
                  <SegButton
                    active={form.neutered === "no"}
                    onClick={() => setForm((prev) => ({ ...prev, neutered: "no" }))}
                  >
                    X
                  </SegButton>
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label className="block text-xs font-medium text-[#8D867E]">
                    성격 (중복 선택 가능)
                  </label>
                  <span className="text-xs font-semibold text-[#D45E23]">
                    {form.personality.length}/5
                  </span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {previewPersonalityOptions.map((item) => (
                    <Chip
                      key={item}
                      active={form.personality.includes(item)}
                      onClick={() => togglePersonality(item)}
                    >
                      {item}
                    </Chip>
                  ))}

                  <button
                    type="button"
                    onClick={() => setIsPersonalityModalOpen(true)}
                    className="inline-flex items-center gap-2 rounded-full border border-[#E6E1DB] bg-white px-4 py-2 text-sm font-medium text-[#7B746B] transition hover:border-[#F1B18C] hover:text-[#D45E23]"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                    성격 더보기
                  </button>
                </div>

                {form.personality.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {form.personality.map((item) => (
                      <span
                        key={item}
                        className="rounded-full bg-[#FFF2EA] px-3 py-1 text-xs font-semibold text-[#D45E23] ring-1 ring-[#F3D3BF]"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                )}

                {personalityError && (
                  <p className="mt-2 text-xs text-red-500">{personalityError}</p>
                )}
              </div>

              <div className="rounded-[18px] bg-[#FFF5EE] p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold text-[#D45E23]">성격 요약</p>
                    <p className="mt-1 text-sm leading-6 text-[#5E5750]">
                      {getPersonalitySummary(form.personality)}
                    </p>
                  </div>
                  <div className="rounded-[14px] bg-white px-3 py-2 text-center shadow-sm">
                    <p className="text-[10px] text-[#A29A91]">선택</p>
                    <p className="text-lg font-bold text-[#D45E23]">{form.personality.length}</p>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {getPersonalityBadges(form.personality).map((badge) => (
                    <span
                      key={badge}
                      className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-[#D45E23] ring-1 ring-[#F3D3BF]"
                    >
                      {badge}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <button
            type="button"
            onClick={handleStart}
            className="w-full rounded-[16px] bg-[#DB5F2E] px-6 py-5 text-lg font-bold text-white shadow-sm transition hover:bg-[#D05523]"
          >
            시작하기! 🐾
          </button>
        </div>
      </main>

      <BreedModal
        isOpen={isBreedModalOpen}
        onClose={() => setIsBreedModalOpen(false)}
        onSelect={(breed) => setForm((prev) => ({ ...prev, breed }))}
        selectedBreed={form.breed}
      />

      <PersonalityModal
        isOpen={isPersonalityModalOpen}
        onClose={() => setIsPersonalityModalOpen(false)}
        selectedItems={form.personality}
        onToggle={togglePersonality}
      />
    </div>
  );
}