import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  try {
    if (typeof document !== 'undefined') {
      rootElement = document.getElementById('root');
    }
  } catch (inner) {}
} catch (e) {
  // Ignore errors in restricted environments
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
