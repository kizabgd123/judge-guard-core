import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let doc;
  try {
    doc = document;
  } catch {}

  if (doc) {
    let hasGetElementById = false;
    try {
      hasGetElementById = 'getElementById' in doc;
    } catch {}

    if (hasGetElementById) {
      let rootEl;
      try {
        rootEl = doc.getElementById('root');
      } catch {}

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
