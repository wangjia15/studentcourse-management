from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.analytics import (
    GPACalculationResponse,
    GradeDistributionResponse,
    StudentTrendResponse,
    SemesterComparisonResponse,
    ClassRankingResponse,
)
from app.services.analytics import AnalyticsService

router = APIRouter()
analytics_service = AnalyticsService()


@router.get("/gpa/student/{student_id}", response_model=GPACalculationResponse)
async def get_student_gpa(
    student_id: int,
    academic_year: Optional[str] = Query(None, description="学年，如 2024-2025"),
    semester: Optional[str] = Query(None, description="学期，如 Fall, Spring"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生GPA计算结果"""
    # 权限检查：只有管理员、教师本人或相关教师可以查看
    if (current_user.role != UserRole.ADMIN and
        current_user.id != student_id and
        current_user.role != UserRole.TEACHER):
        # 如果是教师，需要检查是否有权限查看该学生的GPA
        if not analytics_service.can_teacher_access_student_gpa(db, current_user.id, student_id):
            raise HTTPException(status_code=403, detail="无权限查看该学生GPA")

    try:
        gpa_data = analytics_service.calculate_student_gpa(
            db, student_id, academic_year, semester
        )
        return gpa_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/gpa/class/{class_id}", response_model=List[GPACalculationResponse])
async def get_class_gpa(
    class_id: str,
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级GPA统计"""
    # 权限检查：只有管理员和教师可以查看班级GPA
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="无权限查看班级GPA")

    try:
        gpa_list = analytics_service.calculate_class_gpa(
            db, class_id, academic_year, semester
        )
        return gpa_list
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/gpa/ranking/{class_id}", response_model=List[ClassRankingResponse])
async def get_class_gpa_ranking(
    class_id: str,
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级GPA排名"""
    # 权限检查：只有管理员和教师可以查看班级排名
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="无权限查看班级排名")

    try:
        ranking = analytics_service.get_class_gpa_ranking(
            db, class_id, academic_year, semester
        )
        return ranking
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/distribution/course/{course_id}", response_model=GradeDistributionResponse)
async def get_course_grade_distribution(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程成绩分布"""
    # 权限检查：管理员、授课教师或选修该课程的学生可以查看
    if not analytics_service.can_access_course_distribution(
        db, current_user.id, course_id
    ):
        raise HTTPException(status_code=403, detail="无权限查看该课程成绩分布")

    try:
        distribution = analytics_service.get_course_grade_distribution(db, course_id)
        return distribution
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trends/student/{student_id}", response_model=StudentTrendResponse)
async def get_student_grade_trends(
    student_id: int,
    academic_years: Optional[List[str]] = Query(None, description="学年列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生成绩趋势分析"""
    # 权限检查：只有管理员、学生本人或相关教师可以查看
    if (current_user.role != UserRole.ADMIN and
        current_user.id != student_id and
        current_user.role != UserRole.TEACHER):
        raise HTTPException(status_code=403, detail="无权限查看该学生成绩趋势")

    try:
        trends = analytics_service.get_student_grade_trends(
            db, student_id, academic_years
        )
        return trends
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/comparison/semesters", response_model=SemesterComparisonResponse)
async def get_semester_comparison(
    academic_year1: str = Query(..., description="第一个学年，如 2024-2025"),
    semester1: str = Query(..., description="第一个学期，如 Fall"),
    academic_year2: str = Query(..., description="第二个学年，如 2023-2024"),
    semester2: str = Query(..., description="第二个学期，如 Spring"),
    student_id: Optional[int] = Query(None, description="学生ID，如果不提供则分析整体"),
    class_id: Optional[str] = Query(None, description="班级ID"),
    department: Optional[str] = Query(None, description="院系"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学期成绩对比分析"""
    # 权限检查
    if student_id and current_user.role == UserRole.STUDENT and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="无权限查看其他学生的学期对比")

    if current_user.role == UserRole.STUDENT and not student_id:
        raise HTTPException(status_code=403, detail="学生只能查看自己的学期对比")

    try:
        comparison = analytics_service.compare_semesters(
            db, academic_year1, semester1, academic_year2, semester2,
            student_id, class_id, department
        )
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))