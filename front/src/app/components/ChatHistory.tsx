import { useState, useEffect } from 'react'
import { ArrowLeft, MessageSquare, Clock } from 'lucide-react'
import { getMe } from '../services/userService'
import { getChatRooms, getMessages, getPlaceByName, type ChatRoom, type ChatMessage } from '../services/chatService'
import { type PlaceResult } from '../services/placeService'

interface Props {
  onBack: () => void
  onShowPlaces?: (places: PlaceResult[], selected: PlaceResult) => void
}

// 장소 추천 메시지 여부 감지
function isPlaceMessage(content: string): boolean {
  return /\d+\.\s+.+/.test(content) && /주소:/.test(content)
}

// 텍스트에서 번호 + 장소명 추출
function extractPlaceEntries(content: string): { name: string; address: string }[] {
  const entries: { name: string; address: string }[] = []
  const lines = content.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const nameMatch = lines[i].match(/^\d+\.\s+(.+)$/)
    if (nameMatch) {
      const name = nameMatch[1].trim()
      let address = ''
      for (let j = i + 1; j < Math.min(i + 12, lines.length); j++) {
        if (!address) {
          const addrMatch = lines[j].match(/[-–]\s*주소:\s*(.+)/)
          if (addrMatch) address = addrMatch[1].trim()
        }
      }
      entries.push({ name, address })
    }
  }
  return entries
}

// 장소 메시지를 파싱해서 장소명만 링크로 렌더링
function renderHistoryPlaceMessage(
  content: string,
  loadingName: string | null,
  notFoundName: string | null,
  onPlaceClick: (entry: { name: string; address: string }) => void,
) {
  const entries = extractPlaceEntries(content)
  const lines = content.split('\n')

  return (
    <div className="space-y-0.5 text-sm leading-7">
      {lines.map((line, i) => {
        const nameMatch = line.match(/^(\d+)\.\s+(.+)$/)
        if (nameMatch) {
          const num = nameMatch[1]
          const name = nameMatch[2].trim()
          const found = entries.find((e) => e.name === name)
          if (found) {
            const isLoading = loadingName === name
            const isNotFound = notFoundName === name
            return (
              <p key={i}>
                {num}.{' '}
                <button
                  onClick={() => !isLoading && onPlaceClick(found)}
                  disabled={isLoading}
                  className="font-semibold text-[#F4845F] underline underline-offset-2 hover:text-[#e8764f] transition-colors disabled:opacity-60"
                >
                  {isLoading ? '불러오는 중...' : name}
                </button>
                {isNotFound && (
                  <span className="ml-2 text-xs text-[#B08B7A]">정보를 찾을 수 없어요</span>
                )}
              </p>
            )
          }
        }
        return <p key={i}>{line}</p>
      })}
    </div>
  )
}

