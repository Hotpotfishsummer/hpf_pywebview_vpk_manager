<template>
  <div :class="['status-banner', `status-${store.notification.type}`]">
    <div class="status-content">
      <span class="status-icon">
        {{ store.notification.type === 'success' ? '✅' : (store.notification.type === 'error' ? '⚠️' : 'ℹ️') }}
      </span>
      <span class="status-text">{{ store.notification.message }}</span>
      <button @click="store.notification.message = ''" class="status-close">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useVpkManagerStore } from '@/stores/vpk-manager'

const store = useVpkManagerStore()
</script>

<style scoped>
/* Status banner */
.status-banner {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideDown 0.3s ease;
  z-index: 1000;
}

.status-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.status-error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.status-info {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.status-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: white;
}

.status-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.status-text {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.status-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.status-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
