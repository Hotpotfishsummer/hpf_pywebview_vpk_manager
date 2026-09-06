<template>
  <div class="vpk-files-list">
    <!-- Local VPK Files -->
    <section class="vpk-section">
      <div class="section-header" @click="toggleLocalExpanded">
        <h2 class="section-title">
          {{ $t('localVpkFiles') }} ({{ store.localVpkFiles.length }})
        </h2>
        <span class="section-toggle" :class="{ rotated: localExpanded }">▶</span>
      </div>
      <p class="section-subtitle">{{ $t('localVpkFilesSubtitle') }}</p>

      <transition name="expand">
        <div v-if="localExpanded" class="section-content-wrapper">
          <div class="section-content">
            <div v-if="store.localVpkFiles.length === 0" class="empty-message">
              {{ $t('noLocalVpkFiles') }}
            </div>
            <div v-else class="file-list">
              <div class="list-actions">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    :checked="allLocalSelected"
                    @change="toggleAllLocal"
                  />
                  <span>{{ allLocalSelected ? $t('deselectAll') : $t('selectAll') }}</span>
                </label>
                <button 
                  class="action-icon-btn" 
                  @click.stop="store.openAddonsFolder" 
                  :title="$t('openInFileManager')"
                >
                  <span class="icon">📂</span>
                </button>
              </div>
              <VpkFileItem
                v-for="vpk in store.localVpkFiles"
                :key="vpk.path"
                :vpk="vpk"
                :is-selected="store.selectedLocalVpks.has(vpk.path)"
                @toggle="() => store.toggleLocalVpkSelection(vpk.path)"
              />
            </div>
          </div>
        </div>
      </transition>
    </section>

    <!-- Workshop Files -->
    <section class="vpk-section">
      <div class="section-header" @click="toggleWorkshopExpanded">
        <h2 class="section-title">
          {{ $t('workshopFiles') }} ({{ store.workshopVpkFiles.length }})
        </h2>
        <span class="section-toggle" :class="{ rotated: workshopExpanded }">▶</span>
      </div>
      <p class="section-subtitle">{{ $t('workshopFilesSubtitle') }}</p>

      <transition name="expand">
        <div v-if="workshopExpanded" class="section-content-wrapper">
          <div class="section-content">
            <div v-if="store.workshopVpkFiles.length === 0" class="empty-message">
              {{ $t('noWorkshopFiles') }}
            </div>
            <div v-else class="file-list">
              <div class="list-actions">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    :checked="allWorkshopSelected"
                    @change="toggleAllWorkshop"
                  />
                  <span>{{ allWorkshopSelected ? $t('deselectAll') : $t('selectAll') }}</span>
                </label>
                <button 
                  class="action-icon-btn" 
                  @click.stop="store.openWorkshopFolder" 
                  :title="$t('openInFileManager')"
                >
                  <span class="icon">📂</span>
                </button>
              </div>
              <VpkFileItem
                v-for="vpk in store.workshopVpkFiles"
                :key="vpk.path"
                :vpk="vpk"
                :is-selected="store.selectedWorkshopVpks.has(vpk.path)"
                @toggle="() => store.toggleWorkshopVpkSelection(vpk.path)"
              />
            </div>
          </div>
        </div>
      </transition>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useVpkManagerStore } from '@/stores/vpk-manager'
import VpkFileItem from '@/components/VpkFileItem.vue'
import { useVpkSection } from '@/composables/useVpkSection'

const store = useVpkManagerStore()

const localSection = useVpkSection(
  () => store.localVpkFiles,
  () => store.selectedLocalVpks,
  () => store.selectAllLocal(),
  () => store.deselectAllLocal()
)

const workshopSection = useVpkSection(
  () => store.workshopVpkFiles,
  () => store.selectedWorkshopVpks,
  () => store.selectAllWorkshop(),
  () => store.deselectAllWorkshop()
)

const {
  expanded: localExpanded,
  allSelected: allLocalSelected,
  toggleExpanded: toggleLocalExpanded,
  toggleAll: toggleAllLocal,
} = localSection

const {
  expanded: workshopExpanded,
  allSelected: allWorkshopSelected,
  toggleExpanded: toggleWorkshopExpanded,
  toggleAll: toggleAllWorkshop,
} = workshopSection
</script>

<style scoped>
.vpk-files-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

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
</style>

