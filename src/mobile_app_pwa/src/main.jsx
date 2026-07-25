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
  // Defensive guard for Cloudflare Worker CI/CD builds
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
