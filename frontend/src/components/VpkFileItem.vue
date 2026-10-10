<template>
  <div class="vpk-file-item" :class="{ 'is-disabled': vpk.is_disabled }">
    <div class="item-content">
      <label class="checkbox-label">
        <input
          type="checkbox"
          :checked="isSelected"
          @change="$emit('toggle')"
        />
      </label>
      
      <!-- 缩略图显示 -->
      <div class="thumbnail-container">
        <img 
          v-if="vpk.thumbnail_path" 
          :src="vpk.thumbnail_path" 
          class="vpk-thumbnail" 
          :alt="vpk.display_name"
          loading="lazy"
          decoding="async"
        />
        <div v-else class="vpk-thumbnail-placeholder">
          <span>VPK</span>
        </div>
      </div>

      <div class="file-info">
        <p class="file-name">{{ vpk.display_name }}</p>
        <p class="file-details">
          {{ vpk.name }} · {{ formatSize(vpk.size) }}
        </p>
        <button 
          v-if="workshopId" 
          @click.stop="openWorkshop" 
          class="workshop-btn"
          :title="$t('viewInWorkshop')"
        >
          <span class="btn-icon">🌐</span>
          {{ $t("openWorkshopPage") }}
        </button>
      </div>
      <div class="item-actions">
        <button
          v-if="vpk.is_disabled"
          class="quick-action-btn enable-btn"
          :title="$t('enable')"
          @click.stop="$emit('enable', vpk.path)"
        >✔️</button>
        <button
          v-else
          class="quick-action-btn disable-btn"
          :title="$t('disable')"
          @click.stop="$emit('disable', vpk.path)"
        >🚫</button>
        <button
          class="quick-action-btn delete-btn"
          :title="$t('hardDelete')"
          @click.stop="handleDelete"
        >🗑️</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { VpkFile } from '@/stores/vpk-manager'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { callApi } from '@/composables/useApi'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  vpk: VpkFile
  isSelected: boolean
}>()

const emit = defineEmits<{
  toggle: []
  enable: [path: string]
  disable: [path: string]
  delete: [path: string]
}>()

const { t: $t } = useI18n()

async function handleDelete() {
  const confirmed = await useVpkManagerStore().showConfirm($t('confirmHardDelete'))
  if (confirmed) {
    emit('delete', props.vpk.path)
  }
}

const workshopId = computed(() => {
  // 匹配连续 8 位或以上的数字
  const match = props.vpk.name.match(/\d{8,}/)
  return match ? match[0] : null
})

async function openWorkshop() {
  if (workshopId.value) {
    const url = `https://steamcommunity.com/sharedfiles/filedetails/?id=${workshopId.value}`
    await callApi(api => api.open_external_url(url), undefined)
  }
}

function formatSize(bytes: number): string {
  const mb = bytes / (1024 * 1024)
  if (mb < 1) {
    const kb = bytes / 1024
    return kb < 1 ? `${bytes} B` : `${kb.toFixed(2)} KB`
  }
  return `${mb.toFixed(2)} MB`
}
</script>

<style scoped>
.vpk-file-item {
  padding: 14px;
  background-color: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.vpk-file-item:hover {
  background-color: rgba(15, 23, 42, 0.8);
  border-color: rgba(148, 163, 184, 0.25);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}

.item-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  flex-shrink: 0;
}

.checkbox-label input[type='checkbox'] {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
  transition: all 0.2s ease;
}

.checkbox-label:hover input[type='checkbox'] {
  transform: scale(1.1);
}

.thumbnail-container {
  width: 160px;
  height: 90px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.vpk-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.vpk-thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  color: #64748b;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 2px;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #e2e8f0;
  word-break: break-word;
  letter-spacing: -0.3px;
}

.file-details {
  margin: 6px 0 0 0;
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.workshop-btn {
  margin-top: 8px;
  padding: 4px 10px;
  font-size: 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
  width: fit-content;
}

.workshop-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: white;
  transform: translateY(-1px);
}

.workshop-btn .btn-icon {
  font-size: 12px;
}

.vpk-file-item.is-disabled {
  opacity: 0.5;
}

.item-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.vpk-file-item:hover .item-actions {
  opacity: 1;
}

.quick-action-btn {
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s ease;
}

.quick-action-btn:hover {
  background: rgba(148, 163, 184, 0.25);
  transform: translateY(-1px);
}

.quick-action-btn.enable-btn:hover {
  border-color: rgba(16, 185, 129, 0.4);
}

.quick-action-btn.disable-btn:hover {
  border-color: rgba(245, 158, 11, 0.4);
}

.quick-action-btn.delete-btn:hover {
  border-color: rgba(239, 68, 68, 0.4);
}

.vpk-file-item.is-disabled .file-name {
  text-decoration: line-through;
  color: #64748b;
}

.vpk-file-item.is-disabled .thumbnail-container {
  filter: grayscale(100%) brightness(0.6);
}
</style>
