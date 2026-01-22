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
  const useBetterNaming = ref(true) // 默认开启
  const errorMessage = ref<string>('')

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
    errorMessage.value = ''
  }

  async function scanVpks(directory: string) {
    if (!directory) return

    isScanning.value = true
    errorMessage.value = ''

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
        errorMessage.value = result.error || 'Failed to scan VPK files'
      }
    } catch (error) {
      errorMessage.value = `Scan error: ${error}`
    } finally {
      isScanning.value = false
    }
  }

  async function importVpks() {
    if (!currentDirectory.value) {
      errorMessage.value = '请先选择 L4D2 安装目录'
      return
    }

    isImporting.value = true
    errorMessage.value = ''

    try {
      const result = await (window as any).pywebview.api.import_compressed_vpks()

      if (result.success) {
        // 导入成功，刷新列表
        await scanVpks(currentDirectory.value)
        return result
      } else {
        errorMessage.value = result.error || '导入失败'
        return result
      }
    } catch (error) {
      errorMessage.value = `导入错误: ${error}`
      throw error
    } finally {
      isImporting.value = false
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

  async function exportVpks(outputDir: string) {
    const paths = getSelectedVpkPaths()
    if (paths.length === 0) {
      errorMessage.value = 'No files selected for export'
      return
    }

    isExporting.value = true
    errorMessage.value = ''

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
      } else {
        errorMessage.value = result.error || 'Export failed'
      }

      return result
    } catch (error) {
      errorMessage.value = `Export error: ${error}`
    } finally {
      isExporting.value = false
    }
  }

  async function deleteVpks(disable: boolean = true) {
    const paths = getSelectedVpkPaths()
    if (paths.length === 0) {
      errorMessage.value = 'No files selected for deletion'
      return
    }

    isDeleting.value = true
    errorMessage.value = ''

    try {
      // Use batch delete method for better performance
      const result = await (window as any).pywebview.api.delete_multiple_vpk_files(paths, disable)
      
      if (!result.success && result.error_count > 0) {
        errorMessage.value = `${result.error_count} files failed to delete`
      } else if (result.success) {
        // Deleted successfully, clear selections
        selectedLocalVpks.clear()
        selectedWorkshopVpks.clear()
      }

      // Always rescan after deletion attempt to update UI
      await scanVpks(currentDirectory.value)
    } catch (error) {
      errorMessage.value = `Delete error: ${error}`
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
    useBetterNaming,
    errorMessage,
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
    initialize,
    exportVpks,
    deleteVpks,
    getLastDirectory
  }
})
