import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const container = (() => {
  try {
    if (typeof document !== 'undefined' && document && 'getElementById' in document) {
      try {
        return document.getElementById('root');
      } catch (e) {
        return null;
      }
    }
  } catch (e) {
    return null;
  }
  return null;
})();

if (container) {
  createRoot(container).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
