import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// CI Safety: Robust guards for browser-worker environments
let rootElement = null;
try {
  if (typeof document !== 'undefined') {
    try {
      if (document !== null && typeof document.getElementById === 'function') {
        rootElement = document.getElementById('root');
      }
    } catch (e) {}
  }
} catch (e) {}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } catch (e) {}
}
