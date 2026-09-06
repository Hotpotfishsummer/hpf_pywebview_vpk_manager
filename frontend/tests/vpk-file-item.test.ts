import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import VpkFileItem from '@/components/VpkFileItem.vue'
import type { VpkFile } from '@/stores/vpk-manager'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: { viewInWorkshop: '查看', openWorkshopPage: '打开创意工坊' },
  },
})

function makeVpk(overrides: Partial<VpkFile> = {}): VpkFile {
  return {
    name: '12345678.vpk',
    path: '/a/12345678.vpk',
    size: 2 * 1024 * 1024,
    modified_time: 0,
    is_valid: true,
    is_disabled: false,
    display_name: 'My Mod',
    ...overrides,
  }
}

function mountItem(vpk: VpkFile, selected = false) {
  return mount(VpkFileItem, { props: { vpk, isSelected: selected }, global: { plugins: [i18n] } })
}

describe('VpkFileItem 组件', () => {
  it('显示 display_name 与格式化大小', () => {
    const wrapper = mountItem(makeVpk())
    expect(wrapper.find('.file-name').text()).toBe('My Mod')
    expect(wrapper.find('.file-details').text()).toContain('2.00 MB')
  })

  it('有工坊 ID 时显示工坊按钮,点击打开外链', async () => {
    ;(window as any).pywebview = { api: { open_external_url: vi.fn(async () => undefined) } }
    const wrapper = mountItem(makeVpk())
    const btn = wrapper.find('.workshop-btn')
    expect(btn.exists()).toBe(true)

    await btn.trigger('click')
    expect((window as any).pywebview.api.open_external_url).toHaveBeenCalledWith(
      'https://steamcommunity.com/sharedfiles/filedetails/?id=12345678'
    )
    delete (window as any).pywebview
  })

  it('无工坊 ID 时不显示工坊按钮', () => {
    const wrapper = mountItem(makeVpk({ name: 'nomod.vpk', path: '/a/nomod.vpk' }))
    expect(wrapper.find('.workshop-btn').exists()).toBe(false)
  })

  it('禁用文件带 is-disabled 类', () => {
    const wrapper = mountItem(makeVpk({ is_disabled: true, name: 'x.vpk.disabled', path: '/a/x.vpk.disabled' }))
    expect(wrapper.find('.vpk-file-item').classes()).toContain('is-disabled')
  })

  it('选中态透传到复选框', () => {
    const wrapper = mountItem(makeVpk(), true)
    expect((wrapper.find('input[type="checkbox"]').element as HTMLInputElement).checked).toBe(true)
  })

  it('勾选变化触发 toggle 事件', async () => {
    const wrapper = mountItem(makeVpk())
    await wrapper.find('input[type="checkbox"]').setValue(true)
    expect(wrapper.emitted('toggle')).toHaveLength(1)
  })
})
