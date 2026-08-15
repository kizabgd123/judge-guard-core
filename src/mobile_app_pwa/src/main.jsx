import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  if (typeof document !== 'undefined' && document && typeof document.getElementById === 'function') {
    rootElement = document.getElementById('root');
  }
} catch {
  // Silent fallback for restrictive proxied environments like Cloudflare Workers
}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } catch {
    // Ignore render error in non-DOM worker environment
  }
}
