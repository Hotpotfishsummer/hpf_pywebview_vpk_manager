<template>
  <header class="app-header" :class="{ 'collapsed': collapsed }">
    <div class="header-content">
      <div class="header-left">
        <h1 class="app-title">
          <span class="title-icon">🎮</span>
          {{ $t('appTitle') }}
        </h1>
        <p class="app-subtitle">Left 4 Dead 2 VPK Manager</p>
      </div>
      <div class="header-right">
        <div class="language-switcher">
          <button
            @click="switchLanguage('en')"
            :class="{ active: currentLocale === 'en' }"
            class="lang-btn"
          >
            EN
          </button>
          <button
            @click="switchLanguage('zh')"
            :class="{ active: currentLocale === 'zh' }"
            class="lang-btn"
          >
            中文
          </button>
        </div>
        <button
          @click="store.isSftpActive = !store.isSftpActive"
          class="sftp-toggle-btn"
          :class="{ active: store.isSftpActive }"
          :title="store.isSftpActive ? $t('sftpDisable') : $t('sftpEnable')"
        >
          🌐
        </button>
        <button @click="$emit('open-settings')" class="settings-btn" :title="$t('settings')">
          ⚙️
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'
import { useI18n } from 'vue-i18n'

defineProps<{ collapsed: boolean }>()
defineEmits<{ (e: 'open-settings'): void }>()

const store = useVpkManagerStore()
const { locale, t: $t } = useI18n()

const currentLocale = computed(() => locale.value)

const STORAGE_KEY = 'locale'

function saveLocale(lang: string) {
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // 忽略不可写 localStorage(如隐私模式/安全策略)
  }
}

function switchLanguage(lang: string) {
  locale.value = lang
  saveLocale(lang)
}
</script>

<style scoped>
/* Header */
.app-header {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: white;
  padding: 20px 24px;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.25);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
  position: relative;
}

.app-header.collapsed {
  padding: 4px 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-left {
  flex: 1;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 12px;
  letter-spacing: -0.5px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-header.collapsed .app-title {
  font-size: 16px;
  gap: 8px;
}

.title-icon {
  font-size: 32px;
  line-height: 1;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-header.collapsed .title-icon {
  font-size: 20px;
}

.app-subtitle {
  margin: 4px 0 0 44px;
  font-size: 13px;
  opacity: 0.85;
  letter-spacing: 0.5px;
  font-weight: 500;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 20px;
  overflow: hidden;
}

.app-header.collapsed .app-subtitle {
  max-height: 0;
  margin-top: 0;
  opacity: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* Language switcher */
.language-switcher {
  display: flex;
  gap: 6px;
  background: rgba(255, 255, 255, 0.12);
  padding: 6px;
  border-radius: 8px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.lang-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  border-radius: 6px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-header.collapsed .lang-btn {
  padding: 3px 8px;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.settings-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s ease;
  margin-left: 8px;
}

.settings-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(45deg);
}

.app-header.collapsed .settings-btn {
  width: 28px;
  height: 28px;
  font-size: 14px;
}

.lang-btn.active {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.sftp-toggle-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s ease;
  margin-left: 8px;
}

.sftp-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.sftp-toggle-btn.active {
  background: #3b82f6;
  border-color: #60a5fa;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
}

.app-header.collapsed .sftp-toggle-btn {
  width: 28px;
  height: 28px;
  font-size: 14px;
}

/* Responsive */
@media (max-width: 768px) {
  .app-title {
    font-size: 18px;
  }

  .app-subtitle {
    margin-left: 24px;
    font-size: 11px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-right {
    align-self: flex-end;
  }
}
</style>
