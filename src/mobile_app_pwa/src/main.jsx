import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  if (typeof globalThis !== 'undefined' && globalThis) {
    try {
      if ('document' in globalThis) {
        try {
          const doc = globalThis.document;
          if (doc && 'getElementById' in doc) {
            try {
              rootElement = doc.getElementById('root');
            } catch (e) {}
          }
        } catch (e) {}
      }
    } catch (e) {}
  }
} catch (e) {}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
