import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

/**
 * CI Safety: In browser-worker environments (e.g., Cloudflare Workers),
 * robust guards verify window and document presence to prevent crashes.
 */
const startApp = () => {
  try {
    if (typeof window !== 'undefined' && typeof document !== 'undefined' && document !== null && typeof document.getElementById === 'function') {
      const rootElement = document.getElementById('root');
      if (rootElement) {
        createRoot(rootElement).render(
          <StrictMode>
            <App />
          </StrictMode>,
        )
      }
    }
  } catch (err) {
    // Silent fail for non-browser environments (e.g. Workers)
  }
};

startApp();
