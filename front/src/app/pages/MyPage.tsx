import { useMemo, useState } from "react";
import { motion } from "motion/react";
import {
  User,
  Plus,
  HeartPulse,
  MapPin,
  Sparkles,
  BookOpenText,
  Pencil,
  Eye,
  ChevronRight,
  Dog,
  CalendarDays,
  BadgeCheck,
} from "lucide-react";

type PetProfile = {
  id: number;
  name: string;
  breed: string;
  age: string;
  weight: string;
  gender?: "male" | "female";
  neutered?: "yes" | "no";
  personality?: string[];
  birthDate?: string;
  image?: string;
  nickname?: string;
};

const initialPets: PetProfile[] = [
  {
    id: 1,
    name: "콩이",
    breed: "말티즈",
    age: "5세",
    weight: "8.2kg",
    gender: "female",
    neutered: "yes",
    birthDate: "2020-05-12",
    nickname: "우리집 공주",
    personality: ["활발함", "산책 좋아함", "야외 선호"],
  },
  {
    id: 2,
    name: "보리",
    breed: "푸들",
    age: "3세",
    weight: "4.1kg",
    gender: "male",
    neutered: "no",
    birthDate: "2022-03-17",
    nickname: "말썽꾸러기",
    personality: ["호기심 많음", "사람 좋아함", "놀이 좋아함"],
  },
];

function getPersonalitySummary(personality?: string[]): string {
  if (!personality || personality.length === 0) {
    return "아직 성격 정보가 등록되지 않았어요. 성격 정보를 추가하면 더 정확한 추천을 받을 수 있어요.";
  }

  const traits = personality.join(", ");
  return `${traits} 등의 성향을 가지고 있어서, 그에 맞는 여행지와 활동을 추천해드릴게요.`;
}

function getPersonalityBadges(personality?: string[]): string[] {
  if (!personality || personality.length === 0) {
    return ["성격 정보 없음"];
  }

  const badges: string[] = [];

  const activeTraits = ["활발함", "에너지 넘침", "놀이 좋아함"];
  const outdoorTraits = ["산책 좋아함", "야외 선호", "자연 좋아함"];
  const socialTraits = ["사람 좋아함", "친화적", "사교적"];
  const curiousTraits = ["호기심 많음", "탐험 좋아함"];

  if (personality.some((p) => activeTraits.includes(p))) {
    badges.push("활동적");
  }
  if (personality.some((p) => outdoorTraits.includes(p))) {
    badges.push("야외형");
  }
  if (personality.some((p) => socialTraits.includes(p))) {
    badges.push("친화형");
  }
  if (personality.some((p) => curiousTraits.includes(p))) {
    badges.push("탐험형");
  }

  return badges.length > 0 ? badges : ["일반형"];
}

function PetFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialPet,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (pet: PetProfile) => void;
  initialPet?: PetProfile | null;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 p-6">
      <div className="mx-auto mt-10 max-w-xl rounded-[28px] bg-white p-8 shadow-2xl">
        <h2 className="text-2xl font-bold text-slate-900">
          {initialPet ? "반려동물 수정" : "반려동물 추가"}
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          기존 모달 컴포넌트로 교체해서 사용하면 돼.
        </p>

        <div className="mt-6 flex gap-3">
          <button
            type="button"
            className="rounded-2xl border border-slate-200 px-5 py-3"
            onClick={onClose}
          >
            닫기
          </button>

          <button
            type="button"
            className="rounded-2xl bg-orange-500 px-5 py-3 text-white"
            onClick={() => {
              onSubmit(
                initialPet ?? {
                  id: Date.now(),
                  name: "새 반려견",
                  breed: "견종 미입력",
                  age: "추가 정보 필요",
                  weight: "미입력",
                  gender: undefined,
                  neutered: undefined,
                  birthDate: "",
                  image: undefined,
                  nickname: "",
                  personality: [],
                }
              );
              onClose();
            }}
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}

