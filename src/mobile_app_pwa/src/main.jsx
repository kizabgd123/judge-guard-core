import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  try {
    if (typeof document !== 'undefined') {
      try {
        if ('getElementById' in document) {
          try {
            const rootEl = document.getElementById('root');
            if (rootEl) {
              createRoot(rootEl).render(
                <StrictMode>
                  <App />
                </StrictMode>,
              );
            }
          } catch (err) {}
        }
      } catch (err) {}
    }
  } catch (err) {}
} catch (err) {}
