from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.course import CourseResponse, CourseCreate, CourseUpdate
from app.schemas.grade import GradeBatchCreate, GradeResponse, GradeUpdate
from app.schemas.students import StudentImportResponse, StudentListResponse
from app.services.teacher import TeacherService
from app.services.course import CourseService
from app.services.grade import GradeService

router = APIRouter()
teacher_service = TeacherService()
course_service = CourseService()
grade_service = GradeService()


def teacher_required(current_user: User = Depends(get_current_user)):
    """教师权限检查装饰器"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="需要教师权限")
    return current_user


@router.get("/courses", response_model=List[CourseResponse])
async def get_teacher_courses(
    academic_year: Optional[str] = Query(None, description="学年过滤"),
    semester: Optional[str] = Query(None, description="学期过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """获取教师授课课程列表"""
    try:
        courses = teacher_service.get_teacher_courses(
            db, current_user.id, academic_year, semester, status
        )
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课程列表失败: {str(e)}")


@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """教师创建新课程"""
    try:
        # 设置授课教师为当前用户
        course_data.teacher_id = current_user.id

        course = course_service.create_course(db, course_data, current_user.id)
        return course
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建课程失败: {str(e)}")


@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """教师更新课程信息"""
    try:
        # 检查权限
        if not teacher_service.can_teacher_manage_course(db, current_user.id, course_id):
            raise HTTPException(status_code=403, detail="无权限管理该课程")

        course = course_service.update_course(db, course_id, course_data, current_user.id)
        return course
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新课程失败: {str(e)}")


@router.get("/courses/{course_id}/students", response_model=StudentListResponse)
async def get_course_students(
    course_id: int,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """获取课程学生列表"""
    try:
        # 检查权限
        if not teacher_service.can_teacher_manage_course(db, current_user.id, course_id):
            raise HTTPException(status_code=403, detail="无权限查看该课程学生")

        students = teacher_service.get_course_students(
            db, course_id, skip, limit, search
        )
        return students
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学生列表失败: {str(e)}")


@router.post("/courses/{course_id}/import-students", response_model=StudentImportResponse)
async def import_course_students(
    course_id: int,
    file: UploadFile = File(..., description="学生信息文件 (Excel/CSV)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """批量导入课程学生"""
    try:
        # 检查权限
        if not teacher_service.can_teacher_manage_course(db, current_user.id, course_id):
            raise HTTPException(status_code=403, detail="无权限管理该课程")

        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="只支持Excel和CSV文件")

        result = await teacher_service.import_students_from_file(
            db, course_id, file, current_user.id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入学生失败: {str(e)}")


@router.post("/courses/{course_id}/enroll")
async def enroll_student(
    course_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """手动添加学生到课程"""
    try:
        # 检查权限
        if not teacher_service.can_teacher_manage_course(db, current_user.id, course_id):
            raise HTTPException(status_code=403, detail="无权限管理该课程")

        teacher_service.enroll_student_to_course(db, course_id, student_id, current_user.id)
        return {"message": "学生添加成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加学生失败: {str(e)}")


@router.delete("/courses/{course_id}/unenroll/{student_id}")
async def unenroll_student(
    course_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """从课程中移除学生"""
    try:
        # 检查权限
        if not teacher_service.can_teacher_manage_course(db, current_user.id, course_id):
            raise HTTPException(status_code=403, detail="无权限管理该课程")

        teacher_service.unenroll_student_from_course(db, course_id, student_id, current_user.id)
        return {"message": "学生移除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除学生失败: {str(e)}")


@router.post("/grades/batch", response_model=List[GradeResponse])
async def batch_create_grades(
    grades_data: GradeBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """批量录入成绩"""
    try:
        # 检查权限 - 教师只能录入自己授课课程的成绩
        for grade in grades_data.grades:
            if not teacher_service.can_teacher_manage_course(db, current_user.id, grade.course_id):
                raise HTTPException(status_code=403, detail=f"无权限录入课程 {grade.course_id} 的成绩")

        grades = grade_service.batch_create_grades(db, grades_data.grades, current_user.id)
        return grades
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量录入成绩失败: {str(e)}")


@router.put("/grades/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: int,
    grade_data: GradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """更新成绩"""
    try:
        # 检查权限
        grade = grade_service.get_grade(db, grade_id)
        if not grade:
            raise HTTPException(status_code=404, detail="成绩不存在")

        if not teacher_service.can_teacher_manage_course(db, current_user.id, grade.course_id):
            raise HTTPException(status_code=403, detail="无权限修改该成绩")

        updated_grade = grade_service.update_grade(db, grade_id, grade_data, current_user.id)
        return updated_grade
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新成绩失败: {str(e)}")


@router.delete("/grades/{grade_id}")
async def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """删除成绩"""
    try:
        # 检查权限
        grade = grade_service.get_grade(db, grade_id)
        if not grade:
            raise HTTPException(status_code=404, detail="成绩不存在")

        if not teacher_service.can_teacher_manage_course(db, current_user.id, grade.course_id):
            raise HTTPException(status_code=403, detail="无权限删除该成绩")

        grade_service.delete_grade(db, grade_id, current_user.id)
        return {"message": "成绩删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除成绩失败: {str(e)}")


@router.get("/courses/{course_id}/grades/statistics")
async def get_course_grade_statistics(
    course_id: int,
    grade_type: Optional[str] = Query(None, description="成绩类型过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """获取课程成绩统计"""
    try:
        # 检查权限
        if not teacher_service.can_teacher_manage_course(db, current_user.id, course_id):
            raise HTTPException(status_code=403, detail="无权限查看该课程统计")

        statistics = teacher_service.get_course_grade_statistics(db, course_id, grade_type)
        return statistics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成绩统计失败: {str(e)}")


@router.post("/courses/{course_id}/publish-grades")
async def publish_course_grades(
    course_id: int,
    grade_type: Optional[str] = Query(None, description="成绩类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """发布课程成绩"""
    try:
        # 检查权限
        if not teacher_service.can_teacher_manage_course(db, current_user.id, course_id):
            raise HTTPException(status_code=403, detail="无权限发布该课程成绩")

        teacher_service.publish_course_grades(db, course_id, grade_type, current_user.id)
        return {"message": "成绩发布成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发布成绩失败: {str(e)}")


@router.get("/students/{student_id}/grades")
async def get_student_grades_for_teacher(
    student_id: int,
    academic_year: Optional[str] = Query(None, description="学年过滤"),
    semester: Optional[str] = Query(None, description="学期过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(teacher_required),
):
    """教师查看学生成绩（仅限自己授课的课程）"""
    try:
        grades = teacher_service.get_student_grades_for_teacher(
            db, current_user.id, student_id, academic_year, semester
        )
        return grades
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学生成绩失败: {str(e)}")