from enum import Enum
from typing import Dict, List, Set

from app.models.user import UserRole


class Permission(Enum):
    """Permission definitions."""
    # User management permissions
    READ_USERS = "read_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    ACTIVATE_USERS = "activate_users"
    DEACTIVATE_USERS = "deactivate_users"

    # Course management permissions
    READ_COURSES = "read_courses"
    CREATE_COURSES = "create_courses"
    UPDATE_COURSES = "update_courses"
    DELETE_COURSES = "delete_courses"
    MANAGE_COURSE_ENROLLMENT = "manage_course_enrollment"

    # Grade management permissions
    READ_GRADES = "read_grades"
    CREATE_GRADES = "create_grades"
    UPDATE_GRADES = "update_grades"
    DELETE_GRADES = "delete_grades"
    IMPORT_GRADES = "import_grades"
    EXPORT_GRADES = "export_grades"

    # Enrollment permissions
    ENROLL_IN_COURSES = "enroll_in_courses"
    DROP_COURSES = "drop_courses"
    VIEW_ENROLLMENTS = "view_enrollments"

    # System permissions
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM = "manage_system"
    VIEW_ANALYTICS = "view_analytics"
    BACKUP_DATA = "backup_data"
    RESTORE_DATA = "restore_data"

    # Profile permissions
    UPDATE_OWN_PROFILE = "update_own_profile"
    VIEW_OWN_PROFILE = "view_own_profile"

    # Academic permissions
    VIEW_ACADEMIC_RECORDS = "view_academic_records"
    UPDATE_ACADEMIC_RECORDS = "update_academic_records"
    PRINT_TRANSCRIPTS = "print_transcripts"

    # Department permissions
    MANAGE_DEPARTMENT = "manage_department"
    VIEW_DEPARTMENT_STATS = "view_department_stats"


class RolePermissions:
    """Define permissions for each role."""

    # Student permissions
    STUDENT_PERMISSIONS: Set[Permission] = {
        Permission.VIEW_OWN_PROFILE,
        Permission.UPDATE_OWN_PROFILE,
        Permission.READ_COURSES,
        Permission.ENROLL_IN_COURSES,
        Permission.DROP_COURSES,
        Permission.VIEW_ENROLLMENTS,
        Permission.READ_GRADES,
        Permission.VIEW_ACADEMIC_RECORDS,
        Permission.PRINT_TRANSCRIPTS,
    }

    # Teacher permissions
    TEACHER_PERMISSIONS: Set[Permission] = {
        Permission.VIEW_OWN_PROFILE,
        Permission.UPDATE_OWN_PROFILE,
        Permission.READ_COURSES,
        Permission.CREATE_COURSES,
        Permission.UPDATE_COURSES,
        Permission.DELETE_COURSES,  # Only their own courses
        Permission.MANAGE_COURSE_ENROLLMENT,
        Permission.READ_GRADES,
        Permission.CREATE_GRADES,
        Permission.UPDATE_GRADES,
        Permission.DELETE_GRADES,
        Permission.IMPORT_GRADES,
        Permission.EXPORT_GRADES,
        Permission.VIEW_ENROLLMENTS,
        Permission.VIEW_DEPARTMENT_STATS,
        Permission.PRINT_TRANSCRIPTS,  # For their students
    }

    # Admin permissions (all permissions)
    ADMIN_PERMISSIONS: Set[Permission] = {
        # All permissions
        permission for permission in Permission
    }

    @classmethod
    def get_permissions_for_role(cls, role: UserRole) -> Set[Permission]:
        """Get all permissions for a given role."""
        role_permissions_map = {
            UserRole.STUDENT: cls.STUDENT_PERMISSIONS,
            UserRole.TEACHER: cls.TEACHER_PERMISSIONS,
            UserRole.ADMIN: cls.ADMIN_PERMISSIONS,
        }
        return role_permissions_map.get(role, set())

    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        return permission in cls.get_permissions_for_role(role)

    @classmethod
    def has_any_permission(cls, role: UserRole, permissions: List[Permission]) -> bool:
        """Check if a role has any of the specified permissions."""
        role_permissions = cls.get_permissions_for_role(role)
        return any(permission in role_permissions for permission in permissions)

    @classmethod
    def has_all_permissions(cls, role: UserRole, permissions: List[Permission]) -> bool:
        """Check if a role has all of the specified permissions."""
        role_permissions = cls.get_permissions_for_role(role)
        return all(permission in role_permissions for permission in permissions)


