import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let rootElement = null;
  try {
    if (typeof document !== 'undefined') {
      try {
        if ('getElementById' in document) {
          try {
            rootElement = document.getElementById('root');
          } catch {
            // ignore
          }
        }
      } catch {
        // ignore
      }
    }
  } catch {
    // ignore
  }

  if (rootElement) {
    try {
      createRoot(rootElement).render(
        <StrictMode>
          <App />
        </StrictMode>,
      );
    } catch {
      // ignore
    }
  }
} catch {
  // Global defensive catch to prevent build-time crashes
}
