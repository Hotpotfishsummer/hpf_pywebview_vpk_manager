import { ref, computed } from 'vue'
import type { VpkFile } from '@/stores/vpk-manager'

/**
 * VpkFilesList 中"本地区块/创意工坊区块"共用的折叠与全选逻辑。
 * 文件列表、选中集合与全选操作由调用方以 getter/函数注入,
 * 使同一段逻辑可同时驱动两个区块。
 */
export function useVpkSection(
  files: () => VpkFile[],
  isSelectedSet: () => Set<string>,
  selectAll: () => void,
  deselectAll: () => void
) {
  const expanded = ref(true)

  const allSelected = computed(() => {
    return files().length > 0 && files().every((vpk: VpkFile) => isSelectedSet().has(vpk.path))
  })

  function toggleExpanded() {
    expanded.value = !expanded.value
  }

  function toggleAll() {
    if (allSelected.value) {
      deselectAll()
    } else {
      selectAll()
    }
  }

  return { expanded, allSelected, toggleExpanded, toggleAll }
}
