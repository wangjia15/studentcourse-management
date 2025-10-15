from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import UploadFile

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade
from app.models.enrollment import Enrollment
from app.schemas.course import CourseResponse
from app.schemas.grade import GradeBatchCreate, GradeResponse
from app.schemas.students import StudentImportResponse, StudentListResponse


class TeacherService:
    """教师服务类"""

    def get_teacher_courses(
        self,
        db: Session,
        teacher_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[CourseResponse]:
        """获取教师授课课程列表"""

        conditions = [Course.teacher_id == teacher_id]

        if academic_year:
            conditions.append(Course.academic_year == academic_year)
        if semester:
            conditions.append(Course.semester == semester)
        if status:
            conditions.append(Course.status == status)

        courses = db.query(Course).filter(and_(*conditions)).all()

        return [
            CourseResponse(
                id=course.id,
                course_code=course.course_code,
                course_name=course.course_name,
                course_name_en=course.course_name_en,
                credits=course.credits,
                hours=course.hours,
                academic_year=course.academic_year,
                semester=course.semester,
                max_students=course.max_students,
                current_enrolled=course.current_enrolled,
                status=course.status,
                department=course.department,
                classroom=course.classroom,
                exam_time=course.exam_time,
                exam_location=course.exam_location,
                created_at=course.created_at
            )
            for course in courses
        ]

    def can_teacher_manage_course(self, db: Session, teacher_id: int, course_id: int) -> bool:
        """检查教师是否可以管理课程"""

        course = db.query(Course).filter(
            and_(Course.id == course_id, Course.teacher_id == teacher_id)
        ).first()

        return course is not None

    def get_course_students(
        self,
        db: Session,
        course_id: int,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None
    ) -> StudentListResponse:
        """获取课程学生列表"""

        # 检查课程存在
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        # 构建查询
        query = db.query(User).join(Enrollment).filter(
            and_(
                Enrollment.course_id == course_id,
                Enrollment.status == "approved",
                User.role == UserRole.STUDENT
            )
        )

        if search:
            query = query.filter(
                or_(
                    User.full_name.contains(search),
                    User.student_id.contains(search),
                    User.email.contains(search)
                )
            )

        total = query.count()
        students = query.offset(skip).limit(limit).all()

        student_data = [
            {
                "id": student.id,
                "student_id": student.student_id,
                "full_name": student.full_name,
                "email": student.email,
                "class_name": student.class_name,
                "department": student.department,
                "enrollment_date": student.created_at
            }
            for student in students
        ]

        return StudentListResponse(
            students=student_data,
            total=total,
            skip=skip,
            limit=limit
        )

    async def import_students_from_file(
        self,
        db: Session,
        course_id: int,
        file: UploadFile,
        teacher_id: int
    ) -> StudentImportResponse:
        """从文件批量导入学生"""

        # 检查教师权限
        if not self.can_teacher_manage_course(db, teacher_id, course_id):
            raise ValueError("无权限管理该课程")

        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise ValueError("只支持Excel和CSV文件")

        try:
            # 读取文件内容
            content = await file.read()

            # 解析文件（这里应该使用实际的解析库）
            students_data = self._parse_student_file(content, file.filename)

            # 导入学生
            successful_imports = 0
            failed_imports = 0
            errors = []
            imported_students = []

            for student_data in students_data:
                try:
                    # 检查学生是否已存在
                    existing_student = db.query(User).filter(
                        User.student_id == student_data.get("student_id")
                    ).first()

                    if existing_student:
                        # 如果学生已存在，直接添加到课程
                        enrollment = Enrollment(
                            student_id=existing_student.id,
                            course_id=course_id,
                            academic_year=student_data.get("academic_year", "2024-2025"),
                            semester=student_data.get("semester", "Fall"),
                            status="approved"
                        )
                        db.add(enrollment)
                        successful_imports += 1
                        imported_students.append({
                            "student_id": existing_student.student_id,
                            "name": existing_student.full_name,
                            "status": "已存在用户，添加到课程"
                        })
                    else:
                        # 创建新学生
                        new_student = User(
                            username=student_data.get("student_id"),
                            email=student_data.get("email"),
                            full_name=student_data.get("name"),
                            student_id=student_data.get("student_id"),
                            role=UserRole.STUDENT,
                            department=student_data.get("department"),
                            class_name=student_data.get("class_name"),
                            password_hash="default_hash",  # 需要生成默认密码
                            is_active=True
                        )
                        db.add(new_student)
                        db.flush()  # 获取新用户ID

                        # 添加到课程
                        enrollment = Enrollment(
                            student_id=new_student.id,
                            course_id=course_id,
                            academic_year=student_data.get("academic_year", "2024-2025"),
                            semester=student_data.get("semester", "Fall"),
                            status="approved"
                        )
                        db.add(enrollment)
                        successful_imports += 1
                        imported_students.append({
                            "student_id": new_student.student_id,
                            "name": new_student.full_name,
                            "status": "新用户创建并添加到课程"
                        })

                except Exception as e:
                    failed_imports += 1
                    errors.append(f"导入学生 {student_data.get('student_id', 'unknown')} 失败: {str(e)}")

            # 更新课程选课人数
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                course.current_enrolled = db.query(Enrollment).filter(
                    and_(
                        Enrollment.course_id == course_id,
                        Enrollment.status == "approved"
                    )
                ).count()

            db.commit()

            return StudentImportResponse(
                total_records=len(students_data),
                successful_imports=successful_imports,
                failed_imports=failed_imports,
                errors=errors,
                imported_students=imported_students
            )

        except Exception as e:
            db.rollback()
            raise ValueError(f"文件处理失败: {str(e)}")

    def enroll_student_to_course(self, db: Session, course_id: int, student_id: int, teacher_id: int):
        """手动添加学生到课程"""

        # 检查教师权限
        if not self.can_teacher_manage_course(db, teacher_id, course_id):
            raise ValueError("无权限管理该课程")

        # 检查学生是否存在
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise ValueError("学生不存在")

        if student.role != UserRole.STUDENT:
            raise ValueError("只能添加学生到课程")

        # 检查是否已经选课
        existing_enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id
            )
        ).first()

        if existing_enrollment:
            raise ValueError("学生已经选择了该课程")

        # 检查课程人数限制
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        current_enrolled = db.query(Enrollment).filter(
            and_(
                Enrollment.course_id == course_id,
                Enrollment.status == "approved"
            )
        ).count()

        if current_enrolled >= course.max_students:
            raise ValueError("课程人数已满")

        # 创建选课记录
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            academic_year=course.academic_year,
            semester=course.semester,
            status="approved"
        )
        db.add(enrollment)

        # 更新课程选课人数
        course.current_enrolled = current_enrolled + 1

        db.commit()

    def unenroll_student_from_course(self, db: Session, course_id: int, student_id: int, teacher_id: int):
        """从课程中移除学生"""

        # 检查教师权限
        if not self.can_teacher_manage_course(db, teacher_id, course_id):
            raise ValueError("无权限管理该课程")

        # 检查选课记录
        enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id
            )
        ).first()

        if not enrollment:
            raise ValueError("学生未选择该课程")

        # 删除选课记录
        db.delete(enrollment)

        # 更新课程选课人数
        course = db.query(Course).filter(Course.id == course_id).first()
        if course and course.current_enrolled > 0:
            course.current_enrolled -= 1

        db.commit()

    def get_course_grade_statistics(self, db: Session, course_id: int, grade_type: Optional[str] = None) -> Dict[str, Any]:
        """获取课程成绩统计"""

        # 构建查询条件
        conditions = [Grade.course_id == course_id, Grade.is_published == True]

        if grade_type:
            conditions.append(Grade.grade_type == grade_type)

        grades = db.query(Grade).filter(and_(*conditions)).all()

        if not grades:
            return {
                "total_students": 0,
                "average_score": 0,
                "pass_rate": 0,
                "grade_distribution": {}
            }

        # 计算统计指标
        scores = []
        pass_count = 0
        grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

        for grade in grades:
            if grade.score and grade.max_score:
                percentage = (grade.score / grade.max_score) * 100
                scores.append(percentage)

                if percentage >= 60:
                    pass_count += 1

                if grade.letter_grade:
                    grade_distribution[grade.letter_grade] += 1

        average_score = sum(scores) / len(scores) if scores else 0
        pass_rate = (pass_count / len(grades)) * 100 if grades else 0

        return {
            "total_students": len(set(grade.student_id for grade in grades)),
            "total_grades": len(grades),
            "average_score": round(average_score, 2),
            "pass_rate": round(pass_rate, 2),
            "grade_distribution": grade_distribution,
            "score_ranges": self._calculate_score_ranges(scores)
        }

    def publish_course_grades(self, db: Session, course_id: int, grade_type: Optional[str], teacher_id: int):
        """发布课程成绩"""

        # 检查教师权限
        if not self.can_teacher_manage_course(db, teacher_id, course_id):
            raise ValueError("无权限发布该课程成绩")

        # 构建查询条件
        conditions = [Grade.course_id == course_id, Grade.is_published == False]

        if grade_type:
            conditions.append(Grade.grade_type == grade_type)

        # 查询未发布的成绩
        unpublished_grades = db.query(Grade).filter(and_(*conditions)).all()

        if not unpublished_grades:
            raise ValueError("没有找到需要发布的成绩")

        # 发布成绩
        for grade in unpublished_grades:
            grade.is_published = True
            grade.published_at = datetime.utcnow()

        db.commit()

    def get_student_grades_for_teacher(
        self,
        db: Session,
        teacher_id: int,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """教师查看学生成绩（仅限自己授课的课程）"""

        # 获取教师授课的课程ID
        teacher_courses = db.query(Course).filter(Course.teacher_id == teacher_id).all()
        course_ids = [course.id for course in teacher_courses]

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.course_id.in_(course_ids),
            Grade.is_published == True
        ]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        grades = db.query(Grade).join(Course).filter(and_(*conditions)).all()

        return [
            {
                "id": grade.id,
                "course_id": grade.course_id,
                "course_name": grade.course.course_name,
                "course_code": grade.course.course_code,
                "grade_type": grade.grade_type,
                "score": grade.score,
                "max_score": grade.max_score,
                "percentage": round((grade.score / grade.max_score) * 100, 2) if grade.max_score else 0,
                "letter_grade": grade.letter_grade,
                "gpa_points": grade.gpa_points,
                "academic_year": grade.academic_year,
                "semester": grade.semester,
                "graded_at": grade.submitted_at
            }
            for grade in grades
        ]

    def _parse_student_file(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        """解析学生文件"""
        # 这里应该使用实际的解析库（如pandas、openpyxl等）
        # 暂时返回模拟数据
        return [
            {
                "student_id": "2024001",
                "name": "张三",
                "email": "zhangsan@example.com",
                "department": "计算机学院",
                "class_name": "计科2101",
                "academic_year": "2024-2025",
                "semester": "Fall"
            },
            {
                "student_id": "2024002",
                "name": "李四",
                "email": "lisi@example.com",
                "department": "计算机学院",
                "class_name": "计科2101",
                "academic_year": "2024-2025",
                "semester": "Fall"
            }
        ]

    def _calculate_score_ranges(self, scores: List[float]) -> Dict[str, int]:
        """计算分数段分布"""
        ranges = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "0-59": 0
        }

        for score in scores:
            if score >= 90:
                ranges["90-100"] += 1
            elif score >= 80:
                ranges["80-89"] += 1
            elif score >= 70:
                ranges["70-79"] += 1
            elif score >= 60:
                ranges["60-69"] += 1
            else:
                ranges["0-59"] += 1

        return ranges