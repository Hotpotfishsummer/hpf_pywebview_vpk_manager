<template>
  <div class="fixed-top-section">
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
          {{ store.isExporting ? $t('exporting') : $t('exportFiles') }}
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
          {{ store.isLocalizing ? $t('converting') : $t('localize') }}
        </button>
        <button
          v-if="store.isSftpActive && (store.selectedLocalVpks.size > 0 || store.selectedWorkshopVpks.size > 0)"
          @click="store.uploadLocalVpks"
          :disabled="store.isUploading"
          class="btn btn-upload"
          :class="{ 'btn-loading': store.isUploading }"
        >
          <span class="btn-icon" v-if="!store.isUploading">☁️</span>
          <span class="btn-spinner" v-else></span>
          {{ store.isUploading ? $t('uploading') : $t('uploadToSftp') }}
        </button>
        <button
          @click="handleDisable"
          :disabled="store.isDeleting"
          class="btn btn-disable"
        >
          <span class="btn-icon">🚫</span>
          {{ store.isDeleting ? $t('processing') : $t('disable') }}
        </button>
        <button
          @click="handleEnable"
          :disabled="store.isDeleting"
          class="btn btn-enable"
        >
          <span class="btn-icon">✔️</span>
          {{ store.isDeleting ? $t('processing') : $t('enable') }}
        </button>
        <button
          @click="handleDelete"
          :disabled="store.isDeleting"
          class="btn btn-delete"
        >
          <span class="btn-icon">🗑️</span>
          {{ store.isDeleting ? $t('deleting') : $t('hardDelete') }}
        </button>

        <!-- Better Naming Checkbox -->
        <label class="better-naming-checkbox">
          <input type="checkbox" v-model="store.useBetterNaming" />
          <span class="checkbox-text">{{ $t('betterNaming') }}</span>
          <span class="checkbox-help" :title="$t('betterNamingHelp')">❓</span>
        </label>

        <label class="better-naming-checkbox">
          <input type="checkbox" v-model="store.useAutoOpenExport" />
          <span class="checkbox-text">{{ $t('autoOpenExport') }}</span>
        </label>

        <span class="selection-info">
          {{ selectionCountText }}
        </span>
      </div>

      <!-- Export progress indicator -->
      <!-- Unified busy progress indicator -->
      <div v-if="isAnyBusy" class="export-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressWidth }"></div>
        </div>
        <span class="progress-text">{{ busyText }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'

const store = useVpkManagerStore()
const { t: $t } = useI18n()

const selectionCount = computed(() => {
  return store.selectedLocalVpks.size + store.selectedWorkshopVpks.size
})

const selectionCountText = computed(() => {
  return $t('selectionInfo', { count: selectionCount.value })
})

const isAnyBusy = computed(() => {
  return store.isExporting || store.isUploading || store.isDownloading ||
         store.isImporting || store.isLocalizing || store.isDeleting
})

const busyText = computed(() => {
  if (store.isExporting) return $t('packingFiles')
  if (store.isExporting) {
    const { stage, done, total } = store.exportProgress
    if (stage === 'compressing') return $t('compressingArchive')
    if (stage === 'copying' && total > 0) return `${$t('packingFiles')} (${done}/${total})`
    return $t('packingFiles')
  }
  if (store.isUploading) return $t('uploadingLocal')
  if (store.isDownloading) return $t('downloadingRemote')
  if (store.isImporting) return $t('importing')
  if (store.isLocalizing) return $t('converting')
  if (store.isDeleting) return $t('processing')
  return ''
})

const progressWidth = computed(() => {
  if (store.isExporting && store.exportProgress.total > 0) {
    const pct = Math.round((store.exportProgress.done / store.exportProgress.total) * 100)
    return `${pct}%`
  }
  return '100%' // 非导出操作保持装饰性动画
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

    const result = await store.exportVpks(outputDir)
    if (result && result.exists) {
      // 目标归档已存在，询问是否覆盖
      if (await store.showConfirm($t('confirmOverwriteExport'))) {
        await store.exportVpks(outputDir, true)
      }
    }
  } catch (error) {
    store.showNotification(error instanceof Error ? error.message : $t('exportError'), 'error')
  }
}

async function handleLocalize() {
  try {
    await store.localizeVpks()
  } catch (error) {
    store.showNotification(error instanceof Error ? error.message : $t('localizeFailed'), 'error')
  }
}

async function handleDisable() {
  if (selectionCount.value === 0) return
  const pathsToDisable = [...store.selectedLocalVpks, ...store.selectedWorkshopVpks]
    .filter(path => !path.endsWith('.disabled'))

  if (pathsToDisable.length > 0) {
    await store.deleteVpks(true, pathsToDisable)
  }
}

async function handleEnable() {
  if (selectionCount.value === 0) return
  const pathsToEnable = [...store.selectedLocalVpks, ...store.selectedWorkshopVpks]
    .filter(path => path.endsWith('.disabled'))

  if (pathsToEnable.length > 0) {
    await store.deleteVpks(true, pathsToEnable)
  }
}

async function handleDelete() {
  const selectedCount = selectionCount.value
  if (selectedCount === 0) {
    store.showNotification($t('selectFiles'), 'error')
    return
  }

  const message = $t('confirmHardDelete') + ` (${selectedCount})`
  if (await store.showConfirm(message)) {
    await store.deleteVpks(false)
  }
}
</script>

<style scoped>
/* Fixed top section */
.fixed-top-section {
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  z-index: 90;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* 原 App.vue 中该元素同时挂 .main-wrapper;子组件不继承父级 scoped 样式,基础规则在此复制 */
.main-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.action-bar {
  padding-top: 10px;
  padding-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
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

.btn-upload {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.btn-upload:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8b5cf6;
}

.btn-delete {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.btn-disable {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.btn-enable {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.btn-delete:hover:not(:disabled),
.btn-disable:hover:not(:disabled),
.btn-enable:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.btn-delete:active:not(:disabled),
.btn-disable:active:not(:disabled),
.btn-enable:active:not(:disabled) {
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

/* 原 App.vue 中 .selection-info 定义了两次,此处合并为一条(取后者覆盖后的最终样式) */
.selection-info {
  font-size: 13px;
  color: #cbd5e1;
  font-weight: 500;
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.05);
  padding: 0 12px;
  border-radius: 20px;
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

/* Animations */
@keyframes spin {
  to {
    transform: rotate(360deg);
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

/* Responsive */
@media (max-width: 768px) {
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
}
</style>
