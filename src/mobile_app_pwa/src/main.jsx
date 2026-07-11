import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

/**
 * ⚡ Bolt: Extremely robust CI Safety for browser-worker environments.
 * Checks for document, getElementById, and handles potential property-access throws.
 */
function init() {
  try {
    if (typeof document === 'undefined' || document === null) {
      console.warn("Document not available. Skipping render.");
      return;
    }

    if (typeof document.getElementById !== 'function') {
      console.warn("document.getElementById is not a function. Skipping render.");
      return;
    }

    const rootElement = document.getElementById('root');
    if (rootElement) {
      createRoot(rootElement).render(
        <StrictMode>
          <App />
        </StrictMode>,
      );
    } else {
      console.warn("Root element '#root' not found. Skipping render.");
    }
  } catch (error) {
    console.error("Critical error during React initialization:", error);
  }
}

init();
