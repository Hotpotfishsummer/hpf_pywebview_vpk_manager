import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import i18n from '@/i18n'
import { getApi } from '@/composables/useApi'

// 组件外使用 vue-i18n 的全局实例,保证通知文案跟随当前语言
const $t = i18n.global.t

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
      const result = await getApi().scan_vpk_files(directory)

      if (result.success) {
        currentDirectory.value = directory
        localVpkFiles.value = result.local_vpks || []
        workshopVpkFiles.value = result.workshop_vpks || []
        selectedLocalVpks.clear()
        selectedWorkshopVpks.clear()
        console.log(`Successfully scanned ${localVpkFiles.value.length + workshopVpkFiles.value.length} files`)
      } else {
        showNotification(result.error || $t('scanFailed'), 'error')
      }
    } catch (error) {
      showNotification($t('scanError', { error }), 'error')
    } finally {
      isScanning.value = false
    }
  }

  async function importVpks() {
    if (!currentDirectory.value) {
      showNotification($t('needDirectoryFirst'), 'error')
      return
    }

    isImporting.value = true
    showNotification('', 'info')

    try {
      const result = await getApi().import_compressed_vpks()

      if (result.success) {
        // 导入成功，刷新列表
        await scanVpks(currentDirectory.value)
        showNotification($t('importSuccessPacks', { count: result.imported_count }), 'success')
        return result
      } else {
        showNotification(result.error || $t('importFailed'), 'error')
        return result
      }
    } catch (error) {
      showNotification($t('importError', { error }), 'error')
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
      const result = await getApi().localize_workshop_vpks(
        paths, 
        useBetterNaming.value
      )

      if (result.success_count > 0) {
        // 本地化成功（至少部分），刷新列表
        selectedWorkshopVpks.clear()
        await scanVpks(currentDirectory.value)
        const type = result.success ? 'success' : 'info'
        let msg = result.success 
          ? $t('localizeSuccess', { count: result.success_count })
          : $t('localizePartial', { count: result.success_count })
        
        if (result.errors && result.errors.length > 0) {
          msg += $t('localizePartialFailed', { count: result.errors.length })
        }
        showNotification(msg, type)
        return result
      } else {
        const errorMsg = result.error || (result.errors && result.errors.length > 0 ? result.errors[0] : $t('localizeFailed'))
        showNotification(errorMsg, 'error')
        return result
      }
    } catch (error) {
      showNotification($t('localizeError', { error }), 'error')
      throw error
    } finally {
      isLocalizing.value = false
    }
  }

  async function initialize() {
    console.log('Initializing VpkManager store...')
    try {
      // 加载上次目录
      const lastDir = await getApi().get_last_directory()
      if (lastDir) {
        console.log('Last directory found:', lastDir)
        await scanVpks(lastDir)
      } else {
        console.log('No last directory stored.')
      }

      // 加载 SFTP 设置
      const settings = await getApi().get_sftp_settings()
      if (settings) {
        Object.assign(sftpSettings, settings)
      }
    } catch (error) {
      console.warn('Failed to initialize settings:', error)
    }
  }

  async function saveSftpSettings() {
    try {
      const result = await getApi().save_sftp_settings({ ...sftpSettings })
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
      const result = await getApi().list_remote_vpks()
      if (result.success) {
        remoteVpkFiles.value = result.files || []
        selectedRemoteVpks.clear() // 扫描后清除之前的选中
      } else {
        showNotification(result.error || $t('remoteScanFailed'), 'error')
      }
    } catch (error) {
      showNotification($t('remoteScanError', { error }), 'error')
    } finally {
      isRemoteScanning.value = false
    }
  }

  async function deleteRemoteVpk(path: string) {
    try {
      const result = await getApi().delete_remote_vpk(path)
      if (result.success) {
        showNotification($t('remoteDeleted'), 'success')
        await scanRemoteVpks()
      } else {
        showNotification(result.error || $t('remoteDeleteFailed'), 'error')
      }
    } catch (error) {
      showNotification($t('remoteDeleteError', { error }), 'error')
    }
  }

  async function deleteMultipleRemoteVpks() {
    const paths = Array.from(selectedRemoteVpks)
    if (paths.length === 0) return
    
    isDeleting.value = true
    try {
      const result = await getApi().delete_multiple_remote_vpks(paths)
      if (result.success) {
        showNotification($t('remoteDeletedSelected'), 'success')
      } else if (result.success_count > 0) {
        showNotification($t('remoteDeletePartial', { success: result.success_count, failed: result.error_count }), 'info')
      } else {
        showNotification($t('deleteActionFailed'), 'error')
      }
      await scanRemoteVpks()
    } catch (error) {
      showNotification($t('deleteActionError', { error }), 'error')
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
        const result = await getApi().rename_remote_vpk(path, `${path}.disabled`)
        if (result.success) successCount++
      }
      showNotification($t('remoteDisabled', { count: successCount }), 'success')
      await scanRemoteVpks()
    } catch (error) {
      showNotification($t('remoteDisableError', { error }), 'error')
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
        const result = await getApi().rename_remote_vpk(path, path.substring(0, path.length - 9))
        if (result.success) successCount++
      }
      showNotification($t('remoteEnabled', { count: successCount }), 'success')
      await scanRemoteVpks()
    } catch (error) {
      showNotification($t('remoteEnableError', { error }), 'error')
    } finally {
      isDeleting.value = false
    }
  }

  async function downloadRemoteVpks() {
    const paths = Array.from(selectedRemoteVpks)
    if (paths.length === 0) return
    
    isDownloading.value = true
    showNotification($t('downloadingRemote'), 'info')
    try {
      const result = await getApi().download_remote_vpks(paths)
      if (result.success) {
        showNotification($t('downloadSuccess', { count: result.downloaded_count }), 'success')
        // 刷新本地列表
        if (currentDirectory.value) {
          await scanVpks(currentDirectory.value)
        }
      } else {
        showNotification(result.error || $t('downloadFailed'), 'error')
      }
    } catch (error) {
      showNotification($t('downloadError', { error }), 'error')
    } finally {
      isDownloading.value = false
    }
  }

  async function uploadLocalVpks() {
    const paths = getSelectedVpkPaths()
    if (paths.length === 0) return
    
    isUploading.value = true
    showNotification($t('uploadingLocal'), 'info')
    try {
      const result = await getApi().upload_local_vpks(
        paths, 
        useBetterNaming.value
      )
      if (result.success) {
        showNotification($t('uploadSuccess', { count: result.uploaded_count }), 'success')
        // 刷新远程列表
        if (isSftpActive.value) {
          await scanRemoteVpks()
        }
      } else {
        showNotification(result.error || $t('uploadFailed'), 'error')
      }
    } catch (error) {
      showNotification($t('uploadError', { error }), 'error')
    } finally {
      isUploading.value = false
    }
  }

  async function openAddonsFolder() {
    if (!currentDirectory.value) return
    const path = `${currentDirectory.value}/left4dead2/addons`
    await getApi().open_directory(path)
  }

  async function openWorkshopFolder() {
    if (!currentDirectory.value) return
    const path = `${currentDirectory.value}/left4dead2/addons/workshop`
    await getApi().open_directory(path)
  }

  async function exportVpks(outputDir: string) {
    const paths = getSelectedVpkPaths()
    if (paths.length === 0) {
      showNotification($t('selectFiles'), 'error')
      return
    }

    isExporting.value = true
    showNotification('', 'info')

    try {
      const result = await getApi().export_vpks(
        paths, 
        outputDir, 
        useBetterNaming.value
      )

      if (result.success) {
        // Clear selection after export
        selectedLocalVpks.clear()
        selectedWorkshopVpks.clear()
        showNotification($t('exportDone'), 'success')
      } else {
        showNotification(result.error || $t('exportError'), 'error')
      }

      return result
    } catch (error) {
      showNotification($t('exportErrorMsg', { error }), 'error')
    } finally {
      isExporting.value = false
    }
  }

  async function deleteVpks(disable: boolean = true, targetPaths?: string[]) {
    const paths = targetPaths || getSelectedVpkPaths()
    if (paths.length === 0) {
      showNotification($t('selectFiles'), 'error')
      return
    }

    isDeleting.value = true
    showNotification('', 'info')

    try {
      // Use batch delete method for better performance
      const result = await getApi().delete_multiple_vpk_files(paths, disable)
      
      if (!result.success && result.error_count > 0) {
        showNotification($t('deletePartialFailed', { count: result.error_count }), 'error')
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
        showNotification(disable ? $t('statusUpdated') : $t('deleteSuccess'), 'success')
      }

      // Always rescan after deletion attempt to update UI
      await scanVpks(currentDirectory.value)
    } catch (error) {
      showNotification($t('deleteActionError', { error }), 'error')
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
      const lastDir = await getApi().get_last_directory()
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
