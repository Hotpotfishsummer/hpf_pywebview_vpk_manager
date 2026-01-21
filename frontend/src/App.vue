<template>
  <div id="app" class="app-container">
    <!-- Header -->
    <header class="app-header" :class="{ 'collapsed': isScrolled }">
      <div class="header-content">
        <div class="header-left">
          <h1 class="app-title">
            <span class="title-icon">🎮</span>
            {{ $t('appTitle') }}
          </h1>
          <p class="app-subtitle">Left 4 Dead 2 VPK Manager</p>
        </div>
        <div class="header-right">
          <div class="language-switcher">
            <button 
              @click="switchLanguage('en')" 
              :class="{ active: currentLocale === 'en' }"
              class="lang-btn"
            >
              EN
            </button>
            <button 
              @click="switchLanguage('zh')" 
              :class="{ active: currentLocale === 'zh' }"
              class="lang-btn"
            >
              中文
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Error banner -->
    <transition name="slide-down">
      <div v-if="store.errorMessage" class="error-banner">
        <div class="error-content">
          <span class="error-icon">⚠️</span>
          <span class="error-text">{{ store.errorMessage }}</span>
          <button @click="store.errorMessage = ''" class="error-close">×</button>
        </div>
      </div>
    </transition>

    <!-- Fixed Action Section (Shows when files are selected) -->
    <transition name="slide-down">
      <div v-if="hasSelection" class="fixed-top-section">
        <div class="main-wrapper action-bar">
          <div class="action-buttons">
            <button 
              @click="handleExport"
              :disabled="store.isExporting"
              class="btn btn-export"
              :class="{ 'btn-loading': store.isExporting }"
            >
              <span class="btn-icon" v-if="!store.isExporting">⬇️</span>
              <span class="btn-spinner" v-else></span>
              {{ store.isExporting ? $t('exporting') : '导出文件' }}
            </button>
            <button 
              @click="handleDelete"
              :disabled="store.isDeleting"
              class="btn btn-delete"
            >
              <span class="btn-icon">🗑️</span>
              {{ store.isDeleting ? '删除中...' : '删除文件' }}
            </button>

            <!-- Better Naming Checkbox -->
            <label class="better-naming-checkbox">
              <input type="checkbox" v-model="store.useBetterNaming" />
              <span class="checkbox-text">更好的命名</span>
              <span class="checkbox-help" title="在压缩包内将 VPK 和图片重命名为游戏内显示的名称，并去除空格">❓</span>
            </label>

            <span class="selection-info">
              {{ selectionCountText }}
            </span>
          </div>

          <!-- Export progress indicator -->
          <div v-if="store.isExporting" class="export-progress">
            <div class="progress-bar">
              <div class="progress-fill"></div>
            </div>
            <span class="progress-text">正在打包文件...</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- Main content -->
    <main class="app-main" @scroll="handleScroll">
      <div class="main-wrapper">
        <!-- Directory selector section -->
        <section class="directory-section">
          <DirectorySelector />
        </section>

        <!-- Loading state -->
        <div v-if="store.isScanning" class="loading-state">
          <div class="spinner"></div>
          <p class="loading-text">{{ $t('loading') }}</p>
        </div>

        <!-- Files found -->
        <template v-else-if="hasAnyFiles">
          <!-- File lists section -->
          <section class="files-section">
            <VpkFilesList />
          </section>
        </template>

        <!-- Empty state -->
        <section v-else class="empty-state">
          <div class="empty-content">
            <span class="empty-icon">📁</span>
            <h2>未找到 VPK 文件</h2>
            <p>请选择包含 VPK 文件的目录</p>
          </div>
        </section>
      </div>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <p class="footer-text">© 2026 L4D2 VPK Manager • Powered by Vue3 + PyWebView</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'
import { usePyWebViewApi } from '@/composables/useApi'
import DirectorySelector from '@/components/DirectorySelector.vue'
import VpkFilesList from '@/components/VpkFilesList.vue'

const store = useVpkManagerStore()
const { locale, t: $t } = useI18n()
const { waitForApiReady } = usePyWebViewApi()

const currentLocale = computed(() => locale.value)
const isScrolled = ref(false)

// Handle scroll for layout changes
function handleScroll(event: Event) {
  const target = event.target as HTMLElement
  isScrolled.value = target.scrollTop > 20
}

// Initialize store on mount
onMounted(async () => {
  console.log('App mounted, waiting for API...')
  const ready = await waitForApiReady(5000)
  if (ready) {
    console.log('API ready, initializing store...')
    await store.initialize()
  } else {
    console.error('API failed to initialize within timeout')
  }
})

const hasSelection = computed(() => {
  return store.selectedLocalVpks.size > 0 || store.selectedWorkshopVpks.size > 0
})

const hasAnyFiles = computed(() => {
  return store.localVpkFiles.length > 0 || store.workshopVpkFiles.length > 0
})

const selectionCount = computed(() => {
  return store.selectedLocalVpks.size + store.selectedWorkshopVpks.size
})

const selectionCountText = computed(() => {
  const count = selectionCount.value
  return `已选择 ${count} 项`
})

