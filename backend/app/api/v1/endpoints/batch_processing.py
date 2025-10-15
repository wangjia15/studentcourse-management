import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import pandas as pd
from io import BytesIO

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.services.batch_processing import BatchProcessingService
from app.schemas.batch_processing import (
    FileUploadRequest,
    BatchProcessingResponse,
    TemplateRequest,
    ExportRequest,
    TaskStatusResponse,
    ImportPreviewResponse,
    ProcessingOptions,
    BatchStatisticsResponse,
)
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter()

# 全局任务存储 (在生产环境中应该使用Redis或数据库)
active_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/upload", response_model=BatchProcessingResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: str = None,  # JSON string of FileUploadRequest
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传并处理批量文件"""
    try:
        # 检查权限
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=403,
                detail="只有管理员和教师可以上传批量文件"
            )

        # 检查文件大小
        if file.size and file.size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=413,
                detail="文件大小超过限制(100MB)"
            )

        # 读取文件内容
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="文件内容为空"
            )

        # 创建任务ID
        task_id = str(uuid.uuid4())

        # 初始化任务状态
        task_info = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0.0,
            "current_stage": "初始化",
            "started_at": datetime.utcnow(),
            "user_id": current_user.id,
            "filename": file.filename,
        }
        active_tasks[task_id] = task_info

        # 启动后台处理任务
        background_tasks.add_task(
            process_file_background,
            task_id,
            file_content,
            file.filename,
            current_user.id,
            db,
            options
        )

        # 返回任务信息
        return BatchProcessingResponse(
            task_id=task_id,
            status="pending",
            total_records=0,
            processed_records=0,
            successful_records=0,
            failed_records=0,
            duplicate_records=0,
            processing_time=0.0,
            created_at=datetime.utcnow(),
            file_path=file.filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取任务状态"""
    try:
        # 检查任务是否存在
        if task_id not in active_tasks:
            raise HTTPException(
                status_code=404,
                detail="任务不存在"
            )

        task_info = active_tasks[task_id]

        # 检查权限
        if (current_user.role != UserRole.ADMIN and
            task_info.get("user_id") != current_user.id):
            raise HTTPException(
                status_code=403,
                detail="无权访问此任务"
            )

        return TaskStatusResponse(
            task_id=task_id,
            status=task_info.get("status", "pending"),
            progress=task_info.get("progress", 0.0),
            current_stage=task_info.get("current_stage", ""),
            estimated_remaining_time=task_info.get("estimated_remaining_time"),
            error_message=task_info.get("error_message"),
            result=task_info.get("result")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task status failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.delete("/task/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """取消任务"""
    try:
        # 检查任务是否存在
        if task_id not in active_tasks:
            raise HTTPException(
                status_code=404,
                detail="任务不存在"
            )

        task_info = active_tasks[task_id]

        # 检查权限
        if (current_user.role != UserRole.ADMIN and
            task_info.get("user_id") != current_user.id):
            raise HTTPException(
                status_code=403,
                detail="无权取消此任务"
            )

        # 检查任务状态
        if task_info.get("status") in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail="任务已完成或已取消，无法再次取消"
            )

        # 更新任务状态
        task_info["status"] = "cancelled"
        task_info["cancelled_at"] = datetime.utcnow()

        return {"message": "任务已取消"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel task failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"取消任务失败: {str(e)}"
        )


@router.get("/template/{template_type}")
async def download_template(
    template_type: str = "basic",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """下载导入模板"""
    try:
        # 检查权限
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=403,
                detail="只有管理员和教师可以下载模板"
            )

        service = BatchProcessingService(db)
        df = await service.get_processing_template(template_type)

        # 创建Excel文件
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='导入模板', index=False)

        output.seek(0)

        filename = f"成绩导入模板_{template_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template download failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"模板下载失败: {str(e)}"
        )


@router.post("/export")
async def export_data(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """导出数据"""
    try:
        # 检查权限
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=403,
                detail="只有管理员和教师可以导出数据"
            )

        service = BatchProcessingService(db)

        if request.format == "excel":
            output = await service.export_grades_to_excel(
                course_id=request.course_id,
                academic_year=request.academic_year,
                semester=request.semester,
                grade_type=request.grade_type
            )

            filename = f"成绩导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif request.format == "pdf":
            output = await service.generate_pdf_report(
                course_id=request.course_id,
                academic_year=request.academic_year,
                semester=request.semester,
                grade_type=request.grade_type
            )

            filename = f"成绩报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            return StreamingResponse(
                output,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的导出格式: {request.format}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"数据导出失败: {str(e)}"
        )


@router.get("/tasks")
async def list_tasks(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """列出任务"""
    try:
        # 检查权限
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="只有管理员可以查看所有任务"
            )

        # 过滤任务
        tasks = []
        for task_id, task_info in active_tasks.items():
            if status and task_info.get("status") != status:
                continue

            tasks.append({
                "task_id": task_id,
                "status": task_info.get("status"),
                "progress": task_info.get("progress", 0.0),
                "current_stage": task_info.get("current_stage"),
                "filename": task_info.get("filename"),
                "started_at": task_info.get("started_at"),
                "user_id": task_info.get("user_id")
            })

        # 排序和分页
        tasks.sort(key=lambda x: x.get("started_at", datetime.min), reverse=True)
        paginated_tasks = tasks[offset:offset + limit]

        return {
            "tasks": paginated_tasks,
            "total": len(tasks),
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List tasks failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/statistics", response_model=BatchStatisticsResponse)
async def get_batch_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取批量处理统计信息"""
    try:
        # 检查权限
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="只有管理员可以查看统计信息"
            )

        # 计算统计信息
        total_files = len(active_tasks)
        total_records = sum(
            task.get("result", {}).get("total_records", 0)
            for task in active_tasks.values()
            if task.get("result")
        )

        successful_tasks = sum(
            1 for task in active_tasks.values()
            if task.get("status") == "completed"
        )

        success_rate = successful_tasks / total_files if total_files > 0 else 0.0

        processing_times = [
            task.get("result", {}).get("processing_time", 0)
            for task in active_tasks.values()
            if task.get("result")
        ]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

        # 最近活动
        recent_tasks = sorted(
            active_tasks.items(),
            key=lambda x: x[1].get("started_at", datetime.min),
            reverse=True
        )[:10]

        recent_activities = []
        for task_id, task_info in recent_tasks:
            recent_activities.append({
                "task_id": task_id,
                "filename": task_info.get("filename"),
                "status": task_info.get("status"),
                "started_at": task_info.get("started_at")
            })

        # 错误分布
        error_distribution = {}
        for task_info in active_tasks.values():
            result = task_info.get("result")
            if result and result.get("errors"):
                for error in result["errors"]:
                    field = error.get("field", "unknown")
                    error_distribution[field] = error_distribution.get(field, 0) + 1

        return BatchStatisticsResponse(
            total_files_processed=total_files,
            total_records_processed=total_records,
            success_rate=success_rate,
            average_processing_time=avg_processing_time,
            recent_activities=recent_activities,
            error_distribution=error_distribution
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get statistics failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.post("/preview")
async def preview_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """预览文件内容"""
    try:
        # 检查权限
        if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise HTTPException(
                status_code=403,
                detail="只有管理员和教师可以预览文件"
            )

        # 读取文件内容
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="文件内容为空"
            )

        # 预览文件
        service = BatchProcessingService(db)

        # 检测文件格式
        from app.services.batch_processing import FileProcessor
        file_processor = FileProcessor()
        file_format = await file_processor.detect_file_format(file_content)

        # 读取文件内容 (限制行数以避免内存问题)
        if file_format == "excel":
            df = await file_processor.read_excel_file(file_content)
            if isinstance(df, dict):
                df = list(df.values())[0]  # 取第一个sheet
        elif file_format == "csv":
            df = await file_processor.read_csv_file(file_content)
        else:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件格式"
            )

        # 限制预览行数
        sample_rows = min(10, len(df))
        sample_data = df.head(sample_rows).fillna("").to_dict('records')

        # 列映射
        column_mapping = {col: col for col in df.columns}

        # 潜在问题检测
        potential_issues = []
        if len(df) > 10000:
            potential_issues.append(f"文件包含 {len(df)} 行数据，处理可能需要较长时间")

        required_columns = ['学号', '课程代码', '分数']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            potential_issues.append(f"缺少必要列: {', '.join(missing_columns)}")

        return ImportPreviewResponse(
            file_info={
                "filename": file.filename,
                "format": file_format,
                "size": len(file_content),
                "total_rows": len(df),
                "columns": list(df.columns)
            },
            column_mapping=column_mapping,
            sample_data=sample_data,
            detected_format=file_format,
            estimated_records=len(df),
            potential_issues=potential_issues
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File preview failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文件预览失败: {str(e)}"
        )


