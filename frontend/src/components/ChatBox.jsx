import { useState, useRef, useEffect } from 'react'
import { queriesAPI, documentsAPI } from '../utils/api'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { Bot, Send, Paperclip, ChevronDown, Bookmark, AlertTriangle } from 'lucide-react'

function TypingIndicator() {
  return (
    <div className="flex gap-3 items-start">
      <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-blue-400" />
      </div>
      <div className="bg-gray-800 border border-gray-700 px-4 py-3 rounded-lg flex items-center gap-1.5">
        <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" />
        <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0.2s' }} />
        <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0.4s' }} />
      </div>
    </div>
  )
}

function Message({ msg, userInitial, onBookmark }) {
  const isUser = msg.role === 'user'
  const isError = !isUser && msg.content && msg.content.startsWith('⚠️')

  if (isError) {
    return (
      <div className="flex gap-3 items-start">
        <div className="w-8 h-8 rounded-full bg-red-900/50 flex items-center justify-center flex-shrink-0">
          <AlertTriangle size={16} className="text-red-400" />
        </div>
        <div className="bg-red-900/30 border border-red-800 px-4 py-3 rounded-lg max-w-[80%]">
          <p className="text-sm text-red-200">{msg.content.replace(/^⚠️\s*/, '')}</p>
        </div>
      </div>
    )
  }

  if (isUser) {
    return (
      <div className="flex gap-3 items-start justify-end">
        <div className="bg-blue-600 px-4 py-3 rounded-lg max-w-[75%]">
          <p className="text-sm text-white whitespace-pre-wrap">{msg.content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 text-white text-sm font-bold">
          {userInitial}
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3 items-start">
      <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-blue-400" />
      </div>
      <div className="bg-gray-800 border border-gray-700 px-4 py-3 rounded-lg max-w-[80%]">
        <p className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{msg.content}</p>
        {msg.confidence != null && (
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-700">
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${Math.round(msg.confidence * 100)}%` }}
                />
              </div>
              <span className="text-xs text-gray-400">{Math.round(msg.confidence * 100)}%</span>
            </div>
            <button
              onClick={() => onBookmark(msg.queryId)}
              className={`p-1 rounded transition-colors ${
                msg.bookmarked ? 'text-yellow-400' : 'text-gray-500 hover:text-yellow-400'
              }`}
            >
              <Bookmark size={14} fill={msg.bookmarked ? 'currentColor' : 'none'} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatBox() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Namaste! Main aapka AI document assistant hoon. Apne documents ke baare mein kuch bhi poochho — main unhe dhundh ke jawab dunga. 🚀',
      id: 'welcome',
    }
  ])
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [docId, setDocId]         = useState(null)
  const [documents, setDocuments] = useState([])
  const [showDocs, setShowDocs]   = useState(false)

  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  const userInitial = user?.name
    ? user.name.charAt(0).toUpperCase()
    : '?'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    documentsAPI.list()
      .then(res => setDocuments(res.data))
      .catch(() => {})
  }, [])

  const sendMessage = async () => {
    const q = input.trim()
    if (!q || loading) return

    if (q.length < 5) {
      toast.error('Question kam se kam 5 characters ka hona chahiye')
      return
    }

    const userMsg = { role: 'user', content: q, id: Date.now() }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)
    inputRef.current?.focus()

    try {
      const res = await queriesAPI.ask({ question: q, document_id: docId || null })
      const data = res.data
      const aiMsg = {
        role:       'assistant',
        content:    data.answer,
        confidence: data.confidence,
        queryId:    data.id,
        bookmarked: data.is_bookmarked,
        id:         data.id,
      }
      setMessages(m => [...m, aiMsg])
    } catch (err) {
      const raw = err.response?.data?.detail
      const detail = Array.isArray(raw)
        ? raw.map(e => e.msg || JSON.stringify(e)).join(', ')
        : (typeof raw === 'string' ? raw : 'Kuch error hua, dobara try karo')
      setMessages(m => [...m, {
        role: 'assistant',
        content: `⚠️ ${detail}`,
        id: Date.now(),
      }])
      toast.error(detail)
    } finally {
      setLoading(false)
    }
  }

  const handleBookmark = async (queryId) => {
    if (!queryId) return
    try {
      await queriesAPI.bookmark(queryId)
      setMessages(m =>
        m.map(msg => msg.queryId === queryId ? { ...msg, bookmarked: !msg.bookmarked } : msg)
      )
    } catch {
      toast.error('Bookmark failed')
    }
  }

  const selectedDoc = documents.find(d => d.id === docId)

  return (
    <div className="flex flex-col h-full">
      {/* Document selector bar */}
      <div className="px-4 py-2 border-b border-gray-700 bg-gray-900/50">
        <div className="relative inline-block">
          <button
            onClick={() => setShowDocs(s => !s)}
            className="flex items-center gap-2 text-sm text-gray-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <FileTextIcon size={14} />
            {selectedDoc ? selectedDoc.filename : 'All documents'}
            <ChevronDown size={14} className={`transition-transform ${showDocs ? 'rotate-180' : ''}`} />
          </button>

          {showDocs && (
            <div className="absolute top-full left-0 mt-1 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden">
              <button
                onClick={() => { setDocId(null); setShowDocs(false) }}
                className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                  !docId ? 'text-blue-400 bg-blue-600/10' : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                All documents
              </button>
              {documents.map(d => (
                <button
                  key={d.id}
                  onClick={() => { setDocId(d.id); setShowDocs(false) }}
                  className={`w-full text-left px-4 py-2 text-sm truncate transition-colors ${
                    docId === d.id ? 'text-blue-400 bg-blue-600/10' : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {d.filename}
                </button>
              ))}
              {documents.length === 0 && (
                <p className="px-4 py-2 text-sm text-gray-500">No documents uploaded</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <Message key={msg.id} msg={msg} userInitial={userInitial} onBookmark={handleBookmark} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700 bg-gray-900">
        <div className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-lg px-3 focus-within:border-blue-500 transition-colors">
          <button className="text-gray-400 hover:text-white transition-colors p-1">
            <Paperclip size={18} />
          </button>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
            }}
            placeholder="Ask a question about your documents..."
            autoComplete="off"
            className="flex-1 bg-transparent border-none text-white placeholder-gray-500 focus:ring-0 focus:outline-none py-3 text-sm"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="text-blue-400 hover:text-blue-300 disabled:text-gray-600 disabled:cursor-not-allowed transition-colors p-1"
          >
            <Send size={18} />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">AI can make mistakes. Verify important info.</p>
      </div>
    </div>
  )
}

function FileTextIcon({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  )
}
