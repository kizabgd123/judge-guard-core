import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootEl = null;
try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
    rootEl = document.getElementById('root');
  }
} catch {
  // Safe fallback for restricted environments (e.g. Cloudflare CI Worker)
}

if (rootEl) {
  createRoot(rootEl).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
