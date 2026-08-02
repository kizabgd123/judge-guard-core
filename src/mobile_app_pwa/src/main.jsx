import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  if (typeof document !== 'undefined') {
    try {
      if ('getElementById' in document) {
        rootElement = document.getElementById('root');
      }
    } catch {
      // nested fallback
    }
  }
} catch {
  // outer fallback
}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } catch {
    // nested fallback
  }
}
