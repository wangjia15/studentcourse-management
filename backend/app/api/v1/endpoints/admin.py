from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.admin import (
    SystemHealthResponse,
    SystemMetricsResponse,
    BackupRequest,
    BackupResponse,
    RestoreRequest,
    AuditLogResponse,
    SystemConfigResponse,
    SystemConfigUpdate,
)
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.admin import AdminService
from app.services.user import UserService

router = APIRouter()
admin_service = AdminService()
user_service = UserService()


def admin_required(current_user: User = Depends(get_current_user)):
    """管理员权限检查装饰器"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """获取系统健康状态"""
    try:
        health = admin_service.get_system_health(db)
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统健康状态失败: {str(e)}")


@router.get("/system/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """获取系统性能指标"""
    try:
        metrics = admin_service.get_system_metrics(db)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")


@router.get("/system/logs", response_model=List[dict])
async def get_system_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    component: Optional[str] = Query(None, description="组件过滤"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回日志条数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """获取系统日志"""
    try:
        logs = admin_service.get_system_logs(
            db, level, component, start_time, end_time, limit
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统日志失败: {str(e)}")


@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    backup_request: BackupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """创建数据备份"""
    try:
        # 创建备份记录
        backup = admin_service.create_backup_request(db, backup_request, current_user.id)

        # 添加后台任务执行备份
        background_tasks.add_task(
            admin_service.execute_backup,
            db,
            backup.id
        )

        return backup
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")


@router.get("/backup/list", response_model=List[BackupResponse])
async def list_backups(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    status: Optional[str] = Query(None, description="备份状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """获取备份列表"""
    try:
        backups = admin_service.list_backups(db, skip, limit, status)
        return backups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


@router.post("/restore")
async def restore_backup(
    restore_request: RestoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """恢复数据备份"""
    try:
        # 验证备份文件
        backup = admin_service.get_backup(db, restore_request.backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="备份文件不存在")

        if backup.status != "completed":
            raise HTTPException(status_code=400, detail="备份文件未完成，无法恢复")

        # 创建恢复任务
        restore_task = admin_service.create_restore_task(
            db, restore_request, current_user.id
        )

        # 添加后台任务执行恢复
        background_tasks.add_task(
            admin_service.execute_restore,
            db,
            restore_task.id
        )

        return {"message": "数据恢复任务已启动", "task_id": restore_task.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建恢复任务失败: {str(e)}")


@router.get("/audit-log", response_model=List[AuditLogResponse])
async def get_audit_log(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    action: Optional[str] = Query(None, description="操作类型过滤"),
    resource_type: Optional[str] = Query(None, description="资源类型过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """获取审计日志"""
    try:
        audit_logs = admin_service.get_audit_logs(
            db, skip, limit, user_id, action, resource_type, start_date, end_date
        )
        return audit_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审计日志失败: {str(e)}")


@router.get("/users", response_model=List[UserResponse])
async def admin_list_users(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    role: Optional[UserRole] = Query(None, description="角色过滤"),
    department: Optional[str] = Query(None, description="院系过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """管理员获取用户列表"""
    try:
        users = admin_service.list_users(
            db, skip, limit, role, department, status, search
        )
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.post("/users", response_model=UserResponse)
async def admin_create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """管理员创建用户"""
    try:
        # 检查用户是否已存在
        existing_user = user_service.get_user_by_email(db, email=user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已存在")

        existing_username = user_service.get_user_by_username(db, username=user_data.username)
        if existing_username:
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 创建用户
        user = admin_service.create_user(db, user_data, current_user.id)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")


@router.put("/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """管理员更新用户"""
    try:
        # 检查用户是否存在
        user = user_service.get_user(db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 更新用户
        updated_user = admin_service.update_user(db, user_id, user_data, current_user.id)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """管理员删除用户"""
    try:
        # 检查用户是否存在
        user = user_service.get_user(db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 不能删除自己
        if user_id == current_user.id:
            raise HTTPException(status_code=400, detail="不能删除自己的账户")

        # 删除用户
        admin_service.delete_user(db, user_id, current_user.id)
        return {"message": "用户删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")


@router.get("/system/config", response_model=SystemConfigResponse)
async def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """获取系统配置"""
    try:
        config = admin_service.get_system_config(db)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")


@router.put("/system/config", response_model=SystemConfigResponse)
async def update_system_config(
    config_update: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """更新系统配置"""
    try:
        config = admin_service.update_system_config(db, config_update, current_user.id)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新系统配置失败: {str(e)}")


@router.post("/system/maintenance")
async def toggle_maintenance_mode(
    enable: bool = Query(..., description="是否启用维护模式"),
    message: Optional[str] = Query(None, description="维护消息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """切换维护模式"""
    try:
        admin_service.toggle_maintenance_mode(db, enable, message, current_user.id)
        return {"message": f"维护模式已{'启用' if enable else '禁用'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换维护模式失败: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = Query(None, description="缓存类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    """清除系统缓存"""
    try:
        result = admin_service.clear_cache(db, cache_type, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")