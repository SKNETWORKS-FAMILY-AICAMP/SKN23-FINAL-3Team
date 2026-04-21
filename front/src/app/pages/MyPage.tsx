import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import {
  Settings,
  Plus,
  HeartPulse,
  Pencil,
  Eye,
  Dog,
  CalendarDays,
  BadgeCheck,
  Lock,
  LogIn,
  Save,
} from "lucide-react";
import { getMe, type UserProfile } from "../services/userService";
import { getPets, type Pet } from "../services/petService";
import { getAllBreeds, type Breed } from "../services/breedService";
import { getImage } from "../services/imageService";
import { useNavigate } from "react-router";

// ── 마이페이지 전용 타입 ──────────────────────────────────────────────────────

type PetCard = {
  id: number;
  name: string;
  breedName: string;
  ageLabel: string;
  gender: "MALE" | "FEMALE" | null;
  isNeutered: boolean | null;
  selectedTags: string[];
  birthDate: string | null;
};

// ── 헬퍼 ─────────────────────────────────────────────────────────────────────

function toAgeLabel(age: number | null | undefined): string {
  if (age == null) return "나이 미입력";
  if (age === 0) return "1살 미만";
  return `${age}세`;
}



// ── 상세보기 모달 ─────────────────────────────────────────────────────────────

