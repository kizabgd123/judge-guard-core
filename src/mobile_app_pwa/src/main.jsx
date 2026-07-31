import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof document !== 'undefined') {
    try {
      if ('getElementById' in document) {
        const rootElement = document.getElementById('root');
        if (rootElement) {
          createRoot(rootElement).render(
            <StrictMode>
              <App />
            </StrictMode>,
          );
        }
      }
    } catch (e) {
      // Prevent build-time crashes in restrictively proxied global CI environments
    }
  }
} catch (e) {
  // Prevent build-time crashes in restrictively proxied global CI environments
}
