import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  const rootElement = typeof document !== 'undefined' ? document.getElementById('root') : null;
  if (rootElement) {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  }
} catch (e) {
  console.error("Failed to render App:", e);
}
