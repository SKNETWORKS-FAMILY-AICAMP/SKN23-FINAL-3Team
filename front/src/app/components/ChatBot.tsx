import React, { useRef, useEffect, useState } from 'react'
import { Send, LogIn, Lock } from 'lucide-react'
import { useNavigate } from 'react-router'
import type { Pet } from '../types'
import { useChatbot } from '../hooks/useChatbot'
import { DIARY_TYPES } from '../constants/diaryTypes'
import { EMOTIONS } from '../constants/emotions'
import { generateDiaryImage, type GeneratedDiary } from '../services/diaryService'
import { createChatRoom, sendMessageWithResponse, getPlaceByName, type FacilityCard } from '../services/chatService'
import type { PlaceResult } from '../services/placeService'

const BUTTONS_MARKER = '%%BUTTONS%%'
const DIARY_FLOW_TRIGGER = '%%TRIGGER:START_DIARY%%'

function parseMessageButtons(content: string): { text: string; buttons: string[] } {
  const idx = content.indexOf(BUTTONS_MARKER)
  if (idx === -1) return { text: content, buttons: [] }
  const text = content.slice(0, idx).trim()
  const btnPart = content.slice(idx + BUTTONS_MARKER.length)
  const buttons = btnPart.split('|').map((b) => b.trim()).filter(Boolean)
  return { text, buttons }
}

/**
 * 봇 메시지를 렌더링: 이미지 마크다운·요약 줄 제거, **굵게** → <strong>
 */
