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
          @click="handleBrowse" 
          :disabled="isLoading"
          class="btn btn-browse"
          :class="{ 'btn-loading': isLoading }"
          :title="isLoading ? '浏览中...' : $t('browseFolder')"
        >
          <span v-if="isLoading" class="btn-spinner"></span>
          <span class="btn-text">{{ isLoading ? '浏览中...' : $t('browseFolder') }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { ref } from 'vue'

const store = useVpkManagerStore()
const isLoading = ref(false)

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
      store.errorMessage = 'PyWebView API 未初始化，请刷新页面'
      return
    }
    
    const selectedPath = await window.pywebview.api.browse_directory()
    
    if (selectedPath) {
      store.errorMessage = ''
      await store.scanVpks(selectedPath)
    }
  } catch (error) {
    store.errorMessage = `文件夹选择出错: ${error instanceof Error ? error.message : String(error)}`
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

.btn-browse {
  padding: 8px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-browse:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.1);
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
