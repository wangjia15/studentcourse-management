import { DirectiveBinding } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface PermissionBinding {
  value: {
    permissions?: string | string[]
    roles?: string | string[]
    requireAll?: boolean
    mode?: 'hide' | 'disable' | 'remove'
  }
}

const permissionDirective = {
  mounted(el: HTMLElement, binding: DirectiveBinding<PermissionBinding['value']>) {
    checkPermission(el, binding)
  },
  updated(el: HTMLElement, binding: DirectiveBinding<PermissionBinding['value']>) {
    checkPermission(el, binding)
  },
}

function checkPermission(el: HTMLElement, binding: DirectiveBinding<PermissionBinding['value']>) {
  const authStore = useAuthStore()
  const config = binding.value || {}

  const {
    permissions,
    roles,
    requireAll = false,
    mode = 'hide'
  } = config

  let hasAccess = true

  // If user is not authenticated, deny access
  if (!authStore.isAuthenticated) {
    hasAccess = false
  } else {
    // Check role permissions
    if (roles) {
      const roleArray = Array.isArray(roles) ? roles : [roles]
      const userRole = authStore.userRole

      if (requireAll) {
        // User must have all specified roles
        hasAccess = hasAccess && userRole && roleArray.includes(userRole)
      } else {
        // User needs at least one of the specified roles
        hasAccess = hasAccess && userRole && roleArray.includes(userRole)
      }
    }

    // Check specific permissions
    if (permissions && hasAccess) {
      const permissionArray = Array.isArray(permissions) ? permissions : [permissions]

      if (requireAll) {
        // User must have all specified permissions
        hasAccess = permissionArray.every(permission =>
          authStore.hasPermission(permission)
        )
      } else {
        // User needs at least one of the specified permissions
        hasAccess = permissionArray.some(permission =>
          authStore.hasPermission(permission)
        )
      }
    }
  }

  // Apply the appropriate mode based on access
  if (!hasAccess) {
    switch (mode) {
      case 'disable':
        el.style.pointerEvents = 'none'
        el.style.opacity = '0.5'
        el.setAttribute('aria-disabled', 'true')
        if (el instanceof HTMLButtonElement || el instanceof HTMLInputElement) {
          el.disabled = true
        }
        break
      case 'remove':
        el.remove()
        break
      case 'hide':
      default:
        el.style.display = 'none'
        el.setAttribute('aria-hidden', 'true')
        break
    }
  } else {
    // Reset element styles and attributes when access is granted
    el.style.display = ''
    el.style.pointerEvents = ''
    el.style.opacity = ''
    el.removeAttribute('aria-disabled')
    el.removeAttribute('aria-hidden')
    if (el instanceof HTMLButtonElement || el instanceof HTMLInputElement) {
      el.disabled = false
    }
  }
}

export default permissionDirective