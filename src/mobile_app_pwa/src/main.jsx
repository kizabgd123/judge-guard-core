import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

function getRootElement() {
  try {
    if (typeof globalThis !== 'undefined' && 'document' in globalThis && globalThis.document) {
      if ('getElementById' in globalThis.document) {
        return globalThis.document.getElementById('root');
      }
    }
  } catch {
    // Return null if document access throws in restrictive proxied environments like Cloudflare Workers
  }
  return null;
}

const rootElement = getRootElement();

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
