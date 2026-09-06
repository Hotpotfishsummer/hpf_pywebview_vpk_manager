import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useVpkManagerStore, type VpkFile } from '@/stores/vpk-manager'

function makeVpk(path: string): VpkFile {
  return {
    name: path.split('/').pop() ?? path,
    path,
    size: 1024,
    modified_time: 0,
    is_valid: true,
    is_disabled: false,
    display_name: path,
  }
}

describe('vpk-manager store 选中逻辑', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('toggle 单选切换', () => {
    const store = useVpkManagerStore()
    store.localVpkFiles.push(makeVpk('/a/mod.vpk'), makeVpk('/a/other.vpk'))

    store.toggleLocalVpkSelection('/a/mod.vpk')
    expect(store.selectedLocalVpks.has('/a/mod.vpk')).toBe(true)

    store.toggleLocalVpkSelection('/a/mod.vpk')
    expect(store.selectedLocalVpks.has('/a/mod.vpk')).toBe(false)
  })

  it('全选与取消全选', () => {
    const store = useVpkManagerStore()
    store.workshopVpkFiles.push(makeVpk('/w/1.vpk'), makeVpk('/w/2.vpk'))

    store.selectAllWorkshop()
    expect(store.selectedWorkshopVpks.size).toBe(2)

    store.deselectAllWorkshop()
    expect(store.selectedWorkshopVpks.size).toBe(0)
  })

  it('getSelectedVpkPaths 汇总本地与工坊选择', () => {
    const store = useVpkManagerStore()
    store.localVpkFiles.push(makeVpk('/a/mod.vpk'))
    store.workshopVpkFiles.push(makeVpk('/w/1.vpk'))

    store.toggleLocalVpkSelection('/a/mod.vpk')
    store.toggleWorkshopVpkSelection('/w/1.vpk')

    expect(store.getSelectedVpkPaths().sort()).toEqual(['/a/mod.vpk', '/w/1.vpk'])
  })

  it('通知错误消息不清除,非错误 3 秒后自动清除', () => {
    vi.useFakeTimers()
    const store = useVpkManagerStore()
    store.showNotification('err', 'error')
    expect(store.notification.message).toBe('err')
    vi.advanceTimersByTime(5000)
    expect(store.notification.message).toBe('err')

    store.showNotification('ok', 'success')
    vi.advanceTimersByTime(3000)
    expect(store.notification.message).toBe('')
    vi.useRealTimers()
  })
})
