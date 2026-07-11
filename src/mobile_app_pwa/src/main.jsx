import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: CI Safety for browser-worker environments
const rootElement = typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function'
  ? document.getElementById('root')
  : null;

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
} else {
  console.warn("Root element not found or document not available. Skipping render.");
}
