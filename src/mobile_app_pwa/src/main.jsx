import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: Robust guard for 'browser-worker' CI compatibility.
// Use a local variable to prevent 'document is not defined' during static analysis/workers.
const doc = typeof document !== 'undefined' ? document : null;

if (doc) {
  const rootElement = doc.getElementById('root');
  if (rootElement) {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  }
}
