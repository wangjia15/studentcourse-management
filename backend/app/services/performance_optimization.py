from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
import json
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import time
import threading
from collections import defaultdict

# Redis imports (optional, for distributed caching)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade, GradeType, GradeStatus
from app.models.enrollment import Enrollment
from .gpa_calculation import GPACalculationService
from .grade_distribution import GradeDistributionService
from .trend_analysis import TrendAnalysisService


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.cache_lock = threading.Lock()

        # Redis缓存（如果可用）
        self.redis_client = None
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
            except:
                self.redis_client = None

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = {k: v for k, v in kwargs.items() if v is not None}
        key_string = json.dumps(key_data, sort_keys=True)
        hash_value = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{hash_value}"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 尝试从内存缓存获取
        with self.cache_lock:
            if key in self.memory_cache:
                timestamp = self.cache_timestamps.get(key, 0)
                if time.time() - timestamp < self.default_ttl:
                    return self.memory_cache[key]
                else:
                    # 过期，删除
                    del self.memory_cache[key]
                    if key in self.cache_timestamps:
                        del self.cache_timestamps[key]

        # 尝试从Redis获取
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value.decode('utf-8'))
            except:
                pass

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        success = True

        # 设置内存缓存
        with self.cache_lock:
            self.memory_cache[key] = value
            self.cache_timestamps[key] = time.time()

        # 设置Redis缓存
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            except:
                success = False

        return success

    def delete(self, key: str) -> bool:
        """删除缓存"""
        success = True

        # 删除内存缓存
        with self.cache_lock:
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]

        # 删除Redis缓存
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except:
                success = False

        return success

    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        count = 0

        # 清除内存缓存
        with self.cache_lock:
            keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.memory_cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
                count += 1

        # 清除Redis缓存
        if self.redis_client:
            try:
                redis_keys = self.redis_client.keys(f"*{pattern}*")
                if redis_keys:
                    count += self.redis_client.delete(*redis_keys)
            except:
                pass

        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.cache_lock:
            memory_cache_size = len(self.memory_cache)
            memory_keys = list(self.memory_cache.keys())

        redis_info = {}
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
            except:
                pass

        return {
            "memory_cache_size": memory_cache_size,
            "memory_cache_keys": memory_keys[:10],  # 显示前10个键
            "redis_connected": self.redis_client is not None,
            "redis_info": redis_info
        }


