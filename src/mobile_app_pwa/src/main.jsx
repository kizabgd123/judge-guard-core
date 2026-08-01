import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
    const rootEl = document.getElementById('root');
    if (rootEl) {
      createRoot(rootEl).render(
        <StrictMode>
          <App />
        </StrictMode>,
      );
    }
  }
} catch {
  // Silence error in restricted worker environments
}
