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
          <button @click="showSettings = true" class="settings-btn" :title="$t('settings')">
            ⚙️
          </button>
        </div>
      </div>
    </header>

    <!-- Settings Modal -->
    <transition name="fade">
      <div v-if="showSettings" class="modal-overlay" @click.self="showSettings = false">
        <div class="modal-content settings-modal">
          <div class="modal-header">
            <h2 class="modal-title">⚙️ {{ $t('settingsTitle') }}</h2>
            <button class="modal-close" @click="showSettings = false">×</button>
          </div>
          <div class="modal-body">
            <div class="settings-section">
              <h3 class="section-subtitle">{{ $t('generalSettings') }}</h3>
              <div class="settings-item action-item">
                <div class="setting-text">
                  <span class="setting-title">{{ $t('resetAppData') }}</span>
                  <p class="setting-item-desc">{{ $t('resetAppDataDesc') }}</p>
                </div>
                <button 
                  class="btn btn-outline" 
                  @click="handleResetData"
                  :disabled="isResetting"
                >
                  {{ isResetting ? 'Cleaning...' : 'Execute' }}
                </button>
              </div>
            </div>
            <!-- Future settings can be added here -->
          </div>
          <div class="modal-footer">
            <button class="btn btn-primary" @click="showSettings = false">{{ $t('close') }}</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Error/Success banner -->
    <transition name="slide-down">
      <div v-if="store.notification.message" 
           :class="['status-banner', `status-${store.notification.type}`]">
        <div class="status-content">
          <span class="status-icon">
            {{ store.notification.type === 'success' ? '✅' : (store.notification.type === 'error' ? '⚠️' : 'ℹ️') }}
          </span>
          <span class="status-text">{{ store.notification.message }}</span>
          <button @click="store.notification.message = ''" class="status-close">×</button>
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
              v-if="store.selectedWorkshopVpks.size > 0 && store.selectedLocalVpks.size === 0"
              @click="handleLocalize"
              :disabled="store.isLocalizing"
              class="btn btn-localize"
              :class="{ 'btn-loading': store.isLocalizing }"
              :title="$t('localizeTooltip')"
            >
              <span class="btn-icon" v-if="!store.isLocalizing">📦</span>
              <span class="btn-spinner" v-else></span>
              {{ store.isLocalizing ? '正在转换...' : $t('localize') }}
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
              <span class="checkbox-text">{{ $t('betterNaming') }}</span>
              <span class="checkbox-help" :title="$t('betterNamingHelp')">❓</span>
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

        <!-- Footer Moved Inside -->
        <footer class="app-footer">
          <p class="footer-text">© 2026 L4D2 VPK Manager • Powered by Vue3 + PyWebView</p>
        </footer>
      </div>
    </main>
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
const showSettings = ref(false)
const isResetting = ref(false)

// Handle scroll for layout changes
function handleScroll(event: Event) {
  const target = event.target as HTMLElement
  isScrolled.value = target.scrollTop > 20
}

async function handleResetData() {
  if (confirm($t('resetConfirm'))) {
    try {
      isResetting.value = true
      await (window as any).pywebview.api.reset_app_data()
    } catch (error) {
      console.error('Reset failed:', error)
      isResetting.value = false
    }
  }
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
  return $t('selectionInfo', { count })
})

async function handleExport() {
  try {
    if (store.selectedLocalVpks.size === 0 && store.selectedWorkshopVpks.size === 0) {
      store.showNotification($t('selectFiles'), 'error')
      return
    }

    if (!window.pywebview || !window.pywebview.api) {
      store.showNotification($t('apiNotAvailable'), 'error')
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

    await store.exportVpks(outputDir)
  } catch (error) {
    store.showNotification(error instanceof Error ? error.message : $t('exportError'), 'error')
  }
}

async function handleLocalize() {
  try {
    await store.localizeVpks()
  } catch (error) {
    store.showNotification(error instanceof Error ? error.message : 'Localization failed', 'error')
  }
}

function handleDelete() {
  const selectedCount = selectionCount.value
  if (selectedCount === 0) {
    store.showNotification($t('selectFiles'), 'error')
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

.settings-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s ease;
  margin-left: 8px;
}

.settings-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(45deg);
}

.app-header.collapsed .settings-btn {
  width: 28px;
  height: 28px;
  font-size: 14px;
}

.lang-btn.active {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Status banner */
.status-banner {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideDown 0.3s ease;
  z-index: 1000;
}

.status-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.status-error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.status-info {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.status-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: white;
}

.status-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.status-text {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.status-close {
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

.status-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

/* Main content */
.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.main-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

/* Sections */
.directory-section {
  margin-bottom: 24px;
}

.files-section {
  flex: 1;
  margin-top: 20px;
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

.btn-localize {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
}

.btn-localize:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.35);
}

.btn-localize:active:not(:disabled) {
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
  margin-top: 40px;
  padding: 24px 0;
  text-align: center;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  width: 100%;
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
/* Modal Base */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background: #1e293b;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  animation: modalScale 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalScale {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
}

.modal-close {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.05);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  justify-content: flex-end;
}

/* Settings Specific */
.settings-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settings-item {
  padding: 12px;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.05);
}

.settings-item.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.setting-text {
  flex: 1;
}

.setting-title {
  color: #f1f5f9;
  font-weight: 600;
  font-size: 14px;
}

.setting-item-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #f1f5f9;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.setting-item-desc {
  margin: 6px 0 0 0;
  font-size: 12px;
  color: #94a3b8;
}

/* Fade Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

</style>
