import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let hasDocument = false;
  try {
    if (typeof globalThis !== 'undefined' && 'document' in globalThis) {
      try {
        if (globalThis.document && 'getElementById' in globalThis.document) {
          hasDocument = true;
        }
      } catch (e) {
        // Nested catch for property access on globalThis.document
      }
    }
  } catch (e) {
    // Outer catch
  }

  if (hasDocument) {
    try {
      const container = globalThis.document.getElementById('root');
      if (container) {
        createRoot(container).render(
          <StrictMode>
            <App />
          </StrictMode>,
        )
      }
    } catch (e) {
      // Catch for render
    }
  }
} catch (e) {
  // Silent catch to prevent build/import-time crashes
}
