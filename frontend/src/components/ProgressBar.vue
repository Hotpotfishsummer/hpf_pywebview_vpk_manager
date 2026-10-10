<template>
  <div class="unified-progress" role="status" aria-live="polite">
    <div class="progress-track">
      <div class="progress-indeterminate"></div>
    </div>
    <span class="progress-label">
      <span class="progress-spinner"></span>
      {{ label }}
    </span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
}>()
</script>

<style scoped>
.unified-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.progress-track {
  flex: 1;
  max-width: 260px;
  height: 6px;
  border-radius: 3px;
  background: rgba(148, 163, 184, 0.15);
  overflow: hidden;
}

.progress-indeterminate {
  height: 100%;
  width: 40%;
  border-radius: 3px;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  animation: indeterminate 1.4s ease-in-out infinite;
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.progress-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  white-space: nowrap;
}

.progress-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
