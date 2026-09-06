import { ref, onMounted } from 'vue'
import type {
  ApiResult,
  BatchDeleteResult,
  DownloadResult,
  ExportResult,
  ImportResult,
  LocalizeResult,
  RemoteListResult,
  ScanResult,
  UploadResult,
} from '@/types/api'

// PyWebView API 的类型定义(与 backend/api.py 的 _PUBLIC_METHODS 一一对应)
interface PyWebViewApi {
  get_last_directory(): Promise<string>
  browse_directory(): Promise<string | null>
  get_downloads_directory(): Promise<string>
  scan_vpk_files(directory: string): Promise<ScanResult>
  export_vpks(file_paths: string[], output_dir: string, better_naming?: boolean): Promise<ExportResult>
  import_compressed_vpks(): Promise<ImportResult>
  localize_workshop_vpks(file_paths: string[], better_naming?: boolean): Promise<LocalizeResult>
  open_directory(path: string): Promise<boolean>
  delete_vpk_file(file_path: string, disable?: boolean): Promise<ApiResult>
  delete_multiple_vpk_files(file_paths: string[], disable?: boolean): Promise<BatchDeleteResult>
  enable_vpk_file(file_path: string): Promise<ApiResult>
  reset_app_data(): Promise<boolean>
  log_from_js(level: string, message: string): Promise<void>
  get_sftp_settings(): Promise<Record<string, string>>
  save_sftp_settings(settings: Record<string, string>): Promise<ApiResult>
  list_remote_vpks(): Promise<RemoteListResult>
  delete_remote_vpk(file_path: string): Promise<ApiResult>
  delete_multiple_remote_vpks(file_paths: string[]): Promise<BatchDeleteResult>
  rename_remote_vpk(old_path: string, new_path: string): Promise<ApiResult>
  download_remote_vpks(remote_file_paths: string[]): Promise<DownloadResult>
  upload_local_vpks(local_file_paths: string[], better_naming?: boolean): Promise<UploadResult>
  open_external_url(url: string): Promise<void>
}

declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewApi
    }
  }
}

/**
 * 获取已就绪的 PyWebView API 实例(带类型)。
 * 调用方应先用 waitForApiReady 确认就绪;未就绪时抛错并提示。
 */
export function getApi(): PyWebViewApi {
  const api = window.pywebview?.api
  if (!api) {
    throw new Error('PyWebView API not ready')
  }
  return api
}

/**
 * 统一的 API 调用封装：捕获 API 未就绪与调用异常，避免未处理的 promise rejection。
 * 适用于不需要向用户通知失败细节的场景；需要区分成功/失败的调用仍应自行 try/catch。
 */
export async function callApi<T>(
  operation: (api: PyWebViewApi) => Promise<T>,
  fallback: T
): Promise<T> {
  try {
    return await operation(getApi())
  } catch (error) {
    console.error('PyWebView API 调用失败:', error)
    return fallback
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
