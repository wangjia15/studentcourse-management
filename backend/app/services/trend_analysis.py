from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
import math
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade, GradeType, GradeStatus
from app.models.enrollment import Enrollment
from .gpa_calculation import GPACalculationService


class TrendAnalysisService:
    """趋势分析服务"""

    def __init__(self):
        self.gpa_service = GPACalculationService()
        self.caching_enabled = True
        self._trend_cache = {}

    def analyze_student_grade_trend(
        self,
        db: Session,
        student_id: int,
        academic_years: Optional[List[str]] = None,
        prediction_enabled: bool = True
    ) -> Dict[str, Any]:
        """分析学生个人成绩趋势"""

        # 构建查询条件
        conditions = [
            Grade.student_id == student_id,
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if academic_years:
            conditions.append(Grade.academic_year.in_(academic_years))

        # 查询成绩记录，按时间排序
        grades = db.query(Grade).join(Course).filter(and_(*conditions)).order_by(
            Grade.academic_year, Grade.semester
        ).all()

        if not grades:
            return {
                "student_id": student_id,
                "error": "没有找到符合条件的成绩记录",
                "analysis_timestamp": datetime.utcnow()
            }

        # 获取学生信息
        student = db.query(User).filter(User.id == student_id).first()

        # 按学期分组分析
        semester_data = self._group_grades_by_semester(grades)

        # 计算每学期的统计指标
        semester_trends = []
        cumulative_gpa = 0.0
        cumulative_credits = 0

        for semester_key in sorted(semester_data.keys()):
            data = semester_data[semester_key]
            academic_year, semester = semester_key.split("_")

            # 计算学期GPA
            semester_gpa = self._calculate_semester_gpa(data["grades"])
            semester_avg_score = self._calculate_average_score(data["grades"])

            # 更新累计GPA
            if semester_gpa and data["total_credits"] > 0:
                cumulative_quality_points = cumulative_gpa * cumulative_credits + semester_gpa * data["total_credits"]
                cumulative_credits += data["total_credits"]
                cumulative_gpa = cumulative_quality_points / cumulative_credits if cumulative_credits > 0 else 0.0

            semester_trends.append({
                "academic_year": academic_year,
                "semester": semester,
                "semester_key": semester_key,
                "semester_gpa": round(semester_gpa, 3) if semester_gpa else 0.0,
                "cumulative_gpa": round(cumulative_gpa, 3) if cumulative_gpa > 0 else 0.0,
                "average_score": round(semester_avg_score, 2) if semester_avg_score else 0.0,
                "total_credits": data["total_credits"],
                "course_count": len(data["grades"]),
                "highest_score": data["highest_score"],
                "lowest_score": data["lowest_score"],
                "pass_rate": data["pass_rate"],
                "course_details": [
                    {
                        "course_name": grade.course.course_name,
                        "score": round((grade.score / grade.max_score) * 100, 2),
                        "credits": grade.course.credits
                    }
                    for grade in data["grades"]
                ]
            })

        # 分析总体趋势
        trend_analysis = self._analyze_overall_trend(semester_trends)

        # GPA变化分析
        gpa_trend_analysis = self._analyze_gpa_trend([s["semester_gpa"] for s in semester_trends])

        # 学习进步分析
        progress_analysis = self._analyze_learning_progress(semester_trends)

        # 风险预警
        risk_analysis = self._analyze_learning_risks(semester_trends, student)

        # 预测分析
        prediction_analysis = {}
        if prediction_enabled and len(semester_trends) >= 2:
            prediction_analysis = self._predict_future_performance(semester_trends)

        # 学习建议
        recommendations = self._generate_study_recommendations(
            semester_trends, trend_analysis, risk_analysis
        )

        return {
            "student_info": {
                "student_id": student_id,
                "student_name": student.full_name if student else "Unknown",
                "student_number": student.student_id if student else None,
                "major": student.major if student else None,
                "enrollment_year": student.enrollment_year if student else None
            },
            "semester_trends": semester_trends,
            "trend_analysis": trend_analysis,
            "gpa_trend_analysis": gpa_trend_analysis,
            "progress_analysis": progress_analysis,
            "risk_analysis": risk_analysis,
            "prediction_analysis": prediction_analysis,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow()
        }

    def analyze_class_trend(
        self,
        db: Session,
        class_name: str,
        academic_years: Optional[List[str]] = None,
        comparison_enabled: bool = True
    ) -> Dict[str, Any]:
        """分析班级成绩趋势"""

        # 获取班级学生
        students = db.query(User).filter(
            and_(
                User.role == UserRole.STUDENT,
                User.is_active == True,
                User.class_name == class_name
            )
        ).all()

        if not students:
            return {"error": "班级不存在或没有学生"}

        # 收集所有学生的学期成绩数据
        class_semester_data = defaultdict(list)

        for student in students:
            try:
                student_trend = self.analyze_student_grade_trend(
                    db, student.id, academic_years, prediction_enabled=False
                )

                if "semester_trends" in student_trend:
                    for semester_data in student_trend["semester_trends"]:
                        semester_key = semester_data["semester_key"]
                        class_semester_data[semester_key].append({
                            "student_id": student.id,
                            "student_name": student.full_name,
                            "semester_gpa": semester_data["semester_gpa"],
                            "average_score": semester_data["average_score"],
                            "total_credits": semester_data["total_credits"]
                        })
            except Exception:
                # 跳过分析失败的学生
                continue

        if not class_semester_data:
            return {"error": "没有找到班级成绩数据"}

        # 计算班级每学期的平均指标
        class_trends = []
        for semester_key in sorted(class_semester_data.keys()):
            semester_students = class_semester_data[semester_key]
            academic_year, semester = semester_key.split("_")

            # 计算班级平均值
            gpas = [s["semester_gpa"] for s in semester_students if s["semester_gpa"] > 0]
            scores = [s["average_score"] for s in semester_students if s["average_score"] > 0]

            if gpas and scores:
                class_trends.append({
                    "academic_year": academic_year,
                    "semester": semester,
                    "semester_key": semester_key,
                    "class_average_gpa": round(sum(gpas) / len(gpas), 3),
                    "class_average_score": round(sum(scores) / len(scores), 2),
                    "class_median_gpa": round(self._calculate_median(gpas), 3),
                    "class_median_score": round(self._calculate_median(scores), 2),
                    "gpa_std_dev": round(self._calculate_std_dev(gpas), 3),
                    "score_std_dev": round(self._calculate_std_dev(scores), 2),
                    "student_count": len(semester_students),
                    "active_students": len(gpas),
                    "highest_gpa": max(gpas),
                    "lowest_gpa": min(gpas),
                    "gpa_range": round(max(gpas) - min(gpas), 3)
                })

        # 分析班级整体趋势
        class_trend_analysis = self._analyze_class_trend(class_trends)

        # 成绩分布变化分析
        distribution_analysis = self._analyze_grade_distribution_change(
            db, class_name, academic_years
        )

        # 同级对比分析（如果启用）
        comparison_analysis = {}
        if comparison_enabled and class_trends:
            comparison_analysis = self._compare_with_similar_classes(
                db, class_name, class_trends[-1]["academic_year"], class_trends[-1]["semester"]
            )

        # 班级发展建议
        class_recommendations = self._generate_class_recommendations(
            class_trends, class_trend_analysis, distribution_analysis
        )

        return {
            "class_info": {
                "class_name": class_name,
                "total_students": len(students),
                "active_students": len(set(s["student_id"] for data in class_semester_data.values() for s in data)),
                "academic_years": academic_years
            },
            "class_trends": class_trends,
            "class_trend_analysis": class_trend_analysis,
            "distribution_analysis": distribution_analysis,
            "comparison_analysis": comparison_analysis,
            "class_recommendations": class_recommendations,
            "analysis_timestamp": datetime.utcnow()
        }

    def analyze_course_trend(
        self,
        db: Session,
        course_id: int,
        academic_years: Optional[List[str]] = None,
        teacher_comparison: bool = True
    ) -> Dict[str, Any]:
        """分析课程成绩趋势"""

        # 获取课程信息
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return {"error": "课程不存在"}

        # 构建查询条件
        conditions = [
            Grade.course_id == course_id,
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if academic_years:
            conditions.append(Grade.academic_year.in_(academic_years))

        # 查询不同学期的课程成绩
        grades = db.query(Grade).join(User).filter(and_(*conditions)).order_by(
            Grade.academic_year, Grade.semester
        ).all()

        if not grades:
            return {"error": "没有找到课程成绩记录"}

        # 按学期分组
        semester_groups = defaultdict(list)
        for grade in grades:
            semester_key = f"{grade.academic_year}_{grade.semester}"
            semester_groups[semester_key].append(grade)

        # 分析每学期的课程表现
        course_trends = []
        for semester_key in sorted(semester_groups.keys()):
            semester_grades = semester_groups[semester_key]
            academic_year, semester = semester_key.split("_")

            # 计算学期统计
            scores = [(g.score / g.max_score) * 100 for g in semester_grades if g.score and g.max_score]
            gpas = [self.gpa_service.calculate_score_gpa_points(g.score, g.max_score) for g in semester_grades if g.score and g.max_score]

            if scores and gpas:
                pass_count = sum(1 for score in scores if score >= 60)
                excellent_count = sum(1 for score in scores if score >= 85)

                course_trends.append({
                    "academic_year": academic_year,
                    "semester": semester,
                    "semester_key": semester_key,
                    "student_count": len(semester_grades),
                    "average_score": round(sum(scores) / len(scores), 2),
                    "median_score": round(self._calculate_median(scores), 2),
                    "average_gpa": round(sum(gpas) / len(gpas), 3),
                    "pass_rate": round((pass_count / len(scores)) * 100, 2),
                    "excellent_rate": round((excellent_count / len(scores)) * 100, 2),
                    "score_std_dev": round(self._calculate_std_dev(scores), 2),
                    "highest_score": max(scores),
                    "lowest_score": min(scores),
                    "score_range": round(max(scores) - min(scores), 2)
                })

        # 课程趋势分析
        course_trend_analysis = self._analyze_course_trend(course_trends)

        # 教师对比分析（如果启用）
        teacher_analysis = {}
        if teacher_comparison:
            teacher_analysis = self._analyze_teacher_performance(db, course_id, academic_years)

        # 课程改进建议
        course_recommendations = self._generate_course_recommendations(
            course_trends, course_trend_analysis, teacher_analysis
        )

        return {
            "course_info": {
                "course_id": course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "credits": course.credits,
                "teacher_name": course.teacher.full_name if course.teacher else "Unknown"
            },
            "course_trends": course_trends,
            "course_trend_analysis": course_trend_analysis,
            "teacher_analysis": teacher_analysis,
            "course_recommendations": course_recommendations,
            "analysis_timestamp": datetime.utcnow()
        }

    def _group_grades_by_semester(self, grades: List[Grade]) -> Dict[str, Dict[str, Any]]:
        """按学期分组成绩"""
        semester_data = defaultdict(lambda: {
            "grades": [],
            "total_credits": 0,
            "highest_score": 0,
            "lowest_score": 100,
            "pass_count": 0,
            "pass_rate": 0
        })

        for grade in grades:
            if not grade.course or not grade.score:
                continue

            semester_key = f"{grade.academic_year}_{grade.semester}"
            percentage = (grade.score / grade.max_score) * 100

            semester_data[semester_key]["grades"].append(grade)
            semester_data[semester_key]["total_credits"] += grade.course.credits
            semester_data[semester_key]["highest_score"] = max(
                semester_data[semester_key]["highest_score"], percentage
            )
            semester_data[semester_key]["lowest_score"] = min(
                semester_data[semester_key]["lowest_score"], percentage
            )

            if percentage >= 60:
                semester_data[semester_key]["pass_count"] += 1

        # 计算及格率
        for semester_key, data in semester_data.items():
            if data["grades"]:
                data["pass_rate"] = (data["pass_count"] / len(data["grades"])) * 100

        return dict(semester_data)

    def _calculate_semester_gpa(self, grades: List[Grade]) -> Optional[float]:
        """计算学期GPA"""
        if not grades:
            return None

        total_quality_points = 0.0
        total_credits = 0

        for grade in grades:
            if not grade.course or not grade.score:
                continue

            gpa_points = self.gpa_service.calculate_score_gpa_points(grade.score, grade.max_score)
            total_quality_points += gpa_points * grade.course.credits
            total_credits += grade.course.credits

        return total_quality_points / total_credits if total_credits > 0 else None

    def _calculate_average_score(self, grades: List[Grade]) -> Optional[float]:
        """计算平均分数"""
        if not grades:
            return None

        scores = [(g.score / g.max_score) * 100 for g in grades if g.score and g.max_score]
        return sum(scores) / len(scores) if scores else None

    def _analyze_overall_trend(self, semester_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析总体趋势"""
        if len(semester_trends) < 2:
            return {"trend": "insufficient_data", "description": "数据不足，无法分析趋势"}

        # 提取GPA和分数数据
        gpas = [s["semester_gpa"] for s in semester_trends if s["semester_gpa"] > 0]
        scores = [s["average_score"] for s in semester_trends if s["average_score"] > 0]

        if len(gpas) < 2:
            return {"trend": "insufficient_data", "description": "有效数据不足"}

        # 计算趋势方向
        recent_gpa = gpas[-1]
        previous_gpa = gpas[-2]
        gpa_change = recent_gpa - previous_gpa

        # 计算总体趋势斜率
        n = len(gpas)
        x_values = list(range(n))
        slope = self._calculate_linear_regression_slope(x_values, gpas)

        # 判断趋势类型
        if slope > 0.05:
            trend_direction = "improving"
            trend_description = "持续上升"
        elif slope < -0.05:
            trend_direction = "declining"
            trend_description = "持续下降"
        else:
            trend_direction = "stable"
            trend_description = "基本稳定"

        # 计算变化幅度
        overall_change = gpas[-1] - gpas[0]
        change_rate = (overall_change / gpas[0]) * 100 if gpas[0] > 0 else 0

        return {
            "trend": trend_direction,
            "description": trend_description,
            "slope": round(slope, 4),
            "recent_change": round(gpa_change, 3),
            "overall_change": round(overall_change, 3),
            "change_rate": round(change_rate, 2),
            "consistency": self._analyze_trend_consistency(gpas),
            "volatility": round(self._calculate_std_dev(gpas), 3)
        }

    def _analyze_gpa_trend(self, gpas: List[float]) -> Dict[str, Any]:
        """分析GPA趋势详情"""
        if len(gpas) < 2:
            return {"analysis": "insufficient_data"}

        # 计算移动平均
        moving_averages = []
        window_size = min(3, len(gpas))
        for i in range(window_size - 1, len(gpas)):
            window = gpas[i - window_size + 1:i + 1]
            moving_averages.append(sum(window) / len(window))

        # 找出最高和最低点
        max_gpa_idx = gpas.index(max(gpas))
        min_gpa_idx = gpas.index(min(gpas))

        # 分析波动性
        volatility = self._calculate_std_dev(gpas)
        avg_gpa = sum(gpas) / len(gpas)
        relative_volatility = (volatility / avg_gpa) * 100 if avg_gpa > 0 else 0

        return {
            "average_gpa": round(avg_gpa, 3),
            "max_gpa": max(gpas),
            "min_gpa": min(gpas),
            "max_gpa_semester": max_gpa_idx + 1,
            "min_gpa_semester": min_gpa_idx + 1,
            "volatility": round(volatility, 3),
            "relative_volatility": round(relative_volatility, 2),
            "moving_averages": [round(ma, 3) for ma in moving_averages],
            "trend_strength": self._calculate_trend_strength(gpas)
        }

    def _analyze_learning_progress(self, semester_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析学习进步情况"""
        if len(semester_trends) < 2:
            return {"progress": "insufficient_data"}

        # 计算各项指标的进步情况
        gpa_progress = []
        score_progress = []
        credit_progress = []

        for i in range(1, len(semester_trends)):
            prev = semester_trends[i-1]
            curr = semester_trends[i]

            if prev["semester_gpa"] > 0 and curr["semester_gpa"] > 0:
                gpa_progress.append(curr["semester_gpa"] - prev["semester_gpa"])

            if prev["average_score"] > 0 and curr["average_score"] > 0:
                score_progress.append(curr["average_score"] - prev["average_score"])

            credit_progress.append(curr["total_credits"] - prev["total_credits"])

        # 分析进步模式
        avg_gpa_progress = sum(gpa_progress) / len(gpa_progress) if gpa_progress else 0
        avg_score_progress = sum(score_progress) / len(score_progress) if score_progress else 0

        # 判断进步类型
        if avg_gpa_progress > 0.1:
            progress_type = "significant_improvement"
        elif avg_gpa_progress > 0.02:
            progress_type = "moderate_improvement"
        elif avg_gpa_progress < -0.1:
            progress_type = "significant_decline"
        elif avg_gpa_progress < -0.02:
            progress_type = "moderate_decline"
        else:
            progress_type = "stable"

        # 计算累计进步
        total_gpa_change = semester_trends[-1]["cumulative_gpa"] - semester_trends[0]["semester_gpa"]
        total_score_change = semester_trends[-1]["average_score"] - semester_trends[0]["average_score"]

        return {
            "progress_type": progress_type,
            "average_gpa_progress": round(avg_gpa_progress, 3),
            "average_score_progress": round(avg_score_progress, 2),
            "total_gpa_change": round(total_gpa_change, 3),
            "total_score_change": round(total_score_change, 2),
            "total_credits_earned": sum(credit_progress),
            "semester_improvements": len([p for p in gpa_progress if p > 0]),
            "semester_declines": len([p for p in gpa_progress if p < 0])
        }

    def _analyze_learning_risks(self, semester_trends: List[Dict[str, Any]], student: User) -> Dict[str, Any]:
        """分析学习风险"""
        risks = []
        risk_level = "low"

        if len(semester_trends) < 2:
            return {"risk_level": risk_level, "risks": risks, "recommendations": []}

        recent_semesters = semester_trends[-3:]  # 最近3个学期

        # 检查GPA下降趋势
        recent_gpas = [s["semester_gpa"] for s in recent_semesters if s["semester_gpa"] > 0]
        if len(recent_gpas) >= 2:
            if all(recent_gpas[i] < recent_gpas[i-1] for i in range(1, len(recent_gpas))):
                risks.append("连续GPA下降")
                risk_level = "high"

        # 检查低GPA风险
        if recent_gpas and recent_gpas[-1] < 2.0:
            risks.append("GPA低于2.0")
            risk_level = "high"
        elif recent_gpas and recent_gpas[-1] < 2.5:
            risks.append("GPA接近警戒线")
            if risk_level != "high":
                risk_level = "medium"

        # 检查低及格率
        recent_pass_rates = [s["pass_rate"] for s in recent_semesters]
        if recent_pass_rates and recent_pass_rates[-1] < 70:
            risks.append("及格率偏低")
            if risk_level != "high":
                risk_level = "medium"

        # 检查学分获取不足
        recent_credits = [s["total_credits"] for s in recent_semesters]
        if recent_credits and recent_credits[-1] < 12:  # 假设每学期至少12学分
            risks.append("学分获取不足")
            if risk_level != "high":
                risk_level = "medium"

        # 生成风险应对建议
        recommendations = self._generate_risk_recommendations(risks)

        return {
            "risk_level": risk_level,
            "risks": risks,
            "risk_count": len(risks),
            "recommendations": recommendations,
            "last_assessment": datetime.utcnow()
        }

    def _predict_future_performance(self, semester_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测未来表现"""
        if len(semester_trends) < 3:
            return {"prediction": "insufficient_data"}

        # 提取历史数据
        gpas = [s["semester_gpa"] for s in semester_trends if s["semester_gpa"] > 0]
        scores = [s["average_score"] for s in semester_trends if s["average_score"] > 0]

        if len(gpas) < 3:
            return {"prediction": "insufficient_data"}

        # 线性回归预测
        x_values = list(range(len(gpas)))
        gpa_slope = self._calculate_linear_regression_slope(x_values, gpas)
        gpa_intercept = self._calculate_linear_regression_intercept(x_values, gpas, gpa_slope)

        # 预测未来1-2个学期
        next_semester_gpa = gpa_intercept + gpa_slope * len(gpas)
        next_next_semester_gpa = gpa_intercept + gpa_slope * (len(gpas) + 1)

        # 计算预测置信度
        prediction_confidence = self._calculate_prediction_confidence(gpas, gpa_slope)

        # 趋势外推分析
        trend_projection = self._project_trend_forward(gpas, gpa_slope)

        return {
            "next_semester_gpa": round(max(0.0, min(4.0, next_semester_gpa)), 3),
            "next_next_semester_gpa": round(max(0.0, min(4.0, next_next_semester_gpa)), 3),
            "trend_slope": round(gpa_slope, 4),
            "prediction_confidence": round(prediction_confidence, 2),
            "trend_projection": trend_projection,
            "prediction_method": "linear_regression",
            "data_points": len(gpas)
        }

    def _generate_study_recommendations(
        self,
        semester_trends: List[Dict[str, Any]],
        trend_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成学习建议"""
        recommendations = []

        # 基于趋势的建议
        if trend_analysis.get("trend") == "declining":
            recommendations.append("注意学习状态，建议寻求学习辅导")
        elif trend_analysis.get("trend") == "improving":
            recommendations.append("保持良好学习势头，继续努力")

        # 基于风险的建议
        if risk_analysis.get("risk_level") == "high":
            recommendations.append("建议与辅导员或学习顾问深入交流")
        elif risk_analysis.get("risk_level") == "medium":
            recommendations.append("需要关注学习方法和时间管理")

        # 基于最近表现的建议
        if semester_trends:
            recent_gpa = semester_trends[-1]["semester_gpa"]
            if recent_gpa < 2.0:
                recommendations.append("当前GPA较低，建议优先提高核心课程成绩")
            elif recent_gpa < 3.0:
                recommendations.append("有提升空间，建议制定详细学习计划")
            else:
                recommendations.append("表现良好，可以挑战更高目标")

        # 基于波动性的建议
        if trend_analysis.get("volatility", 0) > 0.3:
            recommendations.append("成绩波动较大，建议保持稳定的学习节奏")

        return recommendations[:6]  # 最多返回6条建议

    def _calculate_median(self, values: List[float]) -> float:
        """计算中位数"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]

    def _calculate_std_dev(self, values: List[float]) -> float:
        """计算标准差"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _calculate_linear_regression_slope(self, x: List[int], y: List[float]) -> float:
        """计算线性回归斜率"""
        n = len(x)
        if n < 2:
            return 0.0

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope

    def _calculate_linear_regression_intercept(self, x: List[int], y: List[float], slope: float) -> float:
        """计算线性回归截距"""
        n = len(x)
        if n == 0:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n
        intercept = mean_y - slope * mean_x
        return intercept

    def _analyze_trend_consistency(self, values: List[float]) -> str:
        """分析趋势一致性"""
        if len(values) < 3:
            return "insufficient_data"

        # 计算相邻变化的一致性
        changes = [values[i] - values[i-1] for i in range(1, len(values))]
        positive_changes = sum(1 for c in changes if c > 0)
        negative_changes = sum(1 for c in changes if c < 0)

        if positive_changes >= len(changes) * 0.8:
            return "consistently_increasing"
        elif negative_changes >= len(changes) * 0.8:
            return "consistently_decreasing"
        else:
            return "fluctuating"

    def _calculate_trend_strength(self, values: List[float]) -> str:
        """计算趋势强度"""
        if len(values) < 3:
            return "weak"

        slope = self._calculate_linear_regression_slope(list(range(len(values))), values)
        std_dev = self._calculate_std_dev(values)

        # 趋势强度 = |slope| / 标准差
        if std_dev > 0:
            strength = abs(slope) / std_dev
            if strength > 0.5:
                return "strong"
            elif strength > 0.2:
                return "moderate"
            else:
                return "weak"
        else:
            return "weak"

    def _calculate_prediction_confidence(self, values: List[float], slope: float) -> float:
        """计算预测置信度"""
        if len(values) < 3:
            return 0.0

        # 基于R²计算置信度
        x_values = list(range(len(values)))
        y_mean = sum(values) / len(values)

        # 计算总平方和
        ss_total = sum((y - y_mean) ** 2 for y in values)

        # 计算预测平方和
        intercept = self._calculate_linear_regression_intercept(x_values, values, slope)
        y_predicted = [intercept + slope * x for x in x_values]
        ss_residual = sum((values[i] - y_predicted[i]) ** 2 for i in range(len(values)))

        # 计算R²
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0

        # 转换为置信度百分比
        confidence = max(0.0, min(1.0, r_squared)) * 100
        return round(confidence, 2)

    def _project_trend_forward(self, values: List[float], slope: float) -> Dict[str, Any]:
        """趋势外推分析"""
        current_value = values[-1] if values else 0.0

        # 预测未来趋势
        future_trend = "improving" if slope > 0.05 else ("declining" if slope < -0.05 else "stable")

        # 计算达到特定目标需要的学期数
        targets = [3.0, 3.5, 3.8]
        semesters_to_target = {}

        for target in targets:
            if slope > 0 and target > current_value:
                semesters = math.ceil((target - current_value) / slope)
                semesters_to_target[f"target_{target}"] = semesters
            else:
                semesters_to_target[f"target_{target}"] = None

        return {
            "future_trend": future_trend,
            "current_value": round(current_value, 3),
            "semesters_to_targets": semesters_to_target,
            "projection_method": "linear_extrapolation"
        }

    def _generate_risk_recommendations(self, risks: List[str]) -> List[str]:
        """生成风险应对建议"""
        recommendations = []

        risk_map = {
            "连续GPA下降": [
                "分析GPA下降原因，重点关注表现较差的课程",
                "寻求任课教师的反馈和建议",
                "考虑参加学习小组或辅导课程"
            ],
            "GPA低于2.0": [
                "立即与学术顾问见面制定改进计划",
                "优先处理必修课程，确保基础知识掌握",
                "考虑减少课外活动，专注于学习"
            ],
            "GPA接近警戒线": [
                "提前预防，制定详细的学习计划",
                "加强时间管理，提高学习效率",
                "定期与任课教师沟通学习进展"
            ],
            "及格率偏低": [
                "复习基础知识，找出薄弱环节",
                "增加练习和复习时间",
                "寻求同学或老师的帮助"
            ],
            "学分获取不足": [
                "合理规划每学期的课程负担",
                "避免过度选修困难课程",
                "考虑暑期课程补足学分"
            ]
        }

        for risk in risks:
            if risk in risk_map:
                recommendations.extend(risk_map[risk][:2])  # 每个风险最多2条建议

        return recommendations[:5]  # 最多返回5条建议

    def _analyze_class_trend(self, class_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析班级趋势"""
        if len(class_trends) < 2:
            return {"trend": "insufficient_data"}

        # 提取数据
        gpas = [t["class_average_gpa"] for t in class_trends]
        scores = [t["class_average_score"] for t in class_trends]

        # 计算趋势
        gpa_slope = self._calculate_linear_regression_slope(list(range(len(gpas))), gpas)
        score_slope = self._calculate_linear_regression_slope(list(range(len(scores))), scores)

        # 判断趋势方向
        if gpa_slope > 0.02:
            trend_direction = "improving"
        elif gpa_slope < -0.02:
            trend_direction = "declining"
        else:
            trend_direction = "stable"

        # 计算发展稳定性
        gpa_volatility = self._calculate_std_dev(gpas)
        stability = "stable" if gpa_volatility < 0.1 else "moderate" if gpa_volatility < 0.2 else "unstable"

        return {
            "trend": trend_direction,
            "gpa_slope": round(gpa_slope, 4),
            "score_slope": round(score_slope, 4),
            "stability": stability,
            "gpa_volatility": round(gpa_volatility, 3),
            "overall_improvement": round(gpas[-1] - gpas[0], 3)
        }

    def _analyze_grade_distribution_change(self, db: Session, class_name: str, academic_years: Optional[List[str]]) -> Dict[str, Any]:
        """分析成绩分布变化"""
        # 这里可以实现更复杂的分布变化分析
        # 由于需要访问大量数据，暂时返回基本分析
        return {
            "analysis_type": "grade_distribution_change",
            "message": "分布变化分析需要更详细的实现"
        }

    def _compare_with_similar_classes(self, db: Session, class_name: str, academic_year: str, semester: str) -> Dict[str, Any]:
        """与相似班级对比"""
        # 这里可以实现班级对比分析
        return {
            "comparison_type": "class_comparison",
            "message": "班级对比分析需要更详细的实现"
        }

    def _generate_class_recommendations(self, class_trends: List[Dict[str, Any]], trend_analysis: Dict[str, Any], distribution_analysis: Dict[str, Any]) -> List[str]:
        """生成班级建议"""
        recommendations = []

        if trend_analysis.get("trend") == "declining":
            recommendations.append("班级整体成绩呈下降趋势，建议加强教学管理")
        elif trend_analysis.get("trend") == "improving":
            recommendations.append("班级表现良好，继续保持现有教学策略")

        if trend_analysis.get("stability") == "unstable":
            recommendations.append("成绩波动较大，建议关注学生学习稳定性")

        return recommendations[:4]

    def _analyze_teacher_performance(self, db: Session, course_id: int, academic_years: Optional[List[str]]) -> Dict[str, Any]:
        """分析教师表现"""
        # 这里可以实现教师表现分析
        return {
            "analysis_type": "teacher_performance",
            "message": "教师表现分析需要更详细的实现"
        }

    def _generate_course_recommendations(self, course_trends: List[Dict[str, Any]], trend_analysis: Dict[str, Any], teacher_analysis: Dict[str, Any]) -> List[str]:
        """生成课程建议"""
        recommendations = []

        if trend_analysis.get("trend") == "declining":
            recommendations.append("课程成绩呈下降趋势，建议评估教学方法")
        elif trend_analysis.get("trend") == "improving":
            recommendations.append("课程教学效果良好，继续保持")

        return recommendations[:3]