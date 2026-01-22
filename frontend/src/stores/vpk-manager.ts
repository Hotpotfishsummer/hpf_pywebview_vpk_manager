import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export interface VpkFile {
  name: string
  path: string
  size: number
  modified_time: number
  is_valid: boolean
  is_disabled: boolean
  thumbnail_path?: string
  addontitle?: string
  display_name: string
}

export const useVpkManagerStore = defineStore('vpkManager', () => {
  const currentDirectory = ref<string>('')
  const localVpkFiles = ref<VpkFile[]>([])
  const workshopVpkFiles = ref<VpkFile[]>([])
  const selectedLocalVpks = reactive(new Set<string>())
  const selectedWorkshopVpks = reactive(new Set<string>())
  const isScanning = ref(false)
  const isExporting = ref(false)
  const isDeleting = ref(false)
  const isImporting = ref(false)
  const isLocalizing = ref(false)
  const useBetterNaming = ref(true) // 默认开启
  
  // 消息提示状态
  const notification = reactive({
    message: '',
    type: 'info' as 'success' | 'error' | 'info'
  })

  function showNotification(message: string, type: 'success' | 'error' | 'info' = 'info') {
    notification.message = message
    notification.type = type
    
    // 如果是成功或提示消息，3秒后自动清除
    if (type !== 'error') {
      setTimeout(() => {
        if (notification.message === message) {
          notification.message = ''
        }
      }, 3000)
    }
  }

  function toggleLocalVpkSelection(path: string) {
    if (selectedLocalVpks.has(path)) {
      selectedLocalVpks.delete(path)
    } else {
      selectedLocalVpks.add(path)
    }
  }

  function toggleWorkshopVpkSelection(path: string) {
    if (selectedWorkshopVpks.has(path)) {
      selectedWorkshopVpks.delete(path)
    } else {
      selectedWorkshopVpks.add(path)
    }
  }

  function selectAllLocal() {
    localVpkFiles.value.forEach(vpk => {
      selectedLocalVpks.add(vpk.path)
    })
  }

  function deselectAllLocal() {
    selectedLocalVpks.clear()
  }

  function selectAllWorkshop() {
    workshopVpkFiles.value.forEach(vpk => {
      selectedWorkshopVpks.add(vpk.path)
    })
  }

  function deselectAllWorkshop() {
    selectedWorkshopVpks.clear()
  }

  function getSelectedVpkPaths(): string[] {
    return [...Array.from(selectedLocalVpks), ...Array.from(selectedWorkshopVpks)]
  }

  function clearError() {
    notification.message = ''
  }

  async function scanVpks(directory: string) {
    if (!directory) return

    isScanning.value = true
    showNotification('', 'info') // 清除之前的消息

    try {
      const result = await (window as any).pywebview.api.scan_vpk_files(directory)

      if (result.success) {
        currentDirectory.value = directory
        localVpkFiles.value = result.local_vpks || []
        workshopVpkFiles.value = result.workshop_vpks || []
        selectedLocalVpks.clear()
        selectedWorkshopVpks.clear()
        console.log(`Successfully scanned ${localVpkFiles.value.length + workshopVpkFiles.value.length} files`)
      } else {
        showNotification(result.error || 'Failed to scan VPK files', 'error')
      }
    } catch (error) {
      showNotification(`Scan error: ${error}`, 'error')
    } finally {
      isScanning.value = false
    }
  }

  async function importVpks() {
    if (!currentDirectory.value) {
      showNotification('请先选择 L4D2 安装目录', 'error')
      return
    }

    isImporting.value = true
    showNotification('', 'info')

    try {
      const result = await (window as any).pywebview.api.import_compressed_vpks()

      if (result.success) {
        // 导入成功，刷新列表
        await scanVpks(currentDirectory.value)
        showNotification(`成功导入了 ${result.imported_count} 个压缩包中的文件`, 'success')
        return result
      } else {
        showNotification(result.error || '导入失败', 'error')
        return result
      }
    } catch (error) {
      showNotification(`导入错误: ${error}`, 'error')
      throw error
    } finally {
      isImporting.value = false
    }
  }

  async function localizeVpks() {
    const paths = Array.from(selectedWorkshopVpks)
    if (paths.length === 0) return

    isLocalizing.value = true
    showNotification('', 'info')

    try {
      const result = await (window as any).pywebview.api.localize_workshop_vpks(
        paths, 
        useBetterNaming.value
      )

      if (result.success_count > 0) {
        // 本地化成功（至少部分），刷新列表
        await scanVpks(currentDirectory.value)
        const type = result.success ? 'success' : 'info'
        const msg = result.success 
          ? `已成功本地化 ${result.success_count} 个文件` 
          : `本地化完成：${result.success_count} 成功, ${result.errors.length} 失败`
        showNotification(msg, type)
        return result
      } else {
        showNotification(result.error || '本地化失败', 'error')
        return result
      }
    } catch (error) {
      showNotification(`本地化错误: ${error}`, 'error')
      throw error
    } finally {
      isLocalizing.value = false
    }
  }

  async function initialize() {
    console.log('Initializing VpkManager store...')
    try {
      const lastDir = await (window as any).pywebview.api.get_last_directory()
      if (lastDir) {
        console.log('Last directory found:', lastDir)
        await scanVpks(lastDir)
      } else {
        console.log('No last directory stored.')
      }
    } catch (error) {
      console.warn('Failed to load last directory:', error)
    }
  }

  async function openAddonsFolder() {
    if (!currentDirectory.value) return
    const path = `${currentDirectory.value}/left4dead2/addons`
    await (window as any).pywebview.api.open_directory(path)
  }

  async function openWorkshopFolder() {
    if (!currentDirectory.value) return
    const path = `${currentDirectory.value}/left4dead2/addons/workshop`
    await (window as any).pywebview.api.open_directory(path)
  }

  async function exportVpks(outputDir: string) {
    const paths = getSelectedVpkPaths()
    if (paths.length === 0) {
      showNotification('No files selected for export', 'error')
      return
    }

    isExporting.value = true
    showNotification('', 'info')

    try {
      const result = await (window as any).pywebview.api.export_vpks(
        paths, 
        outputDir, 
        useBetterNaming.value
      )

      if (result.success) {
        // Clear selection after export
        selectedLocalVpks.clear()
        selectedWorkshopVpks.clear()
        showNotification('文件已成功导出', 'success')
      } else {
        showNotification(result.error || 'Export failed', 'error')
      }

      return result
    } catch (error) {
      showNotification(`Export error: ${error}`, 'error')
    } finally {
      isExporting.value = false
    }
  }

  async function deleteVpks(disable: boolean = true) {
    const paths = getSelectedVpkPaths()
    if (paths.length === 0) {
      showNotification('No files selected for deletion', 'error')
      return
    }

    isDeleting.value = true
    showNotification('', 'info')

    try {
      // Use batch delete method for better performance
      const result = await (window as any).pywebview.api.delete_multiple_vpk_files(paths, disable)
      
      if (!result.success && result.error_count > 0) {
        showNotification(`${result.error_count} files failed to delete`, 'error')
      } else if (result.success) {
        // Deleted successfully, clear selections
        selectedLocalVpks.clear()
        selectedWorkshopVpks.clear()
        showNotification('文件已成功删除', 'success')
      }

      // Always rescan after deletion attempt to update UI
      await scanVpks(currentDirectory.value)
    } catch (error) {
      showNotification(`Delete error: ${error}`, 'error')
      // Still try to rescan even if there was an error
      try {
        await scanVpks(currentDirectory.value)
      } catch (rescanError) {
        console.error('Error rescanning after deletion:', rescanError)
      }
    } finally {
      isDeleting.value = false
    }
  }

  async function getLastDirectory() {
    try {
      const lastDir = await (window as any).pywebview.api.get_last_directory()
      if (lastDir) {
        return lastDir
      }
    } catch (error) {
      console.error('Error getting last directory:', error)
    }
    return ''
  }

  return {
    currentDirectory,
    localVpkFiles,
    workshopVpkFiles,
    selectedLocalVpks,
    selectedWorkshopVpks,
    isScanning,
    isExporting,
    isDeleting,
    isImporting,
    isLocalizing,
    useBetterNaming,
    notification,
    showNotification,
    toggleLocalVpkSelection,
    toggleWorkshopVpkSelection,
    selectAllLocal,
    deselectAllLocal,
    selectAllWorkshop,
    deselectAllWorkshop,
    getSelectedVpkPaths,
    clearError,
    scanVpks,
    importVpks,
    localizeVpks,
    initialize,
    openAddonsFolder,
    openWorkshopFolder,
    exportVpks,
    deleteVpks,
    getLastDirectory
  }
})
