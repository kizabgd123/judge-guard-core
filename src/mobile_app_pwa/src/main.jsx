import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;

try {
  // Defensive guard for restrictive proxied environment like Cloudflare Worker
  if (typeof document !== 'undefined') {
    try {
      if ('getElementById' in document) {
        rootElement = document.getElementById('root');
      }
    } catch (e) {
      // Ignored
    }
  }
} catch (e) {
  // Ignored
}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } catch (e) {
    // Ignored
  }
}
