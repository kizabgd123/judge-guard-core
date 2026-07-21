import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

try {
  let rootEl = null;
  try {
    if (typeof document !== 'undefined' && document && 'getElementById' in document) {
      rootEl = document.getElementById('root');
    }
  } catch (e) {}

  if (rootEl) {
    createRoot(rootEl).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  }
} catch (e) {}
