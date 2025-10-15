from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade
from app.models.enrollment import Enrollment
from app.schemas.course import CourseResponse
from app.schemas.grade import GradeResponse
from app.schemas.enrollment import EnrollmentRequest, EnrollmentResponse, EnrollmentStatus


class StudentService:
    """学生服务类"""

    def get_available_courses(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        department: Optional[str] = None,
        course_type: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[CourseResponse]:
        """获取可选课程列表"""

        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise ValueError("学生不存在")

        # 构建查询条件
        conditions = [
            Course.status == "active",
            Course.is_active == True,
            Course.current_enrolled < Course.max_students
        ]

        if academic_year:
            conditions.append(Course.academic_year == academic_year)
        if semester:
            conditions.append(Course.semester == semester)
        if department:
            conditions.append(Course.department == department)
        if course_type:
            conditions.append(Course.course_type == course_type)

        if search:
            conditions.append(
                or_(
                    Course.course_name.contains(search),
                    Course.course_code.contains(search),
                    Course.description.contains(search)
                )
            )

        # 查询课程
        query = db.query(Course).filter(and_(*conditions))
        total = query.count()
        courses = query.offset(skip).limit(limit).all()

        # 过滤掉已选的课程
        enrolled_course_ids = db.query(Enrollment.course_id).filter(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.status.in_(["approved", "pending"])
            )
        ).subquery()

        available_courses = [
            course for course in courses
            if course.id not in enrolled_course_ids
        ]

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
                description=course.description,
                classroom=course.classroom,
                schedule_info=course.schedule_info,
                created_at=course.created_at
            )
            for course in available_courses
        ]

    def get_enrolled_courses(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[CourseResponse]:
        """获取已选课程列表"""

        # 构建查询条件
        conditions = [
            Enrollment.student_id == student_id,
            Enrollment.status != "withdrawn"
        ]

        if academic_year:
            conditions.append(Enrollment.academic_year == academic_year)
        if semester:
            conditions.append(Enrollment.semester == semester)
        if status:
            conditions.append(Enrollment.status == status)

        # 查询选课记录
        enrollments = db.query(Enrollment).join(Course).filter(and_(*conditions)).all()

        return [
            CourseResponse(
                id=enrollment.course.id,
                course_code=enrollment.course.course_code,
                course_name=enrollment.course.course_name,
                course_name_en=enrollment.course.course_name_en,
                credits=enrollment.course.credits,
                hours=enrollment.course.hours,
                academic_year=enrollment.academic_year,
                semester=enrollment.semester,
                max_students=enrollment.course.max_students,
                current_enrolled=enrollment.course.current_enrolled,
                status=enrollment.course.status,
                department=enrollment.course.department,
                description=enrollment.course.description,
                classroom=enrollment.course.classroom,
                schedule_info=enrollment.course.schedule_info,
                created_at=enrollment.course.created_at
            )
            for enrollment in enrollments
        ]

    def enroll_course(self, db: Session, enrollment_request: EnrollmentRequest) -> EnrollmentResponse:
        """学生选课"""

        # 检查课程是否存在
        course = db.query(Course).filter(Course.id == enrollment_request.course_id).first()
        if not course:
            raise ValueError("课程不存在")

        # 检查课程是否可选
        if course.status != "active" or not course.is_active:
            raise ValueError("课程当前不可选")

        # 检查人数限制
        if course.current_enrolled >= course.max_students:
            raise ValueError("课程人数已满")

        # 检查是否已经选过
        existing_enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == enrollment_request.student_id,
                Enrollment.course_id == enrollment_request.course_id,
                Enrollment.academic_year == enrollment_request.academic_year or course.academic_year,
                Enrollment.semester == enrollment_request.semester or course.semester
            )
        ).first()

        if existing_enrollment:
            if existing_enrollment.status == "withdrawn":
                raise ValueError("该课程已退选，不能重复选择")
            elif existing_enrollment.status == "pending":
                raise ValueError("已提交选课申请，请等待审核")
            else:
                raise ValueError("已经选择了该课程")

        # 检查先修条件（如果有）
        if not self._check_prerequisites(db, enrollment_request.student_id, enrollment_request.course_id):
            raise ValueError("不满足先修课程要求")

        # 检查时间冲突
        if self._has_schedule_conflict(db, enrollment_request.student_id, enrollment_request.course_id):
            raise ValueError("与已选课程时间冲突")

        # 创建选课记录
        enrollment = Enrollment(
            student_id=enrollment_request.student_id,
            course_id=enrollment_request.course_id,
            academic_year=enrollment_request.academic_year or course.academic_year,
            semester=enrollment_request.semester or course.semester,
            status=EnrollmentStatus.APPROVED,  # 可以设置为pending需要审核
            enrolled_at=datetime.utcnow()
        )

        db.add(enrollment)

        # 更新课程选课人数
        course.current_enrolled += 1

        db.commit()
        db.refresh(enrollment)

        return EnrollmentResponse(
            id=enrollment.id,
            course_id=enrollment.course_id,
            student_id=enrollment.student_id,
            academic_year=enrollment.academic_year,
            semester=enrollment.semester,
            status=enrollment.status,
            enrolled_at=enrollment.enrolled_at,
            credits_earned=course.credits
        )

    def unenroll_course(self, db: Session, student_id: int, course_id: int):
        """学生退课"""

        # 查找选课记录
        enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id
            )
        ).first()

        if not enrollment:
            raise ValueError("未选择该课程")

        # 检查是否可以退课（时间限制等）
        if not self._can_unenroll(enrollment):
            raise ValueError("当前时间不允许退课")

        # 更新选课记录状态
        enrollment.status = EnrollmentStatus.WITHDRAWN
        enrollment.withdrawal_date = datetime.utcnow()

        # 更新课程选课人数
        course = db.query(Course).filter(Course.id == course_id).first()
        if course and course.current_enrolled > 0:
            course.current_enrolled -= 1

        db.commit()

    def get_student_grades(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        course_id: Optional[int] = None,
        grade_type: Optional[str] = None,
        is_published: Optional[bool] = True,
        skip: int = 0,
        limit: int = 50
    ) -> List[GradeResponse]:
        """获取学生成绩"""

        # 构建查询条件
        conditions = [Grade.student_id == student_id]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)
        if course_id:
            conditions.append(Grade.course_id == course_id)
        if grade_type:
            conditions.append(Grade.grade_type == grade_type)
        if is_published is not None:
            conditions.append(Grade.is_published == is_published)

        # 查询成绩
        grades = db.query(Grade).join(Course).filter(and_(*conditions)).order_by(
            Grade.academic_year.desc(), Grade.semester.desc()
        ).offset(skip).limit(limit).all()

        return [
            GradeResponse(
                id=grade.id,
                student_id=grade.student_id,
                course_id=grade.course_id,
                course_name=grade.course.course_name,
                course_code=grade.course.course_code,
                grade_type=grade.grade_type,
                score=grade.score,
                max_score=grade.max_score,
                percentage=round((grade.score / grade.max_score) * 100, 2) if grade.max_score else 0,
                letter_grade=grade.letter_grade,
                gpa_points=grade.gpa_points,
                grade_points=grade.grade_points,
                weight=grade.weight,
                academic_year=grade.academic_year,
                semester=grade.semester,
                status=grade.status,
                is_final=grade.is_final,
                is_published=grade.is_published,
                submitted_at=grade.submitted_at,
                comments=grade.comments
            )
            for grade in grades
        ]

    def calculate_student_gpa(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """计算学生GPA"""

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True,
            Grade.is_final == True
        ]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        # 查询成绩记录
        grades = db.query(Grade).join(Course).filter(and_(*conditions)).all()

        if not grades:
            return {
                "total_gpa": 0,
                "total_credits": 0,
                "total_courses": 0,
                "grade_breakdown": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
            }

        # 计算GPA
        total_gpa_points = 0
        total_credits = 0
        grade_breakdown = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

        for grade in grades:
            if grade.gpa_points and grade.course:
                total_gpa_points += grade.gpa_points * grade.course.credits
                total_credits += grade.course.credits

                if grade.letter_grade:
                    grade_breakdown[grade.letter_grade] = grade_breakdown.get(grade.letter_grade, 0) + 1

        overall_gpa = total_gpa_points / total_credits if total_credits > 0 else 0

        return {
            "total_gpa": round(overall_gpa, 3),
            "total_credits": total_credits,
            "total_courses": len(grades),
            "grade_breakdown": grade_breakdown
        }

    def get_student_grade_statistics(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取学生成绩统计"""

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True
        ]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        # 查询成绩
        grades = db.query(Grade).filter(and_(*conditions)).all()

        if not grades:
            return {
                "total_courses": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "pass_rate": 0
            }

        # 计算统计指标
        scores = []
        pass_count = 0

        for grade in grades:
            if grade.score and grade.max_score:
                percentage = (grade.score / grade.max_score) * 100
                scores.append(percentage)

                if percentage >= 60:
                    pass_count += 1

        average_score = sum(scores) / len(scores) if scores else 0
        highest_score = max(scores) if scores else 0
        lowest_score = min(scores) if scores else 0
        pass_rate = (pass_count / len(grades)) * 100 if grades else 0

        return {
            "total_courses": len(grades),
            "average_score": round(average_score, 2),
            "highest_score": round(highest_score, 2),
            "lowest_score": round(lowest_score, 2),
            "pass_rate": round(pass_rate, 2)
        }

    def get_student_grade_trends(
        self,
        db: Session,
        student_id: int,
        academic_years: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """获取学生成绩趋势"""

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True,
            Grade.is_final == True
        ]

        if academic_years:
            conditions.append(Grade.academic_year.in_(academic_years))

        # 查询成绩记录
        grades = db.query(Grade).join(Course).filter(and_(*conditions)).order_by(
            Grade.academic_year, Grade.semester
        ).all()

        if not grades:
            return {"trends": [], "overall_trend": "stable"}

        # 按学期分组
        semester_data = {}
        for grade in grades:
            semester_key = f"{grade.academic_year}_{grade.semester}"

            if semester_key not in semester_data:
                semester_data[semester_key] = {
                    "total_points": 0,
                    "total_credits": 0,
                    "scores": []
                }

            if grade.gpa_points and grade.course:
                semester_data[semester_key]["total_points"] += grade.gpa_points * grade.course.credits
                semester_data[semester_key]["total_credits"] += grade.course.credits

            if grade.score and grade.max_score:
                percentage = (grade.score / grade.max_score) * 100
                semester_data[semester_key]["scores"].append(percentage)

        # 计算趋势
        trends = []
        gpa_trend = []

        for semester_key, data in sorted(semester_data.items()):
            academic_year, semester = semester_key.split("_")
            gpa = data["total_points"] / data["total_credits"] if data["total_credits"] > 0 else 0
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0

            trends.append({
                "academic_year": academic_year,
                "semester": semester,
                "gpa": round(gpa, 3),
                "average_score": round(avg_score, 2),
                "courses_count": len(data["scores"])
            })

            gpa_trend.append(gpa)

        # 分析总体趋势
        if len(gpa_trend) >= 2:
            recent_change = gpa_trend[-1] - gpa_trend[-2]
            if recent_change > 0.1:
                overall_trend = "improving"
            elif recent_change < -0.1:
                overall_trend = "declining"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "stable"

        return {
            "trends": trends,
            "overall_trend": overall_trend
        }

    def get_student_schedule(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取学生课程表"""

        # 构建查询条件
        conditions = [
            Enrollment.student_id == student_id,
            Enrollment.status == "approved"
        ]

        if academic_year:
            conditions.append(Enrollment.academic_year == academic_year)
        if semester:
            conditions.append(Enrollment.semester == semester)

        # 查询选课记录
        enrollments = db.query(Enrollment).join(Course).filter(and_(*conditions)).all()

        schedule = []
        total_credits = 0
        weekly_hours = 0

        for enrollment in enrollments:
            course = enrollment.course
            schedule.append({
                "course_id": course.id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "credits": course.credits,
                "hours": course.hours,
                "classroom": course.classroom,
                "schedule_info": course.schedule_info,
                "teacher": course.teacher.full_name if course.teacher else None
            })

            total_credits += course.credits
            weekly_hours += course.hours

        return {
            "student_id": student_id,
            "academic_year": academic_year,
            "semester": semester,
            "schedule": schedule,
            "total_credits": total_credits,
            "weekly_hours": weekly_hours
        }

    def get_academic_summary(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取学业汇总信息"""

        # 获取GPA信息
        gpa_info = self.calculate_student_gpa(db, student_id, academic_year, semester)

        # 获取成绩统计
        grade_stats = self.get_student_grade_statistics(db, student_id, academic_year, semester)

        # 获取课程数量
        conditions = [
            Enrollment.student_id == student_id,
            Enrollment.status == "approved"
        ]

        if academic_year:
            conditions.append(Enrollment.academic_year == academic_year)
        if semester:
            conditions.append(Enrollment.semester == semester)

        total_courses = db.query(Enrollment).filter(and_(*conditions)).count()

        # 获取已通过课程数
        passed_courses = db.query(Grade).join(Enrollment).filter(
            and_(
                Grade.student_id == student_id,
                Grade.is_published == True,
                Grade.is_final == True,
                *conditions[1:]  # 排除student_id条件
            )
        ).filter(Grade.score >= 60).count() if academic_year or semester else 0

        failed_courses = total_courses - passed_courses if total_courses else 0

        return {
            "student_id": student_id,
            "academic_year": academic_year,
            "semester": semester,
            "total_credits": gpa_info["total_credits"],
            "earned_credits": gpa_info["total_credits"],
            "gpa": gpa_info["total_gpa"],
            "courses_count": total_courses,
            "passed_courses": passed_courses,
            "failed_courses": failed_courses,
            "average_score": grade_stats["average_score"]
        }

    def get_student_credits(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取学分统计"""

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True,
            Grade.is_final == True,
            Grade.score >= 60  # 只统计及格课程
        ]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        # 查询成绩记录
        grades = db.query(Grade).join(Course).filter(and_(*conditions)).all()

        if not grades:
            return {
                "total_credits": 0,
                "earned_credits": 0,
                "required_credits": 0,
                "elective_credits": 0,
                "credits_by_department": {},
                "credits_by_type": {}
            }

        # 统计学分
        total_credits = 0
        required_credits = 0
        elective_credits = 0
        general_credits = 0
        professional_credits = 0
        credits_by_department = {}
        credits_by_type = {}

        for grade in grades:
            if grade.course:
                course_credits = grade.course.credits
                total_credits += course_credits

                # 按课程类型统计
                course_type = grade.course.course_type
                credits_by_type[course_type] = credits_by_type.get(course_type, 0) + course_credits

                if course_type == "required":
                    required_credits += course_credits
                elif course_type == "elective":
                    elective_credits += course_credits
                elif course_type == "general":
                    general_credits += course_credits
                elif course_type == "professional":
                    professional_credits += course_credits

                # 按院系统计
                department = grade.course.department
                credits_by_department[department] = credits_by_department.get(department, 0) + course_credits

        return {
            "total_credits": total_credits,
            "earned_credits": total_credits,
            "required_credits": required_credits,
            "elective_credits": elective_credits,
            "general_credits": general_credits,
            "professional_credits": professional_credits,
            "credits_by_department": credits_by_department,
            "credits_by_type": credits_by_type
        }

    def get_student_class_rankings(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取班级排名信息"""

        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()
        if not student or not student.class_name:
            return {"message": "无法获取班级信息"}

        # 获取班级所有学生的GPA
        from app.services.analytics import AnalyticsService
        analytics_service = AnalyticsService()

        try:
            class_rankings = analytics_service.get_class_gpa_ranking(
                db, student.class_name, academic_year, semester
            )

            # 找到当前学生的排名
            current_ranking = None
            for ranking in class_rankings:
                if ranking.student_id == student_id:
                    current_ranking = ranking
                    break

            if not current_ranking:
                return {"message": "未找到排名信息"}

            return {
                "student_id": student_id,
                "class_name": student.class_name,
                "current_gpa_rank": current_ranking.gpa_rank,
                "total_students": current_ranking.total_students,
                "gpa_percentile": current_ranking.gpa_percentile,
                "current_gpa": current_ranking.current_gpa,
                "class_average_gpa": current_ranking.class_average_gpa
            }

        except Exception:
            return {"message": "无法获取排名信息"}

    def get_graduation_requirements_progress(self, db: Session, student_id: int) -> Dict[str, Any]:
        """获取毕业要求进度"""

        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise ValueError("学生不存在")

        # 获取学分统计
        credits_info = self.get_student_credits(db, student_id)

        # 假设的毕业要求（实际应该从配置或专业计划中获取）
        total_required_credits = 150
        required_credits_needed = 90
        elective_credits_needed = 40
        general_credits_needed = 20

        # 计算进度
        completion_percentage = (credits_info["total_credits"] / total_required_credits) * 100
        remaining_credits = total_required_credits - credits_info["total_credits"]

        # 生成要求列表
        requirements = [
            {
                "name": "总学分要求",
                "required": total_required_credits,
                "earned": credits_info["total_credits"],
                "remaining": max(0, remaining_credits),
                "completed": credits_info["total_credits"] >= total_required_credits
            },
            {
                "name": "必修课学分",
                "required": required_credits_needed,
                "earned": credits_info["required_credits"],
                "remaining": max(0, required_credits_needed - credits_info["required_credits"]),
                "completed": credits_info["required_credits"] >= required_credits_needed
            },
            {
                "name": "选修课学分",
                "required": elective_credits_needed,
                "earned": credits_info["elective_credits"],
                "remaining": max(0, elective_credits_needed - credits_info["elective_credits"]),
                "completed": credits_info["elective_credits"] >= elective_credits_needed
            },
            {
                "name": "通识课学分",
                "required": general_credits_needed,
                "earned": credits_info["general_credits"],
                "remaining": max(0, general_credits_needed - credits_info["general_credits"]),
                "completed": credits_info["general_credits"] >= general_credits_needed
            }
        ]

        # 找出未满足的要求
        missing_requirements = [req for req in requirements if not req["completed"]]

        # 估算毕业时间
        estimated_graduation = None
        if missing_requirements and student.enrollment_year:
            # 简单估算：每学期可获得15-20学分
            remaining_semesters = max(1, (remaining_credits / 18))
            current_year = int(datetime.utcnow().year)
            estimated_graduation_year = current_year + int(remaining_semesters / 2)
            estimated_graduation = datetime(estimated_graduation_year, 7, 1)

        on_track = len(missing_requirements) == 0

        # 生成警告信息
        warnings = []
        if credits_info["total_credits"] < (total_required_credits * 0.5):
            warnings.append("学分进度较慢，建议增加选课数量")
        if len(missing_requirements) > 2:
            warnings.append("多项毕业要求未满足，请关注学分进度")

        return {
            "student_id": student_id,
            "total_required_credits": total_required_credits,
            "current_credits": credits_info["total_credits"],
            "remaining_credits": remaining_credits,
            "completion_percentage": round(completion_percentage, 2),
            "requirements": requirements,
            "missing_requirements": missing_requirements,
            "estimated_graduation_date": estimated_graduation,
            "on_track": on_track,
            "warnings": warnings
        }

    def get_enrollment_history(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取选课历史"""

        # 构建查询条件
        conditions = [Enrollment.student_id == student_id]

        if academic_year:
            conditions.append(Enrollment.academic_year == academic_year)
        if semester:
            conditions.append(Enrollment.semester == semester)

        # 查询选课记录
        enrollments = db.query(Enrollment).join(Course).join(Grade, isouter=True).filter(
            and_(*conditions)
        ).order_by(Enrollment.enrolled_at.desc()).offset(skip).limit(limit).all()

        history = []
        for enrollment in enrollments:
            # 查找最终成绩
            final_grade = db.query(Grade).filter(
                and_(
                    Grade.student_id == student_id,
                    Grade.course_id == enrollment.course_id,
                    Grade.is_final == True,
                    Grade.is_published == True
                )
            ).first()

            history.append({
                "id": enrollment.id,
                "course_id": enrollment.course_id,
                "course_code": enrollment.course.course_code,
                "course_name": enrollment.course.course_name,
                "credits": enrollment.course.credits,
                "academic_year": enrollment.academic_year,
                "semester": enrollment.semester,
                "status": enrollment.status,
                "enrolled_at": enrollment.enrolled_at,
                "completed_at": final_grade.submitted_at if final_grade else None,
                "final_grade": final_grade.score if final_grade else None,
                "letter_grade": final_grade.letter_grade if final_grade else None,
                "gpa_points": final_grade.gpa_points if final_grade else None,
                "withdrawal_date": enrollment.withdrawal_date
            })

        return history

    def get_transcript_data(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """获取成绩单数据"""

        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise ValueError("学生不存在")

        # 获取学术记录
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True,
            Grade.is_final == True
        ]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        academic_records = db.query(Grade).join(Course).filter(and_(*conditions)).order_by(
            Grade.academic_year, Grade.semester, Course.course_code
        ).all()

        # 组织数据
        records_by_semester = {}
        total_credits = 0
        total_gpa_points = 0

        for grade in academic_records:
            semester_key = f"{grade.academic_year} {grade.semester}"

            if semester_key not in records_by_semester:
                records_by_semester[semester_key] = []

            course_info = {
                "course_code": grade.course.course_code,
                "course_name": grade.course.course_name,
                "credits": grade.course.credits,
                "course_type": grade.course.course_type,
                "grade_type": grade.grade_type,
                "score": grade.score,
                "max_score": grade.max_score,
                "percentage": round((grade.score / grade.max_score) * 100, 2) if grade.max_score else 0,
                "letter_grade": grade.letter_grade,
                "gpa_points": grade.gpa_points,
                "status": "通过" if grade.score >= (grade.course.passing_score or 60) else "不通过"
            }

            records_by_semester[semester_key].append(course_info)

            if grade.gpa_points and grade.course:
                total_credits += grade.course.credits
                total_gpa_points += grade.gpa_points * grade.course.credits

        # 计算总体GPA
        overall_gpa = total_gpa_points / total_credits if total_credits > 0 else 0

        # 获取班级排名
        class_rankings = self.get_student_class_rankings(db, student_id)

        return {
            "student_info": {
                "student_id": student.student_id,
                "name": student.full_name,
                "department": student.department,
                "major": student.major,
                "class_name": student.class_name,
                "enrollment_year": student.enrollment_year
            },
            "academic_records": records_by_semester,
            "gpa_summary": {
                "overall_gpa": round(overall_gpa, 3),
                "total_credits": total_credits,
                "total_courses": len(academic_records)
            },
            "credits_summary": self.get_student_credits(db, student_id, academic_year, semester),
            "rankings": class_rankings if "current_gpa_rank" in class_rankings else None,
            "generated_at": datetime.utcnow(),
            "format": format
        }

    # 私有辅助方法

    def _check_prerequisites(self, db: Session, student_id: int, course_id: int) -> bool:
        """检查先修条件"""
        # 这里应该实现实际的先修条件检查逻辑
        # 暂时返回True
        return True

    def _has_schedule_conflict(self, db: Session, student_id: int, course_id: int) -> bool:
        """检查时间冲突"""
        # 这里应该实现实际的时间冲突检查逻辑
        # 暂时返回False
        return False

    def _can_unenroll(self, enrollment: Enrollment) -> bool:
        """检查是否可以退课"""
        # 这里可以实现退课时间限制等逻辑
        # 例如：开学前两周可以退课，之后不允许
        return True