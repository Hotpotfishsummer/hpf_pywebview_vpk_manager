<template>
  <section class="vpk-section">
    <div class="section-header" @click="toggleExpanded">
      <h2 class="section-title">
        {{ title }} ({{ isFiltering ? `${files.length}/${totalCount}` : files.length }})
      </h2>
      <span class="section-toggle" :class="{ rotated: expanded }">▶</span>
    </div>
    <p class="section-subtitle">{{ subtitle }}</p>

    <transition name="expand">
      <div v-if="expanded" class="section-content-wrapper">
        <div class="section-content">
          <div v-if="files.length === 0 && isScanning" class="file-list">
            <SkeletonLoader :item-count="3" />
          </div>
          <div v-else-if="isFiltering && files.length === 0" class="empty-message">
            {{ $t('noSearchResults') }}
          </div>
          <div v-else-if="files.length === 0" class="empty-message">
            {{ emptyText }}
          </div>
          <div v-else-if="isFiltering && files.length === 0" class="empty-message">
            {{ $t('noSearchResults') }}
          </div>
          <div v-else class="file-list">
            <div class="list-actions">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleAll"
                />
                <span>{{ allSelected ? $t('deselectAll') : $t('selectAll') }}</span>
              </label>
              <span v-if="selectedCount > 0" class="selection-stats">
                {{ $t('selectedFilesWithSize', { count: selectedCount, size: selectedTotalSize }) }}
              </span>
              <button
                class="action-icon-btn"
                @click.stop="$emit('open-folder')"
                :title="$t('openInFileManager')"
              >
                <span class="icon">📂</span>
              </button>
            </div>
            <VpkFileItem
              v-for="vpk in files"
              :key="vpk.path"
              :vpk="vpk"
              :is-selected="selectedSet.has(vpk.path)"
              @toggle="$emit('toggle-select', vpk.path)"
              @enable="$emit('enable', $event)"
              @disable="$emit('disable', $event)"
              @delete="$emit('delete', $event)"
            />
          </div>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { VpkFile } from '@/stores/vpk-manager'
import VpkFileItem from '@/components/VpkFileItem.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'

const props = defineProps<{
  title: string
  subtitle: string
  emptyText: string
  files: VpkFile[]
  totalCount?: number
  selectedSet: Set<string>
  isScanning?: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-select', path: string): void
  (e: 'select-all', paths: string[]): void
  (e: 'deselect-all', paths: string[]): void
  (e: 'open-folder'): void
  (e: 'enable', path: string): void
  (e: 'disable', path: string): void
  (e: 'delete', path: string): void
}>()

const SECTION_STATE_KEY = 'vpk-section-expanded'
const SECTION_ID = 'vpk-section'
const expanded = ref(loadExpanded())

const isFiltering = computed(() => {
  return props.totalCount !== undefined && props.files.length < props.totalCount
})

const allSelected = computed(() => {
  return props.files.length > 0 && props.files.every((vpk) => props.selectedSet.has(vpk.path))
})

const selectedCount = computed(() => {
  return props.files.filter((vpk) => props.selectedSet.has(vpk.path)).length
})

const selectedTotalSize = computed(() => {
  const total = props.files
    .filter((vpk) => props.selectedSet.has(vpk.path))
    .reduce((sum, vpk) => sum + vpk.size, 0)
  return formatBytes(total)
})

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1) return `${bytes} B`
  if (kb < 1024) return `${kb.toFixed(2)} KB`
  const mb = kb / 1024
  if (mb < 1024) return `${mb.toFixed(2)} MB`
  const gb = mb / 1024
  return `${gb.toFixed(2)} GB`
}

function toggleExpanded() {
  expanded.value = !expanded.value
}

function loadExpanded(): boolean {
  try {
    const raw = localStorage.getItem(`${SECTION_STATE_KEY}:${SECTION_ID}`)
    if (raw !== null) return raw !== 'false'
  } catch {
    // 忽略 localStorage 不可用(隐私模式/安全策略)
  }
  return true
}

function persistExpanded(value: boolean) {
  try {
    localStorage.setItem(`${SECTION_STATE_KEY}:${SECTION_ID}`, String(value))
  } catch {
    // 忽略不可写 localStorage
  }
}


watch(expanded, (value) => {
  persistExpanded(value)
})

function toggleAll() {
  if (allSelected.value) {
    emit('deselect-all', props.files.map((v) => v.path))
  } else {
    emit('select-all', props.files.map((v) => v.path))
  }
}
</script>

<style scoped>
.vpk-section {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(148, 163, 184, 0.15);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(20px);
}

.vpk-section:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  background: rgba(15, 23, 42, 0.6);
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
  transition: background-color 0.2s ease;
}

.section-header:hover {
  background: rgba(15, 23, 42, 0.8);
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: -0.3px;
}

.section-toggle {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 600;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.section-toggle.rotated {
  transform: rotate(90deg);
}

.section-header:hover .section-toggle {
  color: #cbd5e1;
}

.section-subtitle {
  margin: 0;
  padding: 0 20px;
  padding-top: 10px;
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

/* Expansion Animation */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 2000px; /* Large enough to fit content */
  opacity: 1;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
  transform: translateY(-10px);
}

.section-content-wrapper {
  overflow: hidden;
}

.section-content {
  padding: 16px 20px;
}

.empty-message {
  padding: 28px 20px;
  text-align: center;
  color: #94a3b8;
  font-style: italic;
  font-weight: 500;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
  margin-bottom: 14px;
}

.action-icon-btn {
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-icon-btn:hover {
  background: rgba(148, 163, 184, 0.2);
  border-color: rgba(148, 163, 184, 0.4);
  transform: translateY(-1px);
}

.action-icon-btn .icon {
  font-size: 16px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 600;
  padding: 8px 0;
  transition: color 0.2s ease;
}

.checkbox-label input[type='checkbox'] {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
}

.checkbox-label:hover {
  color: #3b82f6;
}

.selection-stats {
  font-size: 13px;
  font-weight: 600;
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 999px;
  padding: 4px 12px;
  white-space: nowrap;
}
</style>
