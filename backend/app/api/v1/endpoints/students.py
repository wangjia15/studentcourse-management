from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.course import CourseResponse
from app.schemas.grade import GradeResponse
from app.schemas.enrollment import EnrollmentRequest, EnrollmentResponse
from app.services.student import StudentService
from app.services.course import CourseService
from app.services.grade import GradeService

router = APIRouter()
student_service = StudentService()
course_service = CourseService()
grade_service = GradeService()


def student_required(current_user: User = Depends(get_current_user)):
    """学生权限检查装饰器"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="需要学生权限")
    return current_user


@router.get("/courses", response_model=List[CourseResponse])
async def get_available_courses(
    academic_year: Optional[str] = Query(None, description="学年过滤"),
    semester: Optional[str] = Query(None, description="学期过滤"),
    department: Optional[str] = Query(None, description="院系过滤"),
    course_type: Optional[str] = Query(None, description="课程类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取可选课程列表"""
    try:
        courses = student_service.get_available_courses(
            db, current_user.id, academic_year, semester, department,
            course_type, search, skip, limit
        )
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课程列表失败: {str(e)}")


@router.get("/enrolled-courses", response_model=List[CourseResponse])
async def get_enrolled_courses(
    academic_year: Optional[str] = Query(None, description="学年过滤"),
    semester: Optional[str] = Query(None, description="学期过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取已选课程列表"""
    try:
        courses = student_service.get_enrolled_courses(
            db, current_user.id, academic_year, semester, status
        )
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取已选课程失败: {str(e)}")


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_course(
    enrollment_request: EnrollmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """学生选课"""
    try:
        # 设置学生ID为当前用户
        enrollment_request.student_id = current_user.id

        enrollment = student_service.enroll_course(db, enrollment_request)
        return enrollment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"选课失败: {str(e)}")


@router.delete("/unenroll/{course_id}")
async def unenroll_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """学生退课"""
    try:
        student_service.unenroll_course(db, current_user.id, course_id)
        return {"message": "退课成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"退课失败: {str(e)}")


@router.get("/grades", response_model=List[GradeResponse])
async def get_my_grades(
    academic_year: Optional[str] = Query(None, description="学年过滤"),
    semester: Optional[str] = Query(None, description="学期过滤"),
    course_id: Optional[int] = Query(None, description="课程ID过滤"),
    grade_type: Optional[str] = Query(None, description="成绩类型过滤"),
    is_published: Optional[bool] = Query(True, description="是否只显示已发布成绩"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取个人成绩"""
    try:
        grades = student_service.get_student_grades(
            db, current_user.id, academic_year, semester, course_id,
            grade_type, is_published, skip, limit
        )
        return grades
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成绩失败: {str(e)}")


@router.get("/grades/gpa")
async def get_my_gpa(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取个人GPA"""
    try:
        gpa_info = student_service.calculate_student_gpa(
            db, current_user.id, academic_year, semester
        )
        return gpa_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取GPA失败: {str(e)}")


@router.get("/grades/statistics")
async def get_my_grade_statistics(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取个人成绩统计"""
    try:
        statistics = student_service.get_student_grade_statistics(
            db, current_user.id, academic_year, semester
        )
        return statistics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成绩统计失败: {str(e)}")


@router.get("/grades/trends")
async def get_my_grade_trends(
    academic_years: Optional[List[str]] = Query(None, description="学年列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取个人成绩趋势"""
    try:
        trends = student_service.get_student_grade_trends(
            db, current_user.id, academic_years
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成绩趋势失败: {str(e)}")


@router.get("/schedule")
async def get_my_schedule(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取个人课程表"""
    try:
        schedule = student_service.get_student_schedule(
            db, current_user.id, academic_year, semester
        )
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课程表失败: {str(e)}")


@router.get("/academic-summary")
async def get_academic_summary(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取学业汇总信息"""
    try:
        summary = student_service.get_academic_summary(
            db, current_user.id, academic_year, semester
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学业汇总失败: {str(e)}")


@router.get("/credits")
async def get_my_credits(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取学分统计"""
    try:
        credits = student_service.get_student_credits(
            db, current_user.id, academic_year, semester
        )
        return credits
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学分统计失败: {str(e)}")


@router.get("/class-rankings")
async def get_my_class_rankings(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取班级排名信息"""
    try:
        rankings = student_service.get_student_class_rankings(
            db, current_user.id, academic_year, semester
        )
        return rankings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取班级排名失败: {str(e)}")


@router.get("/graduation-requirements")
async def get_graduation_requirements(
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取毕业要求进度"""
    try:
        requirements = student_service.get_graduation_requirements_progress(db, current_user.id)
        return requirements
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取毕业要求失败: {str(e)}")


@router.get("/enrollment-history")
async def get_enrollment_history(
    academic_year: Optional[str] = Query(None, description="学年过滤"),
    semester: Optional[str] = Query(None, description="学期过滤"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取选课历史"""
    try:
        history = student_service.get_enrollment_history(
            db, current_user.id, academic_year, semester, skip, limit
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选课历史失败: {str(e)}")


@router.get("/transcript-data")
async def get_transcript_data(
    format: str = Query("json", description="返回格式: json, pdf"),
    academic_year: Optional[str] = Query(None, description="学年过滤"),
    semester: Optional[str] = Query(None, description="学期过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(student_required),
):
    """获取成绩单数据"""
    try:
        transcript_data = student_service.get_transcript_data(
            db, current_user.id, academic_year, semester, format
        )
        return transcript_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成绩单数据失败: {str(e)}")