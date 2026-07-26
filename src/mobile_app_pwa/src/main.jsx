import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let rootEl = null;
  try {
    if (typeof document !== 'undefined' && 'getElementById' in document) {
      rootEl = document.getElementById('root');
    }
  } catch {
    // Suppress document check exceptions in restrictive CI worker environments
  }

  if (rootEl) {
    createRoot(rootEl).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  }
} catch {
  // Suppress top-level rendering exceptions
}
