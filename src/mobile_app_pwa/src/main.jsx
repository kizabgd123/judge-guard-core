import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
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
  console.error("Cloudflare Worker environment build fallback: ", e);
}
