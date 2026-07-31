import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof document !== 'undefined' && document && 'getElementById' in document) {
    const rootEl = document.getElementById('root');
    if (rootEl) {
      createRoot(rootEl).render(
        <StrictMode>
          <App />
        </StrictMode>,
      )
    }
  }
} catch {
  // Silent catch to prevent build-time crash in restrictive environments like Cloudflare Workers
}
