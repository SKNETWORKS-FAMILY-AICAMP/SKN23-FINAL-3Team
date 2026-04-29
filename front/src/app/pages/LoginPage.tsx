import { useNavigate } from 'react-router';
import { Dog } from 'lucide-react';

const REDIRECT_URI = `${window.location.origin}/oauth/callback`;

const OAUTH_URLS: Record<string, string> = {
  kakao: `https://kauth.kakao.com/oauth/authorize?client_id=${import.meta.env.VITE_KAKAO_CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&response_type=code`,
  google: `https://accounts.google.com/o/oauth2/v2/auth?client_id=${import.meta.env.VITE_GOOGLE_CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&response_type=code&scope=email%20profile`,
  naver: `https://nid.naver.com/oauth2.0/authorize?client_id=${import.meta.env.VITE_NAVER_CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&response_type=code&state=${Math.random().toString(36).substring(2)}`,
};

export function LoginPage() {
  const navigate = useNavigate();

  const handleSocialLogin = (provider: string) => {
    const url = OAUTH_URLS[provider];
    if (!url) return;
    sessionStorage.setItem('oauth_provider', provider); // 콜백에서 provider 식별용
    window.location.href = url;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-orange-100 flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="bg-gradient-to-br from-orange-400 to-orange-600 p-3 rounded-2xl">
              <Dog className="w-8 h-8 text-white" />
            </div>
            <span className="text-3xl font-bold text-gray-900">Dangda</span>
          </div>
          <h1 className="text-gray-900 mx-[0px] mt-[0px] mb-[5px] p-[0px]">로그인</h1>
        </div>

        {/* Login Card */}
        <div className="p-8">

          {/* Social Login Buttons */}
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => handleSocialLogin('google')}
              className="w-16 h-16 flex items-center justify-center bg-white border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 rounded-full transition-all"
              title="Google로 로그인"
            >
              <svg className="w-7 h-7" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            </button>

            <button
              onClick={() => handleSocialLogin('kakao')}
              className="w-16 h-16 flex items-center justify-center rounded-full transition-all hover:opacity-90"
              style={{ backgroundColor: '#FEE500' }}
              title="카카오로 로그인"
            >
              <svg className="w-7 h-7" viewBox="0 0 24 24" fill="#000000">
                <path d="M12 3C6.477 3 2 6.477 2 10.8c0 2.863 1.922 5.374 4.818 6.78-.198.73-.644 2.478-.735 2.868-.11.478.172.471.372.343.164-.107 2.63-1.798 3.048-2.094C10.155 18.884 11.053 19 12 19c5.523 0 10-3.477 10-7.8S17.523 3 12 3z" />
              </svg>
            </button>

            <button
              onClick={() => handleSocialLogin('naver')}
              className="w-16 h-16 flex items-center justify-center rounded-full transition-all hover:opacity-90"
              style={{ backgroundColor: '#03C75A' }}
              title="네이버로 로그인"
            >
              <svg className="w-7 h-7" viewBox="0 0 24 24" fill="white">
                <path d="M16.273 12.845L7.376 0H0v24h7.726V11.156L16.624 24H24V0h-7.727z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Back to Home */}
        <div className="text-center">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 text-sm font-medium px-[0px] py-[20px]"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );
}
