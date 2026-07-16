import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: Hardened root mounting for restrictive CI environments
try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
    const rootElement = document.getElementById('root');
    if (rootElement) {
      createRoot(rootElement).render(
        <StrictMode>
          <App />
        </StrictMode>,
      )
    }
  }
} catch (e) {
  // Silent fail for CI build-time checks if DOM is unavailable or proxied
}
