import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let rootElement = null;
  if (typeof document !== 'undefined') {
    try {
      if ('getElementById' in document) {
        rootElement = document.getElementById('root');
      }
    } catch (inner) {}
  }

  if (rootElement) {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  }
} catch (e) {
  console.error("Critical: Failed to initialize PWA root", e);
}
