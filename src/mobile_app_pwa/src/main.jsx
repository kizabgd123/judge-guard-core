import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof globalThis !== 'undefined' && 'document' in globalThis) {
    const doc = globalThis.document;
    if (doc && 'getElementById' in doc) {
      const rootEl = doc.getElementById('root');
      if (rootEl) {
        createRoot(rootEl).render(
          <StrictMode>
            <App />
          </StrictMode>,
        );
      }
    }
  }
} catch {
  // Suppress errors during Cloudflare Worker builds
}
