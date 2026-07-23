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
  // Silent fallback for CI/CD environments
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
