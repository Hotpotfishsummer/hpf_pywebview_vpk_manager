import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import SettingsModal from '@/components/SettingsModal.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      settingsTitle: '设置', generalSettings: '通用', resetAppData: '重置数据',
      resetAppDataDesc: '重置说明', resetting: '清理中', executeNow: '执行',
      sftpSettings: 'SFTP', sftpHelp: '帮助', sftpAddress: '地址', sftpUsername: '用户名',
      sftpPassword: '密码', sftpAddonsPath: '远程路径', close: '关闭', resetConfirm: '确认重置?',
    },
  },
})

async function mountModal() {
  setActivePinia(createPinia())
  const wrapper = mount(SettingsModal, {
    props: { show: true },
    global: { plugins: [i18n] },
  })
  return wrapper
}

describe('SettingsModal 组件', () => {
  beforeEach(() => {
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  it('show=false 时不渲染', () => {
    setActivePinia(createPinia())
    const wrapper = mount(SettingsModal, {
      props: { show: false },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.settings-modal').exists()).toBe(false)
  })

  it('重置按钮成功后复位为可点击(i18n 文案)', async () => {
    const wrapper = await mountModal()
    const api = {
      reset_app_data: vi.fn(async () => true),
    }
    // 在 jsdom 的 window 上挂 pywebview(不能整体覆盖,否则 DOM 事件构造器丢失)
    ;(window as any).pywebview = { api }

    const btn = wrapper.find('.action-item .btn')
    expect(btn.text()).toBe('执行')
    await btn.trigger('click')
    await flushPromises()

    expect(api.reset_app_data).toHaveBeenCalled()
    expect(btn.text()).toBe('执行') // isResetting 已复位,不再是"清理中"
    delete (window as any).pywebview
  })

  it('关闭按钮触发 update:show', async () => {
    const wrapper = await mountModal()
    await wrapper.find('.modal-close').trigger('click')
    expect(wrapper.emitted('update:show')?.[0]).toEqual([false])
  })
})
