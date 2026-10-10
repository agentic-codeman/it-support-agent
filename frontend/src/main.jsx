import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'sonner'
import App from './App'
import './index.css'

console.log('=== Main.jsx 开始执行 ===')

const rootElement = document.getElementById('root')
console.log('Root 元素:', rootElement)

if (!rootElement) {
  console.error('找不到 root 元素！')
} else {
  const root = ReactDOM.createRoot(rootElement)
  console.log('Root 创建成功')
  
  root.render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </React.StrictMode>,
  )
  
  console.log('=== React 应用已渲染 ===')
}
