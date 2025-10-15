from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import math
from decimal import Decimal, ROUND_HALF_UP

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade, GradeType, GradeStatus
from app.models.enrollment import Enrollment


class GPACalculationService:
    """GPA计算引擎 - 中国教育部4.0标准实现"""

    # 中国教育部4.0 GPA标准映射
    CHINESE_GPA_MAPPING = {
        (90, 100): 4.0,
        (85, 89): 3.7,
        (82, 84): 3.3,
        (78, 81): 3.0,
        (75, 77): 2.7,
        (72, 74): 2.3,
        (68, 71): 2.0,
        (64, 67): 1.5,
        (60, 63): 1.0,
        (0, 59): 0.0
    }

    # 五级制绩点映射
    FIVE_LEVEL_MAPPING = {
        "优秀": 4.0,
        "良好": 3.0,
        "中等": 2.0,
        "及格": 1.0,
        "不及格": 0.0
    }

    def __init__(self):
        self.caching_enabled = True
        self._gpa_cache = {}

    def calculate_score_gpa_points(self, score: float, max_score: float = 100.0) -> float:
        """根据分数计算GPA绩点 - 中国4.0标准"""
        if score is None or max_score is None or max_score <= 0:
            return 0.0

        # 计算百分比分数
        percentage = (score / max_score) * 100

        # 查找对应的GPA绩点
        for (min_score, max_score_range), gpa_points in self.CHINESE_GPA_MAPPING.items():
            if min_score <= percentage <= max_score_range:
                return gpa_points

        return 0.0

    def calculate_letter_grade(self, score: float, max_score: float = 100.0) -> str:
        """计算等级成绩"""
        if score is None or max_score is None or max_score <= 0:
            return "F"

        percentage = (score / max_score) * 100

        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

    def calculate_five_level_grade(self, score: float, max_score: float = 100.0) -> str:
        """计算五级制成绩"""
        if score is None or max_score is None or max_score <= 0:
            return "不及格"

        percentage = (score / max_score) * 100

        if percentage >= 90:
            return "优秀"
        elif percentage >= 80:
            return "良好"
        elif percentage >= 70:
            return "中等"
        elif percentage >= 60:
            return "及格"
        else:
            return "不及格"

    def calculate_student_gpa_detailed(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        include_retake: bool = True,
        course_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """详细计算学生GPA - 包含所有明细信息"""

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        # 查询成绩记录
        query = db.query(Grade).join(Course).filter(and_(*conditions))

        if course_types:
            query = query.filter(Course.course_type.in_(course_types))

        grades = query.all()

        if not grades:
            return {
                "student_id": student_id,
                "total_gpa": 0.0,
                "total_credits": 0,
                "total_courses": 0,
                "course_details": [],
                "grade_breakdown": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
                "five_level_breakdown": {"优秀": 0, "良好": 0, "中等": 0, "及格": 0, "不及格": 0},
                "failed_courses": [],
                "calculation_timestamp": datetime.utcnow()
            }

        # 处理重修课程
        course_grades = {}
        for grade in grades:
            course_id = grade.course_id
            if course_id not in course_grades:
                course_grades[course_id] = []
            course_grades[course_id].append(grade)

        # 选择最佳成绩（用于重修课程）
        final_grades = []
        failed_courses = []

        for course_id, course_grade_list in course_grades.items():
            if include_retake and len(course_grade_list) > 1:
                # 选择最高分数的成绩
                best_grade = max(course_grade_list, key=lambda g: g.score if g.score else 0)
                final_grades.append(best_grade)

                # 记录其他尝试为重修
                for grade in course_grade_list:
                    if grade.id != best_grade.id:
                        grade.is_retake = True
            else:
                # 使用最新成绩
                latest_grade = max(course_grade_list, key=lambda g: g.submitted_at or datetime.min)
                final_grades.append(latest_grade)

        # 计算GPA
        total_quality_points = 0.0
        total_credits = 0
        course_details = []
        grade_breakdown = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        five_level_breakdown = {"优秀": 0, "良好": 0, "中等": 0, "及格": 0, "不及格": 0}

        for grade in final_grades:
            if not grade.course or not grade.score:
                continue

            # 计算课程GPA点和等级
            gpa_points = self.calculate_score_gpa_points(grade.score, grade.max_score)
            letter_grade = self.calculate_letter_grade(grade.score, grade.max_score)
            five_level = self.calculate_five_level_grade(grade.score, grade.max_score)

            # 计算质量点（GPA点 × 学分）
            quality_points = gpa_points * grade.course.credits
            total_quality_points += quality_points
            total_credits += grade.course.credits

            # 更新分布统计
            grade_breakdown[letter_grade] = grade_breakdown.get(letter_grade, 0) + 1
            five_level_breakdown[five_level] = five_level_breakdown.get(five_level, 0) + 1

            # 记录不及格课程
            if letter_grade == "F":
                failed_courses.append({
                    "course_id": grade.course_id,
                    "course_name": grade.course.course_name,
                    "score": grade.score,
                    "credits": grade.course.credits,
                    "academic_year": grade.academic_year,
                    "semester": grade.semester
                })

            # 课程详细信息
            course_details.append({
                "course_id": grade.course_id,
                "course_code": grade.course.course_code,
                "course_name": grade.course.course_name,
                "credits": grade.course.credits,
                "score": grade.score,
                "max_score": grade.max_score,
                "percentage": round((grade.score / grade.max_score) * 100, 2),
                "gpa_points": gpa_points,
                "letter_grade": letter_grade,
                "five_level_grade": five_level,
                "quality_points": quality_points,
                "academic_year": grade.academic_year,
                "semester": grade.semester,
                "course_type": grade.course.course_type,
                "is_retake": getattr(grade, 'is_retake', False)
            })

        # 计算最终GPA（保留2位小数）
        final_gpa = total_quality_points / total_credits if total_credits > 0 else 0.0
        final_gpa = float(Decimal(str(final_gpa)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()

        return {
            "student_id": student_id,
            "student_name": student.full_name if student else "Unknown",
            "student_number": student.student_id if student else None,
            "total_gpa": final_gpa,
            "total_quality_points": round(total_quality_points, 2),
            "total_credits": total_credits,
            "total_courses": len(final_grades),
            "course_details": sorted(course_details, key=lambda x: (x['academic_year'], x['semester'])),
            "grade_breakdown": grade_breakdown,
            "five_level_breakdown": five_level_breakdown,
            "failed_courses": failed_courses,
            "failed_course_count": len(failed_courses),
            "academic_year": academic_year,
            "semester": semester,
            "calculation_timestamp": datetime.utcnow()
        }

    def calculate_cumulative_gpa(
        self,
        db: Session,
        student_id: int,
        up_to_academic_year: Optional[str] = None,
        up_to_semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """计算累计GPA - 支持历史累计计算"""

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if up_to_academic_year:
            conditions.append(Grade.academic_year <= up_to_academic_year)
            if up_to_semester:
                # 处理跨学期的逻辑
                conditions.append(
                    or_(
                        Grade.academic_year < up_to_academic_year,
                        and_(
                            Grade.academic_year == up_to_academic_year,
                            Grade.semester <= up_to_semester
                        )
                    )
                )

        # 查询所有符合条件的成绩
        grades = db.query(Grade).join(Course).filter(and_(*conditions)).all()

        if not grades:
            return {
                "cumulative_gpa": 0.0,
                "total_credits": 0,
                "semester_breakdown": [],
                "academic_years_covered": []
            }

        # 按学期分组
        semester_data = {}
        for grade in grades:
            if not grade.course or not grade.score:
                continue

            semester_key = f"{grade.academic_year}_{grade.semester}"
            if semester_key not in semester_data:
                semester_data[semester_key] = {
                    "academic_year": grade.academic_year,
                    "semester": grade.semester,
                    "total_quality_points": 0.0,
                    "total_credits": 0,
                    "courses": []
                }

            gpa_points = self.calculate_score_gpa_points(grade.score, grade.max_score)
            quality_points = gpa_points * grade.course.credits

            semester_data[semester_key]["total_quality_points"] += quality_points
            semester_data[semester_key]["total_credits"] += grade.course.credits
            semester_data[semester_key]["courses"].append({
                "course_name": grade.course.course_name,
                "credits": grade.course.credits,
                "gpa_points": gpa_points
            })

        # 计算每学期GPA和累计GPA
        semester_breakdown = []
        cumulative_quality_points = 0.0
        cumulative_credits = 0

        for semester_key in sorted(semester_data.keys()):
            data = semester_data[semester_key]
            cumulative_quality_points += data["total_quality_points"]
            cumulative_credits += data["total_credits"]

            semester_gpa = data["total_quality_points"] / data["total_credits"] if data["total_credits"] > 0 else 0.0
            cumulative_gpa = cumulative_quality_points / cumulative_credits if cumulative_credits > 0 else 0.0

            semester_breakdown.append({
                "academic_year": data["academic_year"],
                "semester": data["semester"],
                "semester_gpa": round(float(Decimal(str(semester_gpa)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
                "semester_credits": data["total_credits"],
                "cumulative_gpa": round(float(Decimal(str(cumulative_gpa)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
                "cumulative_credits": cumulative_credits,
                "course_count": len(data["courses"])
            })

        final_cumulative_gpa = cumulative_quality_points / cumulative_credits if cumulative_credits > 0 else 0.0
        final_cumulative_gpa = float(Decimal(str(final_cumulative_gpa)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        academic_years = sorted(list(set(data["academic_year"] for data in semester_data.values())))

        return {
            "student_id": student_id,
            "cumulative_gpa": final_cumulative_gpa,
            "total_credits": cumulative_credits,
            "total_courses": sum(len(data["courses"]) for data in semester_data.values()),
            "semester_breakdown": semester_breakdown,
            "academic_years_covered": academic_years,
            "calculation_timestamp": datetime.utcnow()
        }

    def calculate_class_ranking(
        self,
        db: Session,
        class_name: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        major: Optional[str] = None,
        enrollment_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """计算班级排名 - 包含百分比排名和并列处理"""

        # 构建学生查询条件
        student_conditions = [
            User.role == UserRole.STUDENT,
            User.is_active == True,
            User.class_name == class_name
        ]

        if major:
            student_conditions.append(User.major == major)
        if enrollment_year:
            student_conditions.append(User.enrollment_year == enrollment_year)

        # 获取班级所有学生
        students = db.query(User).filter(and_(*student_conditions)).all()

        if not students:
            return {
                "class_name": class_name,
                "total_students": 0,
                "rankings": [],
                "class_statistics": {},
                "calculation_timestamp": datetime.utcnow()
            }

        # 计算每个学生的GPA
        student_gpas = []
        for student in students:
            try:
                gpa_data = self.calculate_student_gpa_detailed(
                    db, student.id, academic_year, semester
                )
                if gpa_data["total_credits"] > 0:  # 只包含有学分的学生
                    student_gpas.append({
                        "student_id": student.id,
                        "student_name": student.full_name,
                        "student_number": student.student_id,
                        "gpa": gpa_data["total_gpa"],
                        "total_credits": gpa_data["total_credits"],
                        "total_courses": gpa_data["total_courses"]
                    })
            except Exception:
                # 跳过计算失败的学生
                continue

        if not student_gpas:
            return {
                "class_name": class_name,
                "total_students": 0,
                "rankings": [],
                "class_statistics": {},
                "calculation_timestamp": datetime.utcnow()
            }

        # 按GPA降序排序
        student_gpas.sort(key=lambda x: x["gpa"], reverse=True)

        # 处理并列排名
        rankings = []
        current_rank = 1
        processed_count = 0

        i = 0
        while i < len(student_gpas):
            current_gpa = student_gpas[i]["gpa"]
            tied_students = []

            # 找出所有GPA相同的学生
            while i < len(student_gpas) and student_gpas[i]["gpa"] == current_gpa:
                tied_students.append(student_gpas[i])
                i += 1

            # 为并列学生分配相同排名
            for student_data in tied_students:
                percentile = ((len(student_gpas) - current_rank) / len(student_gpas)) * 100
                percentile = float(Decimal(str(percentile)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

                rankings.append({
                    "rank": current_rank,
                    "student_id": student_data["student_id"],
                    "student_name": student_data["student_name"],
                    "student_number": student_data["student_number"],
                    "gpa": student_data["gpa"],
                    "total_credits": student_data["total_credits"],
                    "total_courses": student_data["total_courses"],
                    "percentile": percentile,
                    "is_tied": len(tied_students) > 1,
                    "tied_count": len(tied_students)
                })

            current_rank += len(tied_students)
            processed_count += len(tied_students)

        # 计算班级统计信息
        gpas = [s["gpa"] for s in student_gpas]
        class_average = sum(gpas) / len(gpas)
        class_median = self._calculate_median(gpas)
        class_std_dev = self._calculate_standard_deviation(gpas)

        # 找出最高和最低GPA
        highest_gpa = max(gpas)
        lowest_gpa = min(gpas)

        # 计算GPA分布
        gpa_distribution = self._calculate_gpa_distribution(gpas)

        class_statistics = {
            "total_students": len(student_gpas),
            "average_gpa": round(float(Decimal(str(class_average)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "median_gpa": round(float(Decimal(str(class_median)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "std_deviation": round(float(Decimal(str(class_std_dev)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "highest_gpa": highest_gpa,
            "lowest_gpa": lowest_gpa,
            "gpa_range": round(highest_gpa - lowest_gpa, 2),
            "gpa_distribution": gpa_distribution,
            "students_above_average": len([g for g in gpas if g > class_average]),
            "students_below_average": len([g for g in gpas if g < class_average]),
            "academic_year": academic_year,
            "semester": semester
        }

        return {
            "class_name": class_name,
            "major": major,
            "enrollment_year": enrollment_year,
            "total_students": len(student_gpas),
            "rankings": rankings,
            "class_statistics": class_statistics,
            "calculation_timestamp": datetime.utcnow()
        }

    def _calculate_median(self, values: List[float]) -> float:
        """计算中位数"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)

        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]

    def _calculate_standard_deviation(self, values: List[float]) -> float:
        """计算标准差"""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _calculate_gpa_distribution(self, gpas: List[float]) -> Dict[str, int]:
        """计算GPA分布"""
        distribution = {
            "3.5-4.0": 0,
            "3.0-3.49": 0,
            "2.5-2.99": 0,
            "2.0-2.49": 0,
            "1.5-1.99": 0,
            "1.0-1.49": 0,
            "0.0-0.99": 0
        }

        for gpa in gpas:
            if gpa >= 3.5:
                distribution["3.5-4.0"] += 1
            elif gpa >= 3.0:
                distribution["3.0-3.49"] += 1
            elif gpa >= 2.5:
                distribution["2.5-2.99"] += 1
            elif gpa >= 2.0:
                distribution["2.0-2.49"] += 1
            elif gpa >= 1.5:
                distribution["1.5-1.99"] += 1
            elif gpa >= 1.0:
                distribution["1.0-1.49"] += 1
            else:
                distribution["0.0-0.99"] += 1

        return distribution

    def predict_graduation_gpa(
        self,
        db: Session,
        student_id: int,
        remaining_credits: int,
        expected_gpa: Optional[float] = None
    ) -> Dict[str, Any]:
        """预测毕业GPA"""

        # 获取当前累计GPA
        current_data = self.calculate_cumulative_gpa(db, student_id)

        if current_data["total_credits"] == 0:
            return {
                "prediction_possible": False,
                "reason": "No completed courses found"
            }

        current_gpa = current_data["cumulative_gpa"]
        current_credits = current_data["total_credits"]

        # 如果没有提供期望GPA，使用当前GPA
        if expected_gpa is None:
            expected_gpa = current_gpa

        # 计算预测毕业GPA
        total_credits_at_graduation = current_credits + remaining_credits
        predicted_quality_points = (current_gpa * current_credits) + (expected_gpa * remaining_credits)
        predicted_gpa = predicted_quality_points / total_credits_at_graduation

        # 计算不同场景的预测
        scenarios = {}
        for scenario_gpa in [2.0, 2.5, 3.0, 3.5, 4.0]:
            scenario_quality_points = (current_gpa * current_credits) + (scenario_gpa * remaining_credits)
            scenario_final_gpa = scenario_quality_points / total_credits_at_graduation
            scenarios[f"if_remain_{scenario_gpa}"] = round(scenario_final_gpa, 3)

        # 计算达到目标GPA需要的平均GPA
        target_gpas = [3.0, 3.5, 3.8, 4.0]
        required_gpas = {}

        for target in target_gpas:
            if target <= current_gpa:
                required_gpas[f"to_reach_{target}"] = round(current_gpa, 3)
            else:
                required_gpa = ((target * total_credits_at_graduation) - (current_gpa * current_credits)) / remaining_credits
                required_gpas[f"to_reach_{target}"] = round(min(required_gpa, 4.0), 3)

        return {
            "prediction_possible": True,
            "current_status": {
                "current_gpa": current_gpa,
                "current_credits": current_credits
            },
            "predictions": {
                "with_current_gpa": round(predicted_gpa, 3),
                "with_expected_gpa": round(expected_gpa, 3) if expected_gpa != current_gpa else None
            },
            "scenarios": scenarios,
            "required_remaining_gpa": required_gpas,
            "remaining_credits": remaining_credits,
            "total_credits_at_graduation": total_credits_at_graduation,
            "calculation_timestamp": datetime.utcnow()
        }