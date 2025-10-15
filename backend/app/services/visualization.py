from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
import json

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade, GradeType, GradeStatus
from app.models.enrollment import Enrollment
from .gpa_calculation import GPACalculationService
from .grade_distribution import GradeDistributionService
from .trend_analysis import TrendAnalysisService


class VisualizationService:
    """数据可视化支持服务"""

    def __init__(self):
        self.gpa_service = GPACalculationService()
        self.distribution_service = GradeDistributionService()
        self.trend_service = TrendAnalysisService()

    def get_pie_chart_data(
        self,
        db: Session,
        chart_type: str,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取饼图数据"""

        if chart_type == "grade_distribution":
            return self._get_grade_distribution_pie_data(
                db, entity_id, academic_year, semester
            )
        elif chart_type == "course_type_distribution":
            return self._get_course_type_distribution_pie_data(
                db, entity_id, academic_year, semester
            )
        elif chart_type == "pass_fail_distribution":
            return self._get_pass_fail_distribution_pie_data(
                db, entity_id, academic_year, semester
            )
        elif chart_type == "gpa_level_distribution":
            return self._get_gpa_level_distribution_pie_data(
                db, entity_id, entity_name, academic_year, semester
            )
        else:
            return {"error": "不支持的饼图类型"}

    def get_bar_chart_data(
        self,
        db: Session,
        chart_type: str,
        entity_ids: Optional[List[int]] = None,
        entity_names: Optional[List[str]] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取柱状图数据"""

        if chart_type == "class_comparison":
            return self._get_class_comparison_bar_data(
                db, entity_names, academic_year, semester
            )
        elif chart_type == "department_comparison":
            return self._get_department_comparison_bar_data(
                db, entity_names, academic_year, semester
            )
        elif chart_type == "course_performance":
            return self._get_course_performance_bar_data(
                db, entity_ids, academic_year, semester
            )
        elif chart_type == "grade_range_distribution":
            return self._get_grade_range_distribution_bar_data(
                db, entity_id=entity_ids[0] if entity_ids else None,
                academic_year=academic_year, semester=semester
            )
        elif chart_type == "teacher_performance":
            return self._get_teacher_performance_bar_data(
                db, entity_names, academic_year, semester
            )
        else:
            return {"error": "不支持的柱状图类型"}

    def get_line_chart_data(
        self,
        db: Session,
        chart_type: str,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        academic_years: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """获取折线图数据"""

        if chart_type == "gpa_trend":
            return self._get_gpa_trend_line_data(
                db, entity_id, academic_years
            )
        elif chart_type == "score_trend":
            return self._get_score_trend_line_data(
                db, entity_id, academic_years
            )
        elif chart_type == "class_gpa_trend":
            return self._get_class_gpa_trend_line_data(
                db, entity_name, academic_years
            )
        elif chart_type == "course_performance_trend":
            return self._get_course_performance_trend_line_data(
                db, entity_id, academic_years
            )
        elif chart_type == "enrollment_trend":
            return self._get_enrollment_trend_line_data(
                db, entity_name, academic_years
            )
        else:
            return {"error": "不支持的折线图类型"}

    def get_scatter_plot_data(
        self,
        db: Session,
        chart_type: str,
        x_metric: str,
        y_metric: str,
        entity_type: str = "student",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取散点图数据"""

        if chart_type == "correlation_analysis":
            return self._get_correlation_scatter_data(
                db, x_metric, y_metric, entity_type, filters
            )
        elif chart_type == "performance_distribution":
            return self._get_performance_distribution_scatter_data(
                db, x_metric, y_metric, entity_type, filters
            )
        else:
            return {"error": "不支持的散点图类型"}

    def get_radar_chart_data(
        self,
        db: Session,
        entity_id: int,
        entity_type: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取雷达图数据"""

        if entity_type == "student":
            return self._get_student_radar_data(
                db, entity_id, academic_year, semester
            )
        elif entity_type == "class":
            return self._get_class_radar_data(
                db, entity_id, academic_year, semester
            )
        else:
            return {"error": "不支持的实体类型"}

    def get_heatmap_data(
        self,
        db: Session,
        data_type: str,
        academic_year: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取热力图数据"""

        if data_type == "course_difficulty":
            return self._get_course_difficulty_heatmap_data(db, academic_year, filters)
        elif data_type == "student_performance":
            return self._get_student_performance_heatmap_data(db, academic_year, filters)
        elif data_type == "grade_correlation":
            return self._get_grade_correlation_heatmap_data(db, academic_year, filters)
        else:
            return {"error": "不支持的热力图数据类型"}

    def get_dashboard_summary_data(
        self,
        db: Session,
        user_id: int,
        user_role: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取仪表板汇总数据"""

        if user_role == "student":
            return self._get_student_dashboard_data(db, user_id, academic_year, semester)
        elif user_role == "teacher":
            return self._get_teacher_dashboard_data(db, user_id, academic_year, semester)
        elif user_role == "admin":
            return self._get_admin_dashboard_data(db, academic_year, semester)
        else:
            return {"error": "不支持的用户角色"}

    def _get_grade_distribution_pie_data(
        self,
        db: Session,
        course_id: Optional[int],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """获取成绩分布饼图数据"""
        conditions = [
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if course_id:
            conditions.append(Grade.course_id == course_id)
        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        grades = db.query(Grade).join(Course).filter(and_(*conditions)).all()

        if not grades:
            return {"labels": [], "data": [], "colors": []}

        # 统计等级分布
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for grade in grades:
            if grade.score and grade.max_score:
                percentage = (grade.score / grade.max_score) * 100
                if percentage >= 90:
                    grade_counts["A"] += 1
                elif percentage >= 80:
                    grade_counts["B"] += 1
                elif percentage >= 70:
                    grade_counts["C"] += 1
                elif percentage >= 60:
                    grade_counts["D"] += 1
                else:
                    grade_counts["F"] += 1

        labels = []
        data = []
        colors = {
            "A": "#4CAF50",  # 绿色
            "B": "#2196F3",  # 蓝色
            "C": "#FF9800",  # 橙色
            "D": "#FF5722",  # 深橙色
            "F": "#F44336"   # 红色
        }

        for grade in ["A", "B", "C", "D", "F"]:
            if grade_counts[grade] > 0:
                labels.append(f"{grade}级 ({grade_counts[grade]}人)")
                data.append(grade_counts[grade])

        return {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": [colors[grade] for grade in ["A", "B", "C", "D", "F"] if grade_counts[grade] > 0],
                "borderWidth": 2,
                "borderColor": "#ffffff"
            }],
            "total_students": sum(data),
            "chart_info": {
                "type": "grade_distribution_pie",
                "title": "成绩等级分布",
                "subtitle": f"总计 {sum(data)} 名学生"
            }
        }

    def _get_course_type_distribution_pie_data(
        self,
        db: Session,
        student_id: Optional[int],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """获取课程类型分布饼图数据"""
        conditions = [
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if student_id:
            conditions.append(Grade.student_id == student_id)
        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        grades = db.query(Grade).join(Course).filter(and_(*conditions)).all()

        if not grades:
            return {"labels": [], "data": [], "colors": []}

        # 统计课程类型分布
        course_type_counts = {}
        for grade in grades:
            course_type = grade.course.course_type
            course_type_counts[course_type] = course_type_counts.get(course_type, 0) + 1

        # 中文映射
        type_mapping = {
            "required": "必修课",
            "elective": "选修课",
            "professional": "专业课",
            "general": "通识课"
        }

        colors = {
            "required": "#FF6384",
            "elective": "#36A2EB",
            "professional": "#FFCE56",
            "general": "#4BC0C0"
        }

        labels = []
        data = []
        background_colors = []

        for course_type, count in course_type_counts.items():
            chinese_name = type_mapping.get(course_type, course_type)
            labels.append(f"{chinese_name} ({count}门)")
            data.append(count)
            background_colors.append(colors.get(course_type, "#999999"))

        return {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": background_colors,
                "borderWidth": 2,
                "borderColor": "#ffffff"
            }],
            "chart_info": {
                "type": "course_type_distribution_pie",
                "title": "课程类型分布",
                "subtitle": f"总计 {sum(data)} 门课程"
            }
        }

    def _get_class_comparison_bar_data(
        self,
        db: Session,
        class_names: Optional[List[str]],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """获取班级对比柱状图数据"""
        if not class_names:
            return {"labels": [], "datasets": []}

        class_data = []
        for class_name in class_names:
            # 计算班级平均GPA
            ranking_data = self.gpa_service.calculate_class_ranking(
                db, class_name, academic_year, semester
            )

            if ranking_data.get("class_statistics"):
                class_data.append({
                    "class_name": class_name,
                    "average_gpa": ranking_data["class_statistics"]["average_gpa"],
                    "median_gpa": ranking_data["class_statistics"]["median_gpa"],
                    "student_count": ranking_data["class_statistics"]["total_students"],
                    "pass_rate": ranking_data["class_statistics"].get("pass_rate", 0)
                })

        if not class_data:
            return {"labels": [], "datasets": []}

        labels = [data["class_name"] for data in class_data]
        gpa_data = [data["average_gpa"] for data in class_data]
        median_data = [data["median_gpa"] for data in class_data]
        pass_rate_data = [data["pass_rate"] for data in class_data]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "平均GPA",
                    "data": gpa_data,
                    "backgroundColor": "rgba(54, 162, 235, 0.8)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1
                },
                {
                    "label": "GPA中位数",
                    "data": median_data,
                    "backgroundColor": "rgba(255, 99, 132, 0.8)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "borderWidth": 1
                },
                {
                    "label": "及格率 (%)",
                    "data": pass_rate_data,
                    "backgroundColor": "rgba(75, 192, 192, 0.8)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "borderWidth": 1,
                    "yAxisID": "y1"
                }
            ],
            "chart_info": {
                "type": "class_comparison_bar",
                "title": "班级成绩对比",
                "subtitle": f"学期: {academic_year or '全部'} {semester or ''}"
            }
        }

    def _get_gpa_trend_line_data(
        self,
        db: Session,
        student_id: int,
        academic_years: Optional[List[str]]
    ) -> Dict[str, Any]:
        """获取GPA趋势折线图数据"""
        trend_analysis = self.trend_service.analyze_student_grade_trend(
            db, student_id, academic_years
        )

        if "semester_trends" not in trend_analysis:
            return {"labels": [], "datasets": []}

        semester_trends = trend_analysis["semester_trends"]
        labels = [f"{trend['academic_year']} {trend['semester']}" for trend in semester_trends]

        semester_gpa_data = [trend["semester_gpa"] for trend in semester_trends]
        cumulative_gpa_data = [trend["cumulative_gpa"] for trend in semester_trends]
        average_score_data = [trend["average_score"] / 25 for trend in semester_trends]  # 转换为4.0制

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "学期GPA",
                    "data": semester_gpa_data,
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "borderWidth": 2,
                    "fill": False
                },
                {
                    "label": "累计GPA",
                    "data": cumulative_gpa_data,
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderWidth": 2,
                    "fill": False
                },
                {
                    "label": "平均分 (4.0制)",
                    "data": average_score_data,
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    "borderWidth": 2,
                    "fill": False
                }
            ],
            "chart_info": {
                "type": "gpa_trend_line",
                "title": "GPA变化趋势",
                "subtitle": f"学生ID: {student_id}"
            }
        }

    def _get_correlation_scatter_data(
        self,
        db: Session,
        x_metric: str,
        y_metric: str,
        entity_type: str,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """获取相关性分析散点图数据"""

        if entity_type == "student":
            # 获取学生数据
            students = db.query(User).filter(User.role == UserRole.STUDENT).all()
            scatter_data = []

            for student in students:
                try:
                    # 计算各项指标
                    gpa_data = self.gpa_service.calculate_student_gpa_detailed(db, student.id)

                    x_value = self._extract_metric_value(gpa_data, x_metric)
                    y_value = self._extract_metric_value(gpa_data, y_metric)

                    if x_value is not None and y_value is not None:
                        scatter_data.append({
                            "x": x_value,
                            "y": y_value,
                            "label": student.full_name,
                            "student_id": student.id
                        })
                except:
                    continue

            if scatter_data:
                return {
                    "datasets": [{
                        "label": f"{x_metric} vs {y_metric}",
                        "data": scatter_data,
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "borderWidth": 1
                    }],
                    "chart_info": {
                        "type": "correlation_scatter",
                        "title": f"{x_metric} 与 {y_metric} 相关性分析",
                        "x_axis_label": x_metric,
                        "y_axis_label": y_metric
                    }
                }

        return {"datasets": [], "chart_info": {"error": "无数据"}}

    def _get_student_radar_data(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """获取学生能力雷达图数据"""

        # 获取学生详细数据
        gpa_data = self.gpa_service.calculate_student_gpa_detailed(
            db, student_id, academic_year, semester
        )

        # 获取趋势分析
        trend_data = self.trend_service.analyze_student_grade_trend(
            db, student_id, [academic_year] if academic_year else None
        )

        # 计算各项能力指标（1-5分制）
        metrics = {
            "学术能力": self._calculate_academic_ability_score(gpa_data),
            "学习稳定性": self._calculate_stability_score(trend_data),
            "进步趋势": self._calculate_progress_score(trend_data),
            "课程难度适应性": self._calculate_difficulty_adaptation_score(gpa_data),
            "时间管理": self._calculate_time_management_score(gpa_data),
            "知识掌握度": self._calculate_knowledge_mastery_score(gpa_data)
        }

        labels = list(metrics.keys())
        data = list(metrics.values())

        return {
            "labels": labels,
            "datasets": [{
                "label": "能力评估",
                "data": data,
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 2,
                "pointBackgroundColor": "rgba(54, 162, 235, 1)",
                "pointBorderColor": "#fff",
                "pointHoverBackgroundColor": "#fff",
                "pointHoverBorderColor": "rgba(54, 162, 235, 1)"
            }],
            "chart_info": {
                "type": "student_radar",
                "title": "学生能力雷达图",
                "subtitle": f"学生: {gpa_data.get('student_name', 'Unknown')}"
            },
            "scale": {
                "ticks": {"beginAtZero": True, "max": 5, "min": 0, "stepSize": 1}
            }
        }

    def _get_student_dashboard_data(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """获取学生仪表板数据"""

        # 获取基础数据
        gpa_data = self.gpa_service.calculate_student_gpa_detailed(
            db, student_id, academic_year, semester
        )

        trend_data = self.trend_service.analyze_student_grade_trend(
            db, student_id, [academic_year] if academic_year else None
        )

        # 生成图表数据
        grade_dist_pie = self._get_grade_distribution_pie_data(
            db, None, academic_year, semester
        )

        gpa_trend_line = self._get_gpa_trend_line_data(
            db, student_id, [academic_year] if academic_year else None
        )

        student_radar = self._get_student_radar_data(
            db, student_id, academic_year, semester
        )

        return {
            "summary_stats": {
                "current_gpa": gpa_data.get("total_gpa", 0),
                "total_credits": gpa_data.get("total_credits", 0),
                "total_courses": gpa_data.get("total_courses", 0),
                "failed_courses": gpa_data.get("failed_course_count", 0),
                "trend": trend_data.get("trend_analysis", {}).get("trend", "stable")
            },
            "charts": {
                "grade_distribution": grade_dist_pie,
                "gpa_trend": gpa_trend_line,
                "ability_radar": student_radar
            },
            "recent_alerts": trend_data.get("risk_analysis", {}).get("risks", []),
            "recommendations": trend_data.get("recommendations", [])
        }

    def _extract_metric_value(self, data: Dict[str, Any], metric: str) -> Optional[float]:
        """从数据中提取指定指标的值"""
        metric_mapping = {
            "gpa": "total_gpa",
            "credits": "total_credits",
            "courses": "total_courses",
            "failed_courses": "failed_course_count"
        }

        key = metric_mapping.get(metric, metric)
        return data.get(key)

    def _calculate_academic_ability_score(self, gpa_data: Dict[str, Any]) -> float:
        """计算学术能力分数"""
        gpa = gpa_data.get("total_gpa", 0)
        return min(5.0, max(1.0, gpa))

    def _calculate_stability_score(self, trend_data: Dict[str, Any]) -> float:
        """计算学习稳定性分数"""
        volatility = trend_data.get("trend_analysis", {}).get("volatility", 1.0)
        return max(1.0, 5.0 - volatility)

    def _calculate_progress_score(self, trend_data: Dict[str, Any]) -> float:
        """计算进步趋势分数"""
        trend = trend_data.get("trend_analysis", {}).get("trend", "stable")
        if trend == "improving":
            return 4.5
        elif trend == "stable":
            return 3.0
        else:
            return 1.5

    def _calculate_difficulty_adaptation_score(self, gpa_data: Dict[str, Any]) -> float:
        """计算课程难度适应性分数"""
        # 简化计算，基于不同类型课程的表现
        return 3.5  # 默认值

    def _calculate_time_management_score(self, gpa_data: Dict[str, Any]) -> float:
        """计算时间管理分数"""
        # 基于课程数量和GPA的关系
        courses = gpa_data.get("total_courses", 0)
        gpa = gpa_data.get("total_gpa", 0)

        if courses > 0:
            return min(5.0, max(1.0, (gpa * courses) / 10))
        return 3.0

    def _calculate_knowledge_mastery_score(self, gpa_data: Dict[str, Any]) -> float:
        """计算知识掌握度分数"""
        return min(5.0, max(1.0, gpa_data.get("total_gpa", 0) * 1.25))

    # 其他图表数据获取方法的占位符实现
    def _get_pass_fail_distribution_pie_data(self, db: Session, entity_id: Optional[int], academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"labels": [], "data": [], "message": "需要实现"}

    def _get_gpa_level_distribution_pie_data(self, db: Session, entity_id: Optional[int], entity_name: Optional[str], academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"labels": [], "data": [], "message": "需要实现"}

    def _get_department_comparison_bar_data(self, db: Session, entity_names: Optional[List[str]], academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_course_performance_bar_data(self, db: Session, entity_ids: Optional[List[int]], academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_grade_range_distribution_bar_data(self, db: Session, entity_id: Optional[int], academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_teacher_performance_bar_data(self, db: Session, entity_names: Optional[List[str]], academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_score_trend_line_data(self, db: Session, entity_id: Optional[int], academic_years: Optional[List[str]]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_class_gpa_trend_line_data(self, db: Session, entity_name: Optional[str], academic_years: Optional[List[str]]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_course_performance_trend_line_data(self, db: Session, entity_id: Optional[int], academic_years: Optional[List[str]]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_enrollment_trend_line_data(self, db: Session, entity_name: Optional[str], academic_years: Optional[List[str]]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_performance_distribution_scatter_data(self, db: Session, x_metric: str, y_metric: str, entity_type: str, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"datasets": [], "message": "需要实现"}

    def _get_class_radar_data(self, db: Session, entity_id: int, academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"labels": [], "datasets": [], "message": "需要实现"}

    def _get_course_difficulty_heatmap_data(self, db: Session, academic_year: Optional[str], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"data": [], "message": "需要实现"}

    def _get_student_performance_heatmap_data(self, db: Session, academic_year: Optional[str], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"data": [], "message": "需要实现"}

    def _get_grade_correlation_heatmap_data(self, db: Session, academic_year: Optional[str], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"data": [], "message": "需要实现"}

    def _get_teacher_dashboard_data(self, db: Session, user_id: int, academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"summary": {}, "charts": {}, "message": "需要实现"}

    def _get_admin_dashboard_data(self, db: Session, academic_year: Optional[str], semester: Optional[str]) -> Dict[str, Any]:
        return {"summary": {}, "charts": {}, "message": "需要实现"}