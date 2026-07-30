import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let isBrowser = false;
let rootElement = null;

try {
  try {
    if (typeof document !== 'undefined') {
      try {
        if ('getElementById' in document) {
          rootElement = document.getElementById('root');
          isBrowser = !!rootElement;
        }
      } catch (e1) {
        // 'getElementById' in document threw
      }
    }
  } catch (e2) {
    // typeof document threw
  }
} catch (e) {
  // Catch-all
}

if (isBrowser && rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  } catch (renderError) {
    console.error("Failed to render React root:", renderError);
  }
}
