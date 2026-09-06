import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import ActionBar from '@/components/ActionBar.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      exportFiles: '导出', exporting: '导出中', localize: '本地化', converting: '转换中',
      uploadToSftp: '上传', uploading: '上传中', disable: '禁用', enable: '启用',
      hardDelete: '删除', deleting: '删除中', processing: '处理中',
      selectFiles: '请先选择文件', selectionInfo: '已选 {count} 项',
      betterNaming: '更好的命名', betterNamingHelp: '?', packingFiles: '打包中',
      confirmHardDelete: '确认删除',
    },
  },
})

function makeVpk(path: string) {
  return {
    name: path.split('/').pop(), path, size: 1, modified_time: 0,
    is_valid: true, is_disabled: false, display_name: path,
  }
}

async function mountBar(selected: string[] = []) {
  setActivePinia(createPinia())
  const { useVpkManagerStore } = await import('@/stores/vpk-manager')
  const store = useVpkManagerStore()
  store.localVpkFiles.push(makeVpk('/a/1.vpk'), makeVpk('/a/2.vpk'))
  for (const p of selected) store.selectedLocalVpks.add(p)
  const wrapper = mount(ActionBar, { global: { plugins: [i18n] } })
  return { wrapper, store }
}

describe('ActionBar 组件', () => {
  beforeEach(() => {
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  it('未选择时显示选择计数为 0,仍渲染操作按钮', async () => {
    const { wrapper } = await mountBar([])
    expect(wrapper.find('.selection-info').text()).toContain('已选 0 项')
    expect(wrapper.find('.btn-export').exists()).toBe(true)
  })

  it('handleDelete 在 confirm=true 时调用 deleteVpks(false)', async () => {
    const { wrapper, store } = await mountBar(['/a/1.vpk'])
    const spy = vi.spyOn(store, 'deleteVpks').mockResolvedValue(undefined)

    await wrapper.find('.btn-delete').trigger('click')
    await flushPromises()

    expect(confirm).toHaveBeenCalled()
    expect(spy).toHaveBeenCalledWith(false)
  })

  it('handleDisable 只处理未禁用文件', async () => {
    const { wrapper, store } = await mountBar(['/a/1.vpk', '/a/2.vpk'])
    const spy = vi.spyOn(store, 'deleteVpks').mockResolvedValue(undefined)

    await wrapper.find('.btn-disable').trigger('click')
    await flushPromises()

    expect(spy).toHaveBeenCalledWith(true, ['/a/1.vpk', '/a/2.vpk'])
  })

  it('handleEnable 只处理已禁用文件', async () => {
    const { wrapper, store } = await mountBar([])
    store.selectedLocalVpks.add('/a/1.vpk.disabled')
    store.selectedLocalVpks.add('/a/2.vpk')
    const spy = vi.spyOn(store, 'deleteVpks').mockResolvedValue(undefined)

    await wrapper.find('.btn-enable').trigger('click')
    await flushPromises()

    expect(spy).toHaveBeenCalledWith(true, ['/a/1.vpk.disabled'])
  })
})
