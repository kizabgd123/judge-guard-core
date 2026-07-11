import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  const rootElement = typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function'
    ? document.getElementById('root')
    : null;

  if (rootElement) {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  }
} catch (e) {
  // Silent fail for non-browser environments (e.g. Workers build/SSR/Testing)
}
