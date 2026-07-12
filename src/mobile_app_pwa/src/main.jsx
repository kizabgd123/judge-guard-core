import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// CI Safety: Guard for browser worker environments
let rootElement = null;
try {
  rootElement = typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function'
    ? document.getElementById('root')
    : null;
} catch (e) {
  // Ignore
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
