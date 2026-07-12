import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: CI Safety - Guard document access for browser-worker environments
let rootElement = null;
try {
  if (typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function') {
    rootElement = document.getElementById('root');
  }
} catch (e) {
  // In some environments, accessing document.getElementById may throw
}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } catch (e) {
    console.warn("CI Safety: Failed to render app root", e);
  }
}
