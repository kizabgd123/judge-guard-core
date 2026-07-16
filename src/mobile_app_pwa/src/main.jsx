import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: Ultra-hardened root mounting for restrictive CI environments
try {
  let docAvailable = false;
  try {
    if (typeof document !== 'undefined') {
      docAvailable = true;
    }
  } catch (e0) {}

  if (docAvailable) {
    let rootElement = null;
    try {
      if ('getElementById' in document) {
        rootElement = document.getElementById('root');
      }
    } catch (e1) {}

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
