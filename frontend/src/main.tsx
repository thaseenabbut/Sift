import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { About } from './pages/about.tsx'
import { NotFound } from './pages/not-found.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/search" element={<App />} />
        <Route path="/about" element={<About />} />
        <Route path="/privacy" element={<div>Privacy</div>} />
        <Route path="/terms" element={<div>Terms</div>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
