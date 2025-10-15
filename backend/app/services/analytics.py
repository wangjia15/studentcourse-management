from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade, GradeType, GradeStatus
from app.models.enrollment import Enrollment
from app.schemas.analytics import (
    GPACalculationResponse,
    GradeDistributionResponse,
    StudentTrendResponse,
    SemesterComparisonResponse,
    ClassRankingResponse,
)

# Import new advanced services
from .gpa_calculation import GPACalculationService
from .grade_distribution import GradeDistributionService
from .trend_analysis import TrendAnalysisService
from .statistical_reports import StatisticalReportService
from .visualization import VisualizationService
from .performance_optimization import PerformanceOptimizedAnalytics


class AnalyticsService:
    """增强分析服务类 - 集成高级统计分析功能"""

    def __init__(self, redis_url: Optional[str] = None):
        """初始化分析服务"""
        # 初始化高级服务组件
        self.gpa_service = GPACalculationService()
        self.distribution_service = GradeDistributionService()
        self.trend_service = TrendAnalysisService()
        self.report_service = StatisticalReportService()
        self.visualization_service = VisualizationService()
        self.performance_service = PerformanceOptimizedAnalytics(redis_url)

        # 保持向后兼容的方法映射
        self._setup_backward_compatibility()

    def calculate_student_gpa(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        use_optimized: bool = True
    ) -> GPACalculationResponse:
        """计算学生GPA - 使用优化的计算引擎"""

        if use_optimized:
            # 使用性能优化的计算方法
            gpa_data = self.performance_service.calculate_student_gpa_optimized(
                db, student_id, academic_year, semester
            )
        else:
            # 使用原始的详细计算方法
            gpa_data = self.gpa_service.calculate_student_gpa_detailed(
                db, student_id, academic_year, semester
            )

        # 转换为响应格式
        return GPACalculationResponse(
            student_id=gpa_data["student_id"],
            student_name=gpa_data.get("student_name", "Unknown"),
            total_gpa=gpa_data["total_gpa"],
            academic_year=academic_year,
            semester=semester,
            total_credits=gpa_data["total_credits"],
            total_courses=gpa_data["total_courses"],
            grade_breakdown=gpa_data.get("grade_breakdown", {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}),
            calculation_date=gpa_data.get("calculation_timestamp", datetime.utcnow())
        )

    def calculate_class_gpa(
        self,
        db: Session,
        class_id: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[GPACalculationResponse]:
        """计算班级GPA统计"""

        # 获取班级所有学生
        students = db.query(User).filter(
            and_(
                User.class_name == class_id,
                User.role == UserRole.STUDENT,
                User.is_active == True
            )
        ).all()

        results = []
        for student in students:
            try:
                gpa_data = self.calculate_student_gpa(
                    db, student.id, academic_year, semester
                )
                results.append(gpa_data)
            except ValueError:
                # 跳过没有成绩记录的学生
                continue

        return results

    def get_class_gpa_ranking(
        self,
        db: Session,
        class_id: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[ClassRankingResponse]:
        """获取班级GPA排名"""

        # 计算班级所有学生GPA
        gpa_list = self.calculate_class_gpa(db, class_id, academic_year, semester)

        # 按GPA降序排序
        gpa_list.sort(key=lambda x: x.total_gpa, reverse=True)

        # 计算班级平均GPA
        class_average_gpa = sum(g.total_gpa for g in gpa_list) / len(gpa_list) if gpa_list else 0

        results = []
        for rank, gpa_data in enumerate(gpa_list, 1):
            percentile = (len(gpa_list) - rank) / len(gpa_list) * 100 if gpa_list else 0

            results.append(ClassRankingResponse(
                student_id=gpa_data.student_id,
                student_name=gpa_data.student_name,
                class_name=class_id,
                gpa_rank=rank,
                total_students=len(gpa_list),
                gpa_percentile=round(percentile, 2),
                current_gpa=gpa_data.total_gpa,
                class_average_gpa=round(class_average_gpa, 3)
            ))

        return results

    def get_course_grade_distribution(
        self,
        db: Session,
        course_id: int
    ) -> GradeDistributionResponse:
        """获取课程成绩分布"""

        # 获取课程信息
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        # 查询已发布成绩
        grades = db.query(Grade).filter(
            and_(
                Grade.course_id == course_id,
                Grade.is_published == True
            )
        ).all()

        if not grades:
            raise ValueError("该课程没有已发布的成绩")

        # 计算成绩分布
        grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        score_distribution = {
            "90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "0-59": 0
        }
        scores = []

        for grade in grades:
            if grade.letter_grade:
                grade_distribution[grade.letter_grade] = grade_distribution.get(grade.letter_grade, 0) + 1

            if grade.score and grade.max_score:
                percentage = (grade.score / grade.max_score) * 100
                scores.append(percentage)

                # 分数段分布
                if percentage >= 90:
                    score_distribution["90-100"] += 1
                elif percentage >= 80:
                    score_distribution["80-89"] += 1
                elif percentage >= 70:
                    score_distribution["70-79"] += 1
                elif percentage >= 60:
                    score_distribution["60-69"] += 1
                else:
                    score_distribution["0-59"] += 1

        # 计算统计指标
        if scores:
            average_score = sum(scores) / len(scores)
            sorted_scores = sorted(scores)
            median_score = sorted_scores[len(sorted_scores) // 2] if sorted_scores else 0
            highest_score = max(scores)
            lowest_score = min(scores)

            # 计算及格率和优秀率
            pass_count = sum(1 for score in scores if score >= 60)
            excellent_count = sum(1 for score in scores if score >= 85)
            pass_rate = (pass_count / len(scores)) * 100
            excellent_rate = (excellent_count / len(scores)) * 100
        else:
            average_score = median_score = highest_score = lowest_score = 0
            pass_rate = excellent_rate = 0

        return GradeDistributionResponse(
            course_id=course_id,
            course_name=course.course_name,
            total_students=len(grades),
            grade_distribution=grade_distribution,
            score_distribution=score_distribution,
            average_score=round(average_score, 2),
            median_score=round(median_score, 2),
            highest_score=round(highest_score, 2),
            lowest_score=round(lowest_score, 2),
            pass_rate=round(pass_rate, 2),
            excellent_rate=round(excellent_rate, 2)
        )

    def get_student_grade_trends(
        self,
        db: Session,
        student_id: int,
        academic_years: Optional[List[str]] = None
    ) -> StudentTrendResponse:
        """获取学生成绩趋势"""

        # 构建查询条件
        conditions = [Grade.student_id == student_id, Grade.is_published == True]

        if academic_years:
            conditions.append(Grade.academic_year.in_(academic_years))

        # 查询成绩记录
        grades = db.query(Grade).join(Course).filter(and_(*conditions)).order_by(
            Grade.academic_year, Grade.semester
        ).all()

        if not grades:
            raise ValueError("没有找到符合条件的成绩记录")

        # 按学期分组计算GPA趋势
        semester_gpas = {}
        for grade in grades:
            semester_key = f"{grade.academic_year}_{grade.semester}"

            if semester_key not in semester_gpas:
                semester_gpas[semester_key] = {"total_points": 0, "total_credits": 0}

            if grade.gpa_points and grade.course:
                semester_gpas[semester_key]["total_points"] += grade.gpa_points * grade.course.credits
                semester_gpas[semester_key]["total_credits"] += grade.course.credits

        # 计算每学期GPA
        trends = []
        gpa_trend = []
        credit_trend = []

        for semester_key, data in sorted(semester_gpas.items()):
            academic_year, semester = semester_key.split("_")
            gpa = data["total_points"] / data["total_credits"] if data["total_credits"] > 0 else 0

            trends.append({
                "academic_year": academic_year,
                "semester": semester,
                "gpa": round(gpa, 3),
                "credits": data["total_credits"]
            })

            gpa_trend.append(gpa)
            credit_trend.append(data["total_credits"])

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

        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            raise ValueError("学生不存在")

        return StudentTrendResponse(
            student_id=student_id,
            student_name=student.full_name,
            trends=trends,
            overall_trend=overall_trend,
            average_gpa_trend=[round(gpa, 3) for gpa in gpa_trend],
            credit_earning_trend=credit_trend
        )

    def compare_semesters(
        self,
        db: Session,
        academic_year1: str,
        semester1: str,
        academic_year2: str,
        semester2: str,
        student_id: Optional[int] = None,
        class_id: Optional[str] = None,
        department: Optional[str] = None
    ) -> SemesterComparisonResponse:
        """学期对比分析"""

        # 确定比较范围
        comparison_type = "individual" if student_id else ("class" if class_id else "department")

        # 获取两个学期的数据
        data1 = self._get_semester_data(
            db, academic_year1, semester1, student_id, class_id, department
        )
        data2 = self._get_semester_data(
            db, academic_year2, semester2, student_id, class_id, department
        )

        # 分析改进和下降的地方
        improvements = []
        declines = []

        if data1.get("average_gpa") and data2.get("average_gpa"):
            if data2["average_gpa"] > data1["average_gpa"]:
                improvements.append(f"GPA提升: {data2['average_gpa'] - data1['average_gpa']:.3f}")
            elif data2["average_gpa"] < data1["average_gpa"]:
                declines.append(f"GPA下降: {data1['average_gpa'] - data2['average_gpa']:.3f}")

        if data1.get("pass_rate") and data2.get("pass_rate"):
            if data2["pass_rate"] > data1["pass_rate"]:
                improvements.append(f"及格率提升: {data2['pass_rate'] - data1['pass_rate']:.1f}%")
            elif data2["pass_rate"] < data1["pass_rate"]:
                declines.append(f"及格率下降: {data1['pass_rate'] - data2['pass_rate']:.1f}%")

        # 生成分析总结
        analysis_summary = f"{academic_year1} {semester1} vs {academic_year2} {semester2} "
        if improvements:
            analysis_summary += f"整体表现{'显著' if len(improvements) > 2 else ''}提升"
        elif declines:
            analysis_summary += f"整体表现{'明显' if len(declines) > 2 else ''}下降"
        else:
            analysis_summary += "整体表现稳定"

        return SemesterComparisonResponse(
            comparison_type=comparison_type,
            semester1_data=data1,
            semester2_data=data2,
            improvements=improvements,
            declines=declines,
            analysis_summary=analysis_summary
        )

    def _get_semester_data(
        self,
        db: Session,
        academic_year: str,
        semester: str,
        student_id: Optional[int] = None,
        class_id: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取指定学期的数据"""

        # 构建查询条件
        conditions = [
            Grade.academic_year == academic_year,
            Grade.semester == semester,
            Grade.is_published == True
        ]

        if student_id:
            conditions.append(Grade.student_id == student_id)
        elif class_id:
            conditions.append(User.class_name == class_id)
        elif department:
            conditions.append(User.department == department)

        # 查询成绩数据
        query = db.query(Grade).join(User).join(Course).filter(and_(*conditions))
        grades = query.all()

        if not grades:
            return {"message": "该学期没有成绩数据"}

        # 计算统计指标
        total_points = 0
        total_credits = 0
        total_students = set()
        pass_count = 0

        for grade in grades:
            total_students.add(grade.student_id)

            if grade.gpa_points and grade.course:
                total_points += grade.gpa_points * grade.course.credits
                total_credits += grade.course.credits

            if grade.score and grade.max_score:
                percentage = (grade.score / grade.max_score) * 100
                if percentage >= 60:
                    pass_count += 1

        return {
            "academic_year": academic_year,
            "semester": semester,
            "total_students": len(total_students),
            "total_courses": len(set(grade.course_id for grade in grades)),
            "total_credits": total_credits,
            "average_gpa": round(total_points / total_credits, 3) if total_credits > 0 else 0,
            "pass_rate": round((pass_count / len(grades)) * 100, 1) if grades else 0,
            "total_grades": len(grades)
        }

    def can_teacher_access_student_gpa(self, db: Session, teacher_id: int, student_id: int) -> bool:
        """检查教师是否有权限查看学生GPA"""

        # 查询教师是否教授过该学生的课程
        teacher_courses = db.query(Course).filter(Course.teacher_id == teacher_id).all()
        teacher_course_ids = [course.id for course in teacher_courses]

        student_grades = db.query(Grade).filter(
            and_(
                Grade.student_id == student_id,
                Grade.course_id.in_(teacher_course_ids)
            )
        ).first()

        return student_grades is not None

    def can_access_course_distribution(self, db: Session, user_id: int, course_id: int) -> bool:
        """检查用户是否有权限查看课程成绩分布"""

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 管理员有所有权限
        if user.role == UserRole.ADMIN:
            return True

        # 教师只能查看自己授课的课程
        if user.role == UserRole.TEACHER:
            course = db.query(Course).filter(
                and_(Course.id == course_id, Course.teacher_id == user_id)
            ).first()
            return course is not None

        # 学生只能查看自己选修且成绩已发布的课程
        if user.role == UserRole.STUDENT:
            enrollment = db.query(Enrollment).filter(
                and_(
                    Enrollment.student_id == user_id,
                    Enrollment.course_id == course_id
                )
            ).first()

            if enrollment:
                # 检查是否有已发布的成绩
                published_grade = db.query(Grade).filter(
                    and_(
                        Grade.student_id == user_id,
                        Grade.course_id == course_id,
                        Grade.is_published == True
                    )
                ).first()
                return published_grade is not None

        return False

    # ============ 新增高级分析方法 ============

    def calculate_detailed_student_gpa(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        include_retake: bool = True
    ) -> Dict[str, Any]:
        """计算详细学生GPA - 包含所有明细信息"""
        return self.gpa_service.calculate_student_gpa_detailed(
            db, student_id, academic_year, semester, include_retake
        )

    def calculate_cumulative_gpa(
        self,
        db: Session,
        student_id: int,
        up_to_academic_year: Optional[str] = None,
        up_to_semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """计算累计GPA"""
        return self.gpa_service.calculate_cumulative_gpa(
            db, student_id, up_to_academic_year, up_to_semester
        )

    def predict_graduation_gpa(
        self,
        db: Session,
        student_id: int,
        remaining_credits: int,
        expected_gpa: Optional[float] = None
    ) -> Dict[str, Any]:
        """预测毕业GPA"""
        return self.gpa_service.predict_graduation_gpa(
            db, student_id, remaining_credits, expected_gpa
        )

    def analyze_course_grade_distribution(
        self,
        db: Session,
        course_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """分析课程成绩分布"""
        return self.distribution_service.analyze_course_grade_distribution(
            db, course_id, academic_year, semester, include_details
        )

    def analyze_class_grade_distribution(
        self,
        db: Session,
        class_name: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        course_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """分析班级成绩分布"""
        return self.distribution_service.analyze_class_grade_distribution(
            db, class_name, academic_year, semester, course_types
        )

    def compare_class_performance(
        self,
        db: Session,
        class_names: List[str],
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """班级成绩对比分析"""
        return self.distribution_service.compare_class_performance(
            db, class_names, academic_year, semester
        )

    def analyze_student_grade_trend(
        self,
        db: Session,
        student_id: int,
        academic_years: Optional[List[str]] = None,
        prediction_enabled: bool = True
    ) -> Dict[str, Any]:
        """分析学生成绩趋势"""
        return self.trend_service.analyze_student_grade_trend(
            db, student_id, academic_years, prediction_enabled
        )

    def analyze_class_trend(
        self,
        db: Session,
        class_name: str,
        academic_years: Optional[List[str]] = None,
        comparison_enabled: bool = True
    ) -> Dict[str, Any]:
        """分析班级成绩趋势"""
        return self.trend_service.analyze_class_trend(
            db, class_name, academic_years, comparison_enabled
        )

    def analyze_course_trend(
        self,
        db: Session,
        course_id: int,
        academic_years: Optional[List[str]] = None,
        teacher_comparison: bool = True
    ) -> Dict[str, Any]:
        """分析课程成绩趋势"""
        return self.trend_service.analyze_course_trend(
            db, course_id, academic_years, teacher_comparison
        )

    def generate_personal_statistical_report(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        format_type: str = "detailed"
    ) -> Dict[str, Any]:
        """生成个人统计报表"""
        return self.report_service.generate_personal_statistical_report(
            db, student_id, academic_year, semester, format_type
        )

    def generate_class_statistical_report(
        self,
        db: Session,
        class_name: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        include_individual_details: bool = False
    ) -> Dict[str, Any]:
        """生成班级统计报表"""
        return self.report_service.generate_class_statistical_report(
            db, class_name, academic_year, semester, include_individual_details
        )

    def generate_system_statistical_report(
        self,
        db: Session,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        scope: str = "university"
    ) -> Dict[str, Any]:
        """生成系统统计报表"""
        return self.report_service.generate_system_statistical_report(
            db, academic_year, semester, scope
        )

    def generate_semester_summary_report(
        self,
        db: Session,
        academic_year: str,
        semester: str
    ) -> Dict[str, Any]:
        """生成学期汇总报告"""
        return self.report_service.generate_semester_summary_report(
            db, academic_year, semester
        )

    def get_visualization_data(
        self,
        db: Session,
        chart_type: str,
        chart_subtype: str,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """获取可视化数据"""
        if chart_type == "pie":
            return self.visualization_service.get_pie_chart_data(
                db, chart_subtype, entity_id, entity_name, academic_year, semester
            )
        elif chart_type == "bar":
            return self.visualization_service.get_bar_chart_data(
                db, chart_subtype, kwargs.get("entity_ids"), kwargs.get("entity_names"),
                academic_year, semester
            )
        elif chart_type == "line":
            return self.visualization_service.get_line_chart_data(
                db, chart_subtype, entity_id, entity_name, kwargs.get("academic_years")
            )
        elif chart_type == "scatter":
            return self.visualization_service.get_scatter_plot_data(
                db, chart_subtype, kwargs.get("x_metric"), kwargs.get("y_metric"),
                kwargs.get("entity_type", "student"), kwargs.get("filters")
            )
        elif chart_type == "radar":
            return self.visualization_service.get_radar_chart_data(
                db, entity_id, kwargs.get("entity_type", "student"), academic_year, semester
            )
        elif chart_type == "heatmap":
            return self.visualization_service.get_heatmap_data(
                db, chart_subtype, academic_year, kwargs.get("filters")
            )
        else:
            return {"error": f"不支持的图表类型: {chart_type}"}

    def get_dashboard_data(
        self,
        db: Session,
        user_id: int,
        user_role: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取仪表板数据"""
        return self.visualization_service.get_dashboard_summary_data(
            db, user_id, user_role, academic_year, semester
        )

    def parallel_batch_analyze(
        self,
        db: Session,
        student_ids: List[int],
        analysis_type: str = "gpa",
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """并行批量分析"""
        if analysis_type == "gpa":
            # 这里需要实现异步调用，暂时使用同步方式
            results = []
            for student_id in student_ids:
                try:
                    gpa_data = self.calculate_student_gpa(
                        db, student_id, academic_year, semester
                    )
                    results.append({
                        "student_id": student_id,
                        "gpa": gpa_data.total_gpa,
                        "credits": gpa_data.total_credits,
                        "courses": gpa_data.total_courses
                    })
                except Exception:
                    continue
            return results
        else:
            return [{"error": f"不支持的分析类型: {analysis_type}"}]

    def optimize_performance(
        self,
        db: Session,
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """性能优化操作"""
        if operation == "warm_cache":
            student_ids = kwargs.get("student_ids", [])
            class_names = kwargs.get("class_names", [])
            self.performance_service.warm_up_cache(db, student_ids, class_names)
            return {"status": "success", "message": "缓存预热完成"}
        elif operation == "clear_cache":
            pattern = kwargs.get("pattern", "")
            cleared_count = self.performance_service.invalidate_cache_pattern(pattern)
            return {"status": "success", "cleared_count": cleared_count}
        elif operation == "performance_metrics":
            return self.performance_service.get_performance_metrics()
        elif operation == "cleanup_cache":
            cleared_count = self.performance_service.cleanup_expired_cache()
            return {"status": "success", "cleared_count": cleared_count}
        else:
            return {"error": f"不支持的操作: {operation}"}

    def _setup_backward_compatibility(self):
        """设置向后兼容性"""
        # 确保原有的类方法仍然可用
        pass