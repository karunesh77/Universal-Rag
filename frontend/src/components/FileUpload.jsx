import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { documentsAPI } from '../utils/api'
import toast from 'react-hot-toast'
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react'

const ACCEPT = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
  'text/plain': ['.txt'],
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB'
  return (bytes/(1024*1024)).toFixed(1) + ' MB'
}

function UploadItem({ file, status, error, onRemove }) {
  const statusStyles = {
    done:    'bg-green-900/20 border-green-800',
    error:   'bg-red-900/20 border-red-800',
    loading: 'bg-blue-900/20 border-blue-800',
    waiting: 'bg-gray-800 border-gray-700',
  }

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${statusStyles[status] || statusStyles.waiting}`}>
      <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center flex-shrink-0">
        <FileText size={14} className="text-gray-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{file.name}</p>
        <p className="text-xs text-gray-500">{formatBytes(file.size)}</p>
        {error && <p className="text-xs text-red-400 mt-0.5">{error}</p>}
      </div>
      <div className="flex-shrink-0">
        {status === 'loading' && <Loader2 size={16} className="text-blue-400 animate-spin" />}
        {status === 'done' && <CheckCircle size={16} className="text-green-400" />}
        {status === 'error' && <AlertCircle size={16} className="text-red-400" />}
        {status === 'waiting' && (
          <button onClick={onRemove} className="text-gray-500 hover:text-red-400 transition-colors">
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  )
}

export default function FileUpload({ onUploaded }) {
  const [queue, setQueue] = useState([])

  const onDrop = useCallback((accepted) => {
    const newItems = accepted.map(f => ({ file: f, status: 'waiting', error: null, id: Math.random() }))
    setQueue(q => [...q, ...newItems])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxSize: 50 * 1024 * 1024,
    onDropRejected: (rejects) => {
      rejects.forEach(r => {
        const msg = r.errors[0]?.code === 'file-too-large'
          ? 'File too large (max 50 MB)'
          : 'File type not supported'
        toast.error(`${r.file.name}: ${msg}`)
      })
    }
  })

  const uploadFile = async (item) => {
    setQueue(q => q.map(i => i.id === item.id ? { ...i, status: 'loading' } : i))
    try {
      const fd = new FormData()
      fd.append('file', item.file)
      const res = await documentsAPI.upload(fd)
      setQueue(q => q.map(i => i.id === item.id ? { ...i, status: 'done' } : i))
      toast.success(`${item.file.name} uploaded!`)
      onUploaded?.(res.data)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Upload failed'
      setQueue(q => q.map(i => i.id === item.id ? { ...i, status: 'error', error: msg } : i))
      toast.error(msg)
    }
  }

  const uploadAll = async () => {
    const waiting = queue.filter(i => i.status === 'waiting')
    if (!waiting.length) return toast.error('No files to upload')
    for (const item of waiting) await uploadFile(item)
  }

  const removeItem = (id) => setQueue(q => q.filter(i => i.id !== id))
  const clearDone  = () => setQueue(q => q.filter(i => i.status !== 'done'))
  const waiting    = queue.filter(i => i.status === 'waiting').length

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-blue-500 bg-blue-900/20'
            : 'border-gray-700 hover:border-gray-500 hover:bg-gray-800/50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload size={28} className={`mx-auto mb-3 ${isDragActive ? 'text-blue-400' : 'text-gray-500'}`} />
        {isDragActive ? (
          <p className="text-blue-400 font-semibold">Drop files here!</p>
        ) : (
          <>
            <p className="text-white font-semibold mb-1">Drag files here or click to browse</p>
            <p className="text-gray-500 text-sm">PDF, DOCX, XLSX, PPTX, TXT — max 50 MB</p>
          </>
        )}
      </div>

      {queue.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-white">{queue.length} file(s)</p>
            <button onClick={clearDone} className="text-xs text-gray-500 hover:text-white transition-colors">
              Clear done
            </button>
          </div>
          <div className="space-y-2 max-h-52 overflow-y-auto">
            {queue.map(item => (
              <UploadItem
                key={item.id}
                file={item.file}
                status={item.status}
                error={item.error}
                onRemove={() => removeItem(item.id)}
              />
            ))}
          </div>
          {waiting > 0 && (
            <button
              onClick={uploadAll}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              <Upload size={16} />
              Upload {waiting} file{waiting > 1 ? 's' : ''}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
