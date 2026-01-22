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
  const isSftpActive = ref(false)
  const isRemoteScanning = ref(false)
  const isDownloading = ref(false)
  const isUploading = ref(false)
  const useBetterNaming = ref(true) // 默认开启

  // SFTP 设置
  const sftpSettings = reactive({
    address: '',
    username: '',
    password: '',
    addons_path: ''
  })

  const remoteVpkFiles = ref<any[]>([])
  const selectedRemoteVpks = reactive(new Set<string>())
  
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
      // 加载上次目录
      const lastDir = await (window as any).pywebview.api.get_last_directory()
      if (lastDir) {
        console.log('Last directory found:', lastDir)
        await scanVpks(lastDir)
      } else {
        console.log('No last directory stored.')
      }

      // 加载 SFTP 设置
      const settings = await (window as any).pywebview.api.get_sftp_settings()
      if (settings) {
        Object.assign(sftpSettings, settings)
      }
    } catch (error) {
      console.warn('Failed to initialize settings:', error)
    }
  }

  async function saveSftpSettings() {
    try {
      const result = await (window as any).pywebview.api.save_sftp_settings({ ...sftpSettings })
      if (!result.success) {
        showNotification(result.error || '保存 SFTP 设置失败', 'error')
      }
      return result
    } catch (error) {
      showNotification(`保存 SFTP 设置错误: ${error}`, 'error')
      throw error
    }
  }

  function toggleRemoteVpkSelection(path: string) {
    if (selectedRemoteVpks.has(path)) {
      selectedRemoteVpks.delete(path)
    } else {
      selectedRemoteVpks.add(path)
    }
  }

  function selectAllRemote() {
    remoteVpkFiles.value.forEach(vpk => {
      selectedRemoteVpks.add(vpk.path)
    })
  }

  function deselectAllRemote() {
    selectedRemoteVpks.clear()
  }

  async function scanRemoteVpks() {
    isRemoteScanning.value = true
    try {
      const result = await (window as any).pywebview.api.list_remote_vpks()
      if (result.success) {
        remoteVpkFiles.value = result.files || []
        selectedRemoteVpks.clear() // 扫描后清除之前的选中
      } else {
        showNotification(result.error || '获取远程文件失败', 'error')
      }
    } catch (error) {
      showNotification(`SFTP 扫描错误: ${error}`, 'error')
    } finally {
      isRemoteScanning.value = false
    }
  }

  async function deleteRemoteVpk(path: string) {
    try {
      const result = await (window as any).pywebview.api.delete_remote_vpk(path)
      if (result.success) {
        showNotification('远程文件已删除', 'success')
        await scanRemoteVpks()
      } else {
        showNotification(result.error || '删除远程文件失败', 'error')
      }
    } catch (error) {
      showNotification(`删除远程文件错误: ${error}`, 'error')
    }
  }

  async function deleteMultipleRemoteVpks() {
    const paths = Array.from(selectedRemoteVpks)
    if (paths.length === 0) return
    
    isDeleting.value = true
    try {
      const result = await (window as any).pywebview.api.delete_multiple_remote_vpks(paths)
      if (result.success) {
        showNotification('已删除选中的远程文件', 'success')
      } else if (result.success_count > 0) {
        showNotification(`删除了 ${result.success_count} 个文件，${result.error_count} 个失败`, 'info')
      } else {
        showNotification('删除失败', 'error')
      }
      await scanRemoteVpks()
    } catch (error) {
      showNotification(`删除错误: ${error}`, 'error')
    } finally {
      isDeleting.value = false
    }
  }

  async function disableRemoteVpks() {
    const paths = Array.from(selectedRemoteVpks).filter(p => !p.endsWith('.disabled'))
    if (paths.length === 0) return
    
    isDeleting.value = true
    try {
      let successCount = 0
      for (const path of paths) {
        const result = await (window as any).pywebview.api.rename_remote_vpk(path, `${path}.disabled`)
        if (result.success) successCount++
      }
      showNotification(`已禁用 ${successCount} 个文件`, 'success')
      await scanRemoteVpks()
    } catch (error) {
      showNotification(`禁用错误: ${error}`, 'error')
    } finally {
      isDeleting.value = false
    }
  }

  async function enableRemoteVpks() {
    const paths = Array.from(selectedRemoteVpks).filter(p => p.endsWith('.disabled'))
    if (paths.length === 0) return
    
    isDeleting.value = true
    try {
      let successCount = 0
      for (const path of paths) {
        const result = await (window as any).pywebview.api.rename_remote_vpk(path, path.substring(0, path.length - 9))
        if (result.success) successCount++
      }
      showNotification(`已启用 ${successCount} 个文件`, 'success')
      await scanRemoteVpks()
    } catch (error) {
      showNotification(`启用错误: ${error}`, 'error')
    } finally {
      isDeleting.value = false
    }
  }

  async function downloadRemoteVpks() {
    const paths = Array.from(selectedRemoteVpks)
    if (paths.length === 0) return
    
    isDownloading.value = true
    showNotification('正在下载远程文件...', 'info')
    try {
      const result = await (window as any).pywebview.api.download_remote_vpks(paths)
      if (result.success) {
        showNotification(`成功下载了 ${result.downloaded_count} 个文件`, 'success')
        // 刷新本地列表
        if (currentDirectory.value) {
          await scanVpks(currentDirectory.value)
        }
      } else {
        showNotification(result.error || '下载失败', 'error')
      }
    } catch (error) {
      showNotification(`下载错误: ${error}`, 'error')
    } finally {
      isDownloading.value = false
    }
  }

  async function uploadLocalVpks() {
    const paths = getSelectedVpkPaths()
    if (paths.length === 0) return
    
    isUploading.value = true
    showNotification('正在上传文件到服务器...', 'info')
    try {
      const result = await (window as any).pywebview.api.upload_local_vpks(
        paths, 
        useBetterNaming.value
      )
      if (result.success) {
        showNotification(`成功上传了 ${result.uploaded_count} 个文件`, 'success')
        // 刷新远程列表
        if (isSftpActive.value) {
          await scanRemoteVpks()
        }
      } else {
        showNotification(result.error || '上传失败', 'error')
      }
    } catch (error) {
      showNotification(`上传错误: ${error}`, 'error')
    } finally {
      isUploading.value = false
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

  async function deleteVpks(disable: boolean = true, targetPaths?: string[]) {
    const paths = targetPaths || getSelectedVpkPaths()
    if (paths.length === 0) {
      showNotification('No files selected', 'error')
      return
    }

    isDeleting.value = true
    showNotification('', 'info')

    try {
      // Use batch delete method for better performance
      const result = await (window as any).pywebview.api.delete_multiple_vpk_files(paths, disable)
      
      if (!result.success && result.error_count > 0) {
        showNotification(`${result.error_count} files failed to process`, 'error')
      } else if (result.success) {
        // Deleted successfully, clear selections that were processed
        if (targetPaths) {
          targetPaths.forEach(p => {
            selectedLocalVpks.delete(p)
            selectedWorkshopVpks.delete(p)
          })
        } else {
          selectedLocalVpks.clear()
          selectedWorkshopVpks.clear()
        }
        showNotification(disable ? '文件状态已更新' : '文件已成功删除', 'success')
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
    selectedRemoteVpks,
    isScanning,
    isExporting,
    isDeleting,
    isImporting,
    isLocalizing,
    isSftpActive,
    isRemoteScanning,
    isDownloading,
    isUploading,
    useBetterNaming,
    sftpSettings,
    remoteVpkFiles,
    notification,
    showNotification,
    toggleLocalVpkSelection,
    toggleWorkshopVpkSelection,
    toggleRemoteVpkSelection,
    selectAllLocal,
    deselectAllLocal,
    selectAllWorkshop,
    deselectAllWorkshop,
    selectAllRemote,
    deselectAllRemote,
    getSelectedVpkPaths,
    clearError,
    scanVpks,
    importVpks,
    localizeVpks,
    saveSftpSettings,
    scanRemoteVpks,
    deleteRemoteVpk,
    deleteMultipleRemoteVpks,
    disableRemoteVpks,
    enableRemoteVpks,
    downloadRemoteVpks,
    uploadLocalVpks,
    initialize,
    openAddonsFolder,
    openWorkshopFolder,
    exportVpks,
    deleteVpks,
    getLastDirectory
  }
})
