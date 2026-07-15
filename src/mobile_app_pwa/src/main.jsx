import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// ⚡ Bolt: Hardened root initialization for restricted CI/Worker environments.
const initRoot = () => {
  try {
    if (typeof document !== 'undefined') {
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
    /* Prevent build-time crashes in restricted environments */
  }
};

initRoot();