function renderBotText(content: string): React.ReactNode {
  const lines = content
    .split('\n')
    .filter(line => !/_요약_:/.test(line))
    .filter(line => !/^!\[.*?\]\(https?:\/\//.test(line.trim()))

  return lines.map((line, lineIdx) => {
    const boldParts = line.split(/(\*\*[^*]*\*\*)/g)
    return (
      <span key={lineIdx}>
        {lineIdx > 0 && '\n'}
        {boldParts.map((part, partIdx) =>
          part.startsWith('**') && part.endsWith('**') ? (
            <strong key={partIdx}>{part.slice(2, -2)}</strong>
          ) : (
            <span key={partIdx}>{part}</span>
          )
        )}
      </span>
    )
  })
}

function splitPlaceMessage(text: string) {
  return text
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
}

function buildFallbackPlaceReason(place: {
  category: string
  sub_category: string
  indoor: string
  outdoor: string
  has_parking: string
}) {
  const labels = [place.sub_category, place.category].filter(Boolean)
  const labelText = labels.length > 0 ? `${labels.join(', ')} 장소라서` : '반려견과 함께 방문하기에'

  if (place.indoor === 'Y' && place.outdoor === 'Y') {
    return `${labelText} 실내외 모두 이용할 수 있어 상황에 맞게 방문하기 좋아요.`
  }

  if (place.indoor === 'Y' && place.has_parking === 'Y') {
    return `${labelText} 실내 이용이 가능하고 주차도 가능해 편하게 들르기 좋아요.`
  }

  if (place.indoor === 'Y') {
    return `${labelText} 실내 이용이 가능해 날씨 영향이 적어요.`
  }

  if (place.outdoor === 'Y' && place.has_parking === 'Y') {
    return `${labelText} 야외 활동이 가능하고 주차도 편해서 방문하기 좋아요.`
  }

  if (place.outdoor === 'Y') {
    return `${labelText} 바깥 활동과 함께 들르기 좋아요.`
  }

  if (place.has_parking === 'Y') {
    return `${labelText} 주차가 가능해서 이동 부담이 적어요.`
  }

  return `${labelText} 가볍게 방문해보기 좋아요.`
}

function renderPlaceMessage(
  text: string,
  places?: Array<{
    name: string
    address: string
    category: string
    sub_category: string
    indoor: string
    outdoor: string
    has_parking: string
    reason?: string
  }>,
  onPlaceClick?: (name: string) => void,
) {
  const blocks = splitPlaceMessage(text)
  const fallbackIntro = blocks[0]
  const fallbackOutro = blocks.slice(1)

  return (
    <div className="space-y-3 text-[14px] leading-7 text-[#3D2B1F]">
      {places && places.length > 0 ? (
        <>
          <p>반려견과 함께 가보기 좋은 장소를 정리했어요.</p>
          <div className="space-y-3">
            {places.map((place, index) => {
              return (
                <div key={`${place.name}-${index}`} className="space-y-1">
                  {onPlaceClick ? (
                    <button
                      onClick={() => onPlaceClick(place.name)}
                      className="font-semibold text-[#F4845F] underline underline-offset-2 hover:text-[#e8764f] text-left"
                    >
                      {index + 1}. {place.name} 📍
                    </button>
                  ) : (
                    <p className="font-semibold text-[#2F241D]">
                      {index + 1}. {place.name}
                    </p>
                  )}
                  <p>- 주소: {place.address}</p>
                  <p>- 추천 이유: {place.reason || buildFallbackPlaceReason(place)}</p>
                </div>
              )
            })}
          </div>
          <p>세부 정보는 아래 지도와 장소 카드에서 함께 확인해보세요.</p>
        </>
      ) : (
        <>
          {fallbackIntro && <p>{fallbackIntro}</p>}
          {fallbackOutro.map((line, index) => (
            <p key={`${line}-${index}`}>{line}</p>
          ))}
        </>
      )}
    </div>
  )
}

function renderFacilityMessage(text: string, facility?: FacilityCard, onShowOnMap?: () => void) {
  const lines = text.split('\n').map((l) => l.trim())

  return (
    <div className="space-y-1.5 text-[14px] leading-7 text-[#3D2B1F]">
      {lines.map((line, idx) => {
        if (!line) return null
        const headerM = line.match(/^📍\s*\*\*(.+?)\*\*\s*$/)
        if (headerM) {
          return (
            <p key={idx} className="text-[15px] font-semibold text-[#2F241D]">
              📍 {headerM[1]}
            </p>
          )
        }
        const fieldM = line.match(/^-\s*([^:]+):\s*(.+)$/)
        if (fieldM) {
          const [, label, value] = fieldM
          const muted = value.trim() === '정보 없음'
          return (
            <p key={idx} className={muted ? 'text-[#A89282]' : ''}>
              <span className="font-medium text-[#5C4632]">{label}:</span>{' '}
              <span>{value}</span>
            </p>
          )
        }
        return <p key={idx}>{line}</p>
      })}
      {facility?.match_source === 'vector' && facility.match_confidence < 0.7 && (
        <p className="pt-1 text-[12px] text-[#A89282]">
          (추정 매칭이라 다른 시설일 수 있어요. 정확한 이름을 알려주시면 다시 찾아드릴게요.)
        </p>
      )}
      {onShowOnMap && facility && (
        <button
          onClick={onShowOnMap}
          className="mt-1 flex items-center gap-1 rounded-full border border-[#F4845F] px-3 py-1 text-[12px] font-semibold text-[#F4845F] hover:bg-[#FFF0E6] transition-colors"
        >
          📍 지도에서 보기
        </button>
      )}
    </div>
  )
}

function facilityToPlaceResult(f: FacilityCard): PlaceResult {
  return {
    name: f.name,
    address: f.address,
    category: f.category,
    sub_category: f.sub_category,
    content_id: f.content_id,
    lat: f.lat,
    lng: f.lng,
    tel: f.tel,
    conditions: f.conditions,
    pet_zone: '',
    pet_size: '',
    has_parking: f.has_parking,
    operation: f.operation,
    indoor: f.indoor,
    outdoor: f.outdoor,
    description: f.description,
    firstimage: '',
    similarity: f.match_confidence,
    final_score: f.match_confidence,
  }
}

interface Props {
  pet?: Pet
  onSelectPlace?: (place: PlaceResult) => void
  onPlacesFound?: (places: PlaceResult[]) => void
  onNavigateToMap?: () => void
  onNavigateToDiary?: () => void
  onDiaryReady?: (diary: GeneratedDiary, imageUrl: string) => void
  diaryTrigger?: number
  diaryPlace?: string
  initialMessage?: string
  userLocation?: { lat: number; lng: number }
}

const DEFAULT_PET: Pet = { name: '우리 아이', breed: '강아지' }

export default function ChatBot({
  pet = DEFAULT_PET,
  onSelectPlace: _onSelectPlace,
  onPlacesFound,
  onNavigateToMap,
  onNavigateToDiary,
  onDiaryReady,
  diaryTrigger,
  diaryPlace,
  initialMessage,
  userLocation,
}: Props) {
  const navigate = useNavigate()
  const isLoggedIn = !!localStorage.getItem('access_token')

  const { state, actions } = useChatbot(pet, initialMessage)
  const { step, messages, isGenerating, generatedDiary } = state
  const [inputValue, setInputValue] = useState('')
  const [imageLoading, setImageLoading] = useState(false)
  const [welcomeChatRoomId, setWelcomeChatRoomId] = useState<number | null>(null)
  // welcome 단계 sendMessageWithResponse (KoELECTRA + GPT) 응답 대기 동안 input·send 차단 — race·중복 응답 방지
  const [isResponding, setIsResponding] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const storedPetId = Number(localStorage.getItem('selected_pet_id'))
  const selectedPetId = pet.id ?? (Number.isFinite(storedPetId) && storedPetId > 0 ? storedPetId : undefined)

  // 백엔드 응답에서 일기 데이터 파싱 (형식: "📖 **제목**\n\n내용\n\n_요약_: 요약\n\n![제목](url)")
  const parseDiaryFromResponse = (text: string): { diary: GeneratedDiary; imageUrl: string } | null => {
    const titleM = text.match(/📖 \*\*(.+?)\*\*/)
    const imageM = text.match(/!\[.*?\]\((https?:\/\/.+?)\)/)
    const summaryM = text.match(/_요약_:\s*(.+)/)
    if (!titleM) return null
    const lines = text.split('\n')
    const titleIdx = lines.findIndex(l => /📖 \*\*/.test(l))
    const summaryIdx = summaryM ? lines.findIndex(l => l.includes('_요약_:')) : -1
    const imageIdx = imageM ? lines.findIndex(l => l.includes('![')) : -1
    const contentEnd = [summaryIdx, imageIdx].filter(i => i > 0).sort((a, b) => a - b)[0] ?? lines.length
    const content = lines.slice(titleIdx + 2, contentEnd).join('\n').trim()
    return {
      diary: {
        title: titleM[1],
        content,
        summary: summaryM?.[1]?.trim() ?? '',
      },
      imageUrl: imageM?.[1] ?? '',
    }
  }

  // welcome 스텝에서 백엔드 AI 채팅 호출
  const sendWelcomeMessage = async (text: string) => {
    setIsResponding(true)
    try {
      let roomId = welcomeChatRoomId
      if (roomId === null) {
        const room = await createChatRoom(text.slice(0, 30))
        roomId = room.id
        setWelcomeChatRoomId(roomId)
      }
      const result = await sendMessageWithResponse(roomId, text, selectedPetId, userLocation?.lat, userLocation?.lng)
      const intent = result.intent.intent
      const botText = result.assistant_message.content

      // 순수 시작 요청 트리거 — [그림일기] 버튼 클릭과 동일하게 동작
      if (botText === DIARY_FLOW_TRIGGER) {
        actions.triggerDiaryFlow()
        onNavigateToDiary?.()
        return
      }

      if (intent === '다이어리 작성') {
        const parsed = parseDiaryFromResponse(botText)
        if (parsed?.imageUrl) {
          actions.receiveBotMessage(botText)
          onDiaryReady?.(parsed.diary, parsed.imageUrl)
        } else {
          actions.receiveBotMessage(botText)
        }
      } else if (intent === '장소추천') {
        const places = result.places ?? []
        onPlacesFound?.(places)
        actions.receiveBotMessage(botText, undefined, 'place', places)
        setTimeout(() => onNavigateToMap?.(), 800)
      } else if (intent === '시설정보') {
        const facility = result.facility
        if (facility) {
          const mappedPlace = facilityToPlaceResult(facility)
          onPlacesFound?.([mappedPlace])
          actions.receiveBotMessage(botText, undefined, 'facility', undefined, facility)
          setTimeout(() => onNavigateToMap?.(), 800)
        } else {
          actions.receiveBotMessage(botText)
        }
      } else {
        actions.receiveBotMessage(botText)
      }
    } catch {
      actions.receiveBotMessage('죄송해요, 지금은 응답을 만들지 못했어요. 다시 시도해주세요.')
    } finally {
      setIsResponding(false)
    }
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!diaryTrigger) return
    actions.forceStartDiary(diaryPlace)
    onNavigateToDiary?.()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diaryTrigger])

  const handleSubmitText = () => {
    if (isResponding || isGenerating) return
    const trimmed = inputValue.trim()
    if (!trimmed) return
    if (step === 'main_questions') actions.submitMainAnswer(trimmed)
    else if (step === 'additional_questions') actions.submitAdditionalAnswer(trimmed)
    else if (step === 'welcome' && isLoggedIn) {
      actions.submitWelcomeChat(trimmed)
      sendWelcomeMessage(trimmed)
    }
    setInputValue('')
  }

  const handleGenerateImage = async () => {
    if (!generatedDiary?.image_prompt) {
      alert('이미지 프롬프트가 없어요. 백엔드 서버가 실행 중인지 확인해주세요.')
      return
    }
    setImageLoading(true)
    try {
      const url = await generateDiaryImage(generatedDiary.image_prompt, generatedDiary.session_id)
      // 이미지 완성 → 왼쪽 그림일기 결과 페이지로 전달
      onDiaryReady?.(generatedDiary, url)
    } catch {
      alert('이미지 생성에 실패했어요. 다시 시도해주세요.')
    } finally {
      setImageLoading(false)
    }
  }

  const handleStartDiary = () => {
    actions.startDiary()
    onNavigateToDiary?.()
  }

  return (
    <div className="relative flex h-full flex-col rounded-[20px] overflow-hidden bg-[#FFF8F3]">
      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {messages.map((msg) => {
          const { text: displayText, buttons: inlineButtons } = parseMessageButtons(msg.content)
          return (
            <div key={msg.id} className={`flex items-end gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              {msg.role === 'bot' && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center mb-0.5">
                  <img src="/chatbot_logo.svg" alt="AI 멍봇" className="h-8 w-8 object-contain" />
                </div>
              )}
              <div className={`max-w-[80%]`}>
              <div
                className={`rounded-2xl px-4 py-2.5 text-sm leading-6 whitespace-pre-wrap ${msg.role === 'bot'
                  ? 'bg-white text-[#3D2B1F] shadow-sm'
                  : 'bg-[#F4845F] text-white'
                  }`}
              >
                {msg.role === 'bot'
                  ? (msg.variant === 'place'
                      ? renderPlaceMessage(displayText, msg.places, async (name) => {
                          try {
                            const facility = await getPlaceByName(name)
                            const place = facilityToPlaceResult(facility)
                            onPlacesFound?.([place])
                            setTimeout(() => onNavigateToMap?.(), 100)
                          } catch { /* 장소를 찾지 못한 경우 무시 */ }
                        })
                      : msg.variant === 'facility'
                        ? renderFacilityMessage(displayText, msg.facility, msg.facility ? () => {
                            const place = facilityToPlaceResult(msg.facility!)
                            onPlacesFound?.([place])
                            setTimeout(() => onNavigateToMap?.(), 100)
                          } : undefined)
                        : renderBotText(displayText))
                  : displayText}
              </div>
              {/* 백엔드 %%BUTTONS%% 인라인 버튼 */}
              {inlineButtons.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2">
                  {inlineButtons.map((btn, btnIdx) => (
                    <button
                      key={btn}
                      onClick={() => {
                        actions.submitWelcomeChat(btn)
                        sendWelcomeMessage(btn)
                      }}
                      className={
                        btnIdx === 0
                          ? 'rounded-full border border-[#F4845F] bg-[#F4845F] px-3.5 py-1.5 text-[13px] font-semibold text-white transition hover:bg-[#e8764f]'
                          : 'rounded-full border border-[#F5D6C8] bg-white px-3.5 py-1.5 text-[13px] font-semibold text-[#8B6355] transition hover:bg-[#FFF0E6]'
                      }
                    >
                      {btn}
                    </button>
                  ))}
                </div>
              )}
              {msg.action === 'start_diary' && (
                <button
                  onClick={() => { actions.startDiary(); onNavigateToDiary?.() }}
                  className="mt-2 flex items-center gap-1.5 rounded-full border border-[#F4845F] bg-[#F4845F] px-4 py-2 text-[13px] font-semibold text-white transition hover:bg-[#e8764f]"
                >
                  그림일기 작성하기
                </button>
              )}
              </div>
            </div>
          )
        })}

        {/* 비로그인 안내 말풍선 */}
        {!isLoggedIn && (
          <div className="space-y-2">
            <div className="max-w-[88%] rounded-2xl bg-white px-4 py-2.5 text-sm leading-6 text-[#3D2B1F] shadow-sm">
              🔒 로그인 후 이용 가능한 서비스예요.{'\n'}로그인하고 우리 아이의 일기와 장소 추천을 함께 만들어봐요!
            </div>
            <button
              onClick={() => navigate('/login')}
              className="flex items-center gap-2 rounded-full border border-[#F4845F] bg-[#F4845F] px-4 py-2 text-[13px] font-semibold text-white transition hover:bg-[#e8764f]"
            >
              <LogIn className="h-3.5 w-3.5" />
              로그인 하러 가기
            </button>
          </div>
        )}

        {/* 웰컴 버튼: 말풍선 바로 아래 인라인 */}
        {step === 'welcome' && isLoggedIn && !messages.some(m => m.role === 'user') && (
          <div className="flex flex-wrap gap-2 pt-1 pl-10">
            <button
              onClick={handleStartDiary}
              className="rounded-full border border-[#F4845F] bg-white px-3.5 py-1.5 text-[13px] font-semibold text-[#F4845F] transition hover:bg-[#FFF7F3]"
            >
              그림일기
            </button>
            <button
              onClick={() => {
                actions.submitWelcomeChat('반려견과 함께 가기 좋은 장소를 추천해줘')
                sendWelcomeMessage('반려견과 함께 가기 좋은 장소를 추천해줘')
              }}
              className="rounded-full border border-[#F4845F] bg-white px-3.5 py-1.5 text-[13px] font-semibold text-[#F4845F] transition hover:bg-[#FFF7F3]"
            >
              장소 추천
            </button>
          </div>
        )}

        {/* 일기 완성 후 인라인 버튼 */}
        {step === 'diary_result' && generatedDiary && (
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={handleGenerateImage}
              disabled={imageLoading}
              className="rounded-full border border-[#F4845F] bg-[#F4845F] px-3.5 py-1.5 text-[13px] font-semibold text-white transition hover:bg-[#e8764f] disabled:opacity-60"
            >
              {imageLoading ? '그림 그리는 중... 🎨' : '그림일기로 만들어줘'}
            </button>
            <button
              onClick={actions.restartDiary}
              className="rounded-full border border-[#F5D6C8] bg-white px-3.5 py-1.5 text-[13px] font-semibold text-[#8B6355] transition hover:bg-[#FFF0E6]"
            >
              일기 다시 쓰고 싶어
            </button>
          </div>
        )}

        {/* 생성 중 점 애니메이션 */}
        {isGenerating && (
          <div className="max-w-[88%] rounded-2xl bg-white px-4 py-3 shadow-sm">
            <span className="flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-[#F4845F]" style={{ animationDelay: '0ms' }} />
              <span className="h-2 w-2 animate-bounce rounded-full bg-[#F4845F]" style={{ animationDelay: '150ms' }} />
              <span className="h-2 w-2 animate-bounce rounded-full bg-[#F4845F]" style={{ animationDelay: '300ms' }} />
            </span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* 하단 패널 */}
      <div className="border-t border-[#F5D6C8] bg-[#FFF8F3]">

        {/* 비로그인 잠금 입력창 */}
        {!isLoggedIn && (
          <div className="flex items-center gap-2 p-3">
            <div className="flex flex-1 items-center gap-2 rounded-xl border border-[#F5D6C8] bg-[#F8F5F2] px-3 py-2.5">
              <Lock className="h-4 w-4 shrink-0 text-[#C4A99A]" />
              <span className="text-sm text-[#C4A99A]">로그인 후 사용 가능합니다</span>
            </div>
            <button
              onClick={() => navigate('/login')}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F4845F] text-white"
            >
              <LogIn className="h-4 w-4" />
            </button>
          </div>
        )}

        {isLoggedIn && <>

          {/* 일기 유형 선택 */}
          {step === 'type_select' && (
            <div className="grid grid-cols-2 gap-2 p-3">
              {DIARY_TYPES.map((dt) => (
                <button
                  key={dt.id}
                  onClick={() => actions.selectDiaryType(dt.id)}
                  className="flex flex-col items-start rounded-xl border border-[#F5D6C8] bg-[#FFFAF7] px-3 py-3 text-left transition hover:border-[#F4845F] hover:bg-[#FFF0E6]"
                >
                  <span className="mb-1 text-xl">{dt.icon}</span>
                  <span className="text-xs font-bold text-[#3D2B1F]">{dt.label}</span>
                  <span className="text-[10px] text-[#8B6355]">{dt.description}</span>
                </button>
              ))}
            </div>
          )}

          {/* 보조 관점 제안 */}
          {step === 'additional_prompt' && (
            <div className="flex gap-2 p-3">
              <button
                onClick={() => actions.respondToPerspective(true)}
                className="flex-1 rounded-xl bg-[#F4845F] py-3 text-sm font-bold text-white transition hover:bg-[#e8764f]"
              >
                네, 좋아요!
              </button>
              <button
                onClick={() => actions.respondToPerspective(false)}
                className="flex-1 rounded-xl border border-[#F5D6C8] py-3 text-sm font-medium text-[#8B6355] transition hover:bg-[#FFF0E6]"
              >
                괜찮아요
              </button>
            </div>
          )}

          {/* 감정 선택 */}
          {step === 'emotion_select' && (
            <div className="grid grid-cols-4 gap-2 p-3">
              {EMOTIONS.map((em) => (
                <button
                  key={em.emoji}
                  onClick={() => actions.selectEmotion(em.emoji, em.label)}
                  className="flex flex-col items-center rounded-xl border border-[#F5D6C8] bg-[#FFFAF7] py-2.5 transition hover:border-[#F4845F] hover:bg-[#FFF0E6]"
                >
                  <span className="text-2xl">{em.emoji}</span>
                  <span className="mt-1 text-[10px] text-[#8B6355]">{em.label}</span>
                </button>
              ))}
            </div>
          )}

          {/* 텍스트 입력창 — 응답 진행 중 (welcome 의 KoELECTRA+GPT 또는 다이어리 generating) 입력 차단 */}
          {(step === 'welcome' || step === 'main_questions' || step === 'additional_questions') && (
            <div className="flex items-center gap-2 p-3">
              <input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    if (isResponding || isGenerating) return
                    handleSubmitText()
                  }
                }}
                disabled={isResponding || isGenerating}
                placeholder={isResponding || isGenerating ? '응답 받는 중...' : '편하게 말씀해주세요...'}
                className="flex-1 rounded-xl border border-[#F5D6C8] bg-white px-3 py-2.5 text-sm outline-none transition focus:border-[#F4845F] disabled:cursor-not-allowed disabled:bg-[#FFF8F3] disabled:text-[#B08B7A]"
              />
              <button
                onClick={handleSubmitText}
                disabled={!inputValue.trim() || isResponding || isGenerating}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F4845F] text-white transition disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          )}
        </>}
      </div>

    </div>
  )
}
