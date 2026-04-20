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
} from "lucide-react";

interface SubItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

interface NavItem {
  icon: React.ElementType;
  label: string;
  path?: string;
  subItems?: SubItem[];
}

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem('access_token'));
  const [openSubMenu, setOpenSubMenu] = useState<string | null>(null);
  const [hoveredMenu, setHoveredMenu] = useState<string | null>(null);

  const { scrollY } = useScroll();
  const navigate = useNavigate();
  const location = useLocation();

  // 로그인 상태를 항상 최신으로 동기화
  useEffect(() => {
    const syncAuth = () => setIsLoggedIn(!!localStorage.getItem('access_token'));
    // 같은 탭에서 발생하는 커스텀 이벤트 (로그인/로그아웃)
    window.addEventListener('auth-change', syncAuth);
    // 다른 탭에서 발생하는 storage 이벤트
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
    { icon: Calendar, label: "멍캘린더", path: "/calendar" },
    { icon: User, label: "마이페이지", path: "/mypage" },
  ];

  const handleNavClick = (item: NavItem) => {
    if (item.subItems) {
      setOpenSubMenu(openSubMenu === item.label ? null : item.label);
    } else if (item.path) {
      navigate(item.path);
      setOpenSubMenu(null);
      setMobileOpen(false);
    }
  };

  return (
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
          <Link to="/home" className="flex items-center gap-1.5 select-none cursor-pointer hover:opacity-75 transition-opacity">
            <span className="text-xl font-black tracking-tight text-orange-500">with</span>
            <span className="text-xl font-black tracking-tight text-gray-800">DOG</span>
            <span className="text-lg leading-none">🐾</span>
          </Link>

      {/* 오른쪽: 메뉴 + 로그인 */}
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
        <button
          onClick={() => {
            if (isLoggedIn) {
              localStorage.removeItem('access_token');
              window.dispatchEvent(new Event('auth-change'));
              navigate("/login");
            } else {
              navigate("/login");
            }
          }}
          className="ml-4 px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-sm font-medium transition-colors"
        >
          {isLoggedIn ? "로그아웃" : "로그인"}
        </button>
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
              const isActive = item.path && location.pathname === item.path;
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

            <button
              onClick={() => {
                if (isLoggedIn) {
                  localStorage.removeItem('access_token');
                  setIsLoggedIn(false);
                  navigate("/login");
                } else {
                  navigate("/login");
                }
                setMobileOpen(false);
              }}
              className="mt-2 px-4 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-sm font-medium transition-colors"
            >
              {isLoggedIn ? "로그아웃" : "로그인"}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}