def cache_result(prefix: str, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 提取数据库会话和其他参数
            db = None
            cache_params = {}

            # 查找参数中的数据库会话
            if args and hasattr(args[0], 'query'):
                db = args[0]
                # 跳过db参数，不包含在缓存键中
                cache_args = args[1:]
            else:
                cache_args = args

            # 构建缓存参数
            for i, arg in enumerate(cache_args):
                if isinstance(arg, (int, float, str, bool, type(None))):
                    cache_params[f"arg_{i}"] = arg

            cache_params.update(kwargs)

            # 生成缓存键
            cache_manager = getattr(wrapper, '_cache_manager', None)
            if not cache_manager:
                return func(*args, **kwargs)

            cache_key = cache_manager._generate_cache_key(prefix, **cache_params)

            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


class PerformanceOptimizedAnalytics:
    """性能优化的分析服务"""

    def __init__(self, redis_url: Optional[str] = None):
        self.cache_manager = CacheManager(redis_url)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 初始化核心服务
        self.gpa_service = GPACalculationService()
        self.distribution_service = GradeDistributionService()
        self.trend_service = TrendAnalysisService()

        # 为装饰器设置缓存管理器
        self._setup_cache_decorators()

    def _setup_cache_decorators(self):
        """设置缓存装饰器"""
        # 为关键方法设置缓存
        methods_to_cache = [
            'calculate_student_gpa_optimized',
            'calculate_class_ranking_optimized',
            'analyze_course_distribution_optimized',
            'get_student_trend_analysis_optimized'
        ]

        for method_name in methods_to_cache:
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                # 这里可以通过动态方式添加装饰器
                method._cache_manager = self.cache_manager

    @cache_result("student_gpa", ttl=1800)  # 30分钟缓存
    def calculate_student_gpa_optimized(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        use_batch_query: bool = True
    ) -> Dict[str, Any]:
        """优化的学生GPA计算"""

        # 使用批量查询减少数据库访问
        if use_batch_query:
            return self._calculate_gpa_with_batch_query(db, student_id, academic_year, semester)
        else:
            return self.gpa_service.calculate_student_gpa_detailed(db, student_id, academic_year, semester)

    def _calculate_gpa_with_batch_query(
        self,
        db: Session,
        student_id: int,
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """使用批量查询计算GPA"""

        # 单次查询获取所有相关数据
        query = db.query(
            Grade,
            Course
        ).join(
            Course, Grade.course_id == Course.id
        ).filter(
            and_(
                Grade.student_id == student_id,
                Grade.is_published == True,
                Grade.status == GradeStatus.APPROVED.value
            )
        )

        if academic_year:
            query = query.filter(Grade.academic_year == academic_year)
        if semester:
            query = query.filter(Grade.semester == semester)

        results = query.all()

        if not results:
            return self._empty_gpa_result(student_id)

        # 处理查询结果
        course_grades = defaultdict(list)
        student_info = None

        for grade, course in results:
            course_grades[course.id].append((grade, course))
            if not student_info and grade.student:
                student_info = {
                    "student_id": student_id,
                    "student_name": grade.student.full_name,
                    "student_number": grade.student.student_id
                }

        # 计算GPA
        return self._process_gpa_calculation(course_grades, student_info, academic_year, semester)

    def _process_gpa_calculation(
        self,
        course_grades: Dict[int, List[Tuple[Grade, Course]]],
        student_info: Dict[str, Any],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """处理GPA计算逻辑"""

        total_quality_points = 0.0
        total_credits = 0
        course_details = []
        grade_breakdown = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        failed_courses = []

        for course_id, grade_list in course_grades.items():
            # 选择最佳成绩（处理重修）
            best_grade, course = max(grade_list, key=lambda x: x[0].score if x[0].score else 0)

            if best_grade.score and course:
                percentage = (best_grade.score / best_grade.max_score) * 100
                gpa_points = self.gpa_service.calculate_score_gpa_points(best_grade.score, best_grade.max_score)

                # 计算质量点
                quality_points = gpa_points * course.credits
                total_quality_points += quality_points
                total_credits += course.credits

                # 更新分布
                letter_grade = self._calculate_letter_grade(percentage)
                grade_breakdown[letter_grade] = grade_breakdown.get(letter_grade, 0) + 1

                # 记录不及格课程
                if letter_grade == "F":
                    failed_courses.append({
                        "course_id": course.id,
                        "course_name": course.course_name,
                        "score": best_grade.score,
                        "credits": course.credits
                    })

                # 课程详情
                course_details.append({
                    "course_id": course.id,
                    "course_name": course.course_name,
                    "credits": course.credits,
                    "score": best_grade.score,
                    "percentage": round(percentage, 2),
                    "gpa_points": gpa_points,
                    "letter_grade": letter_grade,
                    "quality_points": quality_points
                })

        # 计算最终GPA
        final_gpa = total_quality_points / total_credits if total_credits > 0 else 0.0
        final_gpa = round(final_gpa, 2)

        return {
            **student_info,
            "total_gpa": final_gpa,
            "total_quality_points": round(total_quality_points, 2),
            "total_credits": total_credits,
            "total_courses": len(course_grades),
            "course_details": course_details,
            "grade_breakdown": grade_breakdown,
            "failed_courses": failed_courses,
            "failed_course_count": len(failed_courses),
            "academic_year": academic_year,
            "semester": semester,
            "calculation_timestamp": datetime.utcnow()
        }

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

    def _empty_gpa_result(self, student_id: int) -> Dict[str, Any]:
        """返回空的GPA结果"""
        return {
            "student_id": student_id,
            "total_gpa": 0.0,
            "total_credits": 0,
            "total_courses": 0,
            "course_details": [],
            "grade_breakdown": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "failed_courses": [],
            "failed_course_count": 0,
            "calculation_timestamp": datetime.utcnow()
        }

    @cache_result("class_ranking", ttl=1800)
    def calculate_class_ranking_optimized(
        self,
        db: Session,
        class_name: str,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """优化的班级排名计算"""

        # 获取班级学生ID列表
        student_ids_query = db.query(User.id).filter(
            and_(
                User.role == UserRole.STUDENT,
                User.is_active == True,
                User.class_name == class_name
            )
        )

        student_ids = [row[0] for row in student_ids_query.all()]

        if not student_ids:
            return self._empty_ranking_result(class_name)

        # 分批处理学生GPA计算
        student_gpas = []
        total_students = len(student_ids)

        # 使用批量查询
        for i in range(0, total_students, batch_size):
            batch_ids = student_ids[i:i + batch_size]
            batch_gpas = self._batch_calculate_student_gpas(db, batch_ids, academic_year, semester)
            student_gpas.extend(batch_gpas)

        # 排序和计算排名
        return self._process_class_ranking(student_gpas, class_name, academic_year, semester)

    def _batch_calculate_student_gpas(
        self,
        db: Session,
        student_ids: List[int],
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> List[Dict[str, Any]]:
        """批量计算学生GPA"""

        # 构建批量查询
        query = db.query(
            Grade.student_id,
            Grade.score,
            Grade.max_score,
            Grade.academic_year,
            Grade.semester,
            Course.id.label('course_id'),
            Course.credits,
            Course.course_name
        ).join(
            Course, Grade.course_id == Course.id
        ).filter(
            and_(
                Grade.student_id.in_(student_ids),
                Grade.is_published == True,
                Grade.status == GradeStatus.APPROVED.value
            )
        )

        if academic_year:
            query = query.filter(Grade.academic_year == academic_year)
        if semester:
            query = query.filter(Grade.semester == semester)

        results = query.all()

        # 按学生分组处理
        student_data = defaultdict(lambda: {
            "total_quality_points": 0.0,
            "total_credits": 0,
            "courses": set()
        })

        for row in results:
            student_id = row.student_id

            if row.score and row.max_score and row.credits:
                percentage = (row.score / row.max_score) * 100
                gpa_points = self.gpa_service.calculate_score_gpa_points(row.score, row.max_score)

                quality_points = gpa_points * row.credits
                student_data[student_id]["total_quality_points"] += quality_points
                student_data[student_id]["total_credits"] += row.credits
                student_data[student_id]["courses"].add(row.course_id)

        # 转换为结果列表
        gpa_list = []
        for student_id, data in student_data.items():
            if data["total_credits"] > 0:
                gpa = data["total_quality_points"] / data["total_credits"]
                gpa_list.append({
                    "student_id": student_id,
                    "gpa": round(gpa, 3),
                    "total_credits": data["total_credits"],
                    "total_courses": len(data["courses"])
                })

        return gpa_list

    def _process_class_ranking(
        self,
        student_gpas: List[Dict[str, Any]],
        class_name: str,
        academic_year: Optional[str],
        semester: Optional[str]
    ) -> Dict[str, Any]:
        """处理班级排名逻辑"""

        if not student_gpas:
            return self._empty_ranking_result(class_name)

        # 按GPA排序
        student_gpas.sort(key=lambda x: x["gpa"], reverse=True)

        # 处理并列排名
        rankings = []
        current_rank = 1
        i = 0

        while i < len(student_gpas):
            current_gpa = student_gpas[i]["gpa"]
            tied_students = []

            # 找出所有相同GPA的学生
            while i < len(student_gpas) and student_gpas[i]["gpa"] == current_gpa:
                tied_students.append(student_gpas[i])
                i += 1

            # 为并列学生分配排名
            for student_data in tied_students:
                percentile = ((len(student_gpas) - current_rank) / len(student_gpas)) * 100

                rankings.append({
                    "student_id": student_data["student_id"],
                    "gpa_rank": current_rank,
                    "gpa_percentile": round(percentile, 2),
                    "current_gpa": student_data["gpa"],
                    "total_credits": student_data["total_credits"],
                    "total_courses": student_data["total_courses"],
                    "is_tied": len(tied_students) > 1,
                    "tied_count": len(tied_students)
                })

            current_rank += len(tied_students)

        # 计算班级统计
        gpas = [s["gpa"] for s in student_gpas]
        class_average = sum(gpas) / len(gpas)
        class_median = self._calculate_median(gpas)

        class_statistics = {
            "total_students": len(student_gpas),
            "average_gpa": round(class_average, 3),
            "median_gpa": round(class_median, 3),
            "highest_gpa": max(gpas),
            "lowest_gpa": min(gpas),
            "gpa_range": round(max(gpas) - min(gpas), 3)
        }

        return {
            "class_name": class_name,
            "total_students": len(student_gpas),
            "rankings": rankings,
            "class_statistics": class_statistics,
            "academic_year": academic_year,
            "semester": semester,
            "calculation_timestamp": datetime.utcnow()
        }

    def _calculate_median(self, values: List[float]) -> float:
        """计算中位数"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]

    def _empty_ranking_result(self, class_name: str) -> Dict[str, Any]:
        """返回空的排名结果"""
        return {
            "class_name": class_name,
            "total_students": 0,
            "rankings": [],
            "class_statistics": {},
            "calculation_timestamp": datetime.utcnow()
        }

    async def parallel_calculate_multiple_students_gpa(
        self,
        db: Session,
        student_ids: List[int],
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """并行计算多个学生的GPA"""

        # 创建任务
        loop = asyncio.get_event_loop()
        tasks = []

        for student_id in student_ids:
            task = loop.run_in_executor(
                self.executor,
                self.calculate_student_gpa_optimized,
                db, student_id, academic_year, semester
            )
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                # 处理异常情况
                continue

        return valid_results

    def invalidate_cache_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        return self.cache_manager.clear_pattern(pattern)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        cache_stats = self.cache_manager.get_cache_stats()

        return {
            "cache_statistics": cache_stats,
            "thread_pool_info": {
                "max_workers": self.executor._max_workers,
                "active_threads": threading.active_count()
            },
            "optimization_features": {
                "batch_queries_enabled": True,
                "caching_enabled": True,
                "parallel_processing_enabled": True,
                "redis_available": REDIS_AVAILABLE and self.cache_manager.redis_client is not None
            }
        }

    def warm_up_cache(self, db: Session, student_ids: List[int] = None, class_names: List[str] = None):
        """预热缓存"""
        if student_ids:
            for student_id in student_ids[:100]:  # 限制预热数量
                try:
                    self.calculate_student_gpa_optimized(db, student_id)
                except:
                    continue

        if class_names:
            for class_name in class_names[:20]:  # 限制预热数量
                try:
                    self.calculate_class_ranking_optimized(db, class_name)
                except:
                    continue

    def cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        # 这里可以实现更复杂的清理逻辑
        return self.cache_manager.clear_pattern("")  # 清除所有缓存