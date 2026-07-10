import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const container = typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function'
  ? document.getElementById('root')
  : null;

if (container) {
  createRoot(container).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
