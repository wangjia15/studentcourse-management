import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock

from app.services.gpa_calculation import GPACalculationService
from app.services.grade_distribution import GradeDistributionService
from app.services.trend_analysis import TrendAnalysisService
from app.services.statistical_reports import StatisticalReportService
from app.services.visualization import VisualizationService
from app.services.performance_optimization import PerformanceOptimizedAnalytics, CacheManager

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade, GradeType, GradeStatus


class TestGPACalculationService:
    """GPA计算服务测试"""

    def setup_method(self):
        """测试前设置"""
        self.gpa_service = GPACalculationService()

    def test_calculate_score_gpa_points_boundary_values(self):
        """测试GPA计算边界值"""
        # 测试各个分数段的边界值
        test_cases = [
            (90, 100, 4.0),  # 90-100: 4.0
            (89.5, 100, 4.0),  # 接近90
            (89.9, 100, 4.0),  # 接近90
            (85, 100, 3.7),    # 85-89: 3.7
            (84.9, 100, 3.3),  # 82-84: 3.3
            (82, 100, 3.3),    # 82-84: 3.3
            (81.9, 100, 3.0),  # 78-81: 3.0
            (60, 100, 1.0),    # 60-63: 1.0
            (59.9, 100, 0.0),  # <60: 0.0
            (0, 100, 0.0),     # 0分
        ]

        for score, max_score, expected_gpa in test_cases:
            result = self.gpa_service.calculate_score_gpa_points(score, max_score)
            assert result == expected_gpa, f"分数 {score}/{max_score} 应该得到 GPA {expected_gpa}，实际得到 {result}"

    def test_calculate_score_gpa_points_edge_cases(self):
        """测试GPA计算边界情况"""
        # 测试None值
        assert self.gpa_service.calculate_score_gpa_points(None, 100) == 0.0
        assert self.gpa_service.calculate_score_gpa_points(80, None) == 0.0
        assert self.gpa_service.calculate_score_gpa_points(80, 0) == 0.0

        # 测试不同满分值
        assert self.gpa_service.calculate_score_gpa_points(45, 50) == 3.7  # 90%
        assert self.gpa_service.calculate_score_gpa_points(85, 100) == 3.7  # 85%
        assert self.gpa_service.calculate_score_gpa_points(170, 200) == 3.7  # 85%

    def test_calculate_letter_grade(self):
        """测试等级成绩计算"""
        test_cases = [
            (95, 100, "A"),
            (90, 100, "A"),
            (89.9, 100, "B"),
            (80, 100, "B"),
            (79.9, 100, "C"),
            (70, 100, "C"),
            (69.9, 100, "D"),
            (60, 100, "D"),
            (59.9, 100, "F"),
            (0, 100, "F"),
        ]

        for score, max_score, expected_grade in test_cases:
            result = self.gpa_service.calculate_letter_grade(score, max_score)
            assert result == expected_grade, f"分数 {score}/{max_score} 应该得到等级 {expected_grade}，实际得到 {result}"

    def test_calculate_five_level_grade(self):
        """测试五级制成绩计算"""
        test_cases = [
            (95, 100, "优秀"),
            (90, 100, "优秀"),
            (89.9, 100, "良好"),
            (80, 100, "良好"),
            (79.9, 100, "中等"),
            (70, 100, "中等"),
            (69.9, 100, "及格"),
            (60, 100, "及格"),
            (59.9, 100, "不及格"),
            (0, 100, "不及格"),
        ]

        for score, max_score, expected_grade in test_cases:
            result = self.gpa_service.calculate_five_level_grade(score, max_score)
            assert result == expected_grade, f"分数 {score}/{max_score} 应该得到五级制 {expected_grade}，实际得到 {result}"

    def test_calculate_student_gpa_detailed_mock(self):
        """测试详细学生GPA计算（使用Mock）"""
        # 创建Mock对象
        mock_db = Mock(spec=Session)
        mock_student = Mock()
        mock_student.id = 1
        mock_student.full_name = "张三"
        mock_student.student_id = "2021001"

        mock_course = Mock()
        mock_course.id = 1
        mock_course.course_name = "数学"
        mock_course.credits = 3

        mock_grade = Mock()
        mock_grade.student_id = 1
        mock_grade.course_id = 1
        mock_grade.score = 85
        mock_grade.max_score = 100
        mock_grade.academic_year = "2024-2025"
        mock_grade.semester = "Fall"
        mock_grade.is_published = True
        mock_grade.status = GradeStatus.APPROVED.value
        mock_grade.course = mock_course
        mock_grade.student = mock_student

        # 模拟数据库查询
        mock_query_result = [mock_grade]
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_query_result
        mock_db.query.return_value.filter.return_value.first.return_value = mock_student

        # 执行测试
        result = self.gpa_service.calculate_student_gpa_detailed(mock_db, 1)

        # 验证结果
        assert result["student_id"] == 1
        assert result["student_name"] == "张三"
        assert result["total_gpa"] == 3.7  # 85分对应3.7
        assert result["total_credits"] == 3
        assert result["total_courses"] == 1
        assert "course_details" in result
        assert "grade_breakdown" in result

    def test_predict_graduation_gpa(self):
        """测试毕业GPA预测"""
        # 创建Mock数据库
        mock_db = Mock(spec=Session)

        # 模拟当前GPA数据
        mock_cumulative_data = {
            "cumulative_gpa": 3.0,
            "total_credits": 60
        }

        with patch.object(self.gpa_service, 'calculate_cumulative_gpa', return_value=mock_cumulative_data):
            result = self.gpa_service.predict_graduation_gpa(mock_db, 1, 60, 3.2)

            assert result["prediction_possible"] is True
            assert "current_status" in result
            assert "predictions" in result
            assert "scenarios" in result
            assert "required_remaining_gpa" in result
            assert result["remaining_credits"] == 60


