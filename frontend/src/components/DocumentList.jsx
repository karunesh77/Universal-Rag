import { useState, useEffect } from 'react'
import { documentsAPI } from '../utils/api'
import toast from 'react-hot-toast'
import { FileText, CheckCircle, Clock, Loader2, AlertCircle, Trash2, RefreshCw, Upload } from 'lucide-react'

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB'
  return (bytes/(1024*1024)).toFixed(1) + ' MB'
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

const STATUS_CONFIG = {
  completed:  { Icon: CheckCircle,  color: 'text-green-400',  bg: 'bg-green-900/30',  label: 'Ready' },
  pending:    { Icon: Clock,        color: 'text-yellow-400', bg: 'bg-yellow-900/30', label: 'Pending' },
  processing: { Icon: Loader2,     color: 'text-blue-400',   bg: 'bg-blue-900/30',   label: 'Processing', spin: true },
  failed:     { Icon: AlertCircle,  color: 'text-red-400',    bg: 'bg-red-900/30',    label: 'Failed' },
}

function DocCard({ doc, onDelete, onReprocess }) {
  const [deleting, setDeleting] = useState(false)
  const status = STATUS_CONFIG[doc.processing_status] || STATUS_CONFIG.pending
  const StatusIcon = status.Icon

  const handleDelete = async () => {
    if (!confirm(`"${doc.filename}" delete karna chahte ho?`)) return
    setDeleting(true)
    try {
      await documentsAPI.delete(doc.id)
      toast.success('Document deleted!')
      onDelete(doc.id)
    } catch {
      toast.error('Delete failed')
      setDeleting(false)
    }
  }

  const handleReprocess = async () => {
    try {
      await documentsAPI.process(doc.id)
      toast.success('Reprocessing started!')
      onReprocess(doc.id)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed')
    }
  }

  return (
    <div className="flex items-center gap-4 p-4 bg-gray-800/50 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors group">
      <div className="w-10 h-10 rounded-lg bg-gray-700 flex items-center justify-center flex-shrink-0">
        <FileText size={18} className="text-gray-400" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{doc.filename}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500">{formatBytes(doc.file_size)}</span>
          <span className="text-gray-600">·</span>
          <span className="text-xs text-gray-500">{formatDate(doc.created_at)}</span>
        </div>
      </div>

      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${status.bg} ${status.color}`}>
        <StatusIcon size={12} className={status.spin ? 'animate-spin' : ''} />
        {status.label}
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {doc.processing_status === 'failed' && (
          <button onClick={handleReprocess} className="p-1.5 rounded-lg text-gray-500 hover:text-blue-400 hover:bg-blue-900/20 transition-colors" title="Retry">
            <RefreshCw size={14} />
          </button>
        )}
        <button onClick={handleDelete} disabled={deleting} className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-900/20 transition-colors disabled:opacity-50" title="Delete">
          {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
        </button>
      </div>
    </div>
  )
}

export default function DocumentList({ refreshTrigger }) {
  const [docs, setDocs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats]     = useState(null)

  const fetchDocs = async () => {
    try {
      const [docRes, statRes] = await Promise.all([
        documentsAPI.list(),
        documentsAPI.stats(),
      ])
      setDocs(docRes.data)
      setStats(statRes.data)
    } catch {
      toast.error('Documents load nahi hue')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDocs() }, [refreshTrigger])

  const removeDoc = (id) => setDocs(d => d.filter(x => x.id !== id))
  const reprocess = () => fetchDocs()

  if (loading) return (
    <div className="flex items-center justify-center py-16">
      <Loader2 size={24} className="text-blue-400 animate-spin" />
    </div>
  )

  return (
    <div className="space-y-5">
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Total', value: stats.total_documents },
            { label: 'Processed', value: stats.processed },
            { label: 'Chunks', value: stats.total_chunks },
          ].map(s => (
            <div key={s.label} className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-center">
              <p className="text-xl font-bold text-white">{s.value}</p>
              <p className="text-xs text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Your Documents ({docs.length})</h3>
        <button onClick={fetchDocs} className="text-xs text-gray-500 hover:text-white flex items-center gap-1 transition-colors">
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {docs.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-gray-700 rounded-xl">
          <Upload size={28} className="text-gray-600 mx-auto mb-3" />
          <p className="text-white font-medium">No documents yet</p>
          <p className="text-gray-500 text-sm mt-1">Upload files from the Chat tab</p>
        </div>
      ) : (
        <div className="space-y-2">
          {docs.map(doc => (
            <DocCard key={doc.id} doc={doc} onDelete={removeDoc} onReprocess={reprocess} />
          ))}
        </div>
      )}
    </div>
  )
}
