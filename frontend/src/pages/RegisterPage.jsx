import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { User, Mail, Lock, Eye, EyeOff, ArrowRight, Check, Circle } from 'lucide-react'

function PasswordStrength({ password }) {
  const checks = [
    { label: '8+ characters', ok: password.length >= 8 },
    { label: 'Uppercase letter', ok: /[A-Z]/.test(password) },
    { label: 'Lowercase letter', ok: /[a-z]/.test(password) },
    { label: 'Number', ok: /\d/.test(password) },
  ]
  const score = checks.filter(c => c.ok).length

  if (!password) return null

  const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500']
  const labels = ['Weak', 'Fair', 'Good', 'Strong']

  return (
    <div className="mt-2 space-y-2">
      <div className="flex gap-1">
        {[0,1,2,3].map(i => (
          <div key={i} className={`h-1 flex-1 rounded-full transition-all ${i < score ? colors[score-1] : 'bg-gray-700'}`} />
        ))}
      </div>
      <p className="text-xs text-gray-400">
        Strength: <span className="text-gray-300">{labels[score-1] || 'Too weak'}</span>
      </p>
      <div className="grid grid-cols-2 gap-1">
        {checks.map(c => (
          <div key={c.label} className={`flex items-center gap-1.5 text-xs ${c.ok ? 'text-green-400' : 'text-gray-600'}`}>
            {c.ok ? <Check size={12} /> : <Circle size={12} />}
            {c.label}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function RegisterPage() {
  const [form, setForm]         = useState({ name: '', email: '', password: '' })
  const [loading, setLoading]   = useState(false)
  const [showPass, setShowPass] = useState(false)
  const { register } = useAuth()
  const navigate     = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name || !form.email || !form.password) return toast.error('Sab fields fill karo')
    setLoading(true)
    try {
      await register(form.email, form.name, form.password)
      toast.success('Account bana gaya! Ab login karo.')
      navigate('/login')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Create account</h1>
          <p className="text-gray-400 text-sm">Free mein start karo aaj hi</p>
        </div>

        <div className="bg-gray-900 border border-gray-700 rounded-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="text"
                  placeholder="John Doe"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type={showPass ? 'text' : 'password'}
                  placeholder="Create a strong password"
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 text-white placeholder-gray-500 rounded-lg pl-10 pr-10 py-3 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <PasswordStrength password={form.password} />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  Create Account
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-gray-400 mt-6">
            Pehle se account hai?{' '}
            <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">
              Login karo
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
