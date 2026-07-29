import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;
try {
  try {
    if (typeof document !== 'undefined' && document && 'getElementById' in document) {
      rootElement = document.getElementById('root');
    }
  } catch (e) {
    // Nested safe catch
  }
} catch (e) {
  // Safe fallback
}

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
