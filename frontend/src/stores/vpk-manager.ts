import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import i18n from '@/i18n'
import { getApi, callApi } from '@/composables/useApi'
import type { RemoteFile } from '@/types/api'

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
  const searchQuery = ref<string>('')

  function matchesQuery(vpk: VpkFile, query: string): boolean {
    const q = query.trim().toLowerCase()
    if (!q) return true
    return vpk.display_name.toLowerCase().includes(q) || vpk.name.toLowerCase().includes(q)
  }

  const filteredLocalVpkFiles = computed(() =>
    localVpkFiles.value.filter((vpk) => matchesQuery(vpk, searchQuery.value))
  )
  const filteredWorkshopVpkFiles = computed(() =>
    workshopVpkFiles.value.filter((vpk) => matchesQuery(vpk, searchQuery.value))
  )
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
  const isRestartingServer = ref(false)
  const useBetterNaming = ref(true) // 默认开启
  const useAutoOpenExport = ref(true) // 默认开启
  const exportProgress = reactive({ stage: '', done: 0, total: 0 })

  // SFTP 设置
  const sftpSettings = reactive({
    address: '',
    username: '',
    password: '',
    addons_path: ''
  })

  const remoteVpkFiles = ref<RemoteFile[]>([])
  const selectedRemoteVpks = reactive(new Set<string>())
  
  // 消息提示状态
  const notification = reactive({
    message: '',
    type: 'info' as 'success' | 'error' | 'info'
  })

  const confirmState = reactive({ show: false, message: '', resolve: null as null | ((v: boolean) => void) })

  function showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      confirmState.message = message
      confirmState.show = true
      confirmState.resolve = resolve
    })
  }

  function resolveConfirm(value: boolean) {
    if (confirmState.resolve) {
      confirmState.resolve(value)
      confirmState.resolve = null
    }
    confirmState.show = false
  }

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

  function selectAllLocal(paths?: string[]) {
    const list = paths ?? localVpkFiles.value.map((v) => v.path)
    list.forEach((p) => selectedLocalVpks.add(p))
  }

  function deselectAllLocal(paths?: string[]) {
    if (paths) {
      paths.forEach((p) => selectedLocalVpks.delete(p))
    } else {
      selectedLocalVpks.clear()
    }
  }

  function selectAllWorkshop(paths?: string[]) {
    const list = paths ?? workshopVpkFiles.value.map((v) => v.path)
    list.forEach((p) => selectedWorkshopVpks.add(p))
  }

  function deselectAllWorkshop(paths?: string[]) {
    if (paths) {
      paths.forEach((p) => selectedWorkshopVpks.delete(p))
    } else {
      selectedWorkshopVpks.clear()
    }
  }

  function getSelectedVpkPaths(): string[] {
    return [...Array.from(selectedLocalVpks), ...Array.from(selectedWorkshopVpks)]
  }

    /** 扫描本地与创意工坊 VPK 列表(经后端 scan_vpk_files) */
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

    /** 弹窗选择压缩包并导入到本地 addons(经后端 import_compressed_vpks) */
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

    /** 将选中的创意工坊 VPK 本地化到 addons(可选 better_naming 重命名) */
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

      if ((result.success_count ?? 0) > 0) {
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

    /** 应用启动初始化:恢复上次目录并立即扫描 */
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

    /** 保存 SFTP 设置到偏好文件 */
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

    /** 列出远端 addons 目录的 VPK 文件 */
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

    /** 删除单个远端 VPK(含关联图片) */
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

    /** 批量删除选中的远端 VPK(含关联图片) */
async function deleteMultipleRemoteVpks() {
    const paths = Array.from(selectedRemoteVpks)
    if (paths.length === 0) return
    
    isDeleting.value = true
    try {
      const result = await getApi().delete_multiple_remote_vpks(paths)
      if (result.success) {
        showNotification($t('remoteDeletedSelected'), 'success')
      } else if ((result.success_count ?? 0) > 0) {
        showNotification($t('remoteDeletePartial', { success: result.success_count ?? 0, failed: result.error_count ?? 0 }), 'info')
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

    /** 远端禁用:重命名为 .disabled(含关联图片) */
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

    /** 远端启用:移除 .disabled 后缀(含关联图片) */
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

    /** 下载选中的远端 VPK 及关联图片到本地 addons */
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

    /** 上传选中的本地 VPK 及关联图片到远端 addons */
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

  /** 重启远端 L4D2 服务器容器 */
  async function restartL4d2Server() {
    isRestartingServer.value = true
    showNotification($t('restartingServer'), 'info')
    try {
      const result = await getApi().restart_l4d2_server()
      if (result.success) {
        const duration = result.duration_s ? ` (${result.duration_s}s)` : ''
        showNotification($t('restartServerSuccess') + duration, 'success')
      } else {
        showNotification(result.error || $t('restartServerFailed'), 'error')
      }
    } catch (error) {
      showNotification($t('restartServerError', { error }), 'error')
    } finally {
      isRestartingServer.value = false
    }
  }

  async function openAddonsFolder() {
    if (!currentDirectory.value) return
    const path = `${currentDirectory.value}/left4dead2/addons`
    await callApi(api => api.open_directory(path), false)
  }

  async function openWorkshopFolder() {
    if (!currentDirectory.value) return
    const path = `${currentDirectory.value}/left4dead2/addons/workshop`
    await callApi(api => api.open_directory(path), false)
  }

  async function exportVpks(outputDir: string, overwrite = false) {
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
        useBetterNaming.value,
        overwrite
      )

      if (result.success) {
        // Clear selection after export
        selectedLocalVpks.clear()
        selectedWorkshopVpks.clear()
        showNotification($t('exportDone'), 'success')
        if (useAutoOpenExport.value && outputDir) {
          await callApi(api => api.open_directory(outputDir), false)
        }
      } else if (result.exists) {
        // 文件已存在，由调用方决定如何处理（前端不自动弹出通知）
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
      
      if (!result.success && (result.error_count ?? 0) > 0) {
        showNotification($t('deletePartialFailed', { count: result.error_count ?? 0 }), 'error')
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
    searchQuery,
    filteredLocalVpkFiles,
    filteredWorkshopVpkFiles,
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
    isRestartingServer,
    useBetterNaming,
    useAutoOpenExport,
    exportProgress,
    sftpSettings,
    remoteVpkFiles,
    notification,
    showNotification,
    showConfirm,
    resolveConfirm,
    confirmState,
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
    restartL4d2Server,
    initialize,
    openAddonsFolder,
    openWorkshopFolder,
    exportVpks,
    deleteVpks,
    getLastDirectory
  }
})
