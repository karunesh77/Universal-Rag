import { MessageSquare, FileText, Clock, LogOut, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV = [
  { id: 'chat',      label: 'Chat',      Icon: MessageSquare },
  { id: 'documents', label: 'Documents',  Icon: FileText },
  { id: 'history',   label: 'History',    Icon: Clock },
]

export default function Sidebar({ active, setActive, mobileOpen, setMobileOpen }) {
  const { user, logout } = useAuth()

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={`
          fixed top-0 left-0 h-full w-64 bg-gray-900 border-r border-gray-700
          flex flex-col z-40 transition-transform duration-200
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Brand */}
        <div className="p-5 border-b border-gray-700">
          <h1 className="text-xl font-bold text-white">RAG System</h1>
          <p className="text-sm text-gray-400 mt-1">AI Document Assistant</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => { setActive(id); setMobileOpen(false) }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                active === id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="p-4 border-t border-gray-700 space-y-2">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
              {user?.name ? user.name.charAt(0).toUpperCase() : '?'}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-medium text-white truncate">{user?.name || 'User'}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email || ''}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-red-400 transition-colors"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </aside>
    </>
  )
}