function PetDetailModal({
  pet,
  onClose,
}: {
  pet: PetProfile | null;
  onClose: () => void;
}) {
  if (!pet) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 p-6" onClick={onClose}>
      <div
        className="mx-auto mt-8 max-w-2xl rounded-[32px] bg-white p-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-5">
          <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-3xl bg-gradient-to-br from-orange-100 to-amber-50">
            {pet.image ? (
              <img
                src={pet.image}
                alt={pet.name}
                className="h-full w-full object-cover"
              />
            ) : (
              <Dog className="h-10 w-10 text-orange-500" />
            )}
          </div>

          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-3xl font-bold text-slate-900">{pet.name}</h2>
              <span className="rounded-full bg-orange-50 px-3 py-1 text-sm font-semibold text-orange-600">
                {pet.gender === "male"
                  ? "수컷"
                  : pet.gender === "female"
                  ? "암컷"
                  : "성별 미입력"}
              </span>
            </div>

            <p className="mt-2 text-slate-500">
              {pet.nickname || "닉네임 미입력"} · {pet.breed}
            </p>
          </div>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">나이</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">{pet.age}</p>
          </div>

          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">몸무게</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">
              {pet.weight}
            </p>
          </div>

          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">중성화 여부</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">
              {pet.neutered === "yes"
                ? "했어요"
                : pet.neutered === "no"
                ? "안 했어요"
                : "미입력"}
            </p>
          </div>

          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">성격</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">
              {pet.personality?.length ? pet.personality.join(" / ") : "미입력"}
            </p>
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-2xl bg-slate-900 px-5 py-3 text-white"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

export default function MyPage() {
  const [pets, setPets] = useState<PetProfile[]>(initialPets);
  const [selectedPetId, setSelectedPetId] = useState<number>(
    initialPets[0]?.id ?? 0
  );
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editPet, setEditPet] = useState<PetProfile | null>(null);
  const [detailPet, setDetailPet] = useState<PetProfile | null>(null);

  const selectedPet = useMemo(
    () => pets.find((pet) => pet.id === selectedPetId) ?? pets[0] ?? null,
    [pets, selectedPetId]
  );

  const handleAddPet = (newPet: PetProfile) => {
    setPets((prev) => [...prev, newPet]);
    setSelectedPetId(newPet.id);
  };

  const handleUpdatePet = (updatedPet: PetProfile) => {
    setPets((prev) =>
      prev.map((pet) => (pet.id === updatedPet.id ? updatedPet : pet))
    );
    setSelectedPetId(updatedPet.id);
  };

  const profileCompletion = useMemo(() => {
    if (!selectedPet) return 0;

    const fields = [
      selectedPet.name,
      selectedPet.nickname,
      selectedPet.breed !== "견종 미입력" ? selectedPet.breed : "",
      selectedPet.birthDate,
      selectedPet.gender,
      selectedPet.neutered,
      selectedPet.image,
      selectedPet.personality?.length ? "personality" : "",
    ];

    const filled = fields.filter(Boolean).length;
    return Math.round((filled / fields.length) * 100);
  }, [selectedPet]);

  return (
    <div className="min-h-screen bg-[#f7f5f1] px-4 py-8 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="overflow-hidden rounded-[36px] bg-gradient-to-r from-[#fff7ef] via-white to-[#fff8f2] p-8 shadow-lg ring-1 ring-orange-100 lg:p-10"
        >
          <div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-orange-50 px-4 py-2 text-sm font-semibold text-orange-600">
                <User className="h-4 w-4" />
                마이페이지
              </div>

              <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900">
                반려견 프로필을 기반으로
                <br />
                여행 추천과 기록을 이어보세요
              </h1>

              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-500">
                세부 정보를 입력하면 AI 맞춤 여행 추천, 지도 탐색, AI 그림일기의
                성능이 더 좋아져요!
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:w-[420px]">
              <SummaryMiniCard label="내 반려동물" value={`${pets.length}마리`} />
              <SummaryMiniCard
                label="프로필 완성도"
                value={`${profileCompletion}%`}
              />
              <SummaryMiniCard
                label="현재 선택"
                value={selectedPet ? selectedPet.name : "없음"}
              />
            </div>
          </div>
        </motion.div>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1.5fr_1fr]">
          <div className="space-y-8">
            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="rounded-[32px] border border-orange-100 bg-white p-8 shadow-lg"
            >
              <div className="mb-6 flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">
                    반려동물 프로필
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    마이페이지 핵심 정보와 등록된 반려동물 목록
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setIsAddOpen(true)}
                  className="inline-flex shrink-0 items-center gap-2 rounded-2xl bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
                >
                  <Plus className="h-4 w-4" />
                  반려동물 추가
                </button>
              </div>

              <div className="-mx-1 overflow-x-auto pb-2 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
                <div className="flex w-max gap-5 px-1">
                  {pets.map((pet) => {
                    const selected = pet.id === selectedPetId;

                    return (
                      <button
                        key={pet.id}
                        type="button"
                        onClick={() => setSelectedPetId(pet.id)}
                        className={`w-[320px] shrink-0 overflow-hidden rounded-[28px] border p-5 text-left transition ${
                          selected
                            ? "border-orange-300 bg-orange-50/40 shadow-md"
                            : "border-slate-100 bg-white hover:border-orange-200 hover:shadow-sm"
                        }`}
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-3xl bg-gradient-to-br from-orange-100 to-amber-50">
                            {pet.image ? (
                              <img
                                src={pet.image}
                                alt={pet.name}
                                className="h-full w-full object-cover"
                              />
                            ) : (
                              <Dog className="h-8 w-8 text-orange-500" />
                            )}
                          </div>

                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="truncate text-xl font-bold text-slate-900">
                                {pet.name}
                              </h3>
                              {selected && (
                                <span className="rounded-full bg-orange-500 px-2 py-1 text-[11px] font-semibold text-white">
                                  선택됨
                                </span>
                              )}
                            </div>

                            <p className="mt-1 truncate text-sm text-slate-500">
                              {pet.nickname || "닉네임 미입력"}
                            </p>

                            <div className="mt-4 flex flex-wrap gap-2">
                              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                {pet.breed}
                              </span>

                              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                {pet.gender === "male"
                                  ? "수컷"
                                  : pet.gender === "female"
                                  ? "암컷"
                                  : "성별 미입력"}
                              </span>

                              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                {pet.neutered === "yes"
                                  ? "중성화 O"
                                  : pet.neutered === "no"
                                  ? "중성화 X"
                                  : "중성화 미입력"}
                              </span>

                              {pet.personality?.map((trait) => (
                                <span
                                  key={trait}
                                  className="rounded-full bg-orange-50 px-3 py-1 text-xs font-medium text-orange-600"
                                >
                                  {trait}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div className="mt-5 grid grid-cols-2 gap-3">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditPet(pet);
                            }}
                            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50"
                          >
                            <Pencil className="h-4 w-4" />
                            수정
                          </button>

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDetailPet(pet);
                            }}
                            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
                          >
                            <Eye className="h-4 w-4" />
                            상세보기
                          </button>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </motion.section>

            <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-[32px] border border-orange-100 bg-white p-8 shadow-lg"
          >
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-50 text-orange-600">
                <HeartPulse className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">
                  선택된 반려견 요약
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  추천과 기록의 기준이 되는 프로필 정보
                </p>
              </div>
            </div>
          
            {selectedPet ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
                  <div className="rounded-[24px] bg-[#F6F7FB] p-5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
                      <Dog className="h-5 w-5" />
                    </div>
                    <p className="mt-4 text-sm text-slate-500">견종</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {selectedPet.breed}
                    </p>
                  </div>
          
                  <div className="rounded-[24px] bg-[#F6F7FB] p-5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
                      <CalendarDays className="h-5 w-5" />
                    </div>
                    <p className="mt-4 text-sm text-slate-500">나이</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {selectedPet.age}
                    </p>
                  </div>
          
                  <div className="rounded-[24px] bg-[#F6F7FB] p-5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
                      <BadgeCheck className="h-5 w-5" />
                    </div>
                    <p className="mt-4 text-sm text-slate-500">성별</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {selectedPet.gender === "male"
                        ? "수컷"
                        : selectedPet.gender === "female"
                        ? "암컷"
                        : "미입력"}
                    </p>
                  </div>
          
                  <div className="rounded-[24px] bg-[#F6F7FB] p-5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
                      <HeartPulse className="h-5 w-5" />
                    </div>
                    <p className="mt-4 text-sm text-slate-500">중성화 여부</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {selectedPet.neutered === "yes"
                        ? "했어요"
                        : selectedPet.neutered === "no"
                        ? "안 했어요"
                        : "미입력"}
                    </p>
                  </div>
                </div>
          
                <div className="rounded-[28px] bg-[#FCF6EA] p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-orange-500">성향 분석</p>
                      <h3 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
                        {selectedPet.name}는 이런 성격이에요
                      </h3>
                      <p className="mt-4 text-base leading-7 text-slate-600">
                        {getPersonalitySummary(selectedPet.personality)}
                      </p>
                    </div>
          
                    <div className="min-w-[92px] rounded-[20px] border border-slate-200 bg-white px-5 py-4 text-center shadow-sm">
                      <p className="text-xs text-slate-400">등록된 성격</p>
                      <p className="mt-1 text-4xl font-bold text-orange-500">
                        {selectedPet.personality?.length ?? 0}
                      </p>
                    </div>
                  </div>
          
                  <div className="mt-5 flex flex-wrap gap-2">
                    {getPersonalityBadges(selectedPet.personality).map((badge) => (
                      <span
                        key={badge}
                        className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-orange-600"
                      >
                        {badge}
                      </span>
                    ))}
                  </div>
          
                  <div className="mt-5 flex flex-wrap gap-2">
                    {(selectedPet.personality ?? []).map((trait) => (
                      <span
                        key={trait}
                        className="rounded-full bg-[#F8E7CC] px-4 py-2 text-sm font-medium text-orange-600"
                      >
                        #{trait}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-3xl bg-slate-50 p-8 text-center text-slate-500">
                등록된 반려동물이 없어요.
              </div>
            )}
          </motion.section>
          </div>

          <div className="space-y-8">
            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="rounded-[32px] border border-orange-100 bg-white p-8 shadow-lg"
            >
              <h2 className="text-2xl font-bold text-slate-900">빠른 실행</h2>
              <p className="mt-1 text-sm text-slate-500">
                선택된 반려견 기준으로 바로 이동할 수 있는 기능
              </p>

              <div className="mt-6 space-y-3">
                <QuickLinkCard
                  icon={<Sparkles className="h-5 w-5" />}
                  title="여행 추천 받기"
                  desc="반려견 성향 기반 추천 시작"
                />
                <QuickLinkCard
                  icon={<MapPin className="h-5 w-5" />}
                  title="지도에서 장소 탐색"
                  desc="동반 가능 여행지/장소 보기"
                />
                <QuickLinkCard
                  icon={<BookOpenText className="h-5 w-5" />}
                  title="AI 그림일기 만들기"
                  desc="여행 후 기록을 감성 콘텐츠로 생성"
                />
              </div>
            </motion.section>

            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="rounded-[32px] border border-orange-100 bg-white p-8 shadow-lg"
            >
              <h2 className="text-2xl font-bold text-slate-900">
                프로필 완성 안내
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                정보가 많을수록 추천 정확도가 높아져요
              </p>

              <div className="mt-6">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-slate-500">완성도</span>
                  <span className="font-semibold text-slate-900">
                    {profileCompletion}%
                  </span>
                </div>

                <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-orange-500 transition-all"
                    style={{ width: `${profileCompletion}%` }}
                  />
                </div>
              </div>

              <div className="mt-6 rounded-3xl bg-orange-50 p-5 text-sm leading-6 text-orange-700">
                생년월일, 성별, 중성화, 견종, 사진, 성격까지 채우면
                <br />
                추천/기록 기능에서 더 자연스럽게 활용할 수 있어요.
              </div>
            </motion.section>
          </div>
        </div>
      </div>

      <PetFormModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onSubmit={handleAddPet}
      />

      <PetFormModal
        isOpen={Boolean(editPet)}
        onClose={() => setEditPet(null)}
        onSubmit={handleUpdatePet}
        initialPet={editPet}
      />

      <PetDetailModal pet={detailPet} onClose={() => setDetailPet(null)} />
    </div>
  );
}

function SummaryMiniCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-orange-100 bg-white/80 p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

function InfoCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[28px] bg-slate-50 p-5">
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
        {icon}
      </div>
      <p className="mt-4 text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function QuickLinkCard({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <button
      type="button"
      className="flex w-full items-center gap-4 rounded-[24px] border border-slate-200 bg-white px-5 py-4 text-left transition hover:border-orange-200 hover:bg-orange-50/40"
    >
      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-orange-50 text-orange-600">
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-slate-900">{title}</p>
        <p className="mt-1 text-sm text-slate-500">{desc}</p>
      </div>
      <ChevronRight className="h-5 w-5 text-slate-400" />
    </button>
  );
}