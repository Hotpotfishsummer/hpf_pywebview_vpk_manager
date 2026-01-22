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
          alt="thumbnail"
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { VpkFile } from '@/stores/vpk-manager'

defineProps<{
  vpk: VpkFile
  isSelected: boolean
}>()

defineEmits<{
  toggle: []
}>()

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

.vpk-file-item.is-disabled {
  opacity: 0.5;
}

.vpk-file-item.is-disabled .file-name {
  text-decoration: line-through;
  color: #64748b;
}

.vpk-file-item.is-disabled .thumbnail-container {
  filter: grayscale(100%) brightness(0.6);
}
</style>
