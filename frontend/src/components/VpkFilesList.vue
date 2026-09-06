<template>
  <div class="vpk-files-list">
    <!-- Local VPK Files -->
    <VpkSection
      :title="$t('localVpkFiles')"
      :subtitle="$t('localVpkFilesSubtitle')"
      :empty-text="$t('noLocalVpkFiles')"
      :files="store.localVpkFiles"
      :selected-set="store.selectedLocalVpks"
      @toggle-select="store.toggleLocalVpkSelection"
      @select-all="store.selectAllLocal"
      @deselect-all="store.deselectAllLocal"
      @open-folder="store.openAddonsFolder"
    />

    <!-- Workshop Files -->
    <VpkSection
      :title="$t('workshopFiles')"
      :subtitle="$t('workshopFilesSubtitle')"
      :empty-text="$t('noWorkshopFiles')"
      :files="store.workshopVpkFiles"
      :selected-set="store.selectedWorkshopVpks"
      @toggle-select="store.toggleWorkshopVpkSelection"
      @select-all="store.selectAllWorkshop"
      @deselect-all="store.deselectAllWorkshop"
      @open-folder="store.openWorkshopFolder"
    />
  </div>
</template>

<script setup lang="ts">
import { useVpkManagerStore } from '@/stores/vpk-manager'
import VpkSection from '@/components/VpkSection.vue'

const store = useVpkManagerStore()
</script>

<style scoped>
.vpk-files-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
</style>
