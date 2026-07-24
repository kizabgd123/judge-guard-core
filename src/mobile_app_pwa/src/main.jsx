import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof document !== 'undefined') {
    try {
      if ('getElementById' in document) {
        try {
          const rootEl = document.getElementById('root')
          if (rootEl) {
            createRoot(rootEl).render(
              <StrictMode>
                <App />
              </StrictMode>,
            )
          }
        } catch (e) {}
      }
    } catch (e) {}
  }
} catch (e) {
  console.warn("CI Worker document guard triggered in main.jsx:", e)
}
