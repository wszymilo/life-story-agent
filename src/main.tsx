import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n'
import './index.css'
import App from './App.tsx'

const rootElement = document.getElementById('root')!

// Only enable StrictMode in development
const app = import.meta.env.DEV ? (
  <StrictMode>
    <App />
  </StrictMode>
) : (
  <App />
)

createRoot(rootElement).render(app)
