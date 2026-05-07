import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import {
  Camera,
  ChevronRight,
  MoreHorizontal,
  Search,
  X,
} from "lucide-react";
import { getMe, updateUser } from "../services/userService";
import { createPet, updatePet } from "../services/petService";
import { getAllBreeds, getTop10Breeds, type Breed } from "../services/breedService";
import { uploadImage } from "../services/imageService";
import {
  validateNickname,
  validatePetName,
  validateUserBirth,
  validatePetBirth,
  validateImageSize,
} from "../utils/validation";

type GuardianGender = "male" | "female" | "other" | undefined;
type PetGender = "male" | "female" | undefined;
type Neutered = "yes" | "no" | undefined;

type ProfileSetupData = {
  guardianName: string;
  guardianBirth: string;
  guardianGender: GuardianGender;
  ownerPersonality: string[];   // 보호자 라이프스타일 태그
  petName: string;
  birthDate: string;
  breed: string;
  petGender: PetGender;
  neutered: Neutered;
  personality: string[];         // 반려견 성격 태그
  image?: string;
};

// scoring.py DOG_TAG_SCORES 기준 (24개)
const personalityOptions = [
  "에너자이저",
  "느긋한 편",
  "애교쟁이",
  "제 갈 길 가는 타입",
  "낯을 가려요",
  "낯선 사람도 좋아요",
  "사람이라면 다 좋아",
  "사람은 좀 무서워요",
  "겁쟁이",
  "겁 없는 탐험가",
  "호기심 폭발",
  "고집 있는 편",
  "예민한 편",
  "먹는 게 최고",
  "낯선 것엔 짖어요",
  "산책이 제일 좋아",
  "밖이 좋아요",
  "집이 편해요",
  "장난감 수집가",
  "공이라면 뭐든지",
  "강아지 친구 환영",
  "혼자도 잘 놀아요",
  "안기는 거 좋아요",
  "시키는 건 다 해요",
];

// scoring.py OWNER_TAG_SCORES 기준 (19개)
const ownerPersonalityOptions = [
  "신나게 뛰어놀기",
  "느긋하게 쉬어가기",
  "자연 속으로",
  "도시 구경",
  "일상 충전",
  "새로운 곳 구경",
  "감성 충만",
  "동네 골목 탐방",
  "계획 없이 떠나기",
  "바다",
  "산",
  "숲",
  "계곡",
  "공원 산책",
  "카페 투어",
  "핫플 인증",
  "사진 건지러",
  "맛있는 거 먹으러",
  "전시 관람",
];

const previewPersonalityOptions = personalityOptions.slice(0, 10);
const previewOwnerPersonalityOptions = ownerPersonalityOptions.slice(0, 9);

async function base64ToFile(base64: string, filename: string): Promise<File> {
  const res = await fetch(base64);
  const blob = await res.blob();
  return new File([blob], filename, { type: blob.type || 'image/jpeg' });
}

const defaultData: ProfileSetupData = {
  guardianName: "",
  guardianBirth: "",
  guardianGender: undefined,
  ownerPersonality: [],
  petName: "",
  birthDate: "",
  breed: "",
  petGender: undefined,
  neutered: undefined,
  personality: [],
  image: undefined,
};


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
  breeds,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (breed: Breed) => void;
  selectedBreed: string;
  breeds: Breed[];
}) {
  const [keyword, setKeyword] = useState("");

  useEffect(() => {
    if (!isOpen) setKeyword("");
  }, [isOpen]);

  const filteredBreeds = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    if (!q) return breeds;
    return breeds.filter((b) => b.name_ko.toLowerCase().includes(q) || b.name_en.toLowerCase().includes(q));
  }, [keyword, breeds]);

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
          {breeds.length === 0 ? (
            <p className="py-12 text-center text-[#8D867E]">견종 목록을 불러오는 중...</p>
          ) : filteredBreeds.length === 0 ? (
            <p className="py-12 text-center text-[#8D867E]">검색 결과가 없습니다.</p>
          ) : (
            <div className="grid grid-cols-2 gap-x-6 gap-y-3 pr-2">
              {filteredBreeds.map((breed) => {
                const active = selectedBreed === breed.name_ko;
                return (
                  <button
                    key={breed.id}
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
                    {breed.name_ko}
                  </button>
                );
              })}
            </div>
          )}
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

