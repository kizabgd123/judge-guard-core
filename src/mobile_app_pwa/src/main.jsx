import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: Guard document for 'browser-worker' CI compatibility
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
