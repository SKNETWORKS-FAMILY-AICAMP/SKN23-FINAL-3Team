import { useReducer, useEffect, useCallback, useRef } from 'react'
import type { Pet } from '../types'
import { DIARY_TYPES, type DiaryTypeId } from '../constants/diaryTypes'
import { EMOTIONS } from '../constants/emotions'
import { generateDiary, type GeneratedDiary } from '../services/diaryService'
import { createChatRoom, saveMessage } from '../services/chatService'

// ── 메시지 타입 ──────────────────────────────────────
export interface Message {
  id: string
  role: 'bot' | 'user'
  content: string
  action?: 'start_diary'
  variant?: 'place'
  places?: Array<{
    name: string
    address: string
    category: string
    sub_category: string
    indoor: string
    outdoor: string
    has_parking: string
    reason?: string
  }>
}

// ── 챗봇 단계 ────────────────────────────────────────
export type Step =
  | 'welcome'
  | 'type_select'
  | 'main_questions'
  | 'additional_prompt'
  | 'additional_questions'
  | 'emotion_select'
  | 'diary_generating'
  | 'diary_result'

// ── 상태 ─────────────────────────────────────────────
export interface ChatbotState {
  step: Step
  pet: Pet
  selectedDiaryType: DiaryTypeId | null
  currentQuestionIndex: number
  messages: Message[]
  mainAnswers: string[]
  additionalPerspectiveAccepted: boolean | null
  additionalAnswers: string[]
  additionalQuestionIndex: number
  selectedEmotionEmoji: string | null
  selectedEmotionLabel: string | null
  generatedDiary: GeneratedDiary | null
  isGenerating: boolean
}

// ── 액션 ─────────────────────────────────────────────
export type ChatbotAction =
  | { type: 'START_DIARY' }
  | { type: 'UPDATE_PET'; pet: Pet }
  | { type: 'FORCE_START_DIARY' }
  | { type: 'SELECT_DIARY_TYPE'; id: DiaryTypeId }
  | { type: 'SUBMIT_MAIN_ANSWER'; answer: string }
  | { type: 'RESPOND_TO_PERSPECTIVE'; accepted: boolean }
  | { type: 'SUBMIT_ADDITIONAL_ANSWER'; answer: string }
  | { type: 'SELECT_EMOTION'; emoji: string; label: string }
  | { type: 'SET_DIARY'; diary: GeneratedDiary }
  | { type: 'RESTART_DIARY' }
  | { type: 'REGENERATE' }
  | { type: 'RESET' }
  | { type: 'SUBMIT_WELCOME_CHAT'; text: string }
  | { type: 'TRIGGER_DIARY_FLOW' }
  | {
      type: 'RECEIVE_BOT_MESSAGE'
      text: string
      action?: 'start_diary'
      variant?: 'place'
      places?: Array<{
        name: string
        address: string
        category: string
        sub_category: string
        indoor: string
        outdoor: string
        has_parking: string
        reason?: string
      }>
    }

// ── 헬퍼 ─────────────────────────────────────────────
let _counter = 0
const nextId = () => `msg-${++_counter}`
const botMsg = (content: string): Message => ({ id: nextId(), role: 'bot', content })
const userMsg = (content: string): Message => ({ id: nextId(), role: 'user', content })
const fmt = (tpl: string, name: string) => tpl.replace(/\{petName\}/g, name)
const ACKS = ['그렇군요 😊', '아, 그랬군요!', '좋아요 🐾', '잘 알겠어요!', '기억해둘게요 🤍', '소중한 순간이네요.']
const randomAck = () => ACKS[Math.floor(Math.random() * ACKS.length)]

// ── 초기 상태 ────────────────────────────────────────
function makeInitialState(pet: Pet, welcomeOverride?: string): ChatbotState {
  const welcome = welcomeOverride ?? `안녕하세요! 저는 ${pet.name}의 반짝이는 하루와\n소중한 추억을 차곡차곡 담아드리는 AI 멍봇이에요 🐾\n\n추억을 함께 기록하고,\n어울리는 장소도 추천해드릴게요.\n\n오늘은 어떤 하루를 남겨볼까요?`
  return {
    step: 'welcome',
    pet,
    selectedDiaryType: null,
    currentQuestionIndex: 0,
    messages: [
      botMsg(welcome),
    ],
    mainAnswers: [],
    additionalPerspectiveAccepted: null,
    additionalAnswers: [],
    additionalQuestionIndex: 0,
    selectedEmotionEmoji: null,
    selectedEmotionLabel: null,
    generatedDiary: null,
    isGenerating: false,
  }
}