@router.get("/error-report/{task_id}")
async def download_error_report(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载错误报告"""
    try:
        # 检查任务是否存在
        if task_id not in active_tasks:
            raise HTTPException(
                status_code=404,
                detail="任务不存在"
            )

        task_info = active_tasks[task_id]

        # 检查权限
        if (current_user.role != UserRole.ADMIN and
            task_info.get("user_id") != current_user.id):
            raise HTTPException(
                status_code=403,
                detail="无权访问此任务报告"
            )

        result = task_info.get("result")
        if not result or not result.get("errors"):
            raise HTTPException(
                status_code=404,
                detail="没有错误报告可下载"
            )

        # 生成错误报告
        service = BatchProcessingService(None)  # 不需要数据库连接
        output = await service.generate_error_report(result)

        filename = f"错误报告_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error report download failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"错误报告下载失败: {str(e)}"
        )


async def process_file_background(
    task_id: str,
    file_content: bytes,
    filename: str,
    user_id: int,
    db: AsyncSession,
    options: str
):
    """后台处理文件"""
    try:
        # 更新任务状态
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "processing",
                "progress": 10.0,
                "current_stage": "正在处理文件"
            })

        # 解析选项
        import json
        processing_options = {}
        if options:
            try:
                processing_options = json.loads(options)
            except:
                logger.warning("Failed to parse processing options, using defaults")

        # 创建数据库会话
        from app.db.session_helper import get_db_session
        async with get_db_session() as db_session:
            # 处理文件
            service = BatchProcessingService(db_session)
            result = await service.process_file_upload(
                file_content, filename, user_id, processing_options
            )

            # 更新任务结果
            if task_id in active_tasks:
                active_tasks[task_id].update({
                    "status": "completed",
                    "progress": 100.0,
                    "current_stage": "处理完成",
                    "result": result,
                    "completed_at": datetime.utcnow()
                })

    except Exception as e:
        logger.error(f"Background processing failed for task {task_id}: {e}")

        # 更新任务状态为失败
        if task_id in active_tasks:
            active_tasks[task_id].update({
                "status": "failed",
                "current_stage": "处理失败",
                "error_message": str(e),
                "completed_at": datetime.utcnow()
            })