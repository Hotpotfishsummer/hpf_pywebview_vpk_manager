<template>
  <transition name="fade">
    <div v-if="store.confirmState.show" class="modal-overlay" @click.self="resolveConfirm(false)">
      <div class="modal-content confirm-dialog">
        <div class="modal-body">
          <p class="confirm-message">{{ store.confirmState.message }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="resolveConfirm(false)">{{ $t('cancel') }}</button>
          <button class="btn btn-danger" @click="resolveConfirm(true)">{{ $t('confirm') }}</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'

const store = useVpkManagerStore()
const { t: $t } = useI18n()

function resolveConfirm(value: boolean) {
  store.resolveConfirm(value)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.confirm-dialog {
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
}

.modal-body {
  padding: 24px 24px 12px;
}

.confirm-message {
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-line;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 24px 20px;
}

.btn-outline {
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.3);
  color: #e2e8f0;
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.btn-outline:hover {
  background: rgba(148, 163, 184, 0.2);
}

.btn-danger {
  background: #ef4444;
  border: 1px solid #ef4444;
  color: white;
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.btn-danger:hover {
  background: #dc2626;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
