import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof document !== 'undefined') {
    try {
      if (document) {
        try {
          if ('getElementById' in document) {
            const rootElement = document.getElementById('root');
            if (rootElement) {
              createRoot(rootElement).render(
                <StrictMode>
                  <App />
                </StrictMode>,
              );
            }
          }
        } catch (e) {}
      }
    } catch (e) {}
  }
} catch (e) {
  console.warn("Skipping main rendering in non-browser environment:", e);
}
