<template>
  <div class="skeleton-list">
    <div class="skeleton-actions">
      <div class="skeleton-checkbox skeleton-pulse"></div>
      <div class="skeleton-text skeleton-pulse"></div>
    </div>
    <div
      v-for="i in itemCount"
      :key="i"
      class="skeleton-item skeleton-pulse"
    >
      <div class="skeleton-checkbox"></div>
      <div class="skeleton-thumb skeleton-pulse"></div>
      <div class="skeleton-info">
        <div class="skeleton-name skeleton-pulse"></div>
        <div class="skeleton-detail skeleton-pulse"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  itemCount?: number
}>(), {
  itemCount: 4,
})
</script>

<style scoped>
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  margin-bottom: 14px;
}

.skeleton-text {
  height: 14px;
  width: 80px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.12);
}

.skeleton-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.12);
  flex-shrink: 0;
}

.skeleton-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(30, 41, 59, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.08);
}

.skeleton-thumb {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: rgba(148, 163, 184, 0.12);
  flex-shrink: 0;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-name {
  height: 14px;
  width: 65%;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.12);
}

.skeleton-detail {
  height: 12px;
  width: 45%;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.08);
}

/* Shimmer pulse animation */
.skeleton-pulse {
  position: relative;
  overflow: hidden;
}

.skeleton-pulse::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(148, 163, 184, 0.08) 50%,
    transparent 100%
  );
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>