// ── Reducer ──────────────────────────────────────────
function reducer(state: ChatbotState, action: ChatbotAction): ChatbotState {
  const petName = state.pet.name

  switch (action.type) {
    case 'START_DIARY': {
      return {
        ...state,
        step: 'type_select',
        messages: [
          ...state.messages,
          userMsg('그림일기 쓸게요 📝'),
          botMsg(`좋아요! ${petName}의 오늘 하루를 어떤 유형으로 기록할까요?`),
        ],
      }
    }

    case 'SELECT_DIARY_TYPE': {
      const dt = DIARY_TYPES.find((t) => t.id === action.id)!
      return {
        ...state,
        step: 'main_questions',
        selectedDiaryType: action.id,
        currentQuestionIndex: 0,
        messages: [
          ...state.messages,
          userMsg(`${dt.icon} ${dt.label}`),
          botMsg(`좋아요! ${dt.description}으로 기록해볼게요 😊\n\n${fmt(dt.questions[0], petName)}`),
        ],
      }
    }

    case 'SUBMIT_MAIN_ANSWER': {
      const dt = DIARY_TYPES.find((t) => t.id === state.selectedDiaryType)!
      const newAnswers = [...state.mainAnswers, action.answer]
      const nextIdx = state.currentQuestionIndex + 1

      if (nextIdx < dt.questions.length) {
        return {
          ...state,
          mainAnswers: newAnswers,
          currentQuestionIndex: nextIdx,
          messages: [
            ...state.messages,
            userMsg(action.answer),
            botMsg(`${randomAck()}\n\n${fmt(dt.questions[nextIdx], petName)}`),
          ],
        }
      }

      return {
        ...state,
        step: 'additional_prompt',
        mainAnswers: newAnswers,
        messages: [
          ...state.messages,
          userMsg(action.answer),
          botMsg(`잘 기록됐어요! 🐾\n\n${fmt(dt.perspectiveSuggestion, petName)}`),
        ],
      }
    }

    case 'RESPOND_TO_PERSPECTIVE': {
      if (action.accepted) {
        const dt = DIARY_TYPES.find((t) => t.id === state.selectedDiaryType)!
        return {
          ...state,
          step: 'additional_questions',
          additionalPerspectiveAccepted: true,
          additionalQuestionIndex: 0,
          messages: [
            ...state.messages,
            userMsg('네, 좋아요!'),
            botMsg(fmt(dt.additionalQuestions[0], petName)),
          ],
        }
      }
      return {
        ...state,
        step: 'emotion_select',
        additionalPerspectiveAccepted: false,
        messages: [
          ...state.messages,
          userMsg('괜찮아요'),
          botMsg(`이해해요! 그럼 마지막 단계예요 😊\n\n오늘 ${petName}의 하루는 어떤 감정으로 기억하고 싶으세요?`),
        ],
      }
    }

    case 'SUBMIT_ADDITIONAL_ANSWER': {
      const dt = DIARY_TYPES.find((t) => t.id === state.selectedDiaryType)!
      const newAnswers = [...state.additionalAnswers, action.answer]
      const nextIdx = state.additionalQuestionIndex + 1

      if (nextIdx < dt.additionalQuestions.length) {
        return {
          ...state,
          additionalAnswers: newAnswers,
          additionalQuestionIndex: nextIdx,
          messages: [
            ...state.messages,
            userMsg(action.answer),
            botMsg(`${randomAck()}\n\n${fmt(dt.additionalQuestions[nextIdx], petName)}`),
          ],
        }
      }

      return {
        ...state,
        step: 'emotion_select',
        additionalAnswers: newAnswers,
        messages: [
          ...state.messages,
          userMsg(action.answer),
          botMsg(`완벽해요! ✨\n\n오늘 ${petName}의 하루는 어떤 감정으로 기억하고 싶으세요?`),
        ],
      }
    }

    case 'SELECT_EMOTION': {
      return {
        ...state,
        step: 'diary_generating',
        selectedEmotionEmoji: action.emoji,
        selectedEmotionLabel: action.label,
        isGenerating: true,
        messages: [
          ...state.messages,
          userMsg(`${action.emoji} ${action.label}`),
          botMsg(`${action.emoji} 느낌으로 ${petName}의 일기를 쓰고 있어요... ✍️\n잠깐만 기다려주세요!`),
        ],
      }
    }

    case 'SET_DIARY': {
      const diary = action.diary
      const diaryMessage = `📖 ${diary.title}\n\n${diary.content}`
      return {
        ...state,
        step: 'diary_result',
        isGenerating: false,
        generatedDiary: diary,
        messages: [
          ...state.messages,
          botMsg(`${petName}의 일기가 완성됐어요 🐾`),
          botMsg(diaryMessage),
        ],
      }
    }

    case 'SUBMIT_WELCOME_CHAT': {
      return {
        ...state,
        isGenerating: true,
        messages: [...state.messages, userMsg(action.text)],
      }
    }

    case 'RECEIVE_BOT_MESSAGE': {
      const msg: Message = { id: nextId(), role: 'bot', content: action.text }
      if (action.action) msg.action = action.action
      if (action.variant) msg.variant = action.variant
      if (action.places) msg.places = action.places
      return {
        ...state,
        isGenerating: false,
        messages: [...state.messages, msg],
      }
    }

    case 'TRIGGER_DIARY_FLOW': {
      return {
        ...state,
        isGenerating: false,
        step: 'type_select',
        messages: [
          ...state.messages,
          botMsg(`${petName}의 오늘 하루를 어떤 유형으로 기록할까요? 🐾`),
        ],
      }
    }

    case 'UPDATE_PET':
      return { ...state, pet: action.pet }

    case 'FORCE_START_DIARY': {
      const fresh = makeInitialState(state.pet)
      return {
        ...fresh,
        step: 'type_select',
        messages: [
          ...fresh.messages,
          userMsg('그림일기 쓸게요 📝'),
          botMsg(`좋아요! ${petName}의 오늘 하루를 어떤 유형으로 기록할까요?`),
        ],
      }
    }

    case 'RESTART_DIARY': {
      return {
        ...state,
        step: 'type_select',
        selectedDiaryType: null,
        currentQuestionIndex: 0,
        mainAnswers: [],
        additionalPerspectiveAccepted: null,
        additionalAnswers: [],
        additionalQuestionIndex: 0,
        selectedEmotionEmoji: null,
        selectedEmotionLabel: null,
        generatedDiary: null,
        isGenerating: false,
        messages: [
          ...state.messages,
          userMsg('일기 다시 쓰고 싶어'),
          botMsg(`일기를 다시 써볼까요? 😊\n\n${petName}의 오늘 하루를 어떤 유형으로 기록할까요?`),
        ],
      }
    }

    case 'REGENERATE': {
      return { ...state, step: 'diary_generating', isGenerating: true, generatedDiary: null }
    }

    case 'RESET':
      return makeInitialState(state.pet)

    default:
      return state
  }
}

