import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import DirectorySelector from '@/components/DirectorySelector.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      apiNotInitialized: 'API 未初始化', browseError: '选择失败: {error}', browseFolder: '浏览文件夹',
    },
  },
})

async function mountSelector() {
  setActivePinia(createPinia())
  const { useVpkManagerStore } = await import('@/stores/vpk-manager')
  const store = useVpkManagerStore()
  const wrapper = mount(DirectorySelector, { global: { plugins: [i18n] } })
  await flushPromises()
  return { wrapper, store }
}

describe('DirectorySelector 组件', () => {
  beforeEach(() => {
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  it('API 就绪时浏览并触发扫描', async () => {
    const { wrapper, store } = await mountSelector()
    const scanSpy = vi.spyOn(store, 'scanVpks').mockResolvedValue()
    ;(window as any).pywebview = {
      api: { browse_directory: vi.fn(async () => '/picked/l4d2') },
    }

    await wrapper.find('.btn-browse').trigger('click')
    await new Promise(r => setTimeout(r, 200))
    await flushPromises()

    expect(scanSpy).toHaveBeenCalledWith('/picked/l4d2')
    delete (window as any).pywebview
  })

  it('用户取消选择(返回 null)不扫描', async () => {
    const { wrapper, store } = await mountSelector()
    const scanSpy = vi.spyOn(store, 'scanVpks').mockResolvedValue()
    ;(window as any).pywebview = {
      api: { browse_directory: vi.fn(async () => null) },
    }

    await wrapper.find('.btn-browse').trigger('click')
    await new Promise(r => setTimeout(r, 200))
    await flushPromises()

    expect(scanSpy).not.toHaveBeenCalled()
    delete (window as any).pywebview
  })

  it('API 超时未就绪提示错误', async () => {
    const { wrapper, store } = await mountSelector()
    const notifySpy = vi.spyOn(store, 'showNotification')

    await wrapper.find('.btn-browse').trigger('click')
    // 组件内部最多等待 API 3 秒
    await new Promise(r => setTimeout(r, 3300))
    await flushPromises()

    expect(notifySpy).toHaveBeenCalledWith('API 未初始化', 'error')
  })
})
