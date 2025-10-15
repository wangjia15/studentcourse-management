"""
Performance and load testing for the grade management system.
"""
import pytest
import time
import threading
import concurrent.futures
from fastapi.testclient import TestClient
from app.core.config import settings


class TestAPIPerformance:
    """Test API endpoint performance."""

    def test_login_response_time(self, client, admin_user):
        """Test login endpoint response time."""
        # Register user first
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        # Measure login response time
        start_time = time.time()
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        end_time = time.time()

        response_time = end_time - start_time

        # Login should be fast (< 1 second)
        assert response.status_code == 200
        assert response_time < 1.0
        print(f"Login response time: {response_time:.3f}s")

    def test_user_list_response_time(self, client, auth_headers_admin):
        """Test user list endpoint response time."""
        start_time = time.time()
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=auth_headers_admin
        )
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.5
        print(f"User list response time: {response_time:.3f}s")

    def test_course_list_response_time(self, client):
        """Test course list endpoint response time."""
        start_time = time.time()
        response = client.get(f"{settings.API_V1_STR}/courses/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.5
        print(f"Course list response time: {response_time:.3f}s")

    def test_grade_statistics_response_time(self, client, auth_headers_teacher, created_course):
        """Test grade statistics endpoint response time."""
        course_id = created_course["id"]
        start_time = time.time()
        response = client.get(
            f"{settings.API_V1_STR}/grades/statistics/course/{course_id}",
            headers=auth_headers_teacher
        )
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0
        print(f"Grade statistics response time: {response_time:.3f}s")

    def test_export_response_time(self, client, auth_headers_teacher, created_course):
        """Test export endpoint response time."""
        course_id = created_course["id"]
        start_time = time.time()
        response = client.get(
            f"{settings.API_V1_STR}/grades/export/{course_id}",
            headers=auth_headers_teacher
        )
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        # Export can be slower but should still be reasonable
        assert response_time < 5.0
        print(f"Export response time: {response_time:.3f}s")

    def test_search_performance(self, client, auth_headers_admin):
        """Test search endpoint performance."""
        search_queries = ["admin", "teacher", "student", "course", "grade"]

        for query in search_queries:
            start_time = time.time()
            response = client.get(
                f"{settings.API_V1_STR}/users/search?name={query}",
                headers=auth_headers_admin
            )
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < 0.5
            print(f"Search '{query}' response time: {response_time:.3f}s")


class TestLoadTesting:
    """Test system performance under load."""

    def test_concurrent_login_requests(self, client, admin_user):
        """Test concurrent login requests."""
        # Register user first
        client.post(f"{settings.API_V1_STR}/auth/register", json=admin_user)

        def make_login_request():
            start_time = time.time()
            response = client.post(
                f"{settings.API_V1_STR}/auth/login",
                json={
                    "username": admin_user["username"],
                    "password": admin_user["password"]
                }
            )
            end_time = time.time()
            return response.status_code, end_time - start_time

        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_login_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Analyze results
        success_count = sum(1 for status, _ in results if status == 200)
        response_times = [rt for _, rt in results if rt > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        assert success_count >= 15  # At least 75% success rate
        assert avg_response_time < 2.0  # Average response time under load
        print(f"Concurrent login: {success_count}/20 successful, avg time: {avg_response_time:.3f}s")

    def test_concurrent_user_requests(self, client, auth_headers_admin):
        """Test concurrent user list requests."""
        def make_user_request():
            start_time = time.time()
            response = client.get(
                f"{settings.API_V1_STR}/users/",
                headers=auth_headers_admin
            )
            end_time = time.time()
            return response.status_code, end_time - start_time

        # Make 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_user_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for status, _ in results if status == 200)
        response_times = [rt for _, rt in results if rt > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        assert success_count >= 45  # At least 90% success rate
        assert avg_response_time < 1.0  # Average response time under load
        print(f"Concurrent user requests: {success_count}/50 successful, avg time: {avg_response_time:.3f}s")

    def test_mixed_workload(self, client, auth_headers_admin, auth_headers_teacher, auth_headers_student):
        """Test mixed workload with different user types."""
        def make_request(user_type, endpoint):
            headers = {
                "admin": auth_headers_admin,
                "teacher": auth_headers_teacher,
                "student": auth_headers_student
            }.get(user_type, {})

            start_time = time.time()
            response = client.get(endpoint, headers=headers)
            end_time = time.time()
            return response.status_code, end_time - start_time

        # Define different types of requests
        requests = [
            ("admin", f"{settings.API_V1_STR}/users/"),
            ("admin", f"{settings.API_V1_STR}/admin/system-stats"),
            ("teacher", f"{settings.API_V1_STR}/courses/my-courses"),
            ("student", f"{settings.API_V1_STR}/courses/"),
            ("student", f"{settings.API_V1_STR}/grades/student"),
            ("", f"{settings.API_V1_STR}/courses/"),  # Public endpoint
        ]

        # Make 100 mixed requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = []
            for _ in range(100):
                user_type, endpoint = requests[_ % len(requests)]
                futures.append(executor.submit(make_request, user_type, endpoint))

            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for status, _ in results if status in [200, 404])  # 404 is ok for missing data
        response_times = [rt for _, rt in results if rt > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        assert success_count >= 90  # At least 90% success rate
        assert avg_response_time < 1.5  # Average response time under mixed load
        print(f"Mixed workload: {success_count}/100 successful, avg time: {avg_response_time:.3f}s")


class TestMemoryUsage:
    """Test memory usage and leak detection."""

    def test_memory_usage_with_large_dataset(self, client, auth_headers_admin):
        """Test memory usage with large dataset operations."""
        # Create large number of users (simulation)
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Make multiple requests that load data
        for i in range(50):
            response = client.get(f"{settings.API_V1_STR}/users/", headers=auth_headers_admin)
            assert response.status_code == 200

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100
        print(f"Memory usage increase: {memory_increase:.2f} MB")

    def test_memory_cleanup_after_requests(self, client, auth_headers_admin):
        """Test that memory is properly cleaned up after requests."""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss

        # Make memory-intensive requests
        for i in range(20):
            client.get(f"{settings.API_V1_STR}/users/", headers=auth_headers_admin)
            client.get(f"{settings.API_V1_STR}/courses/", headers=auth_headers_admin)

        # Force garbage collection
        gc.collect()
        after_requests_memory = process.memory_info().rss

        memory_increase = (after_requests_memory - baseline_memory) / 1024 / 1024  # MB

        # Memory increase should be minimal after garbage collection
        assert memory_increase < 50
        print(f"Memory after cleanup: {memory_increase:.2f} MB increase")


class TestDatabasePerformance:
    """Test database performance and optimization."""

    def test_database_connection_pooling(self, client, auth_headers_admin):
        """Test database connection pooling efficiency."""
        def make_db_request():
            start_time = time.time()
            response = client.get(f"{settings.API_V1_STR}/users/", headers=auth_headers_admin)
            end_time = time.time()
            return response.status_code, end_time - start_time

        # Make sequential requests to test connection reuse
        times = []
        for i in range(10):
            status, response_time = make_db_request()
            assert status == 200
            times.append(response_time)

        # Response times should be consistent (indicating connection reuse)
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        # Variation should be small
        variation = max_time - min_time
        assert variation < avg_time * 0.5  # Less than 50% variation
        print(f"DB connection pooling: avg={avg_time:.3f}s, variation={variation:.3f}s")

    def test_query_optimization(self, client, auth_headers_admin):
        """Test that queries are properly optimized."""
        # Test simple query
        start_time = time.time()
        response = client.get(f"{settings.API_V1_STR}/users/?limit=10", headers=auth_headers_admin)
        simple_query_time = time.time() - start_time

        # Test complex query with joins
        start_time = time.time()
        response = client.get(f"{settings.API_V1_STR}/users/?role=student&department=计算机科学与技术", headers=auth_headers_admin)
        complex_query_time = time.time() - start_time

        # Even complex queries should be reasonably fast
        assert response.status_code == 200
        assert complex_query_time < 1.0
        print(f"Query performance: simple={simple_query_time:.3f}s, complex={complex_query_time:.3f}s")

    def test_pagination_performance(self, client, auth_headers_admin):
        """Test pagination performance with large datasets."""
        # Test different page sizes
        page_sizes = [10, 50, 100]

        for page_size in page_sizes:
            start_time = time.time()
            response = client.get(
                f"{settings.API_V1_STR}/users/?limit={page_size}&offset=0",
                headers=auth_headers_admin
            )
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < 0.5
            print(f"Pagination (size={page_size}): {response_time:.3f}s")


class TestCachingPerformance:
    """Test caching mechanisms and performance."""

    def test_static_file_caching(self, client):
        """Test static file caching headers."""
        response = client.get("/static/test.css")

        # Should have cache headers
        cache_control = response.headers.get("cache-control", "")
        etag = response.headers.get("etag", "")

        assert cache_control or etag  # Should have some caching mechanism

    def test_api_response_caching(self, client):
        """Test API response caching where appropriate."""
        # First request
        start_time = time.time()
        response1 = client.get(f"{settings.API_V1_STR}/courses/")
        first_request_time = time.time() - start_time

        # Second request (should be faster if cached)
        start_time = time.time()
        response2 = client.get(f"{settings.API_V1_STR}/courses/")
        second_request_time = time.time() - start_time

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Check if responses are identical (indicating cache hit)
        if response1.headers.get("etag") == response2.headers.get("etag"):
            print(f"Caching: first={first_request_time:.3f}s, second={second_request_time:.3f}s")


class TestScalability:
    """Test system scalability limits."""

    def test_user_session_scalability(self, client):
        """Test system behavior with many user sessions."""
        def create_user_session(index):
            user_data = {
                "username": f"scale_user_{index}",
                "email": f"scale_user_{index}@example.com",
                "password": "Password123!",
                "full_name": f"Scale User {index}",
                "role": "student"
            }

            # Register user
            register_response = client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)

            if register_response.status_code == 201:
                # Login user
                login_response = client.post(
                    f"{settings.API_V1_STR}/auth/login",
                    json={
                        "username": user_data["username"],
                        "password": user_data["password"]
                    }
                )
                return login_response.status_code
            return register_response.status_code

        # Create multiple user sessions
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user_session, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        successful_sessions = sum(1 for status in results if status == 200)
        assert successful_sessions >= 15  # At least 75% success rate
        print(f"Scalability test: {successful_sessions}/20 sessions created successfully")

    def test_concurrent_file_operations(self, client, auth_headers_teacher):
        """Test concurrent file upload operations."""
        def upload_file(index):
            files = {"file": (f"test_{index}.txt", f"Test content {index}".encode(), "text/plain")}
            start_time = time.time()
            response = client.post(
                f"{settings.API_V1_STR}/courses/1/materials/upload",
                files=files,
                headers=auth_headers_teacher
            )
            end_time = time.time()
            return response.status_code, end_time - start_time

        # Upload multiple files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        successful_uploads = sum(1 for status, _ in results if status == 201)
        avg_time = sum(rt for _, rt in results) / len(results)

        assert successful_uploads >= 8  # At least 80% success rate
        assert avg_time < 5.0  # Average upload time should be reasonable
        print(f"File upload scalability: {successful_uploads}/10 successful, avg time: {avg_time:.3f}s")


class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_performance_benchmarks(self, client, auth_headers_admin):
        """Test performance against established benchmarks."""
        benchmarks = {
            f"{settings.API_V1_STR}/users/": 0.5,  # < 500ms
            f"{settings.API_V1_STR}/courses/": 0.3,  # < 300ms
            f"{settings.API_V1_STR}/auth/me": 0.2,   # < 200ms
            "/health": 0.1,  # < 100ms
        }

        results = {}
        for endpoint, max_time in benchmarks.items():
            start_time = time.time()
            response = client.get(endpoint, headers=auth_headers_admin)
            end_time = time.time()

            response_time = end_time - start_time
            results[endpoint] = response_time

            assert response.status_code == 200
            assert response_time < max_time, f"{endpoint} took {response_time:.3f}s, expected < {max_time}s"

        print("Performance benchmarks passed:")
        for endpoint, time_taken in results.items():
            print(f"  {endpoint}: {time_taken:.3f}s")