// ── Hook ─────────────────────────────────────────────
export function useChatbot(pet: Pet, welcomeOverride?: string) {
  const [state, dispatch] = useReducer(reducer, undefined, () => makeInitialState(pet, welcomeOverride))

  // 대화 저장용 ref
  const chatRoomIdRef = useRef<number | null>(null)
  const lastSavedCountRef = useRef(0)
  const isSavingRef = useRef(false)

  // pet prop이 바뀌면 내부 state.pet도 동기화
  useEffect(() => {
    dispatch({ type: 'UPDATE_PET', pet })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pet.name, pet.breed, pet.ownerName, pet.birthDate])

  // 메시지가 초기화되면(RESET/FORCE_START) 저장 상태도 초기화
  useEffect(() => {
    if (state.messages.length <= 1) {
      chatRoomIdRef.current = null
      lastSavedCountRef.current = 0
    }
  }, [state.messages.length])

  // 새 메시지 백엔드 저장
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    // 'welcome' 스텝은 ChatBot.tsx 의 sendWelcomeMessage 가 sendMessageWithResponse 로
    // API 호출을 직접 담당하므로, 여기서 중복 저장하면 두 채팅방에 AI 응답이 각각 생성됨.
    if (state.step === 'welcome') return

    // 유저 메시지가 하나라도 생긴 뒤부터 저장 시작
    const hasUserMessage = state.messages.some((m) => m.role === 'user')
    if (!hasUserMessage) return

    const unsaved = state.messages.slice(lastSavedCountRef.current)
    if (unsaved.length === 0 || isSavingRef.current) return

    const persist = async () => {
      isSavingRef.current = true
      try {
        // 채팅방 없으면 생성
        if (chatRoomIdRef.current === null) {
          const firstUser = state.messages.find((m) => m.role === 'user')
          const title = (firstUser?.content ?? '챗봇 대화').slice(0, 30)
          const room = await createChatRoom(title)
          chatRoomIdRef.current = room.id
        }
        const roomId = chatRoomIdRef.current!
        // 백엔드가 role='user'만 허용하므로 유저 메시지만 저장
        for (const msg of state.messages.slice(lastSavedCountRef.current)) {
          if (msg.role === 'user') {
            await saveMessage(roomId, 'user', msg.content)
          }
          lastSavedCountRef.current++
        }
      } catch (e) {
        console.warn('[useChatbot] 메시지 저장 실패:', e)
      } finally {
        isSavingRef.current = false
      }
    }

    persist()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.messages, state.step])

  useEffect(() => {
    if (!state.isGenerating || !state.selectedDiaryType || !state.selectedEmotionEmoji) return

    const dt = DIARY_TYPES.find((t) => t.id === state.selectedDiaryType)!
    const em = EMOTIONS.find((e) => e.emoji === state.selectedEmotionEmoji)!

    generateDiary({
      petName: state.pet.name,
      breed: state.pet.breed,
      birthDate: state.pet.birthDate,
      personalities: state.pet.personality,
      ownerName: state.pet.ownerName,
      ownerGender: state.pet.ownerGender,
      diaryType: state.selectedDiaryType,
      typeFocus: dt.typeFocus,
      mainAnswers: state.mainAnswers,
      additionalAnswers: state.additionalAnswers,
      emotionEmoji: state.selectedEmotionEmoji,
      emotionTone: em.tone,
    })
      .then((diary) => dispatch({
        type: 'SET_DIARY',
        diary: { ...diary, emotion: state.selectedEmotionEmoji ?? undefined },
      }))
      .catch(() =>
        dispatch({
          type: 'SET_DIARY',
          diary: {
            title: '생성 실패',
            content: '일기 생성 중 오류가 발생했어요. 다시 시도해주세요.',
            summary: '',
            emotion: state.selectedEmotionEmoji ?? undefined,
          },
        })
      )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.isGenerating])

  const actions = {
    startDiary: useCallback(() => dispatch({ type: 'START_DIARY' }), []),
    forceStartDiary: useCallback(() => dispatch({ type: 'FORCE_START_DIARY' }), []),
    triggerDiaryFlow: useCallback(() => dispatch({ type: 'TRIGGER_DIARY_FLOW' }), []),
    selectDiaryType: useCallback((id: DiaryTypeId) => dispatch({ type: 'SELECT_DIARY_TYPE', id }), []),
    submitMainAnswer: useCallback((answer: string) => dispatch({ type: 'SUBMIT_MAIN_ANSWER', answer }), []),
    respondToPerspective: useCallback((accepted: boolean) => dispatch({ type: 'RESPOND_TO_PERSPECTIVE', accepted }), []),
    submitAdditionalAnswer: useCallback((answer: string) => dispatch({ type: 'SUBMIT_ADDITIONAL_ANSWER', answer }), []),
    selectEmotion: useCallback((emoji: string, label: string) => dispatch({ type: 'SELECT_EMOTION', emoji, label }), []),
    restartDiary: useCallback(() => dispatch({ type: 'RESTART_DIARY' }), []),
    regenerate: useCallback(() => dispatch({ type: 'REGENERATE' }), []),
    reset: useCallback(() => dispatch({ type: 'RESET' }), []),
    submitWelcomeChat: useCallback((text: string) => dispatch({ type: 'SUBMIT_WELCOME_CHAT', text }), []),
    receiveBotMessage: useCallback(
      (
        text: string,
        action?: 'start_diary',
        variant?: 'place',
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
      ) => dispatch({ type: 'RECEIVE_BOT_MESSAGE', text, action, variant, places }),
      [],
    ),
  }

  return { state, actions }
}
