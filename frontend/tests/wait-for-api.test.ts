import { describe, it, expect, vi } from 'vitest'
import { usePyWebViewApi } from '@/composables/useApi'

describe('waitForApiReady', () => {
  it('pywebviewready 事件触发就绪', async () => {
    vi.useFakeTimers()
    delete (globalThis as any).window
    ;(globalThis as any).window = {
      addEventListener: (ev: string, cb: () => void) => {
        setTimeout(cb, 100)
      },
      removeEventListener: () => {},
    }
    const { waitForApiReady } = usePyWebViewApi()

    const promise = waitForApiReady(3000)
    vi.advanceTimersByTime(200)
    await expect(promise).resolves.toBe(true)
    vi.useRealTimers()
  })

  it('超时未就绪返回 false 并移除监听', async () => {
    vi.useFakeTimers()
    const removed: string[] = []
    ;(globalThis as any).window = {
      addEventListener: () => {},
      removeEventListener: (ev: string) => removed.push(ev),
    }
    const { waitForApiReady } = usePyWebViewApi()

    const promise = waitForApiReady(1000)
    vi.advanceTimersByTime(1500)
    await expect(promise).resolves.toBe(false)
    expect(removed).toContain('pywebviewready')
    vi.useRealTimers()
  })
})
