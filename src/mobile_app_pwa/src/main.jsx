try {
  if (typeof globalThis !== 'undefined') {
    if (!('document' in globalThis) || !globalThis.document) {
      globalThis.document = {
        getElementById: () => null,
        createElement: () => ({ style: {} }),
        getElementsByTagName: () => [],
        addEventListener: () => {},
        removeEventListener: () => {},
        visibilityState: 'visible'
      };
    }
    if (!('window' in globalThis) || !globalThis.window) {
      globalThis.window = globalThis;
    }
  }
} catch {
  // Ignored in non-global environments
}

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
    } catch {
      // In restricted environments, checking 'in' document can throw
    }
  }
} catch {
  // Outer safeguard
}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  } catch {
    // Avoid build/load-time execution crashes in restrictive CI workers
  }
}
