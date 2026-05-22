import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Auto-attach token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ─── Auth ────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login', data),
  me:       ()     => api.get('/auth/me'),
}

// ─── Documents ───────────────────────────────
export const documentsAPI = {
  upload:   (formData) => api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  list:     (skip = 0, limit = 20) => api.get(`/documents/?skip=${skip}&limit=${limit}`),
  get:      (id)   => api.get(`/documents/${id}`),
  delete:   (id)   => api.delete(`/documents/${id}`),
  stats:    ()     => api.get('/documents/stats/summary'),
  process:  (id)   => api.post(`/documents/${id}/process`),
}

// ─── Queries ─────────────────────────────────
export const queriesAPI = {
  ask:          (data)  => api.post('/queries/ask', data),
  list:         (skip = 0, limit = 20) => api.get(`/queries/?skip=${skip}&limit=${limit}`),
  get:          (id)    => api.get(`/queries/${id}`),
  delete:       (id)    => api.delete(`/queries/${id}`),
  bookmark:     (id)    => api.post(`/queries/${id}/bookmark`),
  stats:        ()      => api.get('/queries/stats/summary'),
}

export default api
