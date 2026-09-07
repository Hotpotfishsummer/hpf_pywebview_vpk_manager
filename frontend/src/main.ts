import { createApp } from 'vue'
import { createPinia } from 'pinia'
import i18n from '@/i18n'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import App from '@/App.vue'

// ============================================================
// PyWebView API 就绪检测
// ============================================================
const waitForApi = (): Promise<void> => {
  return new Promise((resolve) => {
    if (window.pywebview && window.pywebview.api) {
      resolve()
      return
    }
    
    window.addEventListener('pywebviewready', () => {
      resolve()
    }, { once: true })
    
    // 强制超时，防止白屏
    setTimeout(resolve, 5000)
  })
}

// ============================================================
// 等待 API 就绪，然后启动 Vue 应用
// ============================================================
waitForApi().then(() => {
  // 设置前端日志重定向到 Python 后端
  const api = window.pywebview?.api;
  if (api && typeof api.log_from_js === 'function') {
    const levels = ['log', 'info', 'warn', 'error', 'debug'] as const;
    
    levels.forEach(level => {
      const original = console[level];
      (console as any)[level] = (...args: any[]) => {
        // 先调用原始控制台方法（在浏览器 F12 中可见）
        original.apply(console, args);
        
        // 将日志发送到 Python 后端
        const message = args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ');
        
        // 注意：'log' 映射到 'info'
        const pyLevel = level === 'log' ? 'info' : level;
        api.log_from_js(pyLevel, message).catch(() => {});
      };
    });
    console.log('🚀 前端日志已重定向至 Python 控制台');
  }

  const app = createApp(App)
  
  // 导出进度回调(后端通过 evaluate_js 调用)
  ;(window as any).__onExportProgress = (payload: { stage: string; done: number; total: number }) => {
    const { exportProgress } = useVpkManagerStore()
    exportProgress.stage = payload.stage
    exportProgress.done = payload.done
    exportProgress.total = payload.total
  }
  
  app.use(createPinia())
  app.use(i18n)
  
  app.mount('#app')
})



