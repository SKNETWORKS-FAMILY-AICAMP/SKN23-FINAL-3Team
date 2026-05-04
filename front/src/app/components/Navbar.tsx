import { motion, useScroll, useMotionValueEvent, AnimatePresence } from "motion/react";
import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router";
import {
  Home,
  User,
  Menu,
  X,
  ChevronDown,
  Calendar,
  NotebookPen,
  Map,
  Bell,
  LogOut,
  BookOpen,
  Images,
  LogIn,
} from "lucide-react";
import { getMe } from "../services/userService";
import { getPets } from "../services/petService";
import { getImage } from "../services/imageService";
import { SubscriptionModal } from "./SubscriptionModal";

interface SubItem {
  label: string;
  path: string;
  icon: React.ElementType;
  requiresAuth?: boolean;
}

interface NavItem {
  icon: React.ElementType;
  label: string;
  path?: string;
  requiresAuth?: boolean;
  subItems?: SubItem[];
}

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem('access_token'));
  const [openSubMenu, setOpenSubMenu] = useState<string | null>(null);
  const [hoveredMenu, setHoveredMenu] = useState<string | null>(null);
  const [profilePhoto, setProfilePhoto] = useState<string | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [subscriptionOpen, setSubscriptionOpen] = useState(false);

  const { scrollY } = useScroll();
  const navigate = useNavigate();
  const location = useLocation();

  // 로그인 상태 동기화
  useEffect(() => {
    const syncAuth = () => {
      setIsLoggedIn(!!localStorage.getItem('access_token'));
      if (!localStorage.getItem('access_token')) setProfilePhoto(null);
    };
    window.addEventListener('auth-change', syncAuth);
    window.addEventListener('storage', syncAuth);
    return () => {
      window.removeEventListener('auth-change', syncAuth);
      window.removeEventListener('storage', syncAuth);
    };
  }, []);

  // 라우트 이동마다 토큰 재확인
  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('access_token'));
  }, [location.pathname]);

  // 선택된 반려견 사진 로드 (MyPage와 연동)
  const loadProfilePhoto = async () => {
    if (!isLoggedIn) return;
    try {
      const me = await getMe();
      const pets = await getPets(me.id);
      const pet = pets[0] ?? null;
      const selectedPetId = localStorage.getItem('selected_pet_id');
      const targetPet = (selectedPetId ? pets.find((p) => String(p.id) === selectedPetId) : null) ?? pet;
      if (targetPet) {
        localStorage.setItem('selected_pet_id', String(targetPet.id));
        const cached = localStorage.getItem(`pet_photo_${targetPet.id}`);
        if (cached) { setProfilePhoto(cached); return; }
      }
      // localStorage에 없으면 profile_id로 백엔드에서 가져와서 저장
      if (me.profile_id) {
        const img = await getImage(me.profile_id);
        setProfilePhoto(img.url);
        if (targetPet) localStorage.setItem(`pet_photo_${targetPet.id}`, img.url);
      }
    } catch { /* 무시 */ }
  };

  useEffect(() => {
    if (!isLoggedIn) return;
    loadProfilePhoto();
  }, [isLoggedIn]);

  // MyPage에서 반려견 선택 변경 시 즉시 반영
  useEffect(() => {
    const onPetChange = () => loadProfilePhoto();
    window.addEventListener('pet-select-change', onPetChange);
    return () => window.removeEventListener('pet-select-change', onPetChange);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useMotionValueEvent(scrollY, "change", (latest) => {
    setScrolled(latest > 20);
  });

  const navItems: NavItem[] = [
    {
      icon: Home,
      label: "홈",
      path: "/home",
      subItems: [
        { label: "강아지 일기장", path: "/home?tab=diary", icon: NotebookPen },
        { label: "지도", path: "/home?tab=map", icon: Map },
      ],
    },
    {
      icon: BookOpen,
      label: "다이어리",
      subItems: [
        { label: "앨범", path: "/home?tab=diary&album=true", icon: Images, requiresAuth: true },
        { label: "캘린더", path: "/calendar", icon: Calendar, requiresAuth: true },
      ],
    },
    { icon: User, label: "마이페이지", path: "/mypage", requiresAuth: true },
  ];

  const handleNavClick = (item: NavItem) => {
    if (item.subItems) {
      setOpenSubMenu(openSubMenu === item.label ? null : item.label);
    } else if (item.path) {
      if (item.requiresAuth && !isLoggedIn) {
        setLoginModalOpen(true);
        setMobileOpen(false);
        return;
      }
      navigate(item.path);
      setOpenSubMenu(null);
      setMobileOpen(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    window.dispatchEvent(new Event('auth-change'));
    setProfileOpen(false);
    navigate("/login");
  };

  return (
    <>
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/95 backdrop-blur-md shadow-md"
          : "bg-white/80 backdrop-blur-sm"
      }`}
    >
      <div className="w-full px-6">
        <div className="flex items-center justify-between h-16">
          {/* 왼쪽: 로고 */}
          <Link to="/home" className="flex items-center select-none cursor-pointer hover:opacity-75 transition-opacity">
            <img src="/logo2.svg" alt="withDOG" className="h-12 w-auto" />
          </Link>

          {/* 오른쪽: 메뉴 + 프로필/로그인 */}
          <div className="hidden md:flex items-center gap-2">
            <nav className="flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = item.path && location.pathname === item.path;
                const isHovered = hoveredMenu === item.label;

                return (
                  <div
                    key={item.label}
                    className="relative"
                    onMouseEnter={() => item.subItems && setHoveredMenu(item.label)}
                    onMouseLeave={() => setHoveredMenu(null)}
                  >
                    <button
                      onClick={() => handleNavClick(item)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                        isActive
                          ? "text-orange-600 bg-orange-50"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{item.label}</span>
                      {item.subItems && (
                        <motion.div
                          animate={{ rotate: isHovered ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown className="w-3.5 h-3.5" />
                        </motion.div>
                      )}
                    </button>

                    {/* 데스크탑 드롭다운 */}
                    <AnimatePresence>
                      {item.subItems && isHovered && (
                        <motion.div
                          initial={{ opacity: 0, y: -6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -6 }}
                          transition={{ duration: 0.15 }}
                          className="absolute left-0 top-full pt-2 z-50"
                        >
                          <div className="min-w-[160px] rounded-2xl border border-gray-100 bg-white py-2 shadow-lg">
                            {item.subItems.map((sub) => {
                              const SubIcon = sub.icon;
                              return (
                                <button
                                  key={sub.label}
                                  onClick={() => {
                                    if (sub.requiresAuth && !isLoggedIn) {
                                      setLoginModalOpen(true);
                                      setHoveredMenu(null);
                                      return;
                                    }
                                    navigate(sub.path);
                                    setHoveredMenu(null);
                                  }}
                                  className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-600 transition-colors hover:bg-orange-50 hover:text-orange-600"
                                >
                                  <SubIcon className="w-4 h-4" />
                                  {sub.label}
                                </button>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </nav>

            {/* 프로필 아바타 (로그인) / 로그인 버튼 (비로그인) */}
            {isLoggedIn ? (
              <div
                className="relative ml-2"
                onMouseEnter={() => setProfileOpen(true)}
                onMouseLeave={() => setProfileOpen(false)}
              >
                {/* 아바타 버튼 */}
                <button className="flex items-center justify-center w-10 h-10 rounded-full overflow-hidden ring-2 ring-orange-300 hover:ring-orange-400 transition-all">
                  {profilePhoto ? (
                    <img src={profilePhoto} alt="프로필" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-orange-100 flex items-center justify-center">
                      <User className="w-5 h-5 text-orange-500" />
                    </div>
                  )}
                </button>

                {/* 드롭다운 */}
                <AnimatePresence>
                  {profileOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: -6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 top-full pt-2 z-50"
                    >
                      <div className="min-w-[160px] rounded-2xl border border-gray-100 bg-white py-2 shadow-lg">
                        <button
                          onClick={() => { setProfileOpen(false); setSubscriptionOpen(true); }}
                          className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm font-semibold text-orange-500 transition-colors hover:bg-orange-50 hover:text-orange-600"
                        >
                          <span className="text-base leading-none">🐾</span>
                          구독 패스
                        </button>
                        <button
                          onClick={() => { setProfileOpen(false); alert('알림 설정은 준비 중이에요!'); }}
                          className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-600 transition-colors hover:bg-orange-50 hover:text-orange-600"
                        >
                          <Bell className="w-4 h-4" />
                          알림 설정
                        </button>
                        <button
                          onClick={handleLogout}
                          className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-gray-600 transition-colors hover:bg-red-50 hover:text-red-500"
                        >
                          <LogOut className="w-4 h-4" />
                          로그아웃
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ) : (
              <button
                onClick={() => navigate("/login")}
                className="ml-4 px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-sm font-medium transition-colors"
              >
                로그인
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* 모바일 메뉴 */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="md:hidden bg-white border-t border-gray-100 px-4 py-3 flex flex-col gap-1 shadow-lg"
          >
            {navItems.map((item) => {
              const Icon = item.icon;
              const isOpen = openSubMenu === item.label;

              return (
                <div key={item.label}>
                  <button
                    onClick={() => handleNavClick(item)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-colors ${
                      (item.path && location.pathname === item.path) || isOpen
                        ? "text-orange-600 bg-orange-50 font-semibold"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="flex-1 text-left">{item.label}</span>
                    {item.subItems && (
                      <motion.div
                        animate={{ rotate: isOpen ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronDown className="w-4 h-4" />
                      </motion.div>
                    )}
                  </button>

                  <AnimatePresence>
                    {item.subItems && isOpen && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="ml-4 mt-1 mb-1 flex flex-col gap-1 border-l-2 border-orange-100 pl-4">
                          {item.subItems.map((sub) => {
                            const SubIcon = sub.icon;
                            const isSubActive = location.pathname === sub.path;

                            return (
                              <button
                                key={sub.label}
                                onClick={() => {
                                  if (sub.requiresAuth && !isLoggedIn) {
                                    setLoginModalOpen(true);
                                    setMobileOpen(false);
                                    setOpenSubMenu(null);
                                    return;
                                  }
                                  navigate(sub.path);
                                  setMobileOpen(false);
                                  setOpenSubMenu(null);
                                }}
                                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                                  isSubActive
                                    ? "text-orange-600 bg-orange-50 font-semibold"
                                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                }`}
                              >
                                <SubIcon className="w-3.5 h-3.5" />
                                <span>{sub.label}</span>
                              </button>
                            );
                          })}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}

            {/* 모바일: 로그아웃 / 로그인 */}
            {isLoggedIn ? (
              <>
                <button
                  onClick={() => { setMobileOpen(false); setSubscriptionOpen(true); }}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-orange-500 hover:bg-orange-50 hover:text-orange-600 transition-colors"
                >
                  <span className="text-base leading-none">🐾</span>
                  구독 패스
                </button>
                <button
                  onClick={() => { setMobileOpen(false); alert('알림 설정은 준비 중이에요!'); }}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-gray-600 hover:bg-orange-50 hover:text-orange-600 transition-colors"
                >
                  <Bell className="w-4 h-4" />
                  알림 설정
                </button>
                <button
                  onClick={() => { handleLogout(); setMobileOpen(false); }}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-red-500 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  로그아웃
                </button>
              </>
            ) : (
              <button
                onClick={() => { navigate("/login"); setMobileOpen(false); }}
                className="mt-2 px-4 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-sm font-medium transition-colors"
              >
                로그인
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>

      {/* 비로그인 접근 차단 모달 */}
      <AnimatePresence>
        {loginModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center px-4"
            style={{ background: 'rgba(61,43,31,0.45)', backdropFilter: 'blur(6px)' }}
            onClick={() => setLoginModalOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 24, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 16, scale: 0.97 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="w-full max-w-[360px] overflow-hidden rounded-[28px] bg-white shadow-[0_24px_64px_rgba(61,43,31,0.18)]"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 상단 일러스트 영역 */}
              <div className="relative flex flex-col items-center px-8 pb-6 pt-10"
                style={{ background: 'linear-gradient(145deg, #FFF3EA 0%, #FFE8D6 100%)' }}>
                <button
                  onClick={() => setLoginModalOpen(false)}
                  className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-full bg-white/60 text-[#8B6355] transition hover:bg-white"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-[0_4px_16px_rgba(244,132,95,0.2)]">
                  <span className="text-4xl">🐾</span>
                </div>
                <h2 className="mt-4 text-[22px] font-black tracking-tight text-[#3D2B1F]">로그인이 필요해요</h2>
                <p className="mt-1.5 text-center text-sm text-[#8B6355]">
                  withDOG의 더 많은 기능을<br />로그인 후 이용해보세요
                </p>
              </div>

              {/* 기능 안내 */}
              <div className="px-7 py-5">
                <div className="flex flex-col gap-2.5">
                  {[
                    { emoji: '📸', text: '반려견 앨범 모아보기' },
                    { emoji: '📅', text: '멍캘린더 일정 관리' },
                    { emoji: '📔', text: 'AI 그림일기 생성' },
                    { emoji: '🗺️', text: 'AI 맞춤 여행지 추천' },
                  ].map(({ emoji, text }) => (
                    <div key={text} className="flex items-center gap-3 rounded-2xl bg-[#FFF8F3] px-4 py-2.5">
                      <span className="text-base">{emoji}</span>
                      <span className="text-sm font-medium text-[#5C3D2B]">{text}</span>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => { setLoginModalOpen(false); navigate("/login"); }}
                  className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-[15px] font-bold text-white transition active:scale-95"
                  style={{ background: 'linear-gradient(135deg, #F4845F 0%, #F06030 100%)' }}
                >
                  <LogIn className="h-4 w-4" />
                  로그인 하러 가기
                </button>
                <p className="mt-3 text-center text-xs text-[#B08B7A]">
                  카카오 · 구글 · 네이버로 간편 가입
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <SubscriptionModal open={subscriptionOpen} onClose={() => setSubscriptionOpen(false)} />
    </>
  );
}