function OwnerPersonalityModal({
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
            <h2 className="text-[28px] font-bold tracking-tight text-[#3F3A35]">라이프스타일 더보기</h2>
            <p className="mt-2 text-sm text-[#8D867E]">보호자님의 여행 스타일을 골라주세요 (최대 5개)</p>
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
            {ownerPersonalityOptions.map((item) => (
              <Chip key={item} active={selectedItems.includes(item)} onClick={() => onToggle(item)}>
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
  const navigate = useNavigate();
  const location = useLocation();
  const editState = location.state as {
    editMode?: boolean;
    petOnlyMode?: boolean;
    userOnlyMode?: boolean;
    userId?: number;
    petId?: number;
    userData?: { nickname: string; gender: string | null; birth_date: string; selected_tags?: string[] };
    petData?: {
      name: string;
      breed_id: number | null;
      breed_name: string;
      birth_date: string;
      gender: "MALE" | "FEMALE" | null;
      is_neutered: boolean | null;
      selected_tags: string[];
    };
  } | null;
  const isEditMode = editState?.editMode === true;
  const isPetOnlyMode = editState?.petOnlyMode === true;
  const isUserOnlyMode = editState?.userOnlyMode === true;

  const [form, setForm] = useState<ProfileSetupData>({
    ...defaultData,
    guardianName: "",
    guardianBirth: "",
    guardianGender: "male",
    petName: "",
    breed: "",
    petGender: undefined,
    neutered: undefined,
  });
  const [selectedBreedId, setSelectedBreedId] = useState<number | null>(null);
  const [breeds, setBreeds] = useState<Breed[]>([]);
  const [topBreeds, setTopBreeds] = useState<Breed[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [isBreedModalOpen, setIsBreedModalOpen] = useState(false);
  const [isPersonalityModalOpen, setIsPersonalityModalOpen] = useState(false);
  const [isOwnerPersonalityModalOpen, setIsOwnerPersonalityModalOpen] = useState(false);
  const [personalityError, setPersonalityError] = useState("");
  const [ownerPersonalityError, setOwnerPersonalityError] = useState("");
  const fileRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    getAllBreeds().then(setBreeds).catch(() => {/* 로드 실패 시 하드코딩 목록으로 fallback */});
    getTop10Breeds().then(setTopBreeds).catch(() => setTopBreeds([]));
  }, []);

  // 보호자 전용 수정 모드: 기존 데이터로 폼 초기화
  useEffect(() => {
    if (!isUserOnlyMode || !editState) return;
    const { userData } = editState;
    setForm((prev) => ({
      ...prev,
      guardianName: userData?.nickname ?? "",
      guardianBirth: userData?.birth_date ?? "",
      guardianGender:
        userData?.gender === "MALE" ? "male" : userData?.gender === "FEMALE" ? "female" : "male",
      ownerPersonality: userData?.selected_tags ?? [],
    }));
  }, [isUserOnlyMode]);

  // 수정 모드: 기존 데이터로 폼 초기화
  useEffect(() => {
    if (!isEditMode || !editState) return;
    const { userData, petData } = editState;
    setForm((prev) => ({
      ...prev,
      guardianName: userData?.nickname ?? "",
      guardianBirth: userData?.birth_date ?? "",
      guardianGender:
        userData?.gender === "MALE" ? "male" : userData?.gender === "FEMALE" ? "female" : "male",
      ownerPersonality: userData?.selected_tags ?? [],
      petName: petData?.name ?? "",
      birthDate: petData?.birth_date ?? "",
      breed: petData?.breed_name ?? "",
      petGender:
        petData?.gender === "MALE" ? "male" : petData?.gender === "FEMALE" ? "female" : undefined,
      neutered:
        petData?.is_neutered === true ? "yes" : petData?.is_neutered === false ? "no" : undefined,
      personality: petData?.selected_tags ?? [],
      // 저장된 프로필 사진 불러오기
      image: editState.petId
        ? (localStorage.getItem(`pet_photo_${editState.petId}`) ?? undefined)
        : undefined,
    }));
    if (petData?.breed_id) setSelectedBreedId(petData.breed_id);
  }, [isEditMode]);

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

  const toggleOwnerPersonality = (item: string) => {
    setOwnerPersonalityError("");
    setForm((prev) => {
      if (prev.ownerPersonality.includes(item)) {
        return { ...prev, ownerPersonality: prev.ownerPersonality.filter((v) => v !== item) };
      }
      if (prev.ownerPersonality.length >= 5) {
        setOwnerPersonalityError("라이프스타일은 최대 5개까지 선택할 수 있어요.");
        return prev;
      }
      return { ...prev, ownerPersonality: [...prev.ownerPersonality, item] };
    });
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 정책 #72-A — 5MB 사전 검증 (Nginx·백엔드 매직바이트 검증보다 먼저 차단)
    const sizeError = validateImageSize(file);
    if (sizeError) {
      alert(sizeError);
      e.target.value = "";
      return;
    }

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

  const handleTopBreedSelect = (breed: Breed) => {
    setForm((prev) => ({ ...prev, breed: breed.name_ko }));
    setSelectedBreedId(breed.id);
  };

  const handleStart = async () => {
    if (isUserOnlyMode) {
      // 정책 #62 — 보호자 입력 검증 (닉네임 1~20, 생년월일 1900 ~ 오늘-14년).
      // 닉네임은 빈 입력일 때 기존 값 유지하므로 비어있지 않은 경우만 검증.
      if (form.guardianName) {
        const nicknameError = validateNickname(form.guardianName);
        if (nicknameError) { alert(nicknameError); return; }
      }
      const userBirthError = validateUserBirth(form.guardianBirth);
      if (userBirthError) { alert(userBirthError); return; }

      setIsSubmitting(true);
      try {
        const userId = editState?.userId;
        if (!userId) throw new Error("수정 대상 정보가 없습니다.");
        await updateUser(userId, {
          nickname: form.guardianName || undefined,
          gender: form.guardianGender === "male" ? "MALE" : form.guardianGender === "female" ? "FEMALE" : undefined,
          birth_date: form.guardianBirth || undefined,
          selected_tags: form.ownerPersonality.length ? form.ownerPersonality : undefined,
        });
        navigate("/mypage", { replace: true });
      } catch (err) {
        console.error("보호자 정보 저장 실패", err);
        // 백엔드 detail (욕설 검출 #71 — "부적절한 단어가 포함되어 있습니다" 등) 그대로 표시
        const message = err instanceof Error ? err.message : "저장 중 오류가 발생했습니다.";
        alert(message);
      } finally {
        setIsSubmitting(false);
      }
      return;
    }
    // 정책 #63 — 반려견 입력 검증 (이름 1~20, 생년월일 오늘-30년 ~ 오늘)
    const petNameError = validatePetName(form.petName);
    if (petNameError) {
      alert(petNameError);
      return;
    }
    const petBirthError = validatePetBirth(form.birthDate);
    if (petBirthError) {
      alert(petBirthError);
      return;
    }
    if (selectedBreedId === null) {
      alert("견종을 선택해주세요. (목록에서 선택하거나 견종 선택 버튼을 눌러주세요)");
      return;
    }
    const breedId = selectedBreedId;
    if (!form.petGender) {
      alert("반려견 성별을 선택해주세요.");
      return;
    }
    setIsSubmitting(true);
    try {
      const petGenderApi = form.petGender === "male" ? "MALE" : form.petGender === "female" ? "FEMALE" : undefined;
      const isNeuteredApi = form.neutered === "yes" ? true : form.neutered === "no" ? false : undefined;

      if (isEditMode && editState) {
        // 수정 모드: updateUser + updatePet
        const userId = editState.userId;
        const petId = editState.petId;
        if (!userId || !petId) throw new Error("수정 대상 정보가 없습니다.");

        let profileId: number | undefined;
        let imageUrl: string | undefined;
        if (form.image && form.image.startsWith('data:')) {
          const file = await base64ToFile(form.image, 'profile.jpg');
          const uploaded = await uploadImage(file);
          profileId = uploaded.id;
          imageUrl = uploaded.url;
        }

        await updateUser(userId, {
          nickname: form.guardianName || undefined,
          gender: form.guardianGender === "male" ? "MALE" : form.guardianGender === "female" ? "FEMALE" : undefined,
          birth_date: form.guardianBirth || undefined,
          selected_tags: form.ownerPersonality.length ? form.ownerPersonality : undefined,
          profile_id: profileId,
        });
        const updatedPet = await updatePet(petId, {
          breed_id: breedId,
          name: form.petName,
          birth_date: form.birthDate || undefined,
          gender: petGenderApi,
          is_neutered: isNeuteredApi,
          selected_tags: form.personality,
        });
        if (imageUrl) {
          localStorage.setItem(`pet_photo_${updatedPet.id}`, imageUrl);
        } else if (form.image) {
          localStorage.setItem(`pet_photo_${updatedPet.id}`, form.image);
        }
        navigate("/mypage", { replace: true });
      } else if (isPetOnlyMode) {
        // 반려견 추가 모드: createPet만
        const newPet = await createPet({
          breed_id: breedId,
          name: form.petName,
          birth_date: form.birthDate || undefined,
          gender: petGenderApi,
          is_neutered: isNeuteredApi,
          selected_tags: form.personality,
        });
        if (form.image) localStorage.setItem(`pet_photo_${newPet.id}`, form.image);
        navigate("/mypage", { replace: true });
      } else {
        // 최초 등록 모드: getMe + updateUser + createPet
        const me = await getMe();

        let profileId: number | undefined;
        let imageUrl: string | undefined;
        if (form.image && form.image.startsWith('data:')) {
          const file = await base64ToFile(form.image, 'profile.jpg');
          const uploaded = await uploadImage(file);
          profileId = uploaded.id;
          imageUrl = uploaded.url;
        }

        await updateUser(me.id, {
          nickname: form.guardianName || undefined,
          gender: form.guardianGender === "male" ? "MALE" : form.guardianGender === "female" ? "FEMALE" : undefined,
          birth_date: form.guardianBirth || undefined,
          selected_tags: form.ownerPersonality.length ? form.ownerPersonality : undefined,
          profile_id: profileId,
        });
        const newPet = await createPet({
          breed_id: breedId,
          name: form.petName,
          birth_date: form.birthDate || undefined,
          gender: petGenderApi,
          is_neutered: isNeuteredApi,
          selected_tags: form.personality,
        });
        if (imageUrl) {
          localStorage.setItem(`pet_photo_${newPet.id}`, imageUrl);
        } else if (form.image) {
          localStorage.setItem(`pet_photo_${newPet.id}`, form.image);
        }
        navigate("/home");
      }
    } catch (err) {
      console.error("프로필 저장 실패", err);
      // 백엔드 detail (욕설 검출 #71 / 매직바이트 #72-A 등) 그대로 표시
      const message = err instanceof Error ? err.message : "저장 중 오류가 발생했습니다.";
      alert(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6F1EC]">
      <header className="border-b-[3px] border-[#3DA0FF] bg-[#F6F1EC] px-4 py-4 text-center">
        <h1 className="text-sm font-bold tracking-tight text-[#2F2B27]">
          {isUserOnlyMode ? "보호자 정보 수정" : isEditMode ? "정보 수정" : isPetOnlyMode ? "반려견 추가" : "프로필 설정"}
        </h1>
      </header>

      <main className="mx-auto max-w-[780px] px-4 py-10">
        <div className="mx-auto max-w-[520px] space-y-6">
          {(!isPetOnlyMode && !isEditMode) || isUserOnlyMode ? <section className="rounded-[18px] border border-[#DDD6CF] bg-white px-6 py-5 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
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

            {/* 보호자 라이프스타일 태그 */}
            <div className="mt-4">
              <div className="mb-2 flex items-center justify-between">
                <label className="block text-xs font-medium text-[#8D867E]">
                  라이프스타일 (중복 선택 가능)
                </label>
                <span className="text-xs font-semibold text-[#D45E23]">
                  {form.ownerPersonality.length}/5
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {previewOwnerPersonalityOptions.map((item) => (
                  <Chip
                    key={item}
                    active={form.ownerPersonality.includes(item)}
                    onClick={() => toggleOwnerPersonality(item)}
                  >
                    {item}
                  </Chip>
                ))}
                <button
                  type="button"
                  onClick={() => setIsOwnerPersonalityModalOpen(true)}
                  className="inline-flex items-center gap-2 rounded-full border border-[#E6E1DB] bg-white px-4 py-2 text-sm font-medium text-[#7B746B] transition hover:border-[#F1B18C] hover:text-[#D45E23]"
                >
                  <MoreHorizontal className="h-4 w-4" />
                  더보기
                </button>
              </div>
              {form.ownerPersonality.length > 0 && (
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs text-[#A29A91]">선택된 라이프스타일</span>
                    <button
                      type="button"
                      onClick={() => setForm((prev) => ({ ...prev, ownerPersonality: [] }))}
                      className="text-xs text-[#B0A89F] hover:text-red-400 transition-colors"
                    >
                      전체 지우기
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {form.ownerPersonality.map((item) => (
                      <span
                        key={item}
                        className="rounded-full bg-[#FFF2EA] px-3 py-1 text-xs font-semibold text-[#D45E23] ring-1 ring-[#F3D3BF]"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {ownerPersonalityError && (
                <p className="mt-2 text-xs text-red-500">{ownerPersonalityError}</p>
              )}
            </div>
          </section> : null}

          {!isUserOnlyMode && <section className="rounded-[18px] border border-[#DDD6CF] bg-white px-6 py-5 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
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
                  {topBreeds.map((breed) => (
                    <Chip
                      key={breed.id}
                      active={selectedBreedId === breed.id}
                      onClick={() => handleTopBreedSelect(breed)}
                    >
                      {breed.name_ko}
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
                  <div className="mt-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-[#A29A91]">선택된 성격</span>
                      <button
                        type="button"
                        onClick={() => setForm((prev) => ({ ...prev, personality: [] }))}
                        className="text-xs text-[#B0A89F] hover:text-red-400 transition-colors"
                      >
                        전체 지우기
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {form.personality.map((item) => (
                        <span
                          key={item}
                          className="rounded-full bg-[#FFF2EA] px-3 py-1 text-xs font-semibold text-[#D45E23] ring-1 ring-[#F3D3BF]"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {personalityError && (
                  <p className="mt-2 text-xs text-red-500">{personalityError}</p>
                )}
              </div>

            </div>
          </section>}

          <button
            type="button"
            onClick={handleStart}
            disabled={isSubmitting}
            className="w-full rounded-[16px] bg-[#DB5F2E] px-6 py-5 text-lg font-bold text-white shadow-sm transition hover:bg-[#D05523] disabled:opacity-60"
          >
            {isSubmitting ? "저장 중..." : isUserOnlyMode ? "수정 완료" : isEditMode ? "수정 완료" : isPetOnlyMode ? "추가하기 🐾" : "시작하기! 🐾"}
          </button>
        </div>
      </main>

      <BreedModal
        isOpen={isBreedModalOpen}
        onClose={() => setIsBreedModalOpen(false)}
        onSelect={(breed) => {
          setForm((prev) => ({ ...prev, breed: breed.name_ko }));
          setSelectedBreedId(breed.id);
        }}
        selectedBreed={form.breed}
        breeds={breeds}
      />

      <PersonalityModal
        isOpen={isPersonalityModalOpen}
        onClose={() => setIsPersonalityModalOpen(false)}
        selectedItems={form.personality}
        onToggle={togglePersonality}
      />

      <OwnerPersonalityModal
        isOpen={isOwnerPersonalityModalOpen}
        onClose={() => setIsOwnerPersonalityModalOpen(false)}
        selectedItems={form.ownerPersonality}
        onToggle={toggleOwnerPersonality}
      />
    </div>
  );
}