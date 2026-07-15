import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: Hardened root initialization for restricted CI/Worker environments.
const initRoot = () => {
  try {
    let hasDoc = false;
    try {
      hasDoc = typeof document !== 'undefined';
    } catch (e) {
      /* ignore */
    }

    if (hasDoc) {
      let rootElement = null;
      try {
        if ('getElementById' in document) {
          rootElement = document.getElementById('root');
        }
      } catch (e) {
        /* ignore */
      }

      if (rootElement) {
        createRoot(rootElement).render(
          <StrictMode>
            <App />
          </StrictMode>,
        );
      }
    }
  } catch (e) {
    /* Prevent build-time crashes in restricted environments */
  }
};

initRoot();