export default function ChatHistory({ onBack, onShowPlaces }: Props) {
  const [rooms, setRooms] = useState<ChatRoom[]>([])
  const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [msgLoading, setMsgLoading] = useState(false)
  const [loadingPlace, setLoadingPlace] = useState<string | null>(null)
  const [notFoundPlace, setNotFoundPlace] = useState<string | null>(null)


  useEffect(() => {
    getMe()
      .then((me) => getChatRooms(me.id))
      .then((data) => {
        setRooms([...data].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSelectRoom = (room: ChatRoom) => {
    setSelectedRoom(room)
    setMsgLoading(true)
    getMessages(room.id)
      .then(setMessages)
      .catch(() => setMessages([]))
      .finally(() => setMsgLoading(false))
  }

  const handlePlaceClick = async ({ name }: { name: string; address: string }) => {
    if (!onShowPlaces) return
    setLoadingPlace(name)
    try {
      const facility = await getPlaceByName(name)
      const place: PlaceResult = {
        name: facility.name,
        address: facility.address,
        category: facility.category,
        sub_category: facility.sub_category,
        content_id: facility.content_id,
        lat: facility.lat,
        lng: facility.lng,
        tel: facility.tel,
        conditions: facility.conditions,
        pet_zone: '',
        pet_size: '',
        has_parking: facility.has_parking,
        operation: facility.operation,
        indoor: facility.indoor,
        outdoor: facility.outdoor,
        description: facility.description,
        firstimage: '',
        similarity: facility.match_confidence,
        final_score: facility.match_confidence,
      }
      onShowPlaces([place], place)
    } catch {
      setNotFoundPlace(name)
      setTimeout(() => setNotFoundPlace(null), 3000)
    } finally {
      setLoadingPlace(null)
    }
  }

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })

  /* ── 메시지 상세 뷰 ─────────────────────────────── */
  if (selectedRoom) {
    return (
      <div className="flex h-full flex-col bg-[#FFF8F3]">
        <div className="flex items-center gap-2 border-b border-[#F5D6C8] bg-white px-4 py-3">
          <button
            onClick={() => setSelectedRoom(null)}
            className="flex items-center gap-1 text-[#8B6355] transition hover:text-[#F4845F]"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <p className="flex-1 truncate text-sm font-bold text-[#3D2B1F]">{selectedRoom.title}</p>
          <span className="text-[11px] text-[#B08B7A]">{formatDate(selectedRoom.updated_at)}</span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 p-4">
          {msgLoading ? (
            <div className="flex h-full items-center justify-center">
              <span className="text-sm text-[#B08B7A]">불러오는 중...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <span className="text-sm text-[#B08B7A]">저장된 메시지가 없어요.</span>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-sm leading-6 whitespace-pre-wrap ${
                  msg.role === 'assistant'
                    ? 'bg-white text-[#3D2B1F] shadow-sm'
                    : 'ml-auto bg-[#F4845F] text-white'
                }`}
              >
                {msg.role === 'assistant' && isPlaceMessage(msg.content)
                  ? renderHistoryPlaceMessage(msg.content, loadingPlace, notFoundPlace, handlePlaceClick)
                  : msg.content}
              </div>
            ))
          )}
        </div>

        <div className="border-t border-[#F5D6C8] bg-white px-4 py-3">
          <button
            onClick={onBack}
            className="w-full rounded-xl bg-[#F4845F] py-2.5 text-sm font-bold text-white transition hover:bg-[#e8764f]"
          >
            챗봇 대화로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  /* ── 채팅방 목록 뷰 ─────────────────────────────── */
  return (
    <div className="flex h-full flex-col bg-[#FFF8F3]">
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <span className="text-sm text-[#B08B7A]">불러오는 중...</span>
          </div>
        ) : rooms.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <span className="text-5xl">💬</span>
            <p className="text-sm font-bold text-[#3D2B1F]">저장된 대화 기록이 없어요</p>
            <p className="text-xs text-[#8B6355]">챗봇과 대화를 나눠보세요!</p>
          </div>
        ) : (
          <div className="space-y-2">
            {rooms.map((room) => (
              <button
                key={room.id}
                onClick={() => handleSelectRoom(room)}
                className="w-full rounded-2xl border border-[#F5D6C8] bg-white p-4 text-left transition hover:border-[#F4845F] hover:bg-[#FFF0E6]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#FFE8D6]">
                    <MessageSquare className="h-4 w-4 text-[#F4845F]" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-[#3D2B1F]">{room.title}</p>
                    <div className="mt-0.5 flex items-center gap-1 text-[11px] text-[#B08B7A]">
                      <Clock className="h-3 w-3" />
                      {formatDate(room.updated_at)}
                    </div>
                  </div>
                  <ArrowLeft className="h-4 w-4 rotate-180 text-[#D0B5A8] shrink-0" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-[#F5D6C8] bg-white px-4 py-3">
        <button
          onClick={onBack}
          className="w-full rounded-xl border border-[#F5D6C8] py-2.5 text-sm font-semibold text-[#8B6355] transition hover:bg-[#FFF0E6]"
        >
          ← 챗봇 대화로 돌아가기
        </button>
      </div>
    </div>
  )
}
