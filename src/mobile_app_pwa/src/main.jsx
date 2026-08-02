import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let rootElement = null;
  try {
    if (typeof document !== 'undefined' && 'getElementById' in document) {
      rootElement = document.getElementById('root');
    }
  } catch {
    // Suppress property access errors in restrictive environments like Cloudflare Worker CI
  }

  if (rootElement) {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  }
} catch {
  // Global defensive catch to prevent build-time crashes
}
