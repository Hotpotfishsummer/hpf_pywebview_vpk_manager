<template>
  <div class="sftp-browser">
    <div class="browser-header">
      <div class="header-info">
        <h3>🌐 {{ $t('remoteAddons') }}</h3>
        <span class="path-badge" :title="store.sftpSettings.addons_path">
          {{ store.sftpSettings.addons_path || $t('pathNotConfigured') }}
        </span>
      </div>
      <button @click="store.scanRemoteVpks()" class="btn-refresh" :disabled="store.isRemoteScanning">
        <span :class="{ 'spinning': store.isRemoteScanning }">🔄</span>
        {{ store.isRemoteScanning ? $t('loading') : $t('refresh') }}
      </button>
      <button
        @click="handleRestartServer"
        class="btn-restart"
        :disabled="store.isRestartingServer"
        :title="$t('restartServerTooltip')"
      >
        <span :class="{ 'spinning': store.isRestartingServer }">{{ store.isRestartingServer ? '⏳' : '⚡' }}</span>
        {{ store.isRestartingServer ? $t('restartingServer') : $t('restartServer') }}
      </button>
      <input
        v-model="remoteSearchQuery"
        type="text"
        class="remote-search-input"
        :placeholder="$t('searchFilesPlaceholder')"
      >
      <div class="sort-controls">
        <button
          v-for="key in sortKeys"
          :key="key"
          class="sort-btn"
          :class="{ active: sortField === key }"
          @click="toggleSort(key)"
        >
          {{ $t(sortLabels[key]) }}
          <span v-if="sortField === key">{{ sortAsc ? '↑' : '↓' }}</span>
        </button>
      </div>
    </div>

    <div class="browser-content">
      <!-- 多选操作栏 -->
      <div v-if="store.remoteVpkFiles.length > 0" class="selection-actions">
        <div class="selection-info">
          <label class="checkbox-container">
            <input 
              type="checkbox" 
              :checked="isAllSelected" 
              @change="toggleSelectAll"
            >
            <span class="checkmark"></span>
          </label>
          <span class="count-text">
            {{ store.selectedRemoteVpks.size > 0 ? $t('selectionInfo', { count: store.selectedRemoteVpks.size }) : $t('selectAll') }}
          </span>
        </div>
        
        <div class="action-buttons" v-if="store.selectedRemoteVpks.size > 0">
          <button @click="store.downloadRemoteVpks" class="btn-action download" :title="$t('syncToLocal')" :disabled="store.isDownloading">
            {{ store.isDownloading ? '⏳' : '📥' }}
          </button>
          <button @click="handleBatchEnable" class="btn-action enable" :title="$t('enable')">
            ✔️
          </button>
          <button @click="handleBatchDisable" class="btn-action disable" :title="$t('disable')">
            🚫
          </button>
          <button @click="handleBatchDelete" class="btn-action delete" :title="$t('delete')">
            🗑️
          </button>
        </div>
      </div>

      <div v-if="store.isRemoteScanning" class="remote-loading">
        <div class="mini-spinner"></div>
      </div>
      
      <div v-else-if="store.remoteVpkFiles.length === 0" class="remote-empty">
        <div class="empty-msg">
          <span>📂</span>
          <p>{{ $t('noRemoteFiles') }}</p>
        </div>
      </div>

      <div v-else class="remote-list">
        <div
          v-for="file in sortedRemoteFiles"
          :key="file.path"
          class="remote-item"
          :class="{ 'is-disabled': file.is_disabled, 'is-selected': store.selectedRemoteVpks.has(file.path) }"
          role="button"
          tabindex="0"
          :aria-pressed="store.selectedRemoteVpks.has(file.path)"
          @click="store.toggleRemoteVpkSelection(file.path)"
          @keydown.enter.prevent="store.toggleRemoteVpkSelection(file.path)"
          @keydown.space.prevent="store.toggleRemoteVpkSelection(file.path)"
        >
          <div class="item-checkbox">
            <label class="checkbox-container" @click.stop>
              <input 
                type="checkbox" 
                :checked="store.selectedRemoteVpks.has(file.path)"
                @change="store.toggleRemoteVpkSelection(file.path)"
              >
              <span class="checkmark"></span>
            </label>
          </div>
          <div class="item-icon">{{ file.is_disabled ? '💤' : '📦' }}</div>
          <div class="item-details">
            <span class="item-name" :title="file.name">{{ file.name }}</span>
            <span class="item-meta">{{ file.size }} MB • {{ formatDate(file.modified_time) }}</span>
          </div>
          <div class="item-actions">
            <!-- 单个操作按钮（可选，有了多选可以简化） -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'
import type { RemoteFile } from '@/types/api'

type SortField = 'name' | 'size' | 'modified_time'
const sortKeys: SortField[] = ['name', 'size', 'modified_time']
const sortField = ref<SortField>('name')
const sortAsc = ref(true)
const remoteSearchQuery = ref('')
const sortLabels: Record<SortField, string> = { name: 'sortByName', size: 'sortBySize', modified_time: 'sortByDate' }

function toggleSort(key: SortField) {
  if (sortField.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortField.value = key
    sortAsc.value = true
  }
}

const sortedRemoteFiles = computed(() => {
  const q = remoteSearchQuery.value.trim().toLowerCase()
  let files = [...store.remoteVpkFiles]
  if (q) files = files.filter((f) => f.name.toLowerCase().includes(q))
  const dir = sortAsc.value ? 1 : -1
  files.sort((a: RemoteFile, b: RemoteFile) => {
    const field = sortField.value
    if (field === 'name') return a.name.localeCompare(b.name) * dir
    return ((a[field] as number) - (b[field] as number)) * dir
  })
  return files
})

