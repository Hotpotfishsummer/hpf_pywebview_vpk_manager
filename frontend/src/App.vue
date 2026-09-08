<template>
  <div id="app" class="app-container">
    <!-- Header -->
    <AppHeader :collapsed="isScrolled" @open-settings="showSettings = true" />

    <SettingsModal v-model:show="showSettings" />

    <ConfirmDialog />

    <!-- Error/Success banner -->
    <transition name="slide-down">
      <StatusBanner v-if="store.notification.message" />
    </transition>

    <!-- Fixed Action Section (Shows when files are selected) -->
    <transition name="slide-down">
      <ActionBar v-if="hasSelection" />
    </transition>

    <!-- Main content -->
    <main class="app-main" :class="{ 'split-view': store.isSftpActive }" @scroll="handleScroll">
      <div class="main-wrapper left-panel">
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
            <h2>{{ $t("noVpkFilesHeading") }}</h2>
            <p>{{ $t("selectDirWithVpks") }}</p>
          </div>
        </section>

        <!-- Footer Moved Inside -->
        <footer class="app-footer">
          <p class="footer-text">© 2026 L4D2 VPK Manager • Powered by Vue3 + PyWebView</p>
        </footer>
      </div>

      <div v-if="store.isSftpActive" class="right-panel">
        <SftpBrowser />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'
import { usePyWebViewApi } from '@/composables/useApi'
import AppHeader from '@/components/AppHeader.vue'
import StatusBanner from '@/components/StatusBanner.vue'
import ActionBar from '@/components/ActionBar.vue'
import DirectorySelector from '@/components/DirectorySelector.vue'
import VpkFilesList from '@/components/VpkFilesList.vue'
import SettingsModal from '@/components/SettingsModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import SftpBrowser from '@/components/SftpBrowser.vue'

const store = useVpkManagerStore()
const { t: $t } = useI18n()
const { waitForApiReady } = usePyWebViewApi()

const isScrolled = ref(false)
const showSettings = ref(false)

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

/* Main content */
.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
}

.app-main.split-view {
  overflow: hidden; /* 在分屏模式下由子面板处理滚动 */
}

.left-panel {
  flex: 1;
  overflow-y: auto;
  min-width: 0; /* 防止 flex 子项超出容器 */
}

.right-panel {
  width: 400px;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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

.split-view .main-wrapper {
  max-width: none;
  margin: 0;
}

/* Sections */
.directory-section {
  margin-bottom: 24px;
}

.files-section {
  flex: 1;
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

/* Fade Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

</style>
