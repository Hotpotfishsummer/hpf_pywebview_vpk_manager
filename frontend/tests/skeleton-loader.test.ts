import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SkeletonLoader from '@/components/SkeletonLoader.vue'

describe('SkeletonLoader 组件', () => {
  it('默认渲染 4 个骨架行', () => {
    const wrapper = mount(SkeletonLoader)
    expect(wrapper.findAll('.skeleton-item')).toHaveLength(4)
  })

  it('itemCount 控制行数', () => {
    const wrapper = mount(SkeletonLoader, { props: { itemCount: 2 } })
    expect(wrapper.findAll('.skeleton-item')).toHaveLength(2)
  })

  it('包含操作栏骨架(全选行)', () => {
    const wrapper = mount(SkeletonLoader)
    expect(wrapper.find('.skeleton-actions').exists()).toBe(true)
  })

  it('每行含缩略图与信息占位', () => {
    const wrapper = mount(SkeletonLoader, { props: { itemCount: 1 } })
    expect(wrapper.find('.skeleton-thumb').exists()).toBe(true)
    expect(wrapper.find('.skeleton-name').exists()).toBe(true)
    expect(wrapper.find('.skeleton-detail').exists()).toBe(true)
  })
})