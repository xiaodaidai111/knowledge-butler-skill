import { createApp } from 'vue'
import App from '../App.vue'
import './styles/global.css'

const app = createApp(App)

app.config.errorHandler = (error, _instance, info) => {
  console.error('[一休] 页面运行异常', info, error)
  if (import.meta.env.DEV) {
    const root = document.querySelector('#app')
    if (root && !root.childElementCount) {
      const main = document.createElement('main')
      const panel = document.createElement('section')
      const title = document.createElement('b')
      const message = document.createElement('p')
      const detail = document.createElement('small')

      main.style.cssText = 'min-height:100vh;display:grid;place-items:center;padding:32px;background:#f7f1e5;color:#24484a;font-family:system-ui'
      panel.style.cssText = 'max-width:760px;padding:24px;border:1px solid #d6e3df;border-radius:16px;background:#fff'
      message.style.lineHeight = '1.7'
      title.textContent = '页面初始化失败'
      message.textContent = String(error?.message || error)
      detail.textContent = String(info || '请刷新页面后重试')
      panel.append(title, message, detail)
      main.append(panel)
      root.replaceChildren(main)
    }
  }
}

app.mount('#app')
