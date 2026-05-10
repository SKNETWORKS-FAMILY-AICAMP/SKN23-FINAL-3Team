import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import {
  ArrowLeft,
  Camera,
  ChevronRight,
  Search,
  User,
  X,
} from "lucide-react";
import { getMe, updateUser } from "../services/userService";
import { createPet, updatePet } from "../services/petService";
import { getAllBreeds, getTop10Breeds, type Breed } from "../services/breedService";
import { uploadImage } from "../services/imageService";
import { getPetKeywords, getUserKeywords } from "../services/keywordService";
import {
  validateNickname,
  validatePetName,
  validateUserBirth,
  validatePetBirth,
} from "../utils/validation";
import KeywordChipsField from "../components/KeywordChipsField";
import AvatarUploadField from "../components/AvatarUploadField";
import { KeywordChip as Chip } from "../components/KeywordPickerModal";

type GuardianGender = "male" | "female" | "other" | undefined;
type PetGender = "male" | "female" | undefined;
type Neutered = "yes" | "no" | undefined;

type ProfileSetupData = {
  guardianName: string;
  guardianBirth: string;
  guardianGender: GuardianGender;
  guardianImage?: string;        // 보호자 프로필 사진 (data: 또는 기존 url)
  ownerPersonality: string[];   // 보호자 라이프스타일 태그
  petName: string;
  birthDate: string;
  breed: string;
  petGender: PetGender;
  neutered: Neutered;
  personality: string[];         // 반려견 성격 태그
  image?: string;                // 반려견 프로필 사진
};

// 키워드 목록(반려견 성격 / 보호자 라이프스타일) 은 GET /keywords?category={PET|USER}
// API 로 동적 로드 — 백엔드 keywords 테이블 단일 출처. 메인 = 처음 10개 / 더보기 모달 = 전체.
// 가을쥐 결정 2026-05-07. 기존 하드코딩 24+19개 제거.
const PREVIEW_KEYWORD_COUNT = 10;

async function base64ToFile(base64: string, filename: string): Promise<File> {
  const res = await fetch(base64);
  const blob = await res.blob();
  return new File([blob], filename, { type: blob.type || 'image/jpeg' });
}

