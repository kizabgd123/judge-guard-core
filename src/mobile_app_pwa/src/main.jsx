import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  try {
    if (typeof globalThis !== 'undefined' && 'document' in globalThis) {
      const doc = globalThis.document;
      if (doc && 'getElementById' in doc) {
        rootElement = doc.getElementById('root');
      }
    }
  } catch {
    // ignored
  }
} catch {
  // Silent fallback for restrictive proxied environment like Cloudflare Workers
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
