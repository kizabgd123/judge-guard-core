import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  if (typeof document !== 'undefined' && 'getElementById' in document) {
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
  console.warn("Skipping React root initialization in non-browser environment:", e);
}
