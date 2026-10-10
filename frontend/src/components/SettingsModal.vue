<template>
  <transition name="fade">
    <div v-if="show" class="modal-overlay" @click.self="emit('update:show', false)">
      <div class="modal-content settings-modal">
        <div class="modal-header">
          <h2 class="modal-title">⚙️ {{ $t('settingsTitle') }}</h2>
          <button class="modal-close" @click="emit('update:show', false)">×</button>
        </div>
        <div class="modal-body">
          <!-- General Settings -->
          <div class="settings-section">
            <h3 class="section-subtitle">{{ $t('generalSettings') }}</h3>
            <div class="settings-item action-item">
              <div class="setting-text">
                <span class="setting-title">{{ $t('resetAppData') }}</span>
                <p class="setting-item-desc">{{ $t('resetAppDataDesc') }}</p>
              </div>
              <button
                class="btn btn-outline"
                @click="handleResetData"
                :disabled="isResetting"
              >
                {{ isResetting ? $t('resetting') : $t('executeNow') }}
              </button>
            </div>
          </div>

          <!-- SFTP Settings -->
          <div class="settings-section">
            <h3 class="section-subtitle">{{ $t('sftpSettings') }}</h3>
            <p class="section-desc">{{ $t('sftpHelp') }}</p>
            
            <div class="settings-item">
              <label class="setting-label">{{ $t('sftpAddress') }}</label>
              <input 
                type="text" 
                v-model="store.sftpSettings.address" 
                @change="store.saveSftpSettings()" 
                class="setting-input" 
                placeholder="example.com:22"
              >
            </div>
            
            <div class="settings-item">
              <label class="setting-label">{{ $t('sftpUsername') }}</label>
              <input 
                type="text" 
                v-model="store.sftpSettings.username" 
                @change="store.saveSftpSettings()" 
                class="setting-input"
              >
            </div>
            
            <div class="settings-item">
              <label class="setting-label">{{ $t('sftpPassword') }}</label>
              <input 
                type="password" 
                v-model="store.sftpSettings.password" 
                @change="store.saveSftpSettings()" 
                class="setting-input"
              >
            </div>
            
            <div class="settings-item">
              <label class="setting-label">{{ $t('sftpAddonsPath') }}</label>
              <input 
                type="text" 
                v-model="store.sftpSettings.addons_path" 
                @change="store.saveSftpSettings()" 
                class="setting-input" 
                placeholder="/home/user/l4d2/left4dead2/addons"
              >
            </div>

            <!-- SFTP 连接测试 -->
            <div class="settings-item connection-test">
              <button
                class="btn btn-outline test-connection-btn"
                :disabled="isTestingConnection"
                @click="handleTestConnection"
              >
                <span v-if="isTestingConnection" class="btn-spinner"></span>
                <span v-else>&#128268;</span>
                {{ isTestingConnection ? $t('sftpTesting') : $t('sftpTestConnection') }}
              </button>
              <span
                v-if="connectionTestResult"
                class="connection-test-result"
                :class="connectionTestResult.ok ? 'test-ok' : 'test-fail'"
              >
                {{ connectionTestResult.message }}
              </span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="emit('update:show', false)">{{ $t('close') }}</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'
import { getApi } from '@/composables/useApi'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const store = useVpkManagerStore()
const { t: $t } = useI18n()
const isResetting = ref(false)
const isTestingConnection = ref(false)
const connectionTestResult = ref<{ ok: boolean; message: string } | null>(null)

async function handleTestConnection() {
  isTestingConnection.value = true
  connectionTestResult.value = null
  try {
    const result = await getApi().list_remote_vpks()
    if (result.success) {
      const count = (result.files || []).length
      connectionTestResult.value = { ok: true, message: $t('sftpTestSuccess', { count }) }
    } else {
      connectionTestResult.value = { ok: false, message: $t('sftpTestFailed', { error: result.error || 'unknown' }) }
    }
  } catch (error) {
    connectionTestResult.value = { ok: false, message: $t('sftpTestFailed', { error: String(error) }) }
  } finally {
    isTestingConnection.value = false
  }
}

async function handleResetData() {
  if (await store.showConfirm($t('resetConfirm'))) {
    try {
      isResetting.value = true
      await getApi().reset_app_data()
    } catch (error) {
      console.error('Reset failed:', error)
    } finally {
      isResetting.value = false
    }
  }
}
</script>

<style scoped>
/* Modal Base */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background: #1e293b;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  animation: modalScale 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalScale {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
}

.modal-close {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.05);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  justify-content: flex-end;
}

/* Settings Specific */
.settings-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.settings-section:last-child {
  margin-bottom: 0;
}

.section-subtitle {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
}

.section-desc {
  color: #94a6b8;
  font-size: 13px;
  margin-top: -8px;
  margin-bottom: 8px;
}

.settings-item {
  padding: 12px;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.05);
}

.setting-label {
  display: block;
  color: #94a6b8;
  font-size: 12px;
  margin-bottom: 8px;
  font-weight: 500;
}

.setting-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  color: #f1f5f9;
  font-size: 14px;
  transition: all 0.2s ease;
}

.setting-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: rgba(30, 41, 59, 0.8);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.settings-item.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.connection-test {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.test-connection-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.connection-test-result {
  font-size: 13px;
  font-weight: 500;
}

.connection-test-result.test-ok {
  color: #10b981;
}

.connection-test-result.test-fail {
  color: #ef4444;
}

.setting-text {
  flex: 1;
}

.setting-title {
  color: #f1f5f9;
  font-weight: 600;
  font-size: 14px;
}

.setting-item-desc {
  margin: 6px 0 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-outline {
  background: transparent;
  border: 1px solid rgba(148, 163, 184, 0.3);
  color: #f1f5f9;
}

.btn-outline:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  border-color: #f1f5f9;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
