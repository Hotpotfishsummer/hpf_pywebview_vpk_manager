import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { getApi, callApi } from '@/composables/useApi'

describe('useApi', () => {
  afterEach(() => {
    // 清理全局 window 模拟
    delete (globalThis as any).window
  })

  it('getApi 未就绪时抛错', () => {
    ;(globalThis as any).window = {}
    expect(() => getApi()).toThrow('PyWebView API not ready')
  })

  it('getApi 就绪时返回 api', () => {
    const api = { open_directory: async () => true }
    ;(globalThis as any).window = { pywebview: { api } }
    expect(getApi()).toBe(api)
  })

  it('callApi 成功时返回结果', async () => {
    const api = { open_directory: async (p: string) => p === 'ok' }
    ;(globalThis as any).window = { pywebview: { api } }

    await expect(callApi(a => a.open_directory('ok'), false)).resolves.toBe(true)
  })

  it('callApi 调用异常时回退默认值', async () => {
    const api = { open_directory: async () => { throw new Error('boom') } }
    ;(globalThis as any).window = { pywebview: { api } }

    await expect(callApi(a => a.open_directory('x'), false)).resolves.toBe(false)
  })

  it('callApi 在 API 未就绪时回退默认值', async () => {
    ;(globalThis as any).window = {}

    await expect(callApi(a => a.open_directory('x'), 'fallback')).resolves.toBe('fallback')
  })
})
