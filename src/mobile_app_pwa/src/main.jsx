import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;

try {
  try {
    if ('getElementById' in document) {
      rootElement = document.getElementById('root');
    }
  } catch (innerErr) {
    // Inner catch for property access throwing on proxied document
  }
} catch (outerErr) {
  // Outer catch for typeof or document reference throwing
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
