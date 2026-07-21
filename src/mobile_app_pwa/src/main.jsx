import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  if (typeof document !== 'undefined' && document) {
    try {
      if ('getElementById' in document) {
        rootElement = document.getElementById('root');
      }
    } catch (e) {
      // In restricted environments, checking 'in' document can throw
    }
  }
} catch (e) {
  // Outer safeguard
}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  } catch (e) {
    // Avoid build/load-time execution crashes in restrictive CI workers
  }
}
