from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.reports import (
    ReportRequest,
    ReportResponse,
    ReportStatusResponse,
    TranscriptRequest,
    ClassSummaryRequest,
    GradeAnalysisRequest,
    ReportDownloadResponse,
)
from app.services.reports import ReportsService

router = APIRouter()
reports_service = ReportsService()


@router.post("/transcript", response_model=ReportResponse)
async def request_transcript(
    request: TranscriptRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """请求生成成绩单"""
    # 权限检查：学生只能请求自己的成绩单，教师和管理员可以请求其他人的
    if (current_user.role == UserRole.STUDENT and
        request.student_id != current_user.id):
        raise HTTPException(status_code=403, detail="只能请求自己的成绩单")

    try:
        # 创建报告请求
        report = reports_service.create_transcript_request(
            db, request, current_user.id
        )

        # 添加后台任务生成报告
        background_tasks.add_task(
            reports_service.generate_transcript,
            db,
            report.id
        )

        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/class-summary", response_model=ReportResponse)
async def request_class_summary(
    request: ClassSummaryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """请求生成班级汇总报告"""
    # 权限检查：只有管理员和教师可以请求班级汇总
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="无权限请求班级汇总报告")

    # 教师只能请求自己授课班级的报告
    if (current_user.role == UserRole.TEACHER and
        not reports_service.can_teacher_access_class(db, current_user.id, request.class_id)):
        raise HTTPException(status_code=403, detail="无权限请求该班级的汇总报告")

    try:
        # 创建报告请求
        report = reports_service.create_class_summary_request(
            db, request, current_user.id
        )

        # 添加后台任务生成报告
        background_tasks.add_task(
            reports_service.generate_class_summary,
            db,
            report.id
        )

        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/grade-analysis", response_model=ReportResponse)
async def request_grade_analysis(
    request: GradeAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """请求生成成绩分析报告"""
    # 权限检查：只有管理员和教师可以请求成绩分析
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="无权限请求成绩分析报告")

    # 根据分析类型检查权限
    if not reports_service.can_access_grade_analysis(db, current_user.id, request):
        raise HTTPException(status_code=403, detail="无权限请求该成绩分析")

    try:
        # 创建报告请求
        report = reports_service.create_grade_analysis_request(
            db, request, current_user.id
        )

        # 添加后台任务生成报告
        background_tasks.add_task(
            reports_service.generate_grade_analysis,
            db,
            report.id
        )

        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/download/{report_id}", response_model=ReportDownloadResponse)
async def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载报告文件"""
    # 检查报告是否存在和权限
    report = reports_service.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 权限检查：只有报告创建者和管理员可以下载
    if (report.requested_by != current_user.id and
        current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="无权限下载该报告")

    # 检查报告状态
    if report.status != "completed":
        raise HTTPException(status_code=400, detail="报告尚未生成完成")

    try:
        download_info = reports_service.get_report_download_info(db, report_id)
        return download_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{report_id}", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报告生成状态"""
    # 检查报告是否存在和权限
    report = reports_service.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 权限检查：只有报告创建者和管理员可以查看状态
    if (report.requested_by != current_user.id and
        current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="无权限查看该报告状态")

    return {
        "report_id": report.id,
        "status": report.status,
        "progress": report.progress,
        "created_at": report.created_at,
        "completed_at": report.completed_at,
        "error_message": report.error_message
    }


@router.get("/my-reports", response_model=List[ReportResponse])
async def get_my_reports(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回记录数"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的报告列表"""
    try:
        reports = reports_service.get_user_reports(
            db, current_user.id, skip, limit, status_filter
        )
        return reports
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除报告"""
    # 检查报告是否存在和权限
    report = reports_service.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 权限检查：只有报告创建者和管理员可以删除
    if (report.requested_by != current_user.id and
        current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="无权限删除该报告")

    try:
        reports_service.delete_report(db, report_id)
        return {"message": "报告删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/all-reports", response_model=List[ReportResponse])
async def admin_get_all_reports(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    user_filter: Optional[int] = Query(None, description="用户ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """管理员获取所有报告列表"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以查看所有报告")

    try:
        reports = reports_service.get_all_reports(
            db, skip, limit, status_filter, user_filter
        )
        return reports
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))