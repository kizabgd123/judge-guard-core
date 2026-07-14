import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// 🛡️ CI Safety: Ensure document and getElementById exist before attempting to render.
// This prevents crashes in browser-worker environments (e.g. Cloudflare Workers).
let rootElement = null;
try {
  // Defensive check against environment proxies that might throw on property access
  if (typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function') {
    rootElement = document.getElementById('root');
  }
} catch (e) {
  rootElement = null;
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
