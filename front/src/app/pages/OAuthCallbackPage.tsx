import { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router';

// fallback: VITE_API_URL 미지정 시, 페이지가 열린 호스트의 8000 포트로 자동 결정
// → 같은 Wi-Fi 다른 노트북에서 접속해도 그 노트북이 자기 localhost 가 아닌 호스트 IP 로 호출
const API_URL =
  import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`;
const REDIRECT_URI = `${window.location.origin}/oauth/callback`;

export function OAuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const calledRef = useRef(false); // React StrictMode 이중 호출 방지

  useEffect(() => {
    if (calledRef.current) return; // 이미 실행됐으면 skip
    calledRef.current = true;

    const code = searchParams.get('code');
    const state = searchParams.get('state') ?? '';
    const error = searchParams.get('error');
    const provider = sessionStorage.getItem('oauth_provider');

    // 에러 또는 필수값 누락 시 로그인으로
    if (error || !code || !provider) {
      console.error('OAuth 콜백 오류:', { error, code, provider });
      navigate('/login');
      return;
    }

    const login = async () => {
      try {
        const params = new URLSearchParams({
          code,
          redirect_uri: REDIRECT_URI,
          ...(state ? { state } : {}),
        });

        const res = await fetch(`${API_URL}/auth/${provider}?${params}`, {
          method: 'POST',
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err?.detail ?? '로그인 실패');
        }

        const data = await res.json();
        localStorage.setItem('access_token', data.access_token);
        sessionStorage.removeItem('oauth_provider');
        window.dispatchEvent(new Event('auth-change'));

        // 신규 유저이거나 펫이 없으면 → 온보딩, 펫 있으면 → 홈
        if (data.is_new_user) {
          navigate('/step', { replace: true });
          return;
        }

        // 기존 유저: 약관 동의 / 펫 등록 여부 확인
        const token = data.access_token;
        const meRes = await fetch(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!meRes.ok) {
          navigate('/home', { replace: true });
          return;
        }
        const me = await meRes.json();

        // 약관·개인정보처리방침 미동의 → /step 강제 재진입 (외부팀 QA #76).
        // 마이그레이션 직후 모든 기존 사용자가 일시적으로 NULL 상태 → 1회 동의 후 자연 통과.
        if (!me.terms_agreed_at || !me.privacy_agreed_at) {
          navigate('/step', { replace: true });
          return;
        }

        const petsRes = await fetch(`${API_URL}/pets?user_id=${me.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const pets = petsRes.ok ? await petsRes.json() : [];

        navigate(pets.length === 0 ? '/step' : '/home', { replace: true });
      } catch (err) {
        console.error('소셜 로그인 오류:', err);
        sessionStorage.removeItem('oauth_provider');
        navigate('/login');
      }
    };

    login();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-orange-50 via-white to-orange-100">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-orange-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-600">로그인 중...</p>
      </div>
    </div>
  );
}
