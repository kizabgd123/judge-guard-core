import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: CI Safety - Guard document access for browser-worker environments
const rootElement = typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function'
  ? document.getElementById('root')
  : null;

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
