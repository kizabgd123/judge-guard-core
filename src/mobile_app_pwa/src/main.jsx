import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let rootElement = null;
  try {
    if (typeof document !== 'undefined' && document && 'getElementById' in document) {
      rootElement = document.getElementById('root');
    }
  } catch (e) {
    // Ignore CI/CD environment-specific document exceptions
  }

  if (rootElement) {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  }
} catch (e) {
  // Prevent build-time crashes in restricted environments like Cloudflare Workers
}
