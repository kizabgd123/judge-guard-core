import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
    rootElement = document.getElementById('root');
  }
} catch (e) {
  // Silent catch for build-time safety in restrictive CI environments
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
