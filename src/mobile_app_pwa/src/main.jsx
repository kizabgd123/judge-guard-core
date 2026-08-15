import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  try {
    if ('document' in globalThis && globalThis.document) {
      if ('getElementById' in globalThis.document) {
        rootElement = globalThis.document.getElementById('root');
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
  )
}
