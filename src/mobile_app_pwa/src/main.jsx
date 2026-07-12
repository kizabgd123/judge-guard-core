import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  rootElement = typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function'
    ? document.getElementById('root')
    : null;
} catch (e) {
  // Silent fail for non-browser environments
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
