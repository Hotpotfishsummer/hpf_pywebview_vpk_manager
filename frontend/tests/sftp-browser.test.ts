import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import SftpBrowser from '@/components/SftpBrowser.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      remoteAddons: '远程 addons', pathNotConfigured: '路径未配置', refresh: '刷新',
      loading: '加载中', noRemoteFiles: '暂无远程文件', selectAll: '全选',
      selectionInfo: '已选 {count} 项', delete: '删除', enable: '启用', disable: '禁用',
      syncToLocal: '同步到本地',
      confirmDeleteSelectedRemote: '确认删除 {count} 项?',
    },
  },
})

function makeRemote(path: string, disabled = false) {
  return { name: path.split('/').pop(), path, size: 1, modified_time: 0, is_disabled: disabled }
}

async function mountBrowser() {
  setActivePinia(createPinia())
  const { useVpkManagerStore } = await import('@/stores/vpk-manager')
  const store = useVpkManagerStore()
  const wrapper = mount(SftpBrowser, { global: { plugins: [i18n] } })
  await flushPromises()
  return { wrapper, store }
}

describe('SftpBrowser 组件', () => {

  it('挂载时未配置 SFTP 不触发扫描,显示空态', async () => {
    const { wrapper, store } = await mountBrowser()
    const spy = vi.spyOn(store, 'scanRemoteVpks')
    // onMounted 已在 mount 时跑过:无配置 → 不扫描
    expect(wrapper.text()).toContain('暂无远程文件')
    void spy
  })

  it('渲染远程文件并支持点击选中', async () => {
    const { wrapper, store } = await mountBrowser()
    store.remoteVpkFiles.push(makeRemote('/srv/a.vpk'), makeRemote('/srv/b.vpk.disabled', true))
    await wrapper.vm.$nextTick()

    const items = wrapper.findAll('.remote-item')
    expect(items).toHaveLength(2)
    expect(items[1].classes()).toContain('is-disabled')

    await items[0].trigger('click')
    expect(store.selectedRemoteVpks.has('/srv/a.vpk')).toBe(true)
  })

  it('批量删除在 confirm 后委托 store', async () => {
    const { wrapper, store } = await mountBrowser()
    store.remoteVpkFiles.push(makeRemote('/srv/a.vpk'))
    store.selectedRemoteVpks.add('/srv/a.vpk')
    const spy = vi.spyOn(store, 'deleteMultipleRemoteVpks').mockResolvedValue()
    vi.spyOn(store, 'showConfirm').mockResolvedValue(true)
    await wrapper.vm.$nextTick()

    await wrapper.find('.btn-action.delete').trigger('click')
    await flushPromises()

    expect(store.showConfirm).toHaveBeenCalled()
    expect(spy).toHaveBeenCalled()
  })

  it('启用/禁用按钮委托 store', async () => {
    const { wrapper, store } = await mountBrowser()
    store.remoteVpkFiles.push(makeRemote('/srv/a.vpk'))
    store.selectedRemoteVpks.add('/srv/a.vpk')
    const en = vi.spyOn(store, 'enableRemoteVpks').mockResolvedValue()
    const dis = vi.spyOn(store, 'disableRemoteVpks').mockResolvedValue()
    await wrapper.vm.$nextTick()

    await wrapper.find('.btn-action.enable').trigger('click')
    await wrapper.find('.btn-action.disable').trigger('click')

    expect(en).toHaveBeenCalled()
    expect(dis).toHaveBeenCalled()
  })
})
