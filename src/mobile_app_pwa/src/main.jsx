import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let hasDocument = false;
  try {
    hasDocument = typeof document !== 'undefined' && document !== null;
  } catch (e) {}

  if (hasDocument) {
    let hasGetElement = false;
    try {
      hasGetElement = 'getElementById' in document;
    } catch (e) {}

    if (hasGetElement) {
      const container = document.getElementById('root');
      if (container) {
        createRoot(container).render(
          <StrictMode>
            <App />
          </StrictMode>
        );
      }
    }
  }
} catch (error) {
  // Silent fallback for restrictive environments like Cloudflare Workers CI
}