class TestGradeDistributionService:
    """成绩分布分析服务测试"""

    def setup_method(self):
        """测试前设置"""
        self.distribution_service = GradeDistributionService()

    def test_calculate_basic_statistics(self):
        """测试基础统计指标计算"""
        # 测试正常数据
        scores = [85, 90, 78, 92, 88, 76, 95, 82, 89, 91]
        result = self.distribution_service.calculate_basic_statistics(scores)

        assert result["mean"] == pytest.approx(86.6, rel=1e-2)
        assert result["median"] == pytest.approx(88.5, rel=1e-2)
        assert result["min"] == 76
        assert result["max"] == 95
        assert result["std_dev"] > 0

        # 测试空数据
        empty_result = self.distribution_service.calculate_basic_statistics([])
        assert empty_result["mean"] == 0.0
        assert empty_result["median"] == 0.0
        assert empty_result["count"] == 0

    def test_calculate_median(self):
        """测试中位数计算"""
        # 奇数个数据
        odd_data = [1, 3, 5, 7, 9]
        assert self.distribution_service._calculate_median(odd_data) == 5

        # 偶数个数据
        even_data = [1, 3, 5, 7]
        assert self.distribution_service._calculate_median(even_data) == 4

        # 单个数据
        single_data = [5]
        assert self.distribution_service._calculate_median(single_data) == 5

    def test_calculate_percentile(self):
        """测试百分位数计算"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        # 25百分位数（第一个四分位数）
        q1 = self.distribution_service._calculate_percentile(data, 25)
        assert q1 == pytest.approx(3.25, rel=1e-2)

        # 中位数（50百分位数）
        median = self.distribution_service._calculate_percentile(data, 50)
        assert median == 5.5

        # 75百分位数（第三个四分位数）
        q3 = self.distribution_service._calculate_percentile(data, 75)
        assert q3 == pytest.approx(7.75, rel=1e-2)

    def test_calculate_ten_point_distribution(self):
        """测试10分档分布计算"""
        scores = [95, 88, 76, 65, 54, 43, 32, 21, 15, 8]
        result = self.distribution_service._calculate_ten_point_distribution(scores)

        assert result["90-100"] == 1
        assert result["80-89"] == 1
        assert result["70-79"] == 1
        assert result["60-69"] == 1
        assert result["50-59"] == 1
        assert result["40-49"] == 1
        assert result["30-39"] == 1
        assert result["20-29"] == 1
        assert result["10-19"] == 1
        assert result["0-9"] == 1

    def test_detect_outliers(self):
        """测试异常值检测"""
        # 正常数据（无异常值）
        normal_data = [75, 78, 82, 85, 88, 90, 92]
        result = self.distribution_service._detect_outliers(normal_data)
        assert result["outlier_count"] == 0

        # 包含异常值的数据
        outlier_data = [75, 78, 82, 85, 88, 90, 150]  # 150是异常值
        result = self.distribution_service._detect_outliers(outlier_data)
        assert result["outlier_count"] > 0
        assert 150 in result["outliers"]

    def test_analyze_grade_concentration(self):
        """测试成绩集中度分析"""
        # 高度集中的数据
        concentrated_data = [85, 86, 84, 87, 85, 86, 84]
        result = self.distribution_service._analyze_grade_concentration(concentrated_data)
        assert result["concentration_level"] == "高度集中"

        # 分散的数据
        dispersed_data = [60, 75, 90, 45, 95, 55, 88]
        result = self.distribution_service._analyze_grade_concentration(dispersed_data)
        assert result["concentration_level"] in ["分散", "中度集中"]


class TestTrendAnalysisService:
    """趋势分析服务测试"""

    def setup_method(self):
        """测试前设置"""
        self.trend_service = TrendAnalysisService()

    def test_analyze_overall_trend(self):
        """测试总体趋势分析"""
        # 上升趋势
        improving_trends = [
            {"semester_gpa": 2.5},
            {"semester_gpa": 2.8},
            {"semester_gpa": 3.1},
            {"semester_gpa": 3.3}
        ]
        result = self.trend_service._analyze_overall_trend(improving_trends)
        assert result["trend"] == "improving"
        assert result["description"] == "持续上升"

        # 下降趋势
        declining_trends = [
            {"semester_gpa": 3.5},
            {"semester_gpa": 3.2},
            {"semester_gpa": 2.9},
            {"semester_gpa": 2.7}
        ]
        result = self.trend_service._analyze_overall_trend(declining_trends)
        assert result["trend"] == "declining"
        assert result["description"] == "持续下降"

        # 稳定趋势
        stable_trends = [
            {"semester_gpa": 3.0},
            {"semester_gpa": 3.1},
            {"semester_gpa": 3.0},
            {"semester_gpa": 3.1}
        ]
        result = self.trend_service._analyze_overall_trend(stable_trends)
        assert result["trend"] == "stable"

    def test_calculate_linear_regression_slope(self):
        """测试线性回归斜率计算"""
        # 完全正相关
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]  # y = 2x
        slope = self.trend_service._calculate_linear_regression_slope(x, y)
        assert slope == pytest.approx(2.0, rel=1e-10)

        # 完全负相关
        y_negative = [10, 8, 6, 4, 2]  # y = -2x + 12
        slope = self.trend_service._calculate_linear_regression_slope(x, y_negative)
        assert slope == pytest.approx(-2.0, rel=1e-10)

        # 无相关
        y_random = [5, 3, 7, 2, 8]
        slope = self.trend_service._calculate_linear_regression_slope(x, y_random)
        assert isinstance(slope, float)

    def test_analyze_trend_consistency(self):
        """测试趋势一致性分析"""
        # 一致上升
        consistent_increasing = [2.0, 2.5, 3.0, 3.5, 4.0]
        result = self.trend_service._analyze_trend_consistency(consistent_increasing)
        assert result == "consistently_increasing"

        # 一致下降
        consistent_decreasing = [4.0, 3.5, 3.0, 2.5, 2.0]
        result = self.trend_service._analyze_trend_consistency(consistent_decreasing)
        assert result == "consistently_decreasing"

        # 波动
        fluctuating = [3.0, 2.5, 3.5, 2.0, 4.0]
        result = self.trend_service._analyze_trend_consistency(fluctuating)
        assert result == "fluctuating"

    def test_calculate_prediction_confidence(self):
        """测试预测置信度计算"""
        # 完美线性关系（高置信度）
        perfect_linear = [2.0, 2.5, 3.0, 3.5, 4.0]
        slope = 0.5
        confidence = self.trend_service._calculate_prediction_confidence(perfect_linear, slope)
        assert confidence > 90

        # 随机数据（低置信度）
        random_data = [3.2, 2.8, 3.5, 2.9, 3.1]
        slope = 0.1
        confidence = self.trend_service._calculate_prediction_confidence(random_data, slope)
        assert 0 <= confidence <= 100

    def test_generate_risk_recommendations(self):
        """测试风险建议生成"""
        risks = ["连续GPA下降", "GPA低于2.0", "及格率偏低"]
        recommendations = self.trend_service._generate_risk_recommendations(risks)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("GPA" in rec for rec in recommendations)


class TestVisualizationService:
    """可视化服务测试"""

    def setup_method(self):
        """测试前设置"""
        self.visualization_service = VisualizationService()

    def test_get_pie_chart_data_grade_distribution(self):
        """测试成绩分布饼图数据获取"""
        mock_db = Mock(spec=Session)

        # 创建模拟成绩数据
        mock_grades = []
        for i in range(10):
            mock_grade = Mock()
            mock_grade.score = 85 + i  # 85-94分
            mock_grade.max_score = 100
            mock_grade.course = Mock()
            mock_grades.append(mock_grade)

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_grades

        result = self.visualization_service._get_grade_distribution_pie_data(
            mock_db, None, None, None
        )

        assert "labels" in result
        assert "datasets" in result
        assert "chart_info" in result
        assert result["chart_info"]["type"] == "grade_distribution_pie"

    def test_get_bar_chart_data_class_comparison(self):
        """测试班级对比柱状图数据获取"""
        mock_db = Mock(spec=Session)
        class_names = ["Class A", "Class B"]

        with patch.object(self.visualization_service.gpa_service, 'calculate_class_ranking') as mock_ranking:
            mock_ranking.return_value = {
                "class_statistics": {
                    "average_gpa": 3.2,
                    "median_gpa": 3.1,
                    "total_students": 30,
                    "pass_rate": 85.0
                }
            }

            result = self.visualization_service._get_class_comparison_bar_data(
                mock_db, class_names, None, None
            )

            assert "labels" in result
            assert "datasets" in result
            assert len(result["labels"]) == 2
            assert len(result["datasets"]) > 0

    def test_get_line_chart_data_gpa_trend(self):
        """测试GPA趋势折线图数据获取"""
        mock_db = Mock(spec=Session)
        student_id = 1

        with patch.object(self.visualization_service.trend_service, 'analyze_student_grade_trend') as mock_trend:
            mock_trend.return_value = {
                "semester_trends": [
                    {"academic_year": "2024-2025", "semester": "Fall", "semester_gpa": 3.0, "cumulative_gpa": 3.0, "average_score": 75},
                    {"academic_year": "2024-2025", "semester": "Spring", "semester_gpa": 3.2, "cumulative_gpa": 3.1, "average_score": 80}
                ]
            }

            result = self.visualization_service._get_gpa_trend_line_data(
                mock_db, student_id, None
            )

            assert "labels" in result
            assert "datasets" in result
            assert len(result["labels"]) == 2
            assert len(result["datasets"]) == 3  # GPA, 累计GPA, 平均分

    def test_get_radar_chart_data_student(self):
        """测试学生能力雷达图数据获取"""
        mock_db = Mock(spec=Session)
        student_id = 1

        with patch.object(self.visualization_service.gpa_service, 'calculate_student_gpa_detailed') as mock_gpa:
            mock_gpa.return_value = {
                "student_name": "张三",
                "total_gpa": 3.2
            }

            with patch.object(self.visualization_service.trend_service, 'analyze_student_grade_trend') as mock_trend:
                mock_trend.return_value = {
                    "trend_analysis": {"trend": "improving", "volatility": 0.2}
                }

                result = self.visualization_service._get_student_radar_data(
                    mock_db, student_id, None, None
                )

                assert "labels" in result
                assert "datasets" in result
                assert "scale" in result
                assert len(result["labels"]) == 6  # 6个能力维度
                assert len(result["datasets"][0]["data"]) == 6


class TestPerformanceOptimization:
    """性能优化测试"""

    def setup_method(self):
        """测试前设置"""
        self.cache_manager = CacheManager()
        self.analytics = PerformanceOptimizedAnalytics()

    def test_cache_manager_basic_operations(self):
        """测试缓存管理器基本操作"""
        key = "test_key"
        value = {"test": "data"}

        # 测试设置和获取
        assert self.cache_manager.set(key, value) is True
        assert self.cache_manager.get(key) == value

        # 测试删除
        assert self.cache_manager.delete(key) is True
        assert self.cache_manager.get(key) is None

    def test_cache_manager_ttl(self):
        """测试缓存TTL"""
        key = "test_ttl"
        value = {"test": "ttl"}

        # 设置短TTL
        short_ttl = 1
        assert self.cache_manager.set(key, value, short_ttl) is True
        assert self.cache_manager.get(key) == value

        # 等待过期
        import time
        time.sleep(2)
        assert self.cache_manager.get(key) is None

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        key1 = self.cache_manager._generate_cache_key("prefix", param1="value1", param2="value2")
        key2 = self.cache_manager._generate_cache_key("prefix", param2="value2", param1="value1")

        # 相同参数不同顺序应该生成相同的键
        assert key1 == key2

        # 不同参数应该生成不同的键
        key3 = self.cache_manager._generate_cache_key("prefix", param1="different")
        assert key1 != key3

    def test_batch_calculate_student_gpas(self):
        """测试批量计算学生GPA"""
        mock_db = Mock(spec=Session)
        student_ids = [1, 2, 3]

        # 创建模拟查询结果
        mock_query_result = [
            Mock(
                student_id=1, score=85, max_score=100,
                academic_year="2024-2025", semester="Fall",
                course_id=1, credits=3, course_name="Math"
            ),
            Mock(
                student_id=2, score=90, max_score=100,
                academic_year="2024-2025", semester="Fall",
                course_id=1, credits=3, course_name="Math"
            )
        ]

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = mock_query_result

        result = self.analytics._batch_calculate_student_gpas(mock_db, student_ids, None, None)

        assert isinstance(result, list)
        assert len(result) <= len(student_ids)

        for gpa_data in result:
            assert "student_id" in gpa_data
            assert "gpa" in gpa_data
            assert "total_credits" in gpa_data

    def test_performance_metrics(self):
        """测试性能指标获取"""
        metrics = self.analytics.get_performance_metrics()

        assert "cache_statistics" in metrics
        assert "thread_pool_info" in metrics
        assert "optimization_features" in metrics

        cache_stats = metrics["cache_statistics"]
        assert "memory_cache_size" in cache_stats
        assert "redis_connected" in cache_stats

        features = metrics["optimization_features"]
        assert features["batch_queries_enabled"] is True
        assert features["caching_enabled"] is True


class TestIntegration:
    """集成测试"""

    def test_end_to_end_student_analysis(self):
        """端到端学生分析测试"""
        # 这里应该测试整个分析流程
        # 由于需要真实的数据库连接，这里只提供测试框架
        pass

    def test_performance_benchmarks(self):
        """性能基准测试"""
        # 测试GPA计算性能
        gpa_service = GPACalculationService()

        # 模拟大量数据
        start_time = datetime.now()

        # 执行1000次GPA计算
        for i in range(1000):
            gpa_service.calculate_score_gpa_points(85 + i % 15, 100)

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 验证性能要求（应该在100ms内完成1000次计算）
        assert execution_time < 0.1, f"GPA计算性能不达标: {execution_time}秒"

    def test_concurrent_access(self):
        """并发访问测试"""
        import threading
        import time

        cache_manager = CacheManager()
        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"

                    cache_manager.set(key, value)
                    time.sleep(0.001)  # 模拟处理时间

                    retrieved_value = cache_manager.get(key)
                    if retrieved_value == value:
                        results.append(True)
                    else:
                        errors.append(f"Worker {worker_id}: Expected {value}, got {retrieved_value}")
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {str(e)}")

        # 创建10个工作线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0, f"并发测试出现错误: {errors}"
        assert len(results) == 100, f"预期100个成功操作，实际{len(results)}个"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])