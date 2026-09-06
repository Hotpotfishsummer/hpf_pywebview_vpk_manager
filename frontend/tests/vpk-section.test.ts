import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import VpkSection from '@/components/VpkSection.vue'
import type { VpkFile } from '@/stores/vpk-manager'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      deselectAll: '取消全选',
      selectAll: '全选',
      openInFileManager: '打开目录',
    },
  },
})

function makeVpk(path: string): VpkFile {
  return {
    name: path.split('/').pop() ?? path,
    path,
    size: 1,
    modified_time: 0,
    is_valid: true,
    is_disabled: false,
    display_name: path,
  }
}

function mountSection(files: VpkFile[], selected: Set<string>) {
  return mount(VpkSection, {
    props: {
      title: '本地 VPK',
      subtitle: '副标题',
      emptyText: '没有文件',
      files,
      selectedSet: selected,
    },
    global: { plugins: [i18n] },
  })
}

describe('VpkSection 组件', () => {
  it('空列表显示空文案,不渲染列表', () => {
    const wrapper = mountSection([], new Set())
    expect(wrapper.text()).toContain('没有文件')
    expect(wrapper.find('.file-list').exists()).toBe(false)
  })

  it('标题带文件数量', () => {
    const wrapper = mountSection([makeVpk('/a/1.vpk')], new Set())
    expect(wrapper.find('.section-title').text()).toContain('本地 VPK (1)')
  })

  it('点击表头切换折叠', async () => {
    const wrapper = mountSection([makeVpk('/a/1.vpk')], new Set())
    expect(wrapper.find('.file-list').exists()).toBe(true)
    await wrapper.find('.section-header').trigger('click')
    expect(wrapper.find('.file-list').exists()).toBe(false)
  })

  it('全选勾选后触发 select-all 取消触发 deselect-all', async () => {
    const files = [makeVpk('/a/1.vpk'), makeVpk('/a/2.vpk')]
    const wrapper = mountSection(files, new Set())

    await wrapper.find('.checkbox-label input').setValue(true)
    expect(wrapper.emitted('select-all')).toHaveLength(1)

    const selected = new Set(['/a/1.vpk', '/a/2.vpk'])
    await wrapper.setProps({ selectedSet: selected })
    await wrapper.find('.checkbox-label input').setValue(false)
    expect(wrapper.emitted('deselect-all')).toHaveLength(1)
  })

  it('文件行 toggle 事件携带路径', async () => {
    const files = [makeVpk('/a/1.vpk')]
    const wrapper = mountSection(files, new Set())

    await wrapper.findComponent({ name: 'VpkFileItem' }).vm.$emit('toggle')

    expect(wrapper.emitted('toggle-select')?.[0]).toEqual(['/a/1.vpk'])
  })
})
