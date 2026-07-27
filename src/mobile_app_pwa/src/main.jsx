import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;

try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
    rootElement = document.getElementById('root');
  }
} catch {
  // Safe fallback for restricted global document environments
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
