// 백엔드 REST API (users, pets, breeds, diaries, chat, images 등)
// fallback: VITE_API_URL 미지정 시, 페이지가 열린 호스트의 8000 포트로 자동 결정.
// → 호스트 노트북: http://localhost:8000, 같은 Wi-Fi 다른 노트북: http://<호스트IP>:8000
const BASE_URL =
  import.meta.env.VITE_API_URL ??
  `${window.location.protocol}//${window.location.hostname}:8000`

function getToken(): string | null {
  return localStorage.getItem('access_token')
}

function authHeaders(): HeadersInit {
  const token = getToken()
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

/**
 * 백엔드 detail 페이로드를 사용자 친화 메시지 1줄로 정규화한다.
 *
 * - FastAPI HTTPException(detail=string) → 그대로 사용
 * - Pydantic v2 ValidationError → `[{type,loc,msg,input}]` 배열 → 각 msg join.
 *   Pydantic 의 `Value error, ` 접두사는 제거 (`raise ValueError(...)` 한 한국어 메시지만 노출)
 * - detail 부재 → `API 오류 {status}`
 */
function normalizeDetail(detail: unknown, status: number): string {
  if (typeof detail === 'string' && detail) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail
      .map((d) => {
        if (d && typeof d === 'object' && 'msg' in d) {
          const msg = String((d as { msg: unknown }).msg ?? '')
          return msg.replace(/^Value error,\s*/, '').trim()
        }
        return String(d)
      })
      .filter(Boolean)
    if (messages.length > 0) return messages.join('\n')
  }
  return `API 오류 ${status}`
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    // 토큰 만료 또는 무효 → 자동 로그아웃
    localStorage.removeItem('access_token')
    window.dispatchEvent(new Event('auth-change'))
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: unknown }
    throw new Error(normalizeDetail(err.detail, res.status))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get<T>(path: string): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      headers: authHeaders(),
    }).then((r) => handleResponse<T>(r))
  },

  post<T>(path: string, body?: unknown): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: authHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then((r) => handleResponse<T>(r))
  },

  patch<T>(path: string, body: unknown): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(body),
    }).then((r) => handleResponse<T>(r))
  },

  delete<T = void>(path: string): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: 'DELETE',
      headers: authHeaders(),
    }).then((r) => handleResponse<T>(r))
  },

  /** multipart/form-data 업로드 전용 */
  upload<T>(path: string, file: File): Promise<T> {
    const token = getToken()
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    }).then((r) => handleResponse<T>(r))
  },
}
