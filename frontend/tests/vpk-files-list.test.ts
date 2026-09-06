import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import VpkFilesList from '@/components/VpkFilesList.vue'
import type { VpkFile } from '@/stores/vpk-manager'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      localVpkFiles: '本地 VPK 文件', localVpkFilesSubtitle: '本地',
      workshopFiles: '创意工坊文件', workshopFilesSubtitle: '工坊',
      noLocalVpkFiles: '无本地文件', noWorkshopFiles: '无工坊文件',
      selectAll: '全选', deselectAll: '取消全选', openInFileManager: '打开',
    },
  },
})

function makeVpk(path: string): VpkFile {
  return {
    name: path.split('/').pop() ?? path, path, size: 1, modified_time: 0,
    is_valid: true, is_disabled: false, display_name: path,
  }
}

function mountList() {
  setActivePinia(createPinia())
  const wrapper = mount(VpkFilesList, { global: { plugins: [i18n] } })
  return { wrapper }
}

describe('VpkFilesList 组件', () => {
  it('两区块标题与空文案', () => {
    const { wrapper } = mountList()
    const titles = wrapper.findAll('.section-title').map(t => t.text())
    expect(titles[0]).toContain('本地 VPK 文件 (0)')
    expect(titles[1]).toContain('创意工坊文件 (0)')
    expect(wrapper.text()).toContain('无本地文件')
  })

  it('本地列表项 toggle 委托到 store', async () => {
    const { wrapper } = mountList()
    const { useVpkManagerStore } = await import('@/stores/vpk-manager')
    const store = useVpkManagerStore()
    store.localVpkFiles.push(makeVpk('/a/mod.vpk'))
    await wrapper.vm.$nextTick()

    await wrapper.findAllComponents({ name: 'VpkFileItem' })[0].vm.$emit('toggle')

    expect(store.selectedLocalVpks.has('/a/mod.vpk')).toBe(true)
  })

  it('打开目录按钮委托 store', async () => {
    setActivePinia(createPinia())
    const { useVpkManagerStore } = await import('@/stores/vpk-manager')
    const store = useVpkManagerStore()
    store.localVpkFiles.push(makeVpk('/a/mod.vpk'))
    const spy = vi.spyOn(store, 'openAddonsFolder').mockResolvedValue()
    // spy 必须在挂载前创建,组件渲染时绑定的是当时的 action 引用
    const wrapper = mount(VpkFilesList, { global: { plugins: [i18n] } })
    await wrapper.vm.$nextTick()

    await wrapper.find('.action-icon-btn').trigger('click')

    expect(spy).toHaveBeenCalled()
  })
})
