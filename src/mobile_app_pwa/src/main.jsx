import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  rootElement = document.getElementById('root');
} catch {
  try {
    if (typeof globalThis !== 'undefined' && globalThis && globalThis.document && globalThis.document.getElementById) {
      rootElement = globalThis.document.getElementById('root');
    }
  } catch {
    // Silent fallback for restrictive proxied environment like Cloudflare Workers
  }
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
