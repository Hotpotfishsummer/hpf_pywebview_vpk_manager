import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'

// dev server 固定 5173 端口:main.py 的 PYWEBVIEW_DEV 模式硬编码加载
// http://localhost:5173,strictPort 防止端口被占用时静默漂移到其他端口。
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    strictPort: true,
    open: false
  },
  build: {
    outDir: 'dist',
    // 打包后由 pywebview 直接加载本地文件,sourcemap 无用武之地,关闭以减小体积
    sourcemap: false,
    // terser 比 esbuild 压缩率更高;产物会嵌入 exe,体积敏感
    minify: 'terser'
  }
})