function PetDetailModal({ pet, onClose, petPhotos }: { pet: PetCard | null; onClose: () => void; petPhotos: Record<number, string> }) {
  if (!pet) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 p-6" onClick={onClose}>
      <div
        className="mx-auto mt-8 max-w-2xl rounded-[32px] bg-white p-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-5">
          <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-3xl bg-gradient-to-br from-orange-100 to-amber-50">
            {petPhotos[pet.id] ? (
              <img src={petPhotos[pet.id]} alt={pet.name} className="h-full w-full object-cover" />
            ) : (
              <Dog className="h-10 w-10 text-orange-500" />
            )}
          </div>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-3xl font-bold text-slate-900">{pet.name}</h2>
              <span className="rounded-full bg-orange-50 px-3 py-1 text-sm font-semibold text-orange-600">
                {pet.gender === "MALE" ? "수컷" : pet.gender === "FEMALE" ? "암컷" : "성별 미입력"}
              </span>
            </div>
            <p className="mt-2 text-slate-500">{pet.breedName}</p>
          </div>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">나이</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">{pet.ageLabel}</p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">생년월일</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">{pet.birthDate ?? "미입력"}</p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">중성화 여부</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">
              {pet.isNeutered === true ? "했어요" : pet.isNeutered === false ? "안 했어요" : "미입력"}
            </p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-5">
            <p className="text-sm text-slate-500">성격</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">
              {pet.selectedTags.length ? pet.selectedTags.join(" / ") : "미입력"}
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

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────

export default function MyPage() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem('access_token'));
  const [user, setUser] = useState<UserProfile | null>(null);
  const [pets, setPets] = useState<PetCard[]>([]);
  const [rawPets, setRawPets] = useState<Pet[]>([]);
  const [profilePhoto, setProfilePhoto] = useState<string | null>(null);
  const [petPhotos, setPetPhotos] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [selectedPetId, setSelectedPetId] = useState<number | null>(
    () => Number(localStorage.getItem('selected_pet_id')) || null
  );
  const [detailPet, setDetailPet] = useState<PetCard | null>(null);
  const [savedPetId, setSavedPetId] = useState<number | null>(
    () => Number(localStorage.getItem('selected_pet_id')) || null
  );

  // auth-change 이벤트(토큰 만료/로그아웃) 감지
  useEffect(() => {
    const sync = () => setIsLoggedIn(!!localStorage.getItem('access_token'));
    window.addEventListener('auth-change', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('auth-change', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  useEffect(() => {
    if (!isLoggedIn) {
      setLoading(false);
      return;
    }
    const load = async () => {
      try {
        const [me, breeds] = await Promise.all([getMe(), getAllBreeds()]);
        setUser(me);
        const savedPhoto = localStorage.getItem(`profile_photo_${me.id}`);
        if (savedPhoto) setProfilePhoto(savedPhoto);

        const breedMap = new Map<number, string>(breeds.map((b: Breed) => [b.id, b.name_ko]));

        const fetchedPets: Pet[] = await getPets(me.id);
        setRawPets(fetchedPets);
        const cards: PetCard[] = fetchedPets.map((p) => ({
          id: p.id,
          name: p.name,
          breedName: breedMap.get(p.breed_id) ?? `견종 ID ${p.breed_id}`,
          ageLabel: toAgeLabel(p.age),
          gender: p.gender ?? null,
          isNeutered: p.is_neutered ?? null,
          selectedTags: Array.isArray(p.selected_tags) ? p.selected_tags : [],
          birthDate: p.birth_date ?? null,
        }));
        setPets(cards);
        if (cards.length) {
          const savedId = Number(localStorage.getItem('selected_pet_id')) || null;
          const initialPet = savedId ? cards.find((c) => c.id === savedId) : null;
          setSelectedPetId(initialPet?.id ?? cards[0].id);
        }

        // localStorage 우선, 없으면 profile_id로 백엔드에서 가져와 캐시
        const photos: Record<number, string> = {};
        let backendUrl: string | null = null;
        for (const p of fetchedPets) {
          const cached = localStorage.getItem(`pet_photo_${p.id}`);
          if (cached) {
            photos[p.id] = cached;
          } else {
            if (backendUrl === null && me.profile_id) {
              try {
                const img = await getImage(me.profile_id);
                backendUrl = img.url;
              } catch { backendUrl = ''; }
            }
            if (backendUrl) {
              localStorage.setItem(`pet_photo_${p.id}`, backendUrl);
              photos[p.id] = backendUrl;
            }
          }
        }
        setPetPhotos(photos);
      } catch (err) {
        console.error("마이페이지 로드 실패", err);
        // 401로 인해 token이 이미 삭제된 경우 isLoggedIn이 false로 바뀌므로 별도 처리 불필요
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [isLoggedIn]);

  const [saveSuccess, setSaveSuccess] = useState(false);

  // 외부 저장 버튼 클릭 → localStorage 갱신 + 전체 컴포넌트 동기화
  const handleSavePet = () => {
    if (!selectedPetId) return;
    setSavedPetId(selectedPetId);
    localStorage.setItem('selected_pet_id', String(selectedPetId));
    window.dispatchEvent(new Event('pet-select-change'));
    setSaveSuccess(true);
  };

  const selectedPet = useMemo(
    () => pets.find((p) => p.id === selectedPetId) ?? pets[0] ?? null,
    [pets, selectedPetId]
  );

  // ── 비로그인 상태 ────────────────────────────────────────────────────────────
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-[#f7f5f1]">
        {/* 흐린 배경 레이아웃 (미리보기) */}
        <div className="pointer-events-none select-none opacity-30 blur-sm">
          <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
            <div className="overflow-hidden rounded-[36px] bg-gradient-to-r from-[#fff7ef] via-white to-[#fff8f2] p-8 shadow-lg ring-1 ring-orange-100">
              <div className="h-8 w-48 rounded-full bg-orange-100" />
              <div className="mt-4 h-10 w-80 rounded-xl bg-slate-200" />
              <div className="mt-3 h-5 w-64 rounded-lg bg-slate-100" />
            </div>
            <div className="mt-8 rounded-[32px] border border-orange-100 bg-white p-8 shadow-lg">
              <div className="h-8 w-40 rounded-xl bg-slate-200" />
              <div className="mt-6 flex gap-4">
                {[1, 2].map((i) => (
                  <div key={i} className="h-48 w-72 rounded-[28px] bg-slate-100" />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 로그인 요청 오버레이 */}
        <div className="absolute inset-0 flex items-center justify-center px-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.25 }}
            className="w-full max-w-sm overflow-hidden rounded-[32px] bg-white shadow-2xl ring-1 ring-orange-100"
          >
            {/* 상단 오렌지 배너 */}
            <div className="bg-gradient-to-br from-orange-400 to-orange-500 px-8 py-10 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-white/20">
                <Lock className="h-8 w-8 text-white" />
              </div>
              <h2 className="mt-4 text-2xl font-bold text-white">로그인이 필요해요</h2>
              <p className="mt-2 text-sm text-orange-100">
                마이페이지는 로그인 후 이용할 수 있어요
              </p>
            </div>

            {/* 안내 메시지 */}
            <div className="px-8 py-6">
              <ul className="space-y-3 text-sm text-slate-600">
                {[
                  "🐾 반려견 프로필 등록 및 관리",
                  "🗺️ AI 맞춤 여행지 추천",
                  "📔 AI 그림일기 생성",
                  "📅 멍캘린더 일정 관리",
                ].map((text) => (
                  <li key={text} className="flex items-center gap-2">
                    <span>{text}</span>
                  </li>
                ))}
              </ul>

              <button
                type="button"
                onClick={() => navigate("/login")}
                className="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-orange-500 py-4 text-base font-bold text-white transition hover:bg-orange-600 active:scale-95"
              >
                <LogIn className="h-5 w-5" />
                로그인 하러 가기
              </button>

              <p className="mt-4 text-center text-xs text-slate-400">
                소셜 로그인(카카오 · 구글 · 네이버)으로 간편 가입
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f7f5f1]">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-orange-400 border-t-transparent" />
          <p className="mt-4 text-slate-500">불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f7f5f1] px-4 py-8 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* 헤더 */}
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="overflow-hidden rounded-[36px] bg-gradient-to-r from-[#fff7ef] via-white to-[#fff8f2] p-8 shadow-lg ring-1 ring-orange-100 lg:p-10"
        >
          <div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-center">
            {/* 왼쪽: 프로필 사진 + 인사말 */}
            <div className="flex items-center gap-6">
              <div className="relative shrink-0">
                <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-orange-100 to-amber-50 shadow-md ring-4 ring-orange-200">
                  {(() => {
                    const photo = (selectedPetId ? petPhotos[selectedPetId] : null) ?? profilePhoto;
                    return photo ? (
                      <img src={photo} alt="프로필" className="h-full w-full object-cover" />
                    ) : (
                      <Dog className="h-12 w-12 text-orange-400" />
                    );
                  })()}
                </div>
                <span className="absolute bottom-0 right-0 flex h-7 w-7 items-center justify-center rounded-full bg-orange-500 text-sm shadow">
                  🐾
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  {user?.provider && (
                    <ProviderBadge provider={user.provider} />
                  )}
                </div>
                <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">
                  {user?.nickname ?? "보호자"}님 안녕하세요! 👋
                </h1>
                <p className="mt-2 text-base text-slate-500">
                  오늘은 {selectedPet?.name ?? "반려견"}과 어떤 기록을 이어가볼까요?
                </p>
                {user?.email && (
                  <p className="mt-1 text-sm text-slate-400">{user.email}</p>
                )}
              </div>
            </div>

            {/* 오른쪽: 요약 + 수정 버튼 */}
            <div className="flex flex-col items-start gap-3 lg:items-end">
              <button
                type="button"
                onClick={() =>
                  navigate("/step", {
                    state: {
                      editMode: true,
                      userId: user?.id,
                      petId: selectedPet?.id,
                      userData: {
                        nickname: user?.nickname ?? "",
                        gender: user?.gender ?? null,
                        birth_date: user?.birth_date ?? "",
                      },
                      petData: {
                        name: selectedPet?.name ?? "",
                        breed_id: rawPets.find((p) => p.id === selectedPet?.id)?.breed_id ?? null,
                        breed_name: selectedPet?.breedName ?? "",
                        birth_date: selectedPet?.birthDate ?? "",
                        gender: selectedPet?.gender ?? null,
                        is_neutered: selectedPet?.isNeutered ?? null,
                        selected_tags: selectedPet?.selectedTags ?? [],
                      },
                    },
                  })
                }
                className="inline-flex items-center gap-2 rounded-2xl border border-orange-200 bg-white px-5 py-2.5 text-sm font-semibold text-orange-600 shadow-sm transition hover:bg-orange-50"
              >
                <Settings className="h-4 w-4" />
                회원정보 수정
              </button>
              <div className="grid grid-cols-2 gap-3">
                <SummaryMiniCard label="내 반려견" value={`${pets.length}마리`} />
                <SummaryMiniCard label="현재 선택" value={selectedPet?.name ?? "없음"} />
              </div>
            </div>
          </div>
        </motion.div>

        <div className="mt-8 space-y-8">
          {/* 반려견 프로필 카드 목록 */}
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="rounded-[32px] border border-orange-100 bg-white p-8 shadow-lg"
          >
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">반려견 프로필</h2>
                <p className="mt-1 text-sm text-slate-500">
                  마이페이지 핵심 정보와 등록된 반려견 목록
                </p>
              </div>
              <button
                type="button"
                onClick={() => navigate("/step", { state: { petOnlyMode: true } })}
                className="inline-flex shrink-0 items-center gap-2 rounded-2xl bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
              >
                <Plus className="h-4 w-4" />
                반려견 추가
              </button>
            </div>

            {pets.length === 0 ? (
              <div className="rounded-3xl bg-slate-50 p-8 text-center text-slate-500">
                아직 등록된 반려견이 없어요.{" "}
                <button
                  type="button"
                  onClick={() => navigate("/step", { state: { petOnlyMode: true } })}
                  className="text-orange-500 underline"
                >
                  지금 추가하기
                </button>
              </div>
            ) : (
              <>
              <div className="-mx-1 overflow-x-auto pb-2 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
                <div className="flex w-max gap-5 px-1">
                  {pets.map((pet) => {
                    const selected = pet.id === selectedPetId;
                    return (
                      <button
                        key={pet.id}
                        type="button"
                        onClick={() => { setSelectedPetId(pet.id); setSaveSuccess(false); }}
                        className={`w-[320px] shrink-0 overflow-hidden rounded-[28px] border p-5 text-left transition ${
                          selected
                            ? "border-orange-300 bg-orange-50/40 shadow-md"
                            : "border-slate-100 bg-white hover:border-orange-200 hover:shadow-sm"
                        }`}
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-3xl bg-gradient-to-br from-orange-100 to-amber-50">
                            {petPhotos[pet.id] ? (
                              <img src={petPhotos[pet.id]} alt={pet.name} className="h-full w-full object-cover" />
                            ) : (
                              <Dog className="h-8 w-8 text-orange-500" />
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="truncate text-xl font-bold text-slate-900">{pet.name}</h3>
                              {selected && (
                                <span className="rounded-full bg-orange-500 px-2 py-1 text-[11px] font-semibold text-white">
                                  선택됨
                                </span>
                              )}
                            </div>
                            <p className="mt-1 truncate text-sm text-slate-500">{pet.breedName}</p>
                            <div className="mt-4 flex flex-wrap gap-2">
                              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                {pet.gender === "MALE" ? "수컷" : pet.gender === "FEMALE" ? "암컷" : "성별 미입력"}
                              </span>
                              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                {pet.isNeutered === true ? "중성화 O" : pet.isNeutered === false ? "중성화 X" : "중성화 미입력"}
                              </span>
                              {pet.selectedTags.slice(0, 3).map((tag) => (
                                <span key={tag} className="rounded-full bg-orange-50 px-3 py-1 text-xs font-medium text-orange-600">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div className="mt-5 grid grid-cols-2 gap-2">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              const rawPet = rawPets.find((p) => p.id === pet.id);
                              navigate("/step", {
                                state: {
                                  editMode: true,
                                  userId: user?.id,
                                  petId: pet.id,
                                  userData: {
                                    nickname: user?.nickname ?? "",
                                    gender: user?.gender ?? null,
                                    birth_date: user?.birth_date ?? "",
                                  },
                                  petData: {
                                    name: pet.name,
                                    breed_id: rawPet?.breed_id ?? null,
                                    breed_name: pet.breedName,
                                    birth_date: pet.birthDate ?? "",
                                    gender: pet.gender,
                                    is_neutered: pet.isNeutered,
                                    selected_tags: pet.selectedTags,
                                  },
                                },
                              });
                            }}
                            className="inline-flex items-center justify-center gap-1.5 rounded-2xl bg-white px-3 py-3 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50"
                          >
                            <Pencil className="h-4 w-4" />
                            수정
                          </button>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); setDetailPet(pet); }}
                            className="inline-flex items-center justify-center gap-1.5 rounded-2xl bg-orange-500 px-3 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
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

              {/* 외부 저장 버튼 */}
              {pets.length > 0 && (
                <div className="mt-5 flex justify-end">
                  <button
                    type="button"
                    onClick={handleSavePet}
                    disabled={saveSuccess && selectedPetId === savedPetId}
                    className={`inline-flex items-center gap-2 rounded-2xl px-6 py-3 text-sm font-semibold transition ${
                      saveSuccess && selectedPetId === savedPetId
                        ? "bg-emerald-500 text-white"
                        : "bg-slate-900 text-white hover:bg-slate-700"
                    }`}
                  >
                    <Save className="h-4 w-4" />
                    {saveSuccess && selectedPetId === savedPetId ? "저장 완료" : "저장"}
                  </button>
                </div>
              )}
              </>
            )}
          </motion.section>

          {/* 선택된 동물 요약 */}
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
                  {selectedPet ? `반려견 ${selectedPet.name}의 성격` : "선택된 반려견 성격"}
                </h2>
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
                    <p className="mt-1 text-2xl font-bold text-slate-900">{selectedPet.breedName}</p>
                  </div>

                  <div className="rounded-[24px] bg-[#F6F7FB] p-5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
                      <CalendarDays className="h-5 w-5" />
                    </div>
                    <p className="mt-4 text-sm text-slate-500">나이</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">{selectedPet.ageLabel}</p>
                  </div>

                  <div className="rounded-[24px] bg-[#F6F7FB] p-5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
                      <BadgeCheck className="h-5 w-5" />
                    </div>
                    <p className="mt-4 text-sm text-slate-500">성별</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {selectedPet.gender === "MALE" ? "수컷" : selectedPet.gender === "FEMALE" ? "암컷" : "미입력"}
                    </p>
                  </div>

                  <div className="rounded-[24px] bg-[#F6F7FB] p-5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-orange-500 shadow-sm">
                      <HeartPulse className="h-5 w-5" />
                    </div>
                    <p className="mt-4 text-sm text-slate-500">중성화 여부</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">
                      {selectedPet.isNeutered === true ? "했어요" : selectedPet.isNeutered === false ? "안 했어요" : "미입력"}
                    </p>
                  </div>
                </div>

                {selectedPet.selectedTags.length > 0 && (
                  <div className="rounded-[28px] bg-[#FCF6EA] px-6 pt-5 pb-6">
                    <div className="flex flex-wrap gap-2">
                      {selectedPet.selectedTags.map((tag) => (
                        <span key={tag} className="rounded-full bg-[#F8E7CC] px-5 py-2.5 text-base font-semibold text-orange-600">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-3xl bg-slate-50 p-8 text-center text-slate-500">
                등록된 반려견이 없어요.
              </div>
            )}
          </motion.section>
        </div>
      </div>

      <PetDetailModal pet={detailPet} onClose={() => setDetailPet(null)} petPhotos={petPhotos} />
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

function ProviderBadge({ provider }: { provider: string }) {
  const key = provider.toLowerCase();

  if (key === 'google') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-0.5 text-xs font-semibold text-gray-600 shadow-sm">
        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
        구글 로그인
      </span>
    );
  }

  if (key === 'kakao') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-0.5 text-xs font-semibold text-[#191919] shadow-sm" style={{ backgroundColor: '#FEE500' }}>
        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="#000000">
          <path d="M12 3C6.477 3 2 6.477 2 10.8c0 2.863 1.922 5.374 4.818 6.78-.198.73-.644 2.478-.735 2.868-.11.478.172.471.372.343.164-.107 2.63-1.798 3.048-2.094C10.155 18.884 11.053 19 12 19c5.523 0 10-3.477 10-7.8S17.523 3 12 3z" />
        </svg>
        카카오 로그인
      </span>
    );
  }

  if (key === 'naver') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full px-3 py-0.5 text-xs font-semibold text-white shadow-sm" style={{ backgroundColor: '#03C75A' }}>
        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="white">
          <path d="M16.273 12.845L7.376 0H0v24h7.726V11.156L16.624 24H24V0h-7.727z" />
        </svg>
        네이버 로그인
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-3 py-0.5 text-xs font-semibold text-slate-600 shadow-sm">
      🔑 {provider} 로그인
    </span>
  );
}
