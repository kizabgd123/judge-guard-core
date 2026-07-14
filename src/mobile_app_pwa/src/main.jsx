import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// CI Safety: Robust guard for browser-worker environments
let rootElement = null;
try {
  if (typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function') {
    rootElement = document.getElementById('root');
  }
} catch (e) {}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
