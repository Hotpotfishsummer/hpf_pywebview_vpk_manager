<template>
  <div class="directory-selector">
    <div class="input-group">
      <div class="input-wrapper">
        <span class="folder-icon">📁</span>
        <input
          id="directory-path"
          v-model="store.currentDirectory"
          type="text"
          :placeholder="$t('enterFolderPath')"
          readonly
          class="input-field"
        />
      </div>
      <div class="button-group">
        <button 
          @click="handleImport"
          :disabled="!store.currentDirectory || store.isImporting"
          class="btn btn-import"
          :class="{ 'btn-loading': store.isImporting }"
          :title="!store.currentDirectory ? $t('needSelectL4d2') : $t('importFiles')"
        >
          <span v-if="store.isImporting" class="btn-spinner"></span>
          <span class="btn-text">{{ store.isImporting ? $t('importing') : $t('importFiles') }}</span>
        </button>
        <button 
          @click="handleBrowse" 
          :disabled="isLoading"
          class="btn btn-browse"
          :class="{ 'btn-loading': isLoading }"
          :title="isLoading ? $t('browsing') : $t('browseFolder')"
        >
          <span v-if="isLoading" class="btn-spinner"></span>
          <span class="btn-text">{{ isLoading ? $t('browsing') : $t('browseFolder') }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'
import { ref } from 'vue'

const { t: $t } = useI18n()

const store = useVpkManagerStore()
const isLoading = ref(false)

async function handleImport() {
  if (store.isImporting || !store.currentDirectory) return
  
  try {
    const result = await store.importVpks()
    if (result) {
      if ((result.imported_count ?? 0) > 0) {
        const type = result.success ? 'success' : 'info'
        const msg = result.success 
          ? $t('importSuccess', { count: result.imported_count }) 
          : $t('importDonePartial', { success: result.imported_count, failed: result.errors ? result.errors.length : 0 })
        store.showNotification(msg, type)
      } else if (result.error) {
        store.showNotification($t('importFailedWithError', { error: result.error }), 'error')
      }
    }
  } catch (error) {
    console.error('导入失败:', error)
  }
}

async function handleBrowse() {
  if (isLoading.value) return
  
  try {
    isLoading.value = true
    
    // 等待 API 就绪（最多等待 3 秒）
    let waited = 0
    while (!(window.pywebview && window.pywebview.api) && waited < 3000) {
      await new Promise(resolve => setTimeout(resolve, 100))
      waited += 100
    }
    
    if (!(window.pywebview && window.pywebview.api)) {
      store.showNotification($t('apiNotInitialized'), 'error')
      return
    }
    
    const selectedPath = await window.pywebview.api.browse_directory()
    
    if (selectedPath) {
      await store.scanVpks(selectedPath)
    }
  } catch (error) {
    store.showNotification($t('browseError', { error: error instanceof Error ? error.message : String(error) }), 'error')
    console.error('选择文件夹失败:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.directory-selector {
  background: rgba(30, 41, 59, 0.5);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.input-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.folder-icon {
  position: absolute;
  left: 12px;
  font-size: 16px;
  opacity: 0.7;
}

.input-field {
  width: 100%;
  padding: 8px 14px 8px 38px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 6px;
  font-size: 13px;
  background-color: rgba(15, 23, 42, 0.4);
  color: #e2e8f0;
  transition: all 0.3s ease;
  font-weight: 500;
  cursor: default;
}

.input-field:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.5);
}

.button-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-import {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.btn-import:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-browse {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.btn-browse:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-loading {
  opacity: 0.8;
  cursor: wait;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
