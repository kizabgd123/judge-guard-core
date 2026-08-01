/* eslint-disable no-empty */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  try {
    if (typeof document !== 'undefined' && document !== null) {
      try {
        if ('getElementById' in document) {
          const rootEl = document.getElementById('root');
          if (rootEl) {
            createRoot(rootEl).render(
              <StrictMode>
                <App />
              </StrictMode>,
            );
          }
        }
      } catch {}
    }
  } catch {}
} catch {
  // Suppress errors during Cloudflare Worker builds
}
