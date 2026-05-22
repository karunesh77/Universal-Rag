import { useState } from 'react'
import { Upload, Menu } from 'lucide-react'
import Sidebar     from '../components/Sidebar'
import FileUpload  from '../components/FileUpload'
import ChatBox     from '../components/ChatBox'
import DocumentList from '../components/DocumentList'
import { useAuth } from '../context/AuthContext'

function ChatPanel({ showUpload, onUploadDone }) {
  const [uploadTick, setUploadTick] = useState(0)

  const handleUploaded = () => {
    setUploadTick(t => t + 1)
    onUploadDone?.()
  }

  return (
    <div className="flex flex-col h-full">
      {showUpload && (
        <div className="p-4 border-b border-gray-700 bg-gray-900/50">
          <FileUpload onUploaded={handleUploaded} />
        </div>
      )}
      <div className="flex-1 min-h-0">
        <ChatBox key={uploadTick} />
      </div>
    </div>
  )
}

function DocumentsPanel() {
  const [tick, setTick] = useState(0)
  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold text-white">Documents</h2>
        <p className="text-sm text-gray-400 mt-1">Your uploaded documents</p>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <DocumentList refreshTrigger={tick} />
      </div>
    </div>
  )
}

function HistoryPanel() {
  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold text-white">Query History</h2>
        <p className="text-sm text-gray-400 mt-1">Your past questions</p>
      </div>
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-300 font-medium">Coming soon</p>
          <p className="text-gray-500 text-sm mt-1">Query history will appear here</p>
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [active, setActive]         = useState('chat')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [showUpload, setShowUpload] = useState(false)

  const titles = {
    chat: 'AI Chat',
    documents: 'Documents',
    history: 'Query History',
  }

  return (
    <div className="h-screen bg-gray-950 flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        active={active}
        setActive={setActive}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full md:ml-64">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-gray-700 bg-gray-900">
          {/* Mobile menu */}
          <button
            onClick={() => setMobileOpen(true)}
            className="md:hidden mr-3 text-gray-400 hover:text-white"
          >
            <Menu size={22} />
          </button>

          <h1 className="text-lg font-semibold text-white">{titles[active]}</h1>

          <div className="flex items-center gap-3">
            {active === 'chat' && (
              <button
                onClick={() => setShowUpload(s => !s)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  showUpload
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                <Upload size={16} />
                Upload
              </button>
            )}
          </div>
        </header>

        {/* Panel */}
        <div className="flex-1 min-h-0">
          {active === 'chat' && (
            <ChatPanel
              showUpload={showUpload}
              onUploadDone={() => setShowUpload(false)}
            />
          )}
          {active === 'documents' && <DocumentsPanel />}
          {active === 'history' && <HistoryPanel />}
        </div>
      </div>

      {/* Mobile FAB */}
      <button
        onClick={() => setMobileOpen(true)}
        className="md:hidden fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-lg"
      >
        <Menu size={22} />
      </button>
    </div>
  )
}
