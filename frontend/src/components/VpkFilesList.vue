<template>
  <div class="vpk-files-list">
    <!-- Search / filter box -->
    <div class="search-bar">
      <span class="search-icon">&#128269;</span>
      <input
        v-model="store.searchQuery"
        type="text"
        class="search-input"
        :placeholder="$t('searchFilesPlaceholder')"
        :aria-label="$t('searchFilesPlaceholder')"
      />
      <button
        v-if="store.searchQuery"
        class="search-clear"
        :title="$t('clearSearch')"
        :aria-label="$t('clearSearch')"
        @click="store.searchQuery = ''"
      >
        &times;
      </button>
      <span v-if="store.searchQuery" class="search-count">
        {{ $t('searchResultCount', { count: visibleCount }) }}
      </span>
    </div>

    <!-- Local VPK Files -->
    <VpkSection
      :title="$t('localVpkFiles')"
      :subtitle="$t('localVpkFilesSubtitle')"
      :empty-text="$t('noLocalVpkFiles')"
      :files="store.filteredLocalVpkFiles"
      :total-count="store.localVpkFiles.length"
      :selected-set="store.selectedLocalVpks"
      :is-scanning="store.isScanning"
      @toggle-select="store.toggleLocalVpkSelection"
      @select-all="store.selectAllLocal"
      @deselect-all="store.deselectAllLocal"
      @enable="(path: string) => store.deleteVpks(true, [path])"
      @disable="(path: string) => store.deleteVpks(true, [path])"
      @delete="(path: string) => store.deleteVpks(false, [path])"
      @open-folder="store.openAddonsFolder"
    />

    <!-- Workshop Files -->
    <VpkSection
      :title="$t('workshopFiles')"
      :subtitle="$t('workshopFilesSubtitle')"
      :empty-text="$t('noWorkshopFiles')"
      :files="store.filteredWorkshopVpkFiles"
      :total-count="store.workshopVpkFiles.length"
      :selected-set="store.selectedWorkshopVpks"
      :is-scanning="store.isScanning"
      @toggle-select="store.toggleWorkshopVpkSelection"
      @select-all="store.selectAllWorkshop"
      @deselect-all="store.deselectAllWorkshop"
      @enable="(path: string) => store.deleteVpks(true, [path])"
      @disable="(path: string) => store.deleteVpks(true, [path])"
      @delete="(path: string) => store.deleteVpks(false, [path])"
      @open-folder="store.openWorkshopFolder"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'
import VpkSection from '@/components/VpkSection.vue'

const store = useVpkManagerStore()
const { t: $t } = useI18n()

const visibleCount = computed(
  () => store.filteredLocalVpkFiles.length + store.filteredWorkshopVpkFiles.length
)
</script>

<style scoped>
.vpk-files-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  padding: 0 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.search-bar:focus-within {
  border-color: rgba(59, 130, 246, 0.6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.search-icon {
  font-size: 14px;
  color: #94a3b8;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #e2e8f0;
  font-size: 14px;
  padding: 10px 0;
}

.search-input:focus {
  outline: none;
  box-shadow: none;
}

.search-input::placeholder {
  color: #64748b;
}

.search-clear {
  background: rgba(148, 163, 184, 0.15);
  border: none;
  color: #cbd5e1;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 15px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s ease;
}

.search-clear:hover {
  background: rgba(148, 163, 184, 0.3);
}

.search-count {
  font-size: 12px;
  font-weight: 600;
  color: #60a5fa;
  white-space: nowrap;
  flex-shrink: 0;
}
</style>
