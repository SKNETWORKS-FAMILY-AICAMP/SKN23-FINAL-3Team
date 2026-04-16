import { useRef, useEffect, useState } from 'react'
import { Send } from 'lucide-react'
import type { Pet } from '../types'
import { useChatbot } from '../hooks/useChatbot'
import { DIARY_TYPES } from '../constants/diaryTypes'
import { EMOTIONS } from '../constants/emotions'
import { generateDiaryImage, type GeneratedDiary } from '../services/diaryService'

interface Props {
  pet?: Pet
  onSelectPlace?: (place: string) => void
  onNavigateToMap?: () => void
  onNavigateToDiary?: () => void
  onDiaryReady?: (diary: GeneratedDiary, imageUrl: string) => void
  diaryTrigger?: number
}

const DEFAULT_PET: Pet = { name: '우리 아이', breed: '강아지' }

export default function ChatBot({
  pet = DEFAULT_PET,
  onSelectPlace: _onSelectPlace,
  onNavigateToMap,
  onNavigateToDiary,
  onDiaryReady,
  diaryTrigger,
}: Props) {
  const { state, actions } = useChatbot(pet)
  const { step, messages, isGenerating, generatedDiary } = state
  const [inputValue, setInputValue] = useState('')
  const [imageLoading, setImageLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!diaryTrigger) return
    actions.forceStartDiary()
    onNavigateToDiary?.()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diaryTrigger])

  const handleSubmitText = () => {
    const trimmed = inputValue.trim()
    if (!trimmed) return
    if (step === 'main_questions') actions.submitMainAnswer(trimmed)
    else if (step === 'additional_questions') actions.submitAdditionalAnswer(trimmed)
    setInputValue('')
  }

  const handleGenerateImage = async () => {
    if (!generatedDiary?.image_prompt) return
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

  const handleNavigateToMap = () => {
    onNavigateToMap?.()
  }

  return (
    <div className="flex h-full flex-col">
      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-sm leading-6 whitespace-pre-wrap ${
              msg.role === 'bot'
                ? 'bg-white text-[#3D2B1F] shadow-sm'
                : 'ml-auto bg-[#F4845F] text-white'
            }`}
          >
            {msg.content}
          </div>
        ))}

        {/* 웰컴 버튼: 말풍선 바로 아래 인라인 */}
        {step === 'welcome' && (
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={handleStartDiary}
              className="rounded-full border border-[#F4845F] bg-white px-3.5 py-1.5 text-[13px] font-semibold text-[#F4845F] transition hover:bg-[#FFF7F3]"
            >
              그림일기
            </button>
            <button
              onClick={handleNavigateToMap}
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
      <div className="border-t border-[#F5D6C8] bg-white">

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
          <div className="grid grid-cols-3 gap-2 p-3">
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

        {/* 텍스트 입력창 */}
        {(step === 'welcome' || step === 'main_questions' || step === 'additional_questions') && (
          <div className="flex items-center gap-2 p-3">
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmitText()
                }
              }}
              placeholder="편하게 말씀해주세요..."
              className="flex-1 rounded-xl border border-[#F5D6C8] bg-[#FFFAF7] px-3 py-2.5 text-sm outline-none transition focus:border-[#F4845F]"
            />
            <button
              onClick={handleSubmitText}
              disabled={!inputValue.trim()}
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F4845F] text-white disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