const store = useVpkManagerStore()
const { t: $t } = useI18n()

const isAllSelected = computed(() => {
  return store.remoteVpkFiles.length > 0 && 
         store.selectedRemoteVpks.size === store.remoteVpkFiles.length
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    store.deselectAllRemote()
  } else {
    store.selectAllRemote()
  }
}

function formatDate(timestamp: number) {
  return new Date(timestamp * 1000).toLocaleString()
}

async function handleBatchEnable() {
  await store.enableRemoteVpks()
}

async function handleBatchDisable() {
  await store.disableRemoteVpks()
}

async function handleBatchDelete() {
  if (await store.showConfirm($t('confirmDeleteSelectedRemote', { count: store.selectedRemoteVpks.size }))) {
    await store.deleteMultipleRemoteVpks()
  }
}

async function handleRestartServer() {
  if (await store.showConfirm($t('confirmRestartServer'))) {
    await store.restartL4d2Server()
  }
}

onMounted(() => {
  if (store.sftpSettings.address && store.sftpSettings.addons_path) {
    store.scanRemoteVpks()
  }
})
</script>

<style scoped>
.sftp-browser {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(15, 23, 42, 0.4);
  border-left: 1px solid rgba(148, 163, 184, 0.1);
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.browser-header {
.remote-search-input {
  flex: 1;
  min-width: 120px;
  max-width: 220px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 13px;
  padding: 5px 10px;
}

.remote-search-input::placeholder {
  color: #64748b;
}

.sort-controls {
  display: flex;
  gap: 4px;
}

.sort-btn {
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #94a3b8;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sort-btn.active {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
  color: #60a5fa;
}

.sort-btn:hover {
  color: #e2e8f0;
}
  padding: 16px 20px;
  background: rgba(30, 41, 59, 0.6);
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-info h3 {
  margin: 0;
  font-size: 16px;
  color: #f1f5f9;
}

.path-badge {
  font-size: 11px;
  color: #94a3b8;
  background: rgba(15, 23, 42, 0.5);
  padding: 2px 8px;
  border-radius: 4px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-refresh {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.25);
  border-color: #60a5fa;
}

.btn-restart {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.35);
  color: #f87171;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.btn-restart:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.25);
  border-color: #f87171;
  color: #fca5a5;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

.browser-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.selection-actions {
  padding: 10px 16px;
  background: rgba(30, 41, 59, 0.4);
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.count-text {
  font-size: 13px;
  color: #94a3b8;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-action {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(148, 163, 184, 0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 14px;
}

.btn-action:hover:not(:disabled) {
  background: rgba(148, 163, 184, 0.2);
  transform: translateY(-1px);
}

.btn-action.enable:hover { background: rgba(34, 197, 94, 0.2); border-color: #22c55e; }
.btn-action.download:hover { background: rgba(59, 130, 246, 0.2); border-color: #3b82f6; }
.btn-action.disable:hover { background: rgba(245, 158, 11, 0.2); border-color: #f59e0b; }
.btn-action.delete:hover { background: rgba(239, 68, 68, 0.2); border-color: #ef4444; }

.remote-loading, .remote-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.mini-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(148, 163, 184, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.empty-msg {
  text-align: center;
  color: #64748b;
}

.empty-msg span {
  font-size: 40px;
  margin-bottom: 8px;
  display: block;
}

.remote-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.remote-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(148, 163, 184, 0.05);
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
  gap: 12px;
  position: relative; /* 添加此行 */
  overflow: hidden; /* 确保遮罩不超出圆角 */
}

.remote-item:hover {
  background: rgba(30, 41, 59, 0.5);
  border-color: rgba(59, 130, 246, 0.3);
  transform: translateX(4px);
}

.remote-item:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: -2px;
}

.remote-item.is-selected {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.4);
}

.remote-item.is-disabled {
  background: rgba(15, 23, 42, 0.2);
  border-color: rgba(148, 163, 184, 0.1);
}

.remote-item.is-disabled .item-name {
  text-decoration: line-through;
  color: #64748b;
}

.remote-item.is-disabled .item-icon {
  filter: grayscale(100%) opacity(0.5);
}

.remote-item.is-disabled::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.1);
  pointer-events: none;
}

.item-checkbox {
  display: flex;
  align-items: center;
}

.item-icon {
  font-size: 20px;
}

.item-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.item-name {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  font-size: 11px;
  color: #64748b;
}

.checkbox-container {
  display: block;
  position: relative;
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-container input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: absolute;
  top: 0;
  left: 0;
  height: 18px;
  width: 18px;
  background-color: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 4px;
  transition: all 0.2s;
}

.checkbox-container:hover input ~ .checkmark {
  background-color: rgba(148, 163, 184, 0.2);
}

.checkbox-container input:checked ~ .checkmark {
  background-color: #3b82f6;
  border-color: #3b82f6;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.checkbox-container input:checked ~ .checkmark:after {
  display: block;
}

.checkbox-container .checkmark:after {
  left: 6px;
  top: 2px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.remote-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.remote-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(30, 41, 59, 0.4);
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.05);
  transition: all 0.2s ease;
}

.remote-item:hover {
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(148, 163, 184, 0.2);
}

.item-icon {
  font-size: 20px;
  margin-right: 12px;
}

.item-details {
  flex: 1;
  min-width: 0;
}

.item-name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  font-size: 11px;
  color: #94a3b8;
}

.item-actions {
  margin-left: 12px;
}

.btn-icon-delete {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  opacity: 0.6;
  transition: all 0.2s ease;
}

.btn-icon-delete:hover {
  background: rgba(239, 68, 68, 0.15);
  opacity: 1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