async function handleExport() {
  try {
    if (store.selectedLocalVpks.size === 0 && store.selectedWorkshopVpks.size === 0) {
      store.errorMessage = $t('selectFiles')
      return
    }

    if (!window.pywebview || !window.pywebview.api) {
      store.errorMessage = $t('apiNotAvailable')
      return
    }

    // Get downloads directory from backend
    let outputDir = ''
    try {
      const result = await window.pywebview.api.get_downloads_directory()
      outputDir = result || ''
    } catch (error) {
      console.warn('Failed to get downloads directory, using current directory')
      outputDir = '.'
    }

    const result = await store.exportVpks(outputDir)
    if (result && result.success) {
      store.errorMessage = $t('exportSuccess', { path: result.file_path || outputDir })
    }
  } catch (error) {
    store.errorMessage = error instanceof Error ? error.message : $t('exportError')
  }
}

function handleDelete() {
  const selectedCount = selectionCount.value
  if (selectedCount === 0) {
    store.errorMessage = $t('selectFiles')
    return
  }

  const message = $t('confirmDelete') + ` (${selectedCount})`
  if (confirm(message)) {
    store.deleteVpks(true)
  }
}

function switchLanguage(lang: string) {
  locale.value = lang
}
</script>

<style scoped>
/* Layout */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #0a0e27 0%, #151d38 50%, #1a2847 100%);
  color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  overflow: hidden;
}

/* Header */
.app-header {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: white;
  padding: 20px 24px;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.25);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
  position: relative;
}

.app-header.collapsed {
  padding: 4px 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-left {
  flex: 1;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 12px;
  letter-spacing: -0.5px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-header.collapsed .app-title {
  font-size: 16px;
  gap: 8px;
}

.title-icon {
  font-size: 32px;
  line-height: 1;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-header.collapsed .title-icon {
  font-size: 20px;
}

.app-subtitle {
  margin: 4px 0 0 44px;
  font-size: 13px;
  opacity: 0.85;
  letter-spacing: 0.5px;
  font-weight: 500;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 20px;
  overflow: hidden;
}

.app-header.collapsed .app-subtitle {
  max-height: 0;
  margin-top: 0;
  opacity: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* Fixed top section */
.fixed-top-section {
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  z-index: 90;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.action-bar {
  padding-top: 10px;
  padding-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.selection-info {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 600;
  margin-left: auto;
  background: rgba(255, 255, 255, 0.05);
  padding: 6px 14px;
  border-radius: 20px;
}

.better-naming-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  font-size: 13px;
  color: #cbd5e1;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.better-naming-checkbox:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(148, 163, 184, 0.2);
}

.better-naming-checkbox input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.checkbox-help {
  opacity: 0.6;
  font-size: 12px;
}

/* Language switcher */
.language-switcher {
  display: flex;
  gap: 6px;
  background: rgba(255, 255, 255, 0.12);
  padding: 6px;
  border-radius: 8px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.lang-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  border-radius: 6px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-header.collapsed .lang-btn {
  padding: 3px 8px;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.lang-btn.active {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Error banner */
.error-banner {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideDown 0.3s ease;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.error-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: white;
}

.error-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.error-text {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.error-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.error-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

/* Main content */
.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 60px;
}

.main-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  width: 100%;
}

/* Sections */
.directory-section {
  margin-bottom: 24px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-export {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.btn-export:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.35);
}

.btn-export:active:not(:disabled) {
  transform: translateY(-1px);
}

.btn-delete {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.btn-delete:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.35);
}

.btn-delete:active:not(:disabled) {
  transform: translateY(-1px);
}

.btn-icon {
  font-size: 18px;
}

.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.btn-loading {
  opacity: 0.9;
}

.selection-info {
  font-size: 13px;
  color: #cbd5e1;
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.export-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: rgba(148, 163, 184, 0.15);
  border-radius: 3px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
  animation: progress 1.5s ease-in-out infinite;
  border-radius: 3px;
}

.progress-text {
  font-size: 13px;
  color: #94a3b8;
  white-space: nowrap;
  font-weight: 500;
}

/* File lists */
.files-section {
  margin-top: 20px;
}

/* Loading state */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 20px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(148, 163, 184, 0.15);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}

.loading-text {
  font-size: 15px;
  color: #cbd5e1;
  margin: 0;
  font-weight: 500;
}

/* Empty state */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px 20px;
}

.empty-content {
  text-align: center;
  color: #64748b;
}

.empty-icon {
  font-size: 80px;
  display: block;
  margin-bottom: 24px;
  opacity: 0.6;
}

.empty-content h2 {
  margin: 0 0 10px 0;
  font-size: 20px;
  color: #cbd5e1;
  font-weight: 700;
}

.empty-content p {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}

/* Footer */
.app-footer {
  background: rgba(15, 23, 42, 0.6);
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  padding: 16px 24px;
  text-align: center;
  position: relative;
  backdrop-filter: blur(10px);
}

.footer-text {
  margin: 0;
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

/* Animations */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes progress {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

/* Responsive */
@media (max-width: 768px) {
  .app-title {
    font-size: 18px;
  }

  .app-subtitle {
    margin-left: 24px;
    font-size: 11px;
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }

  .selection-info {
    width: 100%;
    justify-content: center;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-right {
    align-self: flex-end;
  }
}
</style>
