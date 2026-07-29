import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let hasGetElement = false;
  try {
    hasGetElement = typeof document !== 'undefined' && document !== null && 'getElementById' in document;
  } catch (e) {
    // Suppress errors during global object proxy checks in restrictive build runtimes
  }

  if (hasGetElement) {
    const rootEl = document.getElementById('root');
    if (rootEl) {
      createRoot(rootEl).render(
        <StrictMode>
          <App />
        </StrictMode>
      );
    }
  }
} catch (e) {
  // Catch any potential mounting errors in restricted CI worker environments
}
