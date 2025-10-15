export interface User {
  id: number
  email: string
  username: string
  full_name: string
  role: 'admin' | 'teacher' | 'student'
  is_active: boolean
  is_verified: boolean
  student_id?: string
  teacher_id?: string
  department?: string
  major?: string
  class_name?: string
  enrollment_year?: string
  graduation_year?: string
  created_at: string
  updated_at: string
  last_login_at?: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  full_name: string
  password: string
  role: 'admin' | 'teacher' | 'student'
  is_active?: boolean
  student_id?: string
  teacher_id?: string
  department?: string
  major?: string
  class_name?: string
  enrollment_year?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
}

export interface UserPermissions {
  role: string
  permissions: string[]
  accessible_resources: Record<string, string[]>
}

// Form validation rules
export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  message: string
}

export interface FormField {
  value: string
  error: string
  rules: ValidationRule[]
}

export interface LoginForm {
  username: FormField
  password: FormField
  remember: boolean
}

export interface RegisterForm {
  email: FormField
  username: FormField
  full_name: FormField
  password: FormField
  confirmPassword: FormField
  role: 'admin' | 'teacher' | 'student'
  student_id?: FormField
  teacher_id?: FormField
  department?: FormField
  major?: FormField
  class_name?: FormField
  enrollment_year?: FormField
}

export interface PasswordChangeForm {
  currentPassword: FormField
  newPassword: FormField
  confirmPassword: FormField
}

export interface PasswordResetForm {
  email: FormField
}

export interface PasswordResetConfirmForm {
  token: string
  newPassword: FormField
  confirmPassword: FormField
}