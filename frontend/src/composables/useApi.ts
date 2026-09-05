import { ref, onMounted } from 'vue'

// PyWebView API 的类型定义
interface PyWebViewApi {
  scan_vpk_files(directory: string): Promise<any>
  export_vpks(file_paths: string[], output_dir: string): Promise<any>
  delete_vpk_file(file_path: string, disable: boolean): Promise<any>
  delete_multiple_vpk_files(file_paths: string[], disable: boolean): Promise<any>
  get_last_directory(): Promise<string>
  get_downloads_directory(): Promise<string>
  browse_directory(): Promise<string | null>
  download_remote_vpks(remote_file_paths: string[]): Promise<any>
  upload_local_vpks(local_file_paths: string[], better_naming: boolean): Promise<any>
  open_external_url(url: string): Promise<void>
  log_from_js(level: string, message: string): Promise<void>
}

declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewApi
    }
  }
}

export function usePyWebViewApi() {
  const isApiReady = ref(false)

  // 检查 pywebview API 是否可用
  const checkApiReady = () => {
    const ready = !!(window.pywebview && window.pywebview.api)
    isApiReady.value = ready
    if (ready) {
      console.log('✓ PyWebView API 已就绪')
    } else {
      console.log('✗ PyWebView API 尚未准备好')
    }
    return ready
  }

  // 等待 API 就绪，带超时
  const waitForApiReady = (timeout: number = 3000): Promise<boolean> => {
    return new Promise((resolve) => {
      if (window.pywebview && window.pywebview.api) {
        console.log('✓ PyWebView API 立即可用')
        isApiReady.value = true
        resolve(true)
        return
      }

      console.log('⏳ 等待 PyWebView API...')
      
      const onReady = () => {
        console.log('✓ PyWebView API 通过事件就绪')
        isApiReady.value = true
        resolve(true)
      }

      window.addEventListener('pywebviewready', onReady, { once: true })

      setTimeout(() => {
        if (window.pywebview && window.pywebview.api) {
          isApiReady.value = true
          resolve(true)
        } else {
          window.removeEventListener('pywebviewready', onReady)
          console.warn('⚠ PyWebView API 超时未就绪')
          isApiReady.value = false
          resolve(false)
        }
      }, timeout)
    })
  }

  // 组件挂载时检查 API
  onMounted(() => {
    console.log('usePyWebViewApi 组件已挂载')
    checkApiReady()
    
    // 也尝试等待一下
    waitForApiReady()
  })

  return { isApiReady, checkApiReady, waitForApiReady }
}
