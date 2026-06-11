import { useState, useRef, useEffect, useCallback } from 'react'
import './App.css'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'bank' | 'progress' | 'settings'>('chat')
  const [studentId, setStudentId] = useState('demo_student')
  const [studentProfile, setStudentProfile] = useState<any>(null)
  const [isProfileLoading, setIsProfileLoading] = useState(false)
  const [targetLevel, setTargetLevel] = useState('O')

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hello! I'm **Criterion AI**, your O/A Level academic tutor. I can help you with:\n\n" +
        "📝 **Past Paper Questions** — fetch questions by subject, topic, or year\n" +
        "✏️ **Auto-Grading** — evaluate your step-by-step working with partial credit\n" +
        "📊 **Progress Tracking** — monitor your strengths and weaknesses adaptively\n\n" +
        "What would you like to work on today?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [hasUserSent, setHasUserSent] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const fetchProfile = async () => {
    setIsProfileLoading(true)
    try {
      const response = await fetch(`/api/student-profile/${studentId}`)
      if (response.ok) {
        const data = await response.json()
        setStudentProfile(data)
      } else {
        setStudentProfile(null)
      }
    } catch (err) {
      console.error(err)
      setStudentProfile(null)
    } finally {
      setIsProfileLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'progress') {
      fetchProfile()
    }
  }, [activeTab, studentId])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`
    }
  }, [input])

  // TASK 1: Real backend API call
  const handleSend = useCallback(async (overrideText?: string) => {
    const text = overrideText ?? input.trim()
    if (!text || isLoading) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setHasUserSent(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          student_id: studentId,
        }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.reply || 'I received your message but got an empty response.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : 'Unknown error occurred'
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content:
          `⚠️ **Connection Error**\n\n` +
          `Could not reach the backend server. Please make sure the FastAPI server is running on port 8000.\n\n` +
          `\`Error: ${errorMsg}\``,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // TASK 3: Quick action handler
  const handleQuickAction = (text: string) => {
    handleSend(text)
  }

  // TASK 2: Improved markdown-like rendering
  const formatContent = (content: string) => {
    const lines = content.split('\n')
    return lines.map((line, i) => {
      // Bullet points
      const isBullet = /^[-•]\s+/.test(line)
      const bulletContent = isBullet ? line.replace(/^[-•]\s+/, '') : null

      if (isBullet && bulletContent !== null) {
        return (
          <div key={i} className="flex gap-2 py-0.5">
            <span className="text-primary-light select-none mt-0.5">•</span>
            <span>{formatInline(bulletContent)}</span>
          </div>
        )
      }

      // Numbered list items (e.g. "1. ", "2. ")
      const numberedMatch = line.match(/^(\d+)\.\s+(.*)/)
      if (numberedMatch) {
        return (
          <div key={i} className="flex gap-2 py-0.5">
            <span className="text-primary-light font-semibold select-none min-w-[1.25rem] text-right">{numberedMatch[1]}.</span>
            <span>{formatInline(numberedMatch[2])}</span>
          </div>
        )
      }

      // Empty line = paragraph break
      if (line.trim() === '') {
        return <div key={i} className="h-2" />
      }

      // Regular line
      return (
        <div key={i}>
          {formatInline(line)}
        </div>
      )
    })
  }

  // Inline formatting: bold, code, etc.
  const formatInline = (text: string) => {
    // Split by **bold** and `code` patterns
    const parts = text.split(/(\*\*.*?\*\*|`[^`]+`)/)
    return parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={j} className="text-text-primary font-semibold">
            {part.slice(2, -2)}
          </strong>
        )
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={j}
            className="px-1.5 py-0.5 rounded-md bg-surface-lighter text-accent font-mono text-xs"
          >
            {part.slice(1, -1)}
          </code>
        )
      }
      return <span key={j}>{part}</span>
    })
  }

  // TASK 3: Quick action buttons data
  const quickActions = [
    { label: '📐 O-Level Maths', message: 'Give me an O-Level Mathematics question' },
    { label: '📏 A-Level Maths', message: 'Give me an A-Level Mathematics question' },
    { label: '⚛️ O-Level Physics', message: 'Give me an O-Level Physics question' },
    { label: '📊 My Weakest Topic', message: 'What is my weakest topic?' },
  ]

  const SEED_QUESTIONS_LIST = [
    {
      id: "q1",
      subject: "Mathematics",
      level: "O",
      topic: "Quadratic Equations",
      difficulty: "medium",
      total_marks: 4,
      source: "Cambridge 4024/12/M/J/23",
      question_text: "Solve the equation 2x² - 5x + 3 = 0 by factorisation."
    },
    {
      id: "q2",
      subject: "Mathematics",
      level: "O",
      topic: "Differentiation",
      difficulty: "medium",
      total_marks: 3,
      source: "Cambridge 4024/22/O/N/22",
      question_text: "The equation of a curve is y = x³ - 6x² + 9x + 2. Find the gradient of the curve at the point where x = 2."
    },
    {
      id: "q3",
      subject: "Mathematics",
      level: "O",
      topic: "Simultaneous Equations",
      difficulty: "easy",
      total_marks: 3,
      source: "Cambridge 4024/12/M/J/23",
      question_text: "Solve the simultaneous equations:\n3x + 2y = 12\nx - y = 1"
    },
    {
      id: "q4",
      subject: "Mathematics",
      level: "A",
      topic: "Integration",
      difficulty: "hard",
      total_marks: 5,
      source: "Cambridge 9709/12/M/J/23",
      question_text: "Evaluate the definite integral: ∫₁³ (2x + 1)² dx"
    },
    {
      id: "q5",
      subject: "Physics",
      level: "O",
      topic: "Kinematics",
      difficulty: "easy",
      total_marks: 4,
      source: "Cambridge 5054/22/M/J/22",
      question_text: "A car starts from rest and accelerates uniformly at 2 m/s² for 10 seconds. Calculate:\n(a) the final velocity\n(b) the distance travelled"
    }
  ]

  const mockWeaknessData = [
    { topic: "Quadratic Equations", subject: "Mathematics", mastery: 0.75, attempts: 4, fail: 1, pass: 3, wtps: 1.25 },
    { topic: "Differentiation", subject: "Mathematics", mastery: 0.33, attempts: 3, fail: 2, pass: 1, wtps: 3.50 },
    { topic: "Simultaneous Equations", subject: "Mathematics", mastery: 1.00, attempts: 2, fail: 0, pass: 2, wtps: 0.00 },
    { topic: "Integration", subject: "Mathematics", mastery: 0.20, attempts: 5, fail: 4, pass: 1, wtps: 4.80 },
    { topic: "Kinematics", subject: "Physics", mastery: 0.50, attempts: 2, fail: 1, pass: 1, wtps: 2.10 }
  ]

  const getTopicsFromProfile = () => {
    if (!studentProfile || !studentProfile.weakness_map) {
      return mockWeaknessData
    }
    const list: any[] = []
    const map = studentProfile.weakness_map
    Object.keys(map).forEach(sub => {
      Object.keys(map[sub]).forEach(top => {
        const stats = map[sub][top]
        const attempts = stats.attempts || 0
        const fails = stats.fail || 0
        const mastery = stats.mastery || 0
        const wtps = fails * 1.5 + (1.0 - mastery) * 2.0
        list.push({
          topic: top,
          subject: sub,
          mastery: mastery,
          attempts: attempts,
          fail: fails,
          pass: stats.pass || 0,
          wtps: wtps
        })
      })
    })
    return list.length > 0 ? list.sort((a, b) => b.wtps - a.wtps) : mockWeaknessData
  }

  const handleAttemptQuestion = (q: any) => {
    setActiveTab('chat')
    // Reset history if clicking a new question to start fresh, or keep it
    handleSend(`Give me a ${q.subject} ${q.level} Level question on ${q.topic}`)
  }

  return (
    <div className="flex h-dvh bg-surface relative overflow-hidden">
      {/* TASK 5: Subtle animated gradient background orbs */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="gradient-orb gradient-orb-1" />
        <div className="gradient-orb gradient-orb-2" />
        <div className="gradient-orb gradient-orb-3" />
      </div>

      {/* Sidebar */}
      <aside className="hidden md:flex w-72 flex-col border-r border-border bg-surface/90 backdrop-blur-sm relative z-10">
        {/* Brand */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-border">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-primary/25 animate-[pulse-glow_4s_infinite]">
            C
          </div>
          <div>
            <h1 className="text-base font-semibold text-text-primary leading-tight">
              Criterion AI
            </h1>
            <p className="text-xs text-text-muted">O/A Level Tutor</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          <button
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'chat'
                ? 'bg-primary text-white shadow-lg shadow-primary/25'
                : 'text-text-secondary hover:bg-surface-light hover:text-text-primary'
            }`}
          >
            <span className="text-lg">💬</span> Study Chat
          </button>
          <button
            onClick={() => setActiveTab('bank')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'bank'
                ? 'bg-primary text-white shadow-lg shadow-primary/25'
                : 'text-text-secondary hover:bg-surface-light hover:text-text-primary'
            }`}
          >
            <span className="text-lg">📚</span> Question Bank
          </button>
          <button
            onClick={() => setActiveTab('progress')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'progress'
                ? 'bg-primary text-white shadow-lg shadow-primary/25'
                : 'text-text-secondary hover:bg-surface-light hover:text-text-primary'
            }`}
          >
            <span className="text-lg">📊</span> My Progress
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'settings'
                ? 'bg-primary text-white shadow-lg shadow-primary/25'
                : 'text-text-secondary hover:bg-surface-light hover:text-text-primary'
            }`}
          >
            <span className="text-lg">⚙️</span> Settings
          </button>
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-border">
          <div className="flex items-center gap-2 px-2 py-2 rounded-lg bg-surface-light">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent to-accent-light flex items-center justify-center text-xs font-bold text-surface">
              {studentId.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-primary truncate">{studentId}</p>
              <p className="text-xs text-text-muted">{targetLevel}-Level Candidate</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col min-w-0 relative z-10">
        {/* Header */}
        <header className="flex items-center justify-between px-5 py-3.5 border-b border-border bg-surface/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div 
              onClick={() => setActiveTab('chat')}
              className="md:hidden w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-xs cursor-pointer"
            >
              C
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">
                {activeTab === 'chat' && 'Study Session'}
                {activeTab === 'bank' && 'Cambridge Question Bank'}
                {activeTab === 'progress' && 'Student Performance Tracker'}
                {activeTab === 'settings' && 'System & Student Settings'}
              </h2>
              <p className="text-xs text-text-muted flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-success inline-block animate-pulse"></span>
                {studentProfile ? 'Synchronized with Database' : 'Local Session Mode'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full bg-primary/15 text-primary-light text-xs font-medium border border-primary/25">
              MCP Connected
            </span>
          </div>
        </header>

        {/* Tab 1: Chat View */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col min-h-0">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-3xl mx-auto w-full animate-[fade-in_0.3s_ease-out] ${
                    msg.role === 'user' ? 'flex-row-reverse' : ''
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-accent to-accent-light text-surface'
                        : 'bg-gradient-to-br from-primary to-primary-light text-white shadow-lg shadow-primary/20'
                    }`}
                  >
                    {msg.role === 'user' ? 'Y' : 'C'}
                  </div>

                  {/* Bubble */}
                  <div
                    className={`flex-1 rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-primary text-white rounded-tr-sm ml-12'
                        : 'bg-surface-light/80 backdrop-blur-sm text-text-secondary rounded-tl-sm mr-12 border border-border'
                    }`}
                  >
                    {formatContent(msg.content)}
                  </div>
                </div>
              ))}

              {/* Quick action buttons — shown only before first user message */}
              {!hasUserSent && !isLoading && (
                <div className="max-w-3xl mx-auto w-full animate-[fade-in_0.5s_ease-out]">
                  <div className="flex flex-wrap gap-2 ml-11">
                    {quickActions.map((action) => (
                      <button
                        key={action.label}
                        onClick={() => handleQuickAction(action.message)}
                        className="px-4 py-2 rounded-full text-sm font-medium
                          bg-surface-light/80 backdrop-blur-sm border border-border
                          text-text-secondary hover:text-text-primary
                          hover:border-primary/40 hover:bg-primary/10
                          hover:shadow-lg hover:shadow-primary/10
                          transition-all duration-200 cursor-pointer
                          active:scale-95"
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Typing indicator */}
              {isLoading && (
                <div className="flex gap-3 max-w-3xl mx-auto w-full animate-[fade-in_0.3s_ease-out]">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-light flex items-center justify-center text-xs font-bold text-white shadow-lg shadow-primary/20 flex-shrink-0">
                    C
                  </div>
                  <div className="bg-surface-light/80 backdrop-blur-sm rounded-2xl rounded-tl-sm px-5 py-4 border border-border">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-primary-light animate-[typing-dot_1.4s_infinite_0ms]"></span>
                      <span className="w-2 h-2 rounded-full bg-primary-light animate-[typing-dot_1.4s_infinite_200ms]"></span>
                      <span className="w-2 h-2 rounded-full bg-primary-light animate-[typing-dot_1.4s_infinite_400ms]"></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-border bg-surface/80 backdrop-blur-md">
              <div className="max-w-3xl mx-auto">
                <div className="flex items-end gap-2 bg-surface-light/80 backdrop-blur-sm rounded-2xl border border-border focus-within:border-primary/50 focus-within:shadow-lg focus-within:shadow-primary/10 transition-all duration-200 px-4 py-2">
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about a topic, paste your working, or request a question..."
                    rows={1}
                    className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted resize-none outline-none max-h-40 py-1.5"
                  />
                  <button
                    onClick={() => handleSend()}
                    disabled={!input.trim() || isLoading}
                    className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white transition-all duration-200 hover:shadow-lg hover:shadow-primary/30 hover:scale-105 active:scale-95 disabled:opacity-30 disabled:hover:shadow-none disabled:hover:scale-100 flex-shrink-0 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                  </button>
                </div>
                <p className="text-center text-xs text-text-muted mt-2">
                  Criterion AI can make mistakes. Verify important calculations.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Question Bank View */}
        {activeTab === 'bank' && (
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            <div className="bg-surface-light/50 backdrop-blur-md rounded-2xl p-6 border border-border">
              <h3 className="text-lg font-medium text-text-primary mb-2">Past Paper Catalog</h3>
              <p className="text-sm text-text-secondary">
                Select a real Cambridge Assessment International Education (CAIE) question below. Attempts will feed into your weakness profile automatically.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {SEED_QUESTIONS_LIST.map((q) => (
                <div key={q.id} className="bg-surface-light/40 hover:bg-surface-light/60 border border-border hover:border-primary/50 rounded-2xl p-5 transition-all duration-200 flex flex-col justify-between">
                  <div>
                    <div className="flex flex-wrap gap-2 mb-3">
                      <span className="px-2 py-0.5 rounded-md bg-primary/10 text-primary-light text-xs font-semibold uppercase">
                        {q.subject}
                      </span>
                      <span className="px-2 py-0.5 rounded-md bg-accent/10 text-accent-light text-xs font-semibold">
                        {q.level}-Level
                      </span>
                      <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${
                        q.difficulty === 'easy' ? 'bg-success/10 text-success' :
                        q.difficulty === 'medium' ? 'bg-warning/10 text-warning' : 'bg-error/10 text-error'
                      }`}>
                        {q.difficulty}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-text-primary mb-1">{q.topic}</h4>
                    <p className="text-xs text-text-muted mb-4">{q.source} • {q.total_marks} Marks</p>
                    
                    <p className="text-sm text-text-secondary bg-surface-lighter/50 rounded-xl p-3 border border-border/50 font-mono line-clamp-3 mb-4">
                      {q.question_text}
                    </p>
                  </div>

                  <button
                    onClick={() => handleAttemptQuestion(q)}
                    className="w-full py-2.5 rounded-xl bg-primary hover:bg-primary-dark text-white text-sm font-semibold transition-all shadow-md shadow-primary/10 active:scale-95 cursor-pointer"
                  >
                    Attempt Question 🚀
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Progress Tracker */}
        {activeTab === 'progress' && (
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            {isProfileLoading ? (
              <div className="flex items-center justify-center h-64">
                <span className="text-text-muted">Loading progress records...</span>
              </div>
            ) : (
              <>
                <div className="bg-gradient-to-r from-primary/10 to-accent/10 rounded-2xl p-6 border border-border/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-text-primary">Weakness Tracking Profile</h3>
                    <p className="text-sm text-text-secondary">
                      Calculated dynamically using the WTPS (Weakness Topic Prioritisation Score) algorithm.
                    </p>
                  </div>
                  <button 
                    onClick={fetchProfile}
                    className="px-4 py-2 rounded-xl bg-surface-light border border-border text-sm font-semibold text-text-primary hover:bg-surface-lighter transition-all cursor-pointer"
                  >
                    🔄 Refresh Stats
                  </button>
                </div>

                {/* Stat cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-surface-light/40 border border-border rounded-2xl p-5">
                    <span className="text-xs font-semibold text-text-muted uppercase">Global Subject</span>
                    <h4 className="text-2xl font-bold text-text-primary mt-1">Mathematics</h4>
                    <p className="text-xs text-success mt-1">Active Study Goal</p>
                  </div>
                  <div className="bg-surface-light/40 border border-border rounded-2xl p-5">
                    <span className="text-xs font-semibold text-text-muted uppercase">Total Attempts</span>
                    <h4 className="text-2xl font-bold text-text-primary mt-1">
                      {studentProfile?.exam_history?.length || 16} attempts
                    </h4>
                    <p className="text-xs text-text-muted mt-1">Synced to local store</p>
                  </div>
                  <div className="bg-surface-light/40 border border-border rounded-2xl p-5">
                    <span className="text-xs font-semibold text-text-muted uppercase">Recommended Priority</span>
                    <h4 className="text-2xl font-bold text-accent-light mt-1">
                      {getTopicsFromProfile()[0]?.topic || 'Integration'}
                    </h4>
                    <p className="text-xs text-text-muted mt-1">Highest priority score</p>
                  </div>
                </div>

                {/* Progress table */}
                <div className="bg-surface-light/30 border border-border rounded-2xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-border bg-surface-light/20">
                    <h4 className="text-sm font-semibold text-text-primary">Topic Analysis Table</h4>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border text-xs font-semibold text-text-muted uppercase bg-surface-light/10">
                          <th className="px-6 py-3">Topic</th>
                          <th className="px-6 py-3">Attempts</th>
                          <th className="px-6 py-3">Mastery</th>
                          <th className="px-6 py-3">Priority Score (WTPS)</th>
                          <th className="px-6 py-3 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60 text-sm">
                        {getTopicsFromProfile().map((t, idx) => (
                          <tr key={idx} className="hover:bg-surface-light/25 transition-colors">
                            <td className="px-6 py-4">
                              <span className="font-medium text-text-primary">{t.topic}</span>
                              <span className="block text-xs text-text-muted">{t.subject}</span>
                            </td>
                            <td className="px-6 py-4 font-mono text-text-secondary">{t.attempts}</td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <div className="flex-1 w-24 h-2 bg-surface-lighter rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-gradient-to-r from-accent to-primary rounded-full"
                                    style={{ width: `${t.mastery * 100}%` }}
                                  />
                                </div>
                                <span className="font-mono text-xs font-semibold text-text-primary">{Math.round(t.mastery * 100)}%</span>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                                t.wtps > 3.0 ? 'bg-error/10 text-error' :
                                t.wtps > 1.0 ? 'bg-warning/10 text-warning' : 'bg-success/10 text-success'
                              }`}>
                                {t.wtps.toFixed(2)}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <button 
                                onClick={() => handleQuickAction(`Give me a question on ${t.topic}`)}
                                className="px-3 py-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary-light text-xs font-semibold transition-all cursor-pointer"
                              >
                                Practice 🎯
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab 4: Settings View */}
        {activeTab === 'settings' && (
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            <div className="bg-surface-light/40 border border-border rounded-2xl p-6 space-y-6">
              <h3 className="text-base font-bold text-text-primary border-b border-border pb-3">Student Configuration</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-text-muted uppercase mb-2">Student ID</label>
                  <input
                    type="text"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    className="w-full bg-surface-lighter border border-border rounded-xl px-4 py-2.5 text-sm text-text-primary outline-none focus:border-primary transition-all"
                  />
                  <p className="text-xs text-text-muted mt-1">Matches attempts and updates your profile in MongoDB.</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-muted uppercase mb-2">Target Examination Level</label>
                  <select
                    value={targetLevel}
                    onChange={(e) => setTargetLevel(e.target.value)}
                    className="w-full bg-surface-lighter border border-border rounded-xl px-4 py-2.5 text-sm text-text-primary outline-none focus:border-primary transition-all cursor-pointer"
                  >
                    <option value="O">O-Level (Cambridge O Level)</option>
                    <option value="A">A-Level (Cambridge International A Level)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-surface-light/40 border border-border rounded-2xl p-6 space-y-4">
              <h3 className="text-base font-bold text-text-primary border-b border-border pb-3">System Environment</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between p-3 rounded-xl bg-surface-lighter/50 border border-border/40">
                  <span className="text-text-secondary">Database Mode</span>
                  <span className="font-mono font-bold text-primary-light">In-Memory (Auto Fallback)</span>
                </div>
                <div className="flex justify-between p-3 rounded-xl bg-surface-lighter/50 border border-border/40">
                  <span className="text-text-secondary">FastAPI Host/Port</span>
                  <span className="font-mono text-text-primary">localhost:8000</span>
                </div>
                <div className="flex justify-between p-3 rounded-xl bg-surface-lighter/50 border border-border/40">
                  <span className="text-text-secondary">Model Context Protocol</span>
                  <span className="font-mono font-bold text-success">Enabled (mounted at /mcp)</span>
                </div>
                <div className="flex justify-between p-3 rounded-xl bg-surface-lighter/50 border border-border/40">
                  <span className="text-text-secondary">Cross-Origin Resource Sharing</span>
                  <span className="font-mono text-text-primary">allow_origins=["*"]</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
