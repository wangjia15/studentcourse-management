<template>
  <div class="spreadsheet-settings">
    <el-form :model="modelValue" label-width="140px" label-position="left">
      <!-- Virtual Scrolling Settings -->
      <el-form-item label="虚拟滚动">
        <el-switch
          v-model="modelValue.virtualScrolling.enabled"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="setting-description">
          启用虚拟滚动可以提高大数据集的性能
        </div>
      </el-form-item>

      <template v-if="modelValue.virtualScrolling.enabled">
        <el-form-item label="行高度">
          <el-input-number
            v-model="modelValue.virtualScrolling.itemHeight"
            :min="30"
            :max="100"
            :step="5"
            size="small"
          />
          <span class="unit">像素</span>
        </el-form-item>

        <el-form-item label="缓冲区大小">
          <el-input-number
            v-model="modelValue.virtualScrolling.bufferSize"
            :min="5"
            :max="20"
            :step="1"
            size="small"
          />
          <span class="unit">行</span>
          <div class="setting-description">
            预渲染的额外行数，用于提高滚动流畅度
          </div>
        </el-form-item>

        <el-form-item label="启用阈值">
          <el-input-number
            v-model="modelValue.virtualScrolling.threshold"
            :min="50"
            :max="1000"
            :step="50"
            size="small"
          />
          <span class="unit">行</span>
          <div class="setting-description">
            超过此行数时自动启用虚拟滚动
          </div>
        </el-form-item>
      </template>

      <!-- Auto Save Settings -->
      <el-form-item label="自动保存">
        <el-switch
          v-model="modelValue.autoSave.enabled"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="setting-description">
          启用后自动保存您的更改
        </div>
      </el-form-item>

      <template v-if="modelValue.autoSave.enabled">
        <el-form-item label="保存间隔">
          <el-input-number
            v-model="modelValue.autoSave.interval"
            :min="10000"
            :max="300000"
            :step="10000"
            size="small"
          />
          <span class="unit">毫秒</span>
          <div class="setting-description">
            自动保存的时间间隔
          </div>
        </el-form-item>

        <el-form-item label="防抖延迟">
          <el-input-number
            v-model="modelValue.autoSave.debounce"
            :min="500"
            :max="5000"
            :step="500"
            size="small"
          />
          <span class="unit">毫秒</span>
          <div class="setting-description">
            输入后延迟保存的时间
          </div>
        </el-form-item>
      </template>

      <!-- Validation Settings -->
      <el-form-item label="实时验证">
        <el-switch
          v-model="modelValue.validation.enabled"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="setting-description">
          启用后实时验证输入的数据
        </div>
      </el-form-item>

      <template v-if="modelValue.validation.enabled">
        <el-form-item label="显示错误">
          <el-switch
            v-model="modelValue.validation.showError"
            active-text="显示"
            inactive-text="隐藏"
          />
          <div class="setting-description">
            是否在界面上显示验证错误
          </div>
        </el-form-item>
      </template>

      <!-- UI Settings -->
      <el-form-item label="显示行号">
        <el-switch
          v-model="modelValue.ui.showRowNumbers"
          active-text="显示"
          inactive-text="隐藏"
        />
      </el-form-item>

      <el-form-item label="显示列标题">
        <el-switch
          v-model="modelValue.ui.showColumnHeaders"
          active-text="显示"
          inactive-text="隐藏"
        />
      </el-form-item>

      <el-form-item label="交替行颜色">
        <el-switch
          v-model="modelValue.ui.alternatingRowColors"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>

      <el-form-item label="启用选择">
        <el-switch
          v-model="modelValue.ui.enableSelection"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>

      <el-form-item label="键盘导航">
        <el-switch
          v-model="modelValue.ui.enableKeyboardNavigation"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="setting-description">
          启用Excel风格的键盘导航
        </div>
      </el-form-item>

      <!-- Performance Settings -->
      <el-form-item label="最大行数">
        <el-input-number
          v-model="modelValue.performance.maxRows"
          :min="1000"
          :max="10000"
          :step="1000"
          size="small"
        />
        <span class="unit">行</span>
        <div class="setting-description">
          系统支持的最大数据行数
        </div>
      </el-form-item>

      <el-form-item label="最大列数">
        <el-input-number
          v-model="modelValue.performance.maxColumns"
          :min="20"
          :max="100"
          :step="5"
          size="small"
        />
        <span class="unit">列</span>
      </el-form-item>

      <el-form-item label="懒加载">
        <el-switch
          v-model="modelValue.performance.lazyLoad"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="setting-description">
          启用后延迟加载数据以提高初始加载速度
        </div>
      </el-form-item>

      <!-- Reset Button -->
      <el-form-item>
        <el-button @click="resetToDefaults" type="danger" plain>
          恢复默认设置
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Keyboard Shortcuts -->
    <div class="shortcuts-section">
      <h3>键盘快捷键</h3>
      <div class="shortcuts-grid">
        <div class="shortcut-item">
          <kbd class="shortcut-key">↑ ↓ ← →</kbd>
          <span class="shortcut-desc">方向键导航</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Tab</kbd>
          <span class="shortcut-desc">移到下一个单元格</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Shift + Tab</kbd>
          <span class="shortcut-desc">移到上一个单元格</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Enter</kbd>
          <span class="shortcut-desc">确认并移到下一行</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">F2</kbd>
          <span class="shortcut-desc">编辑单元格</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Esc</kbd>
          <span class="shortcut-desc">取消编辑</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Ctrl + A</kbd>
          <span class="shortcut-desc">全选</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Ctrl + C</kbd>
          <span class="shortcut-desc">复制</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Ctrl + V</kbd>
          <span class="shortcut-desc">粘贴</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Ctrl + Z</kbd>
          <span class="shortcut-desc">撤销</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Ctrl + Y</kbd>
          <span class="shortcut-desc">重做</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Ctrl + S</kbd>
          <span class="shortcut-desc">保存</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">Delete</kbd>
          <span class="shortcut-desc">清空单元格</span>
        </div>
        <div class="shortcut-item">
          <kbd class="shortcut-key">0-9</kbd>
          <span class="shortcut-desc">快速输入数字</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DEFAULT_SPREADSHEET_CONFIG } from '@/types/grade'

