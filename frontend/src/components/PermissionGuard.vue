<template>
  <div v-if="hasAccess">
    <slot />
  </div>
  <div v-else-if="$slots.fallback">
    <slot name="fallback" />
  </div>
  <div v-else-if="showUnauthorizedMessage" class="text-gray-500 text-center py-4">
    <Lock class="h-12 w-12 mx-auto mb-2 text-gray-400" />
    <p class="text-sm">您没有权限访问此内容</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { Lock } from 'lucide-vue-next'

interface Props {
  permissions?: string | string[]
  roles?: string | string[]
  requireAll?: boolean
  showUnauthorizedMessage?: boolean
  fallback?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  requireAll: false,
  showUnauthorizedMessage: true,
})

const authStore = useAuthStore()

const hasAccess = computed(() => {
  // If user is not authenticated, deny access
  if (!authStore.isAuthenticated) {
    return false
  }

  // Check role permissions
  if (props.roles) {
    const roles = Array.isArray(props.roles) ? props.roles : [props.roles]
    const hasRole = roles.includes(authStore.userRole || '')

    if (props.requireAll) {
      // User must have all specified roles
      if (!hasRole) return false
    } else {
      // User needs at least one of the specified roles
      if (!hasRole) return false
    }
  }

  // Check specific permissions
  if (props.permissions) {
    const permissions = Array.isArray(props.permissions) ? props.permissions : [props.permissions]

    if (props.requireAll) {
      // User must have all specified permissions
      const hasAllPermissions = permissions.every(permission =>
        authStore.hasPermission(permission)
      )
      if (!hasAllPermissions) return false
    } else {
      // User needs at least one of the specified permissions
      const hasAnyPermission = permissions.some(permission =>
        authStore.hasPermission(permission)
      )
      if (!hasAnyPermission) return false
    }
  }

  // If no specific permissions or roles required, grant access to authenticated users
  return true
})
</script>