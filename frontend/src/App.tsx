import { useState, useRef, useEffect } from 'react'
import './App.css'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

function App() {
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // TODO: Wire up to the FastAPI /mcp endpoint via SSE
    // For now, echo a placeholder response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content:
          '🔧 **MCP backend not connected yet.** Once the backend is running, I will process your request through the Gemini agent and MCP tools.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1200)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatContent = (content: string) => {
    // Simple markdown-like rendering for bold and line breaks
    return content.split('\n').map((line, i) => (
      <span key={i}>
        {line.split(/(\*\*.*?\*\*)/).map((part, j) =>
          part.startsWith('**') && part.endsWith('**') ? (
            <strong key={j} className="text-text-primary font-semibold">
              {part.slice(2, -2)}
            </strong>
          ) : (
            <span key={j}>{part}</span>
          )
        )}
        {i < content.split('\n').length - 1 && <br />}
      </span>
    ))
  }

  return (
    <div className="flex h-dvh bg-surface">
      {/* Sidebar */}
      <aside className="hidden md:flex w-72 flex-col border-r border-border bg-surface">
        {/* Brand */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-border">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-primary/25">
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
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-surface-light text-text-primary text-sm font-medium transition-colors">
            <span className="text-lg">💬</span> New Chat
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary text-sm hover:bg-surface-light hover:text-text-primary transition-colors">
            <span className="text-lg">📚</span> Question Bank
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary text-sm hover:bg-surface-light hover:text-text-primary transition-colors">
            <span className="text-lg">📊</span> My Progress
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary text-sm hover:bg-surface-light hover:text-text-primary transition-colors">
            <span className="text-lg">⚙️</span> Settings
          </button>
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-border">
          <div className="flex items-center gap-2 px-2 py-2 rounded-lg bg-surface-light">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent to-accent-light flex items-center justify-center text-xs font-bold text-surface">
              S
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-primary truncate">Student</p>
              <p className="text-xs text-text-muted">Free Plan</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-5 py-3.5 border-b border-border bg-surface/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="md:hidden w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-xs">
              C
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">
                Study Session
              </h2>
              <p className="text-xs text-text-muted flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-success inline-block animate-pulse"></span>
                Gemini Agent Active
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full bg-primary/15 text-primary-light text-xs font-medium border border-primary/25">
              MCP Connected
            </span>
          </div>
        </header>

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
                    : 'bg-surface-light text-text-secondary rounded-tl-sm mr-12 border border-border'
                }`}
              >
                {formatContent(msg.content)}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="flex gap-3 max-w-3xl mx-auto w-full animate-[fade-in_0.3s_ease-out]">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-light flex items-center justify-center text-xs font-bold text-white shadow-lg shadow-primary/20 flex-shrink-0">
                C
              </div>
              <div className="bg-surface-light rounded-2xl rounded-tl-sm px-5 py-4 border border-border">
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
            <div className="flex items-end gap-2 bg-surface-light rounded-2xl border border-border focus-within:border-primary/50 focus-within:shadow-lg focus-within:shadow-primary/10 transition-all duration-200 px-4 py-2">
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
                onClick={handleSend}
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
      </main>
    </div>
  )
}

export default App
