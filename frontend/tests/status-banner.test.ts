import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import StatusBanner from '@/components/StatusBanner.vue'

function mountBanner() {
  setActivePinia(createPinia())
  return mount(StatusBanner, {
    global: { plugins: [] },
  })
}

describe('StatusBanner 组件', () => {
  it('错误通知显示警告图标且不可自动关闭(手动点 × 清除)', async () => {
    const wrapper = mountBanner()
    const { useVpkManagerStore } = await import('@/stores/vpk-manager')
    const s = useVpkManagerStore()
    s.showNotification('出错了', 'error')
    await nextTick()

    expect(wrapper.text()).toContain('出错了')
    expect(wrapper.find('.status-icon').text()).toContain('⚠️')

    await wrapper.find('.status-close').trigger('click')
    await nextTick()
    expect(s.notification.message).toBe('')
  })
})