const defaultData: ProfileSetupData = {
  guardianName: "",
  guardianBirth: "",
  guardianGender: undefined,
  guardianImage: undefined,
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
      className={`flex h-12 w-full items-center justify-center rounded-2xl border text-base font-semibold transition ${active
        ? "border-[#E86A2C] bg-[#FFF2EA] text-[#D45E23]"
        : "border-[#E6E1DB] bg-white text-[#9B948B] hover:border-[#F1B18C]"
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
                    className={`rounded-[16px] px-4 py-4 text-left text-[18px] font-medium transition ${active
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

export default function ProfileSetupPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const editState = location.state as {
    editMode?: boolean;
    petOnlyMode?: boolean;
    userOnlyMode?: boolean;
    userId?: number;
    petId?: number;
    userData?: { nickname: string; gender: string | null; birth_date: string; selected_tags?: string[]; profile_image_url?: string | null };
    petData?: {
      name: string;
      breed_id: number | null;
      breed_name: string;
      birth_date: string;
      gender: "MALE" | "FEMALE" | null;
      is_neutered: boolean | null;
      selected_tags: string[];
      image_url?: string | null;
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
  const [personalityError, setPersonalityError] = useState("");
  const [ownerPersonalityError, setOwnerPersonalityError] = useState("");
  // 키워드 목록 (백엔드 keywords 테이블 단일 출처, id 오름차순)
  const [petKeywordNames, setPetKeywordNames] = useState<string[]>([]);
  const [userKeywordNames, setUserKeywordNames] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([getPetKeywords(), getUserKeywords()])
      .then(([pet, user]) => {
        if (!active) return;
        setPetKeywordNames(pet.map((k) => k.name));
        setUserKeywordNames(user.map((k) => k.name));
      })
      .catch((err) => {
        console.error("키워드 목록 로드 실패", err);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    getAllBreeds().then(setBreeds).catch(() => {/* 로드 실패 시 하드코딩 목록으로 fallback */ });
    getTop10Breeds().then(setTopBreeds).catch(() => setTopBreeds([]));
  }, []);

  // isEditMode 의 보호자 prefill 스냅샷 — 반려견 수정 진입(MyPage 의 ✏️) 시 보호자 section UI 가
  // 화면에 안 노출되므로 사용자가 보호자 정보 변경할 수 없음. handleStart 가 무조건 updateUser
  // 호출하면 prefill 된 보호자 birth_date 가 PATCH body 에 동봉돼 14세 미만 케이스에서 422 발생.
  // → isEditMode 분기에서 보호자 5 필드의 dirty 비교 후 변경 시만 updateUser 호출.
  const initialGuardianRef = useRef<{
    name: string;
    birth: string;
    gender: GuardianGender;
    tags: string[];
    image: string | undefined;
  } | null>(null);

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
      guardianImage: userData?.profile_image_url ?? undefined,
    }));
  }, [isUserOnlyMode]);

  // 수정 모드: 기존 데이터로 폼 초기화
  useEffect(() => {
    if (!isEditMode || !editState) return;
    const { userData, petData } = editState;
    const guardianGender: GuardianGender =
      userData?.gender === "MALE" ? "male" : userData?.gender === "FEMALE" ? "female" : "male";
    const guardianTags = userData?.selected_tags ?? [];
    const guardianImage = userData?.profile_image_url ?? undefined;
    setForm((prev) => ({
      ...prev,
      guardianName: userData?.nickname ?? "",
      guardianBirth: userData?.birth_date ?? "",
      guardianGender,
      ownerPersonality: guardianTags,
      guardianImage,
      petName: petData?.name ?? "",
      birthDate: petData?.birth_date ?? "",
      breed: petData?.breed_name ?? "",
      petGender:
        petData?.gender === "MALE" ? "male" : petData?.gender === "FEMALE" ? "female" : undefined,
      neutered:
        petData?.is_neutered === true ? "yes" : petData?.is_neutered === false ? "no" : undefined,
      personality: petData?.selected_tags ?? [],
      // 저장된 프로필 사진 — 백엔드 응답 (pets.image_url) 사용. localStorage 폐기 (#67).
      image: petData?.image_url ?? undefined,
    }));
    // dirty check 기준점 — handleStart 의 isEditMode 분기가 이 snapshot 과 비교해서
    // 변경된 보호자 필드가 있을 때만 updateUser PATCH 호출.
    initialGuardianRef.current = {
      name: userData?.nickname ?? "",
      birth: userData?.birth_date ?? "",
      gender: guardianGender,
      tags: guardianTags,
      image: guardianImage,
    };
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

  const handleTopBreedSelect = (breed: Breed) => {
    setForm((prev) => ({ ...prev, breed: breed.name_ko }));
    setSelectedBreedId(breed.id);
  };

  const handleStart = async () => {
    if (isUserOnlyMode) {
      // 정책 #62 — 보호자 입력 검증 (닉네임 1~20, 생년월일 1900 ~ 오늘-14년).
      // 빈 입력도 거부 (사용자 결정 2026-05-07 — 닉네임 필수).
      const nicknameError = validateNickname(form.guardianName);
      if (nicknameError) { alert(nicknameError); return; }
      const userBirthError = validateUserBirth(form.guardianBirth);
      if (userBirthError) { alert(userBirthError); return; }

      setIsSubmitting(true);
      try {
        const userId = editState?.userId;
        if (!userId) throw new Error("수정 대상 정보가 없습니다.");

        // 보호자 사진 업로드 (data: 신규만, 기존 url 은 미변경)
        let userProfileId: number | undefined;
        if (form.guardianImage && form.guardianImage.startsWith('data:')) {
          const file = await base64ToFile(form.guardianImage, 'user-profile.jpg');
          const uploaded = await uploadImage(file);
          userProfileId = uploaded.id;
        }

        await updateUser(userId, {
          nickname: form.guardianName || undefined,
          gender: form.guardianGender === "male" ? "MALE" : form.guardianGender === "female" ? "FEMALE" : undefined,
          birth_date: form.guardianBirth || undefined,
          selected_tags: form.ownerPersonality.length ? form.ownerPersonality : undefined,
          profile_id: userProfileId,
        });
        // Navbar 우측 아바타 + getMe 캐시 의존 컴포넌트 즉시 갱신
        window.dispatchEvent(new Event('user-profile-change'));
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
        // 수정 모드: 보호자 정보가 dirty 일 때만 updateUser, 반려견은 항상 updatePet.
        // isEditMode 진입 = MyPage 의 ✏️ (반려견 수정) — UI 가 보호자 section 숨김 → 사용자가
        // 보호자 정보 변경할 수 없음 → dirty=false → updateUser PATCH 자체를 안 부름.
        // (보호자 birth_date 가 14세 미만 데이터로 박혀있어도 PATCH body 미포함이라 422 회피)
        const userId = editState.userId;
        const petId = editState.petId;
        if (!userId || !petId) throw new Error("수정 대상 정보가 없습니다.");

        // 반려견 사진 업로드 (변경 시만 신규, data: 만 신규로 인식)
        let petProfileId: number | undefined;
        if (form.image && form.image.startsWith('data:')) {
          const file = await base64ToFile(form.image, 'pet-profile.jpg');
          const uploaded = await uploadImage(file);
          petProfileId = uploaded.id;
        }

        // 보호자 dirty 비교 — 5 필드 (이름·생년월일·성별·태그·이미지) 중 하나라도 변경 시 PATCH.
        const init = initialGuardianRef.current;
        const guardianImageDirty = !!form.guardianImage && form.guardianImage.startsWith('data:');
        const guardianDirty = !init
          || init.name !== form.guardianName
          || init.birth !== form.guardianBirth
          || init.gender !== form.guardianGender
          || init.tags.join(',') !== form.ownerPersonality.join(',')
          || guardianImageDirty;

        if (guardianDirty) {
          let userProfileId: number | undefined;
          if (guardianImageDirty && form.guardianImage) {
            const file = await base64ToFile(form.guardianImage, 'user-profile.jpg');
            const uploaded = await uploadImage(file);
            userProfileId = uploaded.id;
          }
          await updateUser(userId, {
            nickname: form.guardianName || undefined,
            gender: form.guardianGender === "male" ? "MALE" : form.guardianGender === "female" ? "FEMALE" : undefined,
            birth_date: form.guardianBirth || undefined,
            selected_tags: form.ownerPersonality.length ? form.ownerPersonality : undefined,
            profile_id: userProfileId,
          });
        }
        await updatePet(petId, {
          breed_id: breedId,
          name: form.petName,
          birth_date: form.birthDate || undefined,
          gender: petGenderApi,
          is_neutered: isNeuteredApi,
          selected_tags: form.personality,
          image_id: petProfileId,
        });
        window.dispatchEvent(new Event('user-profile-change'));
        navigate("/mypage", { replace: true });
      } else if (isPetOnlyMode) {
        // 반려견 추가 모드: 이미지 업로드 → createPet (profile_id 연결)
        let petProfileId: number | undefined;
        if (form.image && form.image.startsWith('data:')) {
          const file = await base64ToFile(form.image, 'pet-profile.jpg');
          const uploaded = await uploadImage(file);
          petProfileId = uploaded.id;
        }

        await createPet({
          breed_id: breedId,
          name: form.petName,
          birth_date: form.birthDate || undefined,
          gender: petGenderApi,
          is_neutered: isNeuteredApi,
          selected_tags: form.personality,
          image_id: petProfileId,
        });
        navigate("/mypage", { replace: true });
      } else {
        // 최초 등록 모드: getMe + updateUser + createPet. 사진 = 보호자 + 반려견 분리 (#67 fix 후속).
        const me = await getMe();

        let userProfileId: number | undefined;
        if (form.guardianImage && form.guardianImage.startsWith('data:')) {
          const file = await base64ToFile(form.guardianImage, 'user-profile.jpg');
          const uploaded = await uploadImage(file);
          userProfileId = uploaded.id;
        }
        let petProfileId: number | undefined;
        if (form.image && form.image.startsWith('data:')) {
          const file = await base64ToFile(form.image, 'pet-profile.jpg');
          const uploaded = await uploadImage(file);
          petProfileId = uploaded.id;
        }

        await updateUser(me.id, {
          nickname: form.guardianName || undefined,
          gender: form.guardianGender === "male" ? "MALE" : form.guardianGender === "female" ? "FEMALE" : undefined,
          birth_date: form.guardianBirth || undefined,
          selected_tags: form.ownerPersonality.length ? form.ownerPersonality : undefined,
          profile_id: userProfileId,
        });
        await createPet({
          breed_id: breedId,
          name: form.petName,
          birth_date: form.birthDate || undefined,
          gender: petGenderApi,
          is_neutered: isNeuteredApi,
          selected_tags: form.personality,
          image_id: petProfileId,
        });
        window.dispatchEvent(new Event('user-profile-change'));
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
      <header className="relative border-b-[3px] border-[#3DA0FF] bg-[#F6F1EC] px-4 py-4 text-center">
        <button
          type="button"
          onClick={() => navigate(-1)}
          aria-label="뒤로가기"
          className="absolute left-3 top-1/2 -translate-y-1/2 grid h-9 w-9 place-items-center rounded-full text-[#8A837B] transition hover:bg-[#EFE8E0]"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <h1 className="text-sm font-bold tracking-tight text-[#2F2B27]">
          {isUserOnlyMode ? "보호자 정보 수정" : isEditMode ? "정보 수정" : isPetOnlyMode ? "반려견 추가" : "프로필 설정"}
        </h1>
      </header>

      <main className="mx-auto max-w-[780px] px-4 py-10">
        <div className="mx-auto max-w-[520px] space-y-6">
          {(!isPetOnlyMode && !isEditMode) || isUserOnlyMode ? <section className="rounded-[18px] border border-[#DDD6CF] bg-white px-6 py-5 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
            <h2 className="text-[16px] font-bold text-[#37322D]">보호자 정보</h2>

            <div className="mt-6">
              <AvatarUploadField
                value={form.guardianImage}
                onChange={(dataUrl) => setForm((prev) => ({ ...prev, guardianImage: dataUrl }))}
                placeholderIcon={User}
                tone="slate"
                alt="보호자"
              />
            </div>

            <div className="mt-4">
              <label className="mb-2 block text-xs font-medium text-[#8D867E]">닉네임</label>
              <div className="relative">
                <input
                  value={form.guardianName}
                  onChange={(e) => setForm((prev) => ({ ...prev, guardianName: e.target.value }))}
                  placeholder="보호자님"
                  maxLength={20}
                  className="h-12 w-full rounded-[10px] border border-[#E3DDD7] pl-4 pr-14 text-sm outline-none placeholder:text-[#BBB3AB] focus:border-[#F0A777]"
                />
                <span className="pointer-events-none absolute bottom-1.5 right-3 text-[11px] text-[#B5ADA4]">
                  {form.guardianName.trim().length}/20
                </span>
              </div>
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
                <SegButton
                  active={form.guardianGender === "male"}
                  onClick={() => setForm((prev) => ({ ...prev, guardianGender: "male" }))}
                >
                  남성
                </SegButton>
                <SegButton
                  active={form.guardianGender === "female"}
                  onClick={() => setForm((prev) => ({ ...prev, guardianGender: "female" }))}
                >
                  여성
                </SegButton>
              </div>
            </div>

            {/* 보호자 라이프스타일 태그 */}
            <div className="mt-4">
              <KeywordChipsField
                label="라이프스타일 (중복 선택 가능)"
                modalTitle="라이프스타일 더보기"
                modalDescription="보호자님의 여행 스타일을 골라주세요 (최대 5개)"
                selectedNoun="라이프스타일"
                options={userKeywordNames}
                value={form.ownerPersonality}
                onToggle={toggleOwnerPersonality}
                onClear={() => setForm((prev) => ({ ...prev, ownerPersonality: [] }))}
                previewLimit={PREVIEW_KEYWORD_COUNT}
                error={ownerPersonalityError}
              />
            </div>
          </section> : null}

          {!isUserOnlyMode && <section className="rounded-[18px] border border-[#DDD6CF] bg-white px-6 py-5 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
            <h2 className="text-[16px] font-bold text-[#37322D]">반려견 정보</h2>

            <div className="mt-6">
              <AvatarUploadField
                value={form.image}
                onChange={(dataUrl) => setForm((prev) => ({ ...prev, image: dataUrl }))}
                placeholderIcon={Camera}
                tone="orange"
                alt="반려견"
              />
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

              <KeywordChipsField
                label="성격 (중복 선택 가능)"
                modalTitle="성격 더보기"
                modalDescription="원하는 성격을 자유롭게 선택해 주세요 (최대 5개)"
                selectedNoun="성격"
                options={petKeywordNames}
                value={form.personality}
                onToggle={togglePersonality}
                onClear={() => setForm((prev) => ({ ...prev, personality: [] }))}
                previewLimit={PREVIEW_KEYWORD_COUNT}
                error={personalityError}
              />

            </div>
          </section>}

          <div className="flex gap-3">
            {(isUserOnlyMode || isEditMode || isPetOnlyMode) && (
              <button
                type="button"
                onClick={() => navigate(-1)}
                disabled={isSubmitting}
                className="rounded-[16px] border border-[#E3DDD7] bg-white px-6 py-5 text-lg font-semibold text-[#7B746B] transition hover:bg-[#F4F1EE] disabled:opacity-60"
              >
                취소
              </button>
            )}
            <button
              type="button"
              onClick={handleStart}
              disabled={isSubmitting}
              className="flex-1 rounded-[16px] bg-[#DB5F2E] px-6 py-5 text-lg font-bold text-white shadow-sm transition hover:bg-[#D05523] disabled:opacity-60"
            >
              {isSubmitting ? "저장 중..." : isUserOnlyMode ? "수정 완료" : isEditMode ? "수정 완료" : isPetOnlyMode ? "추가하기 🐾" : "시작하기! 🐾"}
            </button>
          </div>
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

    </div>
  );
}