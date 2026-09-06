import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import AppHeader from '@/components/AppHeader.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: {
      appTitle: 'L4D2 VPK 管理器',
      sftpEnable: '启用 SFTP',
      sftpDisable: '禁用 SFTP',
      settings: '设置',
    },
  },
})

function mountHeader(collapsed = false) {
  setActivePinia(createPinia())
  return mount(AppHeader, {
    props: { collapsed },
    global: { plugins: [i18n] },
  })
}

describe('AppHeader 组件', () => {
  it('collapsed 时根元素带 collapsed 类', () => {
    expect(mountHeader(true).find('header').classes()).toContain('collapsed')
    expect(mountHeader(false).find('header').classes()).not.toContain('collapsed')
  })

  it('设置按钮触发 open-settings', async () => {
    const wrapper = mountHeader()
    await wrapper.find('.settings-btn').trigger('click')
    expect(wrapper.emitted('open-settings')).toHaveLength(1)
  })

  it('SFTP 开关切换 store 状态', async () => {
    const wrapper = mountHeader()
    const { useVpkManagerStore } = await import('@/stores/vpk-manager')
    const store = useVpkManagerStore()
    expect(store.isSftpActive).toBe(false)

    await wrapper.find('.sftp-toggle-btn').trigger('click')
    expect(store.isSftpActive).toBe(true)
    expect(wrapper.find('.sftp-toggle-btn').classes()).toContain('active')
  })

  it('语言切换更新 locale', async () => {
    const wrapper = mountHeader()
    const { locale } = i18n.global
    await wrapper.findAll('.lang-btn')[0].trigger('click')
    expect(locale.value).toBe('en')
    await wrapper.findAll('.lang-btn')[1].trigger('click')
    expect(locale.value).toBe('zh')
  })
})