// Props
interface Props {
  modelValue: typeof DEFAULT_SPREADSHEET_CONFIG
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'update:modelValue', value: typeof DEFAULT_SPREADSHEET_CONFIG): void
}

const emit = defineEmits<Emits>()

// Methods
const updateValue = (key: string, value: any) => {
  const keys = key.split('.')
  const newConfig = JSON.parse(JSON.stringify(props.modelValue))

  let current: any = newConfig
  for (let i = 0; i < keys.length - 1; i++) {
    current = current[keys[i]]
  }

  current[keys[keys.length - 1]] = value
  emit('update:modelValue', newConfig)
}

const resetToDefaults = () => {
  emit('update:modelValue', { ...DEFAULT_SPREADSHEET_CONFIG })
}
</script>

<style scoped lang="scss">
.spreadsheet-settings {
  .setting-description {
    margin-top: 4px;
    font-size: 12px;
    color: #909399;
    line-height: 1.4;
  }

  .unit {
    margin-left: 8px;
    font-size: 13px;
    color: #606266;
  }

  .shortcuts-section {
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid #e4e7ed;

    h3 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    .shortcuts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 12px;

      .shortcut-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        background: #f8f9fa;
        border-radius: 6px;
        font-size: 13px;

        .shortcut-key {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 4px 8px;
          background: #fff;
          border: 1px solid #dcdfe6;
          border-radius: 4px;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 11px;
          color: #606266;
          min-width: 60px;
          text-align: center;
          box-shadow: 0 2px 0 #dcdfe6;
        }

        .shortcut-desc {
          color: #606266;
          flex: 1;
        }
      }
    }
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .spreadsheet-settings {
    :deep(.el-form-item__label) {
      font-size: 13px;
    }

    .shortcuts-grid {
      grid-template-columns: 1fr;

      .shortcut-item {
        padding: 12px;

        .shortcut-key {
          min-width: 50px;
          font-size: 10px;
          padding: 3px 6px;
        }

        .shortcut-desc {
          font-size: 12px;
        }
      }
    }
  }
}
</style>