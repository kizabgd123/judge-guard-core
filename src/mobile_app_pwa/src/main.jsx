import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

let rootElement = null;

try {
  try {
    if (typeof document !== 'undefined' && document) {
      if ('getElementById' in document) {
        rootElement = document.getElementById('root');
      }
    }
  } catch (innerErr) {
    void innerErr;
  }
} catch (outerErr) {
  void outerErr;
}

if (rootElement) {
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  } catch (renderErr) {
    void renderErr;
  }
}
