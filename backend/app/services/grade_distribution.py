from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
import math
from decimal import Decimal, ROUND_HALF_UP
from collections import Counter

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade, GradeType, GradeStatus
from app.models.enrollment import Enrollment


class GradeDistributionService:
    """成绩分布分析服务"""

    def __init__(self):
        self.caching_enabled = True
        self._distribution_cache = {}

    def calculate_basic_statistics(self, scores: List[float]) -> Dict[str, float]:
        """计算基础统计指标"""
        if not scores:
            return {
                "mean": 0.0,
                "median": 0.0,
                "mode": 0.0,
                "std_dev": 0.0,
                "variance": 0.0,
                "min": 0.0,
                "max": 0.0,
                "range": 0.0,
                "q1": 0.0,
                "q3": 0.0,
                "iqr": 0.0
            }

        # 基础统计
        n = len(scores)
        mean = sum(scores) / n

        sorted_scores = sorted(scores)
        median = self._calculate_median(sorted_scores)

        # 众数（可能有多个）
        score_counts = Counter(scores)
        max_count = max(score_counts.values())
        modes = [score for score, count in score_counts.items() if count == max_count]
        mode = modes[0] if modes else 0.0

        # 标准差和方差
        variance = sum((x - mean) ** 2 for x in scores) / n
        std_dev = math.sqrt(variance)

        # 最值和范围
        min_score = min(scores)
        max_score = max(scores)
        score_range = max_score - min_score

        # 四分位数
        q1 = self._calculate_percentile(sorted_scores, 25)
        q3 = self._calculate_percentile(sorted_scores, 75)
        iqr = q3 - q1

        return {
            "mean": round(float(Decimal(str(mean)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "median": round(float(Decimal(str(median)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "mode": round(float(Decimal(str(mode)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "std_dev": round(float(Decimal(str(std_dev)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "variance": round(float(Decimal(str(variance)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "min": round(float(Decimal(str(min_score)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "max": round(float(Decimal(str(max_score)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "range": round(float(Decimal(str(score_range)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "q1": round(float(Decimal(str(q1)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "q3": round(float(Decimal(str(q3)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "iqr": round(float(Decimal(str(iqr)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 2),
            "count": n
        }

    def analyze_course_grade_distribution(
        self,
        db: Session,
        course_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """分析课程成绩分布"""

        # 获取课程信息
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        # 构建查询条件
        conditions = [
            Grade.course_id == course_id,
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if academic_year:
            conditions.append(Grade.academic_year == academic_year)
        if semester:
            conditions.append(Grade.semester == semester)

        # 查询成绩记录
        grades = db.query(Grade).join(User).filter(and_(*conditions)).all()

        if not grades:
            return {
                "course_id": course_id,
                "course_name": course.course_name,
                "total_students": 0,
                "message": "没有找到符合条件的成绩记录",
                "analysis_timestamp": datetime.utcnow()
            }

        # 准备分析数据
        scores = []
        percentages = []
        letter_grades = []
        five_level_grades = []
        student_details = []

        for grade in grades:
            if grade.score and grade.max_score:
                percentage = (grade.score / grade.max_score) * 100
                scores.append(percentage)
                percentages.append(percentage)

                # 计算等级
                letter_grade = self._calculate_letter_grade(percentage)
                five_level_grade = self._calculate_five_level_grade(percentage)

                letter_grades.append(letter_grade)
                five_level_grades.append(five_level_grade)

                if include_details:
                    student_details.append({
                        "student_id": grade.student_id,
                        "student_name": grade.student.full_name if grade.student else "Unknown",
                        "score": grade.score,
                        "percentage": round(percentage, 2),
                        "letter_grade": letter_grade,
                        "five_level_grade": five_level_grade
                    })

        # 基础统计指标
        statistics = self.calculate_basic_statistics(scores)

        # 成绩等级分布
        grade_distribution = Counter(letter_grades)
        five_level_distribution = Counter(five_level_grades)

        # 分数段分布（10分档）
        ten_point_distribution = self._calculate_ten_point_distribution(scores)

        # 五级制分布
        five_level_dist = {
            "优秀": five_level_distribution.get("优秀", 0),
            "良好": five_level_distribution.get("良好", 0),
            "中等": five_level_distribution.get("中等", 0),
            "及格": five_level_distribution.get("及格", 0),
            "不及格": five_level_distribution.get("不及格", 0)
        }

        # 计算及格率和优秀率
        pass_count = sum(1 for score in scores if score >= 60)
        excellent_count = sum(1 for score in scores if score >= 85)
        good_count = sum(1 for score in scores if score >= 75)

        pass_rate = (pass_count / len(scores)) * 100
        excellent_rate = (excellent_count / len(scores)) * 100
        good_rate = (good_count / len(scores)) * 100

        # 生成直方图数据
        histogram_data = self._generate_histogram_data(scores, bin_size=5)

        # 异常值检测
        outliers = self._detect_outliers(scores)

        # 成绩集中度分析
        concentration_analysis = self._analyze_grade_concentration(scores)

        return {
            "course_info": {
                "course_id": course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "credits": course.credits,
                "teacher_name": course.teacher.full_name if course.teacher else "Unknown",
                "academic_year": academic_year,
                "semester": semester
            },
            "overview": {
                "total_students": len(grades),
                "submitted_count": len(grades),
                "average_score": statistics["mean"],
                "median_score": statistics["median"],
                "highest_score": statistics["max"],
                "lowest_score": statistics["min"],
                "score_range": statistics["range"],
                "standard_deviation": statistics["std_dev"]
            },
            "distribution": {
                "letter_grades": dict(grade_distribution),
                "five_level_distribution": five_level_dist,
                "ten_point_distribution": ten_point_distribution,
                "histogram_data": histogram_data
            },
            "rates": {
                "pass_rate": round(pass_rate, 2),
                "excellent_rate": round(excellent_rate, 2),
                "good_rate": round(good_rate, 2),
                "fail_rate": round(100 - pass_rate, 2)
            },
            "statistics": statistics,
            "quality_analysis": {
                "outliers": outliers,
                "concentration": concentration_analysis,
                "grade_spread": "集中" if statistics["std_dev"] < 10 else "分散"
            },
            "student_details": student_details if include_details else [],
            "analysis_timestamp": datetime.utcnow()
        }

    def analyze_class_grade_distribution(
        self,
        db: Session,
        class_name: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        course_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """分析班级成绩分布"""

        # 获取班级学生
        student_conditions = [
            User.role == UserRole.STUDENT,
            User.is_active == True,
            User.class_name == class_name
        ]

        students = db.query(User).filter(and_(*student_conditions)).all()
        if not students:
            return {"error": "班级不存在或没有学生"}

        student_ids = [s.id for s in students]

        # 构建成绩查询条件
        grade_conditions = [
            Grade.student_id.in_(student_ids),
            Grade.is_published == True,
            Grade.status == GradeStatus.APPROVED.value
        ]

        if academic_year:
            grade_conditions.append(Grade.academic_year == academic_year)
        if semester:
            grade_conditions.append(Grade.semester == semester)

        # 查询成绩
        query = db.query(Grade).join(Course).filter(and_(*grade_conditions))

        if course_types:
            query = query.filter(Course.course_type.in_(course_types))

        grades = query.all()

        if not grades:
            return {
                "class_name": class_name,
                "total_students": len(students),
                "message": "没有找到符合条件的成绩记录",
                "analysis_timestamp": datetime.utcnow()
            }

        # 按课程分组分析
        course_analysis = {}
        all_scores = []

        for grade in grades:
            if not grade.course or not grade.score:
                continue

            course_id = grade.course_id
            if course_id not in course_analysis:
                course_analysis[course_id] = {
                    "course_name": grade.course.course_name,
                    "course_code": grade.course.course_code,
                    "credits": grade.course.credits,
                    "teacher": grade.course.teacher.full_name if grade.course.teacher else "Unknown",
                    "scores": [],
                    "students": []
                }

            percentage = (grade.score / grade.max_score) * 100
            course_analysis[course_id]["scores"].append(percentage)
            all_scores.append(percentage)

            course_analysis[course_id]["students"].append({
                "student_id": grade.student_id,
                "student_name": grade.student.full_name if grade.student else "Unknown",
                "score": percentage
            })

        # 计算整体统计
        overall_statistics = self.calculate_basic_statistics(all_scores)

        # 分析每门课程
        course_details = []
        for course_id, data in course_analysis.items():
            if data["scores"]:
                course_stats = self.calculate_basic_statistics(data["scores"])

                # 计算该课程的及格率等
                pass_count = sum(1 for score in data["scores"] if score >= 60)
                excellent_count = sum(1 for score in data["scores"] if score >= 85)

                course_details.append({
                    "course_id": course_id,
                    "course_name": data["course_name"],
                    "course_code": data["course_code"],
                    "credits": data["credits"],
                    "teacher": data["teacher"],
                    "student_count": len(data["students"]),
                    "statistics": course_stats,
                    "pass_rate": round((pass_count / len(data["scores"])) * 100, 2),
                    "excellent_rate": round((excellent_count / len(data["scores"])) * 100, 2)
                })

        # 班级整体分布
        grade_distribution = self._calculate_grade_distribution(all_scores)
        ten_point_distribution = self._calculate_ten_point_distribution(all_scores)

        # 按学生个人统计
        student_performance = []
        for student in students:
            student_grades = [g for g in grades if g.student_id == student.id]
            if student_grades:
                student_scores = [(g.score / g.max_score) * 100 for g in student_grades if g.score and g.max_score]
                if student_scores:
                    student_avg = sum(student_scores) / len(student_scores)
                    student_performance.append({
                        "student_id": student.id,
                        "student_name": student.full_name,
                        "student_number": student.student_id,
                        "average_score": round(student_avg, 2),
                        "course_count": len(student_scores),
                        "highest_score": max(student_scores),
                        "lowest_score": min(student_scores)
                    })

        # 排序学生表现
        student_performance.sort(key=lambda x: x["average_score"], reverse=True)

        return {
            "class_info": {
                "class_name": class_name,
                "total_students": len(students),
                "students_with_grades": len(student_performance),
                "academic_year": academic_year,
                "semester": semester
            },
            "overall_statistics": overall_statistics,
            "distribution": {
                "grade_distribution": grade_distribution,
                "ten_point_distribution": ten_point_distribution
            },
            "course_analysis": course_details,
            "student_performance": student_performance[:20],  # 前20名
            "quality_metrics": {
                "class_average": overall_statistics["mean"],
                "class_median": overall_statistics["median"],
                "score_consistency": "高" if overall_statistics["std_dev"] < 8 else "中" if overall_statistics["std_dev"] < 15 else "低",
                "performance_gap": overall_statistics["max"] - overall_statistics["min"]
            },
            "analysis_timestamp": datetime.utcnow()
        }

    def compare_class_performance(
        self,
        db: Session,
        class_names: List[str],
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """班级成绩对比分析"""

        class_comparison = {}
        all_class_scores = {}

        for class_name in class_names:
            analysis = self.analyze_class_grade_distribution(
                db, class_name, academic_year, semester
            )

            if "overall_statistics" in analysis:
                class_comparison[class_name] = {
                    "average_score": analysis["overall_statistics"]["mean"],
                    "median_score": analysis["overall_statistics"]["median"],
                    "std_deviation": analysis["overall_statistics"]["std_dev"],
                    "student_count": analysis["class_info"]["students_with_grades"],
                    "pass_rate": analysis["overall_statistics"].get("pass_rate", 0)
                }

                # 收集所有分数用于总体统计
                if "distribution" in analysis and "ten_point_distribution" in analysis["distribution"]:
                    all_class_scores[class_name] = analysis["distribution"]["ten_point_distribution"]

        # 计算班级排名
        ranked_classes = sorted(
            class_comparison.items(),
            key=lambda x: x[1]["average_score"],
            reverse=True
        )

        # 方差分析（ANOVA简化版）
        class_averages = [data["average_score"] for data in class_comparison.values()]
        overall_average = sum(class_averages) / len(class_averages) if class_averages else 0

        variance_between = sum((avg - overall_average) ** 2 for avg in class_averages) / len(class_averages)

        # 生成对比报告
        comparison_summary = {
            "best_class": ranked_classes[0] if ranked_classes else None,
            "worst_class": ranked_classes[-1] if ranked_classes else None,
            "performance_gap": class_comparison[ranked_classes[0][0]]["average_score"] - class_comparison[ranked_classes[-1][0]]["average_score"] if len(ranked_classes) >= 2 else 0,
            "overall_average": overall_average,
            "variance_between_classes": round(variance_between, 2),
            "performance_consistency": "高" if variance_between < 5 else "中" if variance_between < 15 else "低"
        }

        return {
            "comparison_parameters": {
                "classes": class_names,
                "academic_year": academic_year,
                "semester": semester
            },
            "class_comparison": class_comparison,
            "ranked_classes": [{"class_name": name, "rank": idx + 1, **data} for idx, (name, data) in enumerate(ranked_classes)],
            "comparison_summary": comparison_summary,
            "score_distributions": all_class_scores,
            "analysis_timestamp": datetime.utcnow()
        }

    def _calculate_median(self, sorted_values: List[float]) -> float:
        """计算中位数"""
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]

    def _calculate_percentile(self, sorted_values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not sorted_values:
            return 0.0

        n = len(sorted_values)
        position = (percentile / 100) * (n - 1)

        if position.is_integer():
            return sorted_values[int(position)]
        else:
            lower_index = int(position)
            upper_index = lower_index + 1
            weight = position - lower_index

            if upper_index < n:
                return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
            else:
                return sorted_values[lower_index]

    def _calculate_letter_grade(self, percentage: float) -> str:
        """计算等级成绩"""
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

    def _calculate_five_level_grade(self, percentage: float) -> str:
        """计算五级制成绩"""
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

    def _calculate_ten_point_distribution(self, scores: List[float]) -> Dict[str, int]:
        """计算10分档分布"""
        distribution = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "50-59": 0,
            "40-49": 0,
            "30-39": 0,
            "20-29": 0,
            "10-19": 0,
            "0-9": 0
        }

        for score in scores:
            if score >= 90:
                distribution["90-100"] += 1
            elif score >= 80:
                distribution["80-89"] += 1
            elif score >= 70:
                distribution["70-79"] += 1
            elif score >= 60:
                distribution["60-69"] += 1
            elif score >= 50:
                distribution["50-59"] += 1
            elif score >= 40:
                distribution["40-49"] += 1
            elif score >= 30:
                distribution["30-39"] += 1
            elif score >= 20:
                distribution["20-29"] += 1
            elif score >= 10:
                distribution["10-19"] += 1
            else:
                distribution["0-9"] += 1

        return distribution

    def _calculate_grade_distribution(self, scores: List[float]) -> Dict[str, int]:
        """计算等级分布"""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

        for score in scores:
            grade = self._calculate_letter_grade(score)
            distribution[grade] += 1

        return distribution

    def _generate_histogram_data(self, scores: List[float], bin_size: int = 5) -> List[Dict[str, Any]]:
        """生成直方图数据"""
        if not scores:
            return []

        min_score = min(scores)
        max_score = max(scores)

        # 创建区间
        bins = []
        current = min_score
        while current < max_score:
            bin_start = current
            bin_end = min(current + bin_size, max_score)
            bins.append({
                "range": f"{round(bin_start)}-{round(bin_end)}",
                "count": 0,
                "start": bin_start,
                "end": bin_end
            })
            current += bin_size

        # 统计每个区间的数量
        for score in scores:
            for bin_data in bins:
                if bin_data["start"] <= score < bin_data["end"] or (bin_data["end"] == max_score and score == bin_data["end"]):
                    bin_data["count"] += 1
                    break

        return bins

    def _detect_outliers(self, scores: List[float]) -> Dict[str, Any]:
        """检测异常值（使用IQR方法）"""
        if len(scores) < 4:
            return {"outliers": [], "outlier_count": 0, "method": "IQR"}

        sorted_scores = sorted(scores)
        q1 = self._calculate_percentile(sorted_scores, 25)
        q3 = self._calculate_percentile(sorted_scores, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = [score for score in scores if score < lower_bound or score > upper_bound]

        return {
            "outliers": outliers,
            "outlier_count": len(outliers),
            "method": "IQR",
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "iqr": round(iqr, 2)
        }

    def _analyze_grade_concentration(self, scores: List[float]) -> Dict[str, Any]:
        """分析成绩集中度"""
        if not scores:
            return {"concentration_level": "无数据", "details": {}}

        # 计算标准差
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        std_dev = math.sqrt(variance)

        # 根据标准差判断集中度
        if std_dev < 8:
            concentration_level = "高度集中"
        elif std_dev < 15:
            concentration_level = "中度集中"
        else:
            concentration_level = "分散"

        # 计算主要分布区间
        sorted_scores = sorted(scores)
        percentage_68 = len([s for s in scores if mean - std_dev <= s <= mean + std_dev]) / len(scores) * 100
        percentage_95 = len([s for s in scores if mean - 2*std_dev <= s <= mean + 2*std_dev]) / len(scores) * 100

        return {
            "concentration_level": concentration_level,
            "standard_deviation": round(std_dev, 2),
            "details": {
                "within_1_std": round(percentage_68, 1),  # 1个标准差内的百分比
                "within_2_std": round(percentage_95, 1),  # 2个标准差内的百分比
                "main_range": f"{round(mean - std_dev, 1)} - {round(mean + std_dev, 1)}"
            }
        }