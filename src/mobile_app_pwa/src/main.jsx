import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let hasDocument = false;
  try {
    if (typeof document !== 'undefined' && 'getElementById' in document) {
      hasDocument = true;
    }
  } catch (e) {
    // Restrictive CI worker environments can throw on typeof/in checks
  }

  if (hasDocument) {
    const container = document.getElementById('root');
    if (container) {
      createRoot(container).render(
        <StrictMode>
          <App />
        </StrictMode>,
      )
    }
  }
} catch (e) {
  // Silent catch to prevent build/import-time crashes
}