class ResourceOwnership:
    """Define resource ownership rules for fine-grained access control."""

    @staticmethod
    def can_access_course(user_role: UserRole, user_id: int, course_owner_id: int) -> bool:
        """Check if user can access a specific course."""
        # Admin can access all courses
        if user_role == UserRole.ADMIN:
            return True

        # Teachers can only access their own courses
        if user_role == UserRole.TEACHER:
            return user_id == course_owner_id

        # Students can access courses they're enrolled in
        # (This would require checking enrollment table)
        return False

    @staticmethod
    def can_access_grade(user_role: UserRole, user_id: int, grade_student_id: int, course_owner_id: int) -> bool:
        """Check if user can access a specific grade."""
        # Admin can access all grades
        if user_role == UserRole.ADMIN:
            return True

        # Students can only access their own grades
        if user_role == UserRole.STUDENT:
            return user_id == grade_student_id

        # Teachers can access grades for their courses
        if user_role == UserRole.TEACHER:
            return True  # Assuming course ownership is checked elsewhere

        return False

    @staticmethod
    def can_update_user(user_role: UserRole, current_user_id: int, target_user_id: int) -> bool:
        """Check if user can update another user."""
        # Admin can update all users
        if user_role == UserRole.ADMIN:
            return True

        # Users can update their own profile
        return current_user_id == target_user_id


class PermissionService:
    """Service for checking permissions and access control."""

    @staticmethod
    def check_permission(user_role: UserRole, permission: Permission) -> bool:
        """Check if user role has a specific permission."""
        return RolePermissions.has_permission(user_role, permission)

    @staticmethod
    def check_resource_access(
        user_role: UserRole,
        user_id: int,
        permission: Permission,
        resource_owner_id: int = None,
        additional_context: dict = None,
    ) -> bool:
        """Check if user can access a specific resource."""
        # First check basic permission
        if not RolePermissions.has_permission(user_role, permission):
            return False

        # Then check resource ownership if applicable
        if resource_owner_id is not None:
            if permission in [Permission.UPDATE_COURSES, Permission.DELETE_COURSES]:
                return ResourceOwnership.can_access_course(user_role, user_id, resource_owner_id)

            if permission in [Permission.UPDATE_USERS, Permission.DELETE_USERS]:
                return ResourceOwnership.can_update_user(user_role, user_id, resource_owner_id)

        return True

    @staticmethod
    def get_user_permissions(user_role: UserRole) -> List[str]:
        """Get list of permission strings for a user role."""
        permissions = RolePermissions.get_permissions_for_role(user_role)
        return [permission.value for permission in permissions]

    @staticmethod
    def get_accessible_resources(user_role: UserRole, resource_type: str) -> Dict:
        """Get accessible resources for a user role."""
        accessible_resources = {
            UserRole.STUDENT: {
                "courses": ["enrolled"],
                "grades": ["own"],
                "profile": ["own"],
            },
            UserRole.TEACHER: {
                "courses": ["own", "department"],
                "grades": ["course_students"],
                "profile": ["own"],
                "enrollments": ["course"],
            },
            UserRole.ADMIN: {
                "courses": ["all"],
                "grades": ["all"],
                "profile": ["all"],
                "enrollments": ["all"],
                "users": ["all"],
                "system": ["all"],
            },
        }
        return accessible_resources.get(user_role, {})