import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#272a31',
            color: '#e1e2ec',
            border: '1px solid rgba(66, 71, 84, 0.3)',
            borderRadius: '12px',
            fontFamily: 'Inter, sans-serif',
            backdropFilter: 'blur(16px)',
          },
          success: { iconTheme: { primary: '#4d8eff', secondary: '#fff' } },
          error:   { iconTheme: { primary: '#ffb4ab', secondary: '#690005' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
