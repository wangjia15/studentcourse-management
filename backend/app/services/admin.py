from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import psutil
import os
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade
from app.models.audit_log import AuditLog
from app.schemas.admin import (
    SystemHealthResponse, SystemMetricsResponse, SystemStatus,
    BackupRequest, BackupResponse, BackupStatus,
    RestoreRequest, AuditLogResponse,
    SystemConfigResponse, SystemConfigUpdate
)


class AdminService:
    """管理服务类"""

    def get_system_health(self, db: Session) -> SystemHealthResponse:
        """获取系统健康状态"""

        # 检查数据库连接
        db_status = self._check_database_health(db)

        # 检查服务状态
        services_status = self._check_services_health()

        # 获取资源使用情况
        resource_usage = self._get_resource_usage()

        # 计算运行时间
        uptime_seconds = self._get_uptime()

        # 获取错误计数
        error_count_24h = self._get_error_count_24h(db)
        warning_count_24h = self._get_warning_count_24h(db)

        # 确定整体状态
        if db_status["status"] == "error" or services_status.get("api", {}).get("status") == "error":
            status = SystemStatus.ERROR
        elif db_status["status"] == "warning" or any(
            service.get("status") == "warning" for service in services_status.values()
        ):
            status = SystemStatus.WARNING
        else:
            status = SystemStatus.HEALTHY

        return SystemHealthResponse(
            status=status,
            timestamp=datetime.utcnow(),
            services=services_status,
            database_status=db_status,
            resource_usage=resource_usage,
            last_restart=None,  # 可以从配置或日志中获取
            uptime_seconds=uptime_seconds,
            error_count_24h=error_count_24h,
            warning_count_24h=warning_count_24h
        )

    def get_system_metrics(self, db: Session) -> SystemMetricsResponse:
        """获取系统性能指标"""

        # 获取系统资源指标
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # 获取网络IO
        net_io = psutil.net_io_counters()
        network_io = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }

        # 获取数据库指标
        database_metrics = self._get_database_metrics(db)

        # 获取API指标
        api_metrics = self._get_api_metrics(db)

        # 获取活跃会话数
        active_sessions = self._get_active_sessions_count(db)

        # 获取请求统计
        request_stats = self._get_request_statistics(db)

        return SystemMetricsResponse(
            timestamp=datetime.utcnow(),
            cpu_usage=cpu_usage,
            memory_usage={
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percentage": memory.percent
            },
            disk_usage={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percentage": (disk.used / disk.total) * 100
            },
            network_io=network_io,
            database_metrics=database_metrics,
            api_metrics=api_metrics,
            active_sessions=active_sessions,
            request_count_1h=request_stats["count_1h"],
            average_response_time=request_stats["avg_response_time"],
            error_rate_1h=request_stats["error_rate_1h"]
        )

    def get_system_logs(
        self,
        db: Session,
        level: Optional[str] = None,
        component: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取系统日志"""

        # 这里应该从日志系统查询，暂时返回模拟数据
        logs = []
        for i in range(limit):
            logs.append({
                "id": i + 1,
                "level": level or "INFO",
                "message": f"系统日志消息 {i + 1}",
                "timestamp": datetime.utcnow() - timedelta(minutes=i),
                "component": component or "API",
                "details": {"key": "value"}
            })

        return logs

    def create_backup_request(
        self,
        db: Session,
        request: BackupRequest,
        user_id: int
    ) -> BackupResponse:
        """创建备份请求"""

        backup = BackupResponse(
            id=self._generate_backup_id(),
            backup_type=request.backup_type,
            status=BackupStatus.PENDING,
            created_by=user_id,
            created_at=datetime.utcnow(),
            progress=0
        )

        # 这里应该保存到数据库
        return backup

    async def execute_backup(self, db: Session, backup_id: int):
        """执行备份（后台任务）"""

        try:
            # 更新状态为进行中
            self._update_backup_status(backup_id, BackupStatus.IN_PROGRESS, 10)

            # 执行备份逻辑
            backup_path = await self._perform_backup(backup_id)
            self._update_backup_status(backup_id, BackupStatus.IN_PROGRESS, 80)

            # 计算文件大小和校验和
            file_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
            checksum = self._calculate_file_checksum(backup_path)

            # 完成备份
            self._update_backup_status(
                backup_id,
                BackupStatus.COMPLETED,
                100,
                file_path=backup_path,
                file_size=file_size,
                checksum=checksum
            )

        except Exception as e:
            self._update_backup_status(
                backup_id,
                BackupStatus.FAILED,
                0,
                error_message=str(e)
            )

    def list_backups(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[BackupResponse]:
        """获取备份列表"""

        # 这里应该从数据库查询，暂时返回模拟数据
        backups = []
        for i in range(limit):
            backup = BackupResponse(
                id=i + 1,
                backup_type="full",
                status=BackupStatus.COMPLETED if i % 2 == 0 else BackupStatus.FAILED,
                created_by=1,
                created_at=datetime.utcnow() - timedelta(days=i),
                completed_at=datetime.utcnow() - timedelta(days=i) if i % 2 == 0 else None,
                file_size=1024 * 1024 * (i + 1) if i % 2 == 0 else None
            )
            backups.append(backup)

        return backups

    def get_backup(self, db: Session, backup_id: int) -> Optional[BackupResponse]:
        """获取备份信息"""
        # 这里应该从数据库查询
        return None

    def create_restore_task(
        self,
        db: Session,
        request: RestoreRequest,
        user_id: int
    ) -> Dict[str, Any]:
        """创建恢复任务"""

        # 验证备份文件
        backup = self.get_backup(db, request.backup_id)
        if not backup:
            raise ValueError("备份文件不存在")

        if backup.status != BackupStatus.COMPLETED:
            raise ValueError("备份文件未完成，无法恢复")

        # 创建恢复任务
        restore_task = {
            "id": self._generate_restore_id(),
            "backup_id": request.backup_id,
            "restore_type": request.restore_type,
            "status": "pending",
            "created_by": user_id,
            "created_at": datetime.utcnow()
        }

        return restore_task

    def _perform_restore(self, restore_task_id: int):
        """执行恢复操作"""
        # 这里应该实现实际的恢复逻辑
        import time
        time.sleep(3)

    async def execute_restore(self, db: Session, restore_task_id: int):
        """执行恢复（后台任务）"""

        try:
            # 执行恢复逻辑
            import asyncio
            await asyncio.get_event_loop().run_in_executor(
                None, self._perform_restore, restore_task_id
            )

        except Exception as e:
            # 记录错误
            pass

    def get_audit_logs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[AuditLogResponse]:
        """获取审计日志"""

        # 构建查询条件
        conditions = []

        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        # 查询审计日志
        query = db.query(AuditLog).join(User)
        if conditions:
            query = query.filter(and_(*conditions))

        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                username=log.user.username,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                request_method=log.request_method,
                request_path=log.request_path,
                response_status=log.response_status,
                old_values=log.old_values,
                new_values=log.new_values,
                created_at=log.created_at
            )
            for log in logs
        ]

    def list_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        role: Optional[UserRole] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """管理员获取用户列表"""

        query = db.query(User)

        # 应用过滤条件
        if role:
            query = query.filter(User.role == role)
        if department:
            query = query.filter(User.department == department)
        if status:
            query = query.filter(User.status == status)
        if search:
            query = query.filter(
                or_(
                    User.full_name.contains(search),
                    User.email.contains(search),
                    User.username.contains(search),
                    User.student_id.contains(search)
                )
            )

        users = query.offset(skip).limit(limit).all()

        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "department": user.department,
                "status": user.status.value,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            for user in users
        ]

    def create_user(self, db: Session, user_data: Dict[str, Any], admin_id: int) -> Dict[str, Any]:
        """管理员创建用户"""

        # 这里应该实现用户创建逻辑
        # 包括密码哈希、默认值设置等

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            department=user_data["department"],
            password_hash="hashed_password",  # 需要实际哈希
            created_at=datetime.utcnow()
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # 记录审计日志
        self._log_admin_action(db, admin_id, "CREATE_USER", "user", user.id, {}, user_data)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "created_at": user.created_at
        }

    def update_user(self, db: Session, user_id: int, user_data: Dict[str, Any], admin_id: int) -> Dict[str, Any]:
        """管理员更新用户"""

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        old_values = {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "department": user.department,
            "is_active": user.is_active
        }

        # 更新字段
        for key, value in user_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        # 记录审计日志
        new_values = {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "department": user.department,
            "is_active": user.is_active
        }

        self._log_admin_action(db, admin_id, "UPDATE_USER", "user", user_id, old_values, new_values)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "updated_at": user.updated_at
        }

    def delete_user(self, db: Session, user_id: int, admin_id: int):
        """管理员删除用户"""

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 记录删除前的信息
        old_values = {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }

        # 删除用户（软删除）
        user.is_active = False
        user.status = "inactive"
        user.updated_at = datetime.utcnow()
        db.commit()

        # 记录审计日志
        self._log_admin_action(db, admin_id, "DELETE_USER", "user", user_id, old_values, {})

    def get_system_config(self, db: Session) -> List[SystemConfigResponse]:
        """获取系统配置"""

        # 这里应该从配置表查询，暂时返回默认配置
        default_configs = [
            {
                "id": 1,
                "config_key": "max_file_size",
                "config_value": "52428800",
                "config_type": "integer",
                "description": "最大文件上传大小（字节）",
                "is_sensitive": False,
                "is_public": False,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "config_key": "session_timeout",
                "config_value": "3600",
                "config_type": "integer",
                "description": "会话超时时间（秒）",
                "is_sensitive": False,
                "is_public": False,
                "created_at": datetime.utcnow()
            }
        ]

        return [SystemConfigResponse(**config) for config in default_configs]

    def update_system_config(self, db: Session, config_update: SystemConfigUpdate, admin_id: int) -> SystemConfigResponse:
        """更新系统配置"""

        # 这里应该更新配置表
        # 暂时返回模拟数据

        self._log_admin_action(db, admin_id, "UPDATE_CONFIG", "config", 1, {}, config_update.dict())

        return SystemConfigResponse(
            id=1,
            config_key="max_file_size",
            config_value=config_update.config_value,
            config_type="integer",
            description="最大文件上传大小（字节）",
            is_sensitive=False,
            is_public=False,
            updated_by=admin_id,
            updated_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

    def toggle_maintenance_mode(self, db: Session, enable: bool, message: Optional[str], admin_id: int):
        """切换维护模式"""

        # 这里应该更新系统配置
        self._log_admin_action(
            db, admin_id, "TOGGLE_MAINTENANCE", "system", 0,
            {"maintenance_enabled": False},
            {"maintenance_enabled": enable, "message": message}
        )

    def clear_cache(self, db: Session, cache_type: Optional[str], admin_id: int) -> Dict[str, Any]:
        """清除系统缓存"""

        # 这里应该实现实际的缓存清除逻辑
        cleared_caches = []

        if not cache_type or cache_type == "all":
            cleared_caches.extend(["user_cache", "course_cache", "grade_cache"])
        elif cache_type == "user":
            cleared_caches.append("user_cache")
        elif cache_type == "course":
            cleared_caches.append("course_cache")
        elif cache_type == "grade":
            cleared_caches.append("grade_cache")

        self._log_admin_action(
            db, admin_id, "CLEAR_CACHE", "cache", 0,
            {},
            {"cleared_caches": cleared_caches, "cache_type": cache_type}
        )

        return {
            "message": "缓存清除成功",
            "cleared_caches": cleared_caches,
            "cache_type": cache_type or "all"
        }

    # 私有辅助方法

    def _check_database_health(self, db: Session) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            # 执行简单查询测试连接
            db.execute("SELECT 1")
            return {"status": "healthy", "message": "数据库连接正常"}
        except Exception as e:
            return {"status": "error", "message": f"数据库连接失败: {str(e)}"}

    def _check_services_health(self) -> Dict[str, Dict[str, Any]]:
        """检查服务健康状态"""
        return {
            "api": {"status": "healthy", "message": "API服务正常"},
            "database": {"status": "healthy", "message": "数据库服务正常"},
            "cache": {"status": "healthy", "message": "缓存服务正常"}
        }

    def _get_resource_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": memory.percent,
            "disk_percent": (disk.used / disk.total) * 100,
            "memory_available_gb": memory.available / (1024**3),
            "disk_free_gb": disk.free / (1024**3)
        }

    def _get_uptime(self) -> int:
        """获取系统运行时间（秒）"""
        return int(psutil.boot_time())

    def _get_error_count_24h(self, db: Session) -> int:
        """获取24小时内错误数量"""
        # 这里应该从日志表查询
        return 0

    def _get_warning_count_24h(self, db: Session) -> int:
        """获取24小时内警告数量"""
        # 这里应该从日志表查询
        return 0

    def _get_database_metrics(self, db: Session) -> Dict[str, Any]:
        """获取数据库指标"""
        return {
            "active_connections": 5,
            "total_connections": 10,
            "query_count_1h": 100,
            "slow_queries_1h": 2,
            "database_size": "1.2GB"
        }

    def _get_api_metrics(self, db: Session) -> Dict[str, Any]:
        """获取API指标"""
        return {
            "requests_per_minute": 50,
            "average_response_time": 150,
            "error_rate": 0.02,
            "active_endpoints": 25
        }

    def _get_active_sessions_count(self, db: Session) -> int:
        """获取活跃会话数"""
        # 这里应该从会话表查询
        return 15

    def _get_request_statistics(self, db: Session) -> Dict[str, Any]:
        """获取请求统计"""
        return {
            "count_1h": 3000,
            "avg_response_time": 150.5,
            "error_rate_1h": 0.01
        }

    def _generate_backup_id(self) -> int:
        """生成备份ID"""
        import uuid
        return int(uuid.uuid4().hex[:8], 16)

    def _generate_restore_id(self) -> int:
        """生成恢复ID"""
        import uuid
        return int(uuid.uuid4().hex[:8], 16)

    def _update_backup_status(
        self,
        backup_id: int,
        status: BackupStatus,
        progress: int,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """更新备份状态"""
        # 这里应该更新数据库记录
        pass

    async def _perform_backup(self, backup_id: int) -> str:
        """执行备份操作"""
        import asyncio
        # 这里应该实现实际的备份逻辑
        backup_path = f"/tmp/backup_{backup_id}.zip"
        # 模拟备份过程
        await asyncio.sleep(2)
        return backup_path

    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def _perform_restore(self, restore_task_id: int):
        """执行恢复操作"""
        # 这里应该实现实际的恢复逻辑
        await asyncio.sleep(3)

    def _log_admin_action(
        self,
        db: Session,
        admin_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any]
    ):
        """记录管理员操作日志"""
        # 这里应该创建审计日志记录
        pass