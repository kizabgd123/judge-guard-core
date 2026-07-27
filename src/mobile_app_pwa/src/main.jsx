import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: Defensive helper to prevent build-time crashes in restrictively proxied environments like Cloudflare Workers
let rootElement = null;
try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
    rootElement = document.getElementById('root');
  }
} catch (e) {
  // Guard against restrictive proxy exceptions
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
