import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  try {
    if (typeof document !== 'undefined' && document) {
      if ('getElementById' in document) {
        rootElement = document.getElementById('root');
      }
    }
  // eslint-disable-next-line no-unused-vars
  } catch (e) {
    // Nested catch block to fully insulate from restrictively proxied global document checks
  }
// eslint-disable-next-line no-unused-vars
} catch (e) {
  // Outer fallback
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
