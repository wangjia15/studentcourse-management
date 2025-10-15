from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import UploadFile

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.grade import Grade
from app.models.enrollment import Enrollment
from app.schemas.reports import (
    ReportRequest, ReportResponse, ReportType, ReportStatus, ReportFormat,
    TranscriptRequest, ClassSummaryRequest, GradeAnalysisRequest,
    ReportDownloadResponse, ScheduleReportRequest
)


class ReportsService:
    """报告服务类"""

    def __init__(self):
        self.reports_dir = "reports"
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.default_retention_days = 30

    def create_transcript_request(
        self,
        db: Session,
        request: TranscriptRequest,
        user_id: int
    ) -> ReportResponse:
        """创建成绩单请求"""

        # 验证学生权限
        if not self._can_access_student_report(db, user_id, request.student_id):
            raise ValueError("无权限生成该学生的成绩单")

        # 创建报告记录
        report = ReportResponse(
            id=self._generate_report_id(),
            report_type=ReportType.TRANSCRIPT,
            status=ReportStatus.PENDING,
            format=request.format,
            requested_by=user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.default_retention_days),
            progress=0
        )

        # 这里应该保存到数据库，暂时返回模拟数据
        return report

    def create_class_summary_request(
        self,
        db: Session,
        request: ClassSummaryRequest,
        user_id: int
    ) -> ReportResponse:
        """创建班级汇总请求"""

        # 验证权限
        if not self._can_access_class_report(db, user_id, request.class_id):
            raise ValueError("无权限生成该班级的汇总报告")

        report = ReportResponse(
            id=self._generate_report_id(),
            report_type=ReportType.CLASS_SUMMARY,
            status=ReportStatus.PENDING,
            format=request.format,
            requested_by=user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.default_retention_days),
            progress=0
        )

        return report

    def create_grade_analysis_request(
        self,
        db: Session,
        request: GradeAnalysisRequest,
        user_id: int
    ) -> ReportResponse:
        """创建成绩分析请求"""

        # 验证权限
        if not self._can_access_grade_analysis(db, user_id, request):
            raise ValueError("无权限生成该成绩分析报告")

        report = ReportResponse(
            id=self._generate_report_id(),
            report_type=ReportType.GRADE_ANALYSIS,
            status=ReportStatus.PENDING,
            format=request.format,
            requested_by=user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.default_retention_days),
            progress=0
        )

        return report

    async def generate_transcript(self, db: Session, report_id: int):
        """生成成绩单（后台任务）"""

        try:
            # 更新状态为处理中
            self._update_report_status(report_id, ReportStatus.PROCESSING, 10)

            # 获取报告信息
            report = self._get_report(db, report_id)
            if not report:
                return

            # 获取学生数据
            student_data = self._get_student_transcript_data(db, report.requested_by)
            self._update_report_status(report_id, ReportStatus.PROCESSING, 50)

            # 生成文件
            file_path = await self._generate_transcript_file(student_data, report.format)
            self._update_report_status(report_id, ReportStatus.PROCESSING, 90)

            # 完成报告
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            self._update_report_status(
                report_id,
                ReportStatus.COMPLETED,
                100,
                file_path=file_path,
                file_size=file_size
            )

        except Exception as e:
            self._update_report_status(
                report_id,
                ReportStatus.FAILED,
                0,
                error_message=str(e)
            )

    async def generate_class_summary(self, db: Session, report_id: int):
        """生成班级汇总（后台任务）"""

        try:
            self._update_report_status(report_id, ReportStatus.PROCESSING, 10)

            # 获取班级数据
            class_data = self._get_class_summary_data(db, report_id)
            self._update_report_status(report_id, ReportStatus.PROCESSING, 60)

            # 生成文件
            file_path = await self._generate_class_summary_file(class_data)
            self._update_report_status(report_id, ReportStatus.PROCESSING, 90)

            # 完成报告
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            self._update_report_status(
                report_id,
                ReportStatus.COMPLETED,
                100,
                file_path=file_path,
                file_size=file_size
            )

        except Exception as e:
            self._update_report_status(
                report_id,
                ReportStatus.FAILED,
                0,
                error_message=str(e)
            )

    async def generate_grade_analysis(self, db: Session, report_id: int):
        """生成成绩分析（后台任务）"""

        try:
            self._update_report_status(report_id, ReportStatus.PROCESSING, 10)

            # 获取分析数据
            analysis_data = self._get_grade_analysis_data(db, report_id)
            self._update_report_status(report_id, ReportStatus.PROCESSING, 70)

            # 生成文件
            file_path = await self._generate_grade_analysis_file(analysis_data)
            self._update_report_status(report_id, ReportStatus.PROCESSING, 90)

            # 完成报告
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            self._update_report_status(
                report_id,
                ReportStatus.COMPLETED,
                100,
                file_path=file_path,
                file_size=file_size
            )

        except Exception as e:
            self._update_report_status(
                report_id,
                ReportStatus.FAILED,
                0,
                error_message=str(e)
            )

    def get_report(self, db: Session, report_id: int) -> Optional[ReportResponse]:
        """获取报告信息"""
        # 这里应该从数据库查询，暂时返回模拟数据
        return ReportResponse(
            id=report_id,
            report_type=ReportType.TRANSCRIPT,
            status=ReportStatus.COMPLETED,
            format=ReportFormat.PDF,
            requested_by=1,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

    def get_user_reports(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> List[ReportResponse]:
        """获取用户报告列表"""

        # 这里应该从数据库查询，暂时返回模拟数据
        reports = []
        for i in range(limit):
            report = ReportResponse(
                id=i + 1,
                report_type=ReportType.TRANSCRIPT,
                status=ReportStatus.COMPLETED if i % 2 == 0 else ReportStatus.PENDING,
                format=ReportFormat.PDF,
                requested_by=user_id,
                created_at=datetime.utcnow() - timedelta(hours=i),
                completed_at=datetime.utcnow() - timedelta(hours=i) if i % 2 == 0 else None
            )
            reports.append(report)

        return reports

    def get_all_reports(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
        user_filter: Optional[int] = None
    ) -> List[ReportResponse]:
        """获取所有报告列表（管理员）"""

        # 这里应该从数据库查询，暂时返回模拟数据
        reports = []
        for i in range(limit):
            report = ReportResponse(
                id=i + 1,
                report_type=ReportType.TRANSCRIPT,
                status=ReportStatus.COMPLETED if i % 3 == 0 else ReportStatus.PROCESSING if i % 3 == 1 else ReportStatus.FAILED,
                format=ReportFormat.PDF,
                requested_by=user_filter or (i % 5 + 1),
                created_at=datetime.utcnow() - timedelta(hours=i),
                completed_at=datetime.utcnow() - timedelta(hours=i) if i % 3 == 0 else None
            )
            reports.append(report)

        return reports

    def get_report_download_info(self, db: Session, report_id: int) -> ReportDownloadResponse:
        """获取报告下载信息"""

        report = self.get_report(db, report_id)
        if not report:
            raise ValueError("报告不存在")

        if report.status != ReportStatus.COMPLETED:
            raise ValueError("报告尚未生成完成")

        # 生成下载链接
        download_url = f"/api/v1/reports/download/{report_id}"
        file_name = f"report_{report.id}.{report.format.value}"

        return ReportDownloadResponse(
            report_id=report_id,
            download_url=download_url,
            file_name=file_name,
            file_size=report.file_size or 0,
            file_type=report.format.value,
            expires_at=report.expires_at or datetime.utcnow() + timedelta(days=7),
            remaining_downloads=5 - report.download_count
        )

    def delete_report(self, db: Session, report_id: int):
        """删除报告"""

        report = self.get_report(db, report_id)
        if not report:
            raise ValueError("报告不存在")

        # 删除文件
        if report.file_path and os.path.exists(report.file_path):
            os.remove(report.file_path)

        # 从数据库删除记录
        # db.delete(report)
        # db.commit()

    def _generate_report_id(self) -> int:
        """生成报告ID"""
        return int(uuid.uuid4().hex[:8], 16)

    def _update_report_status(
        self,
        report_id: int,
        status: ReportStatus,
        progress: int,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """更新报告状态"""
        # 这里应该更新数据库记录
        pass

    def _get_report(self, db: Session, report_id: int) -> Optional[ReportResponse]:
        """获取报告"""
        # 这里应该从数据库查询
        return None

    def _can_access_student_report(self, db: Session, user_id: int, student_id: int) -> bool:
        """检查是否可以访问学生报告"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 管理员可以查看所有学生
        if user.role == UserRole.ADMIN:
            return True

        # 学生只能查看自己的报告
        if user.role == UserRole.STUDENT and user.id == student_id:
            return True

        # 教师只能查看自己授课的学生
        if user.role == UserRole.TEACHER:
            # 检查是否教授过该学生的课程
            teacher_courses = db.query(Course).filter(Course.teacher_id == user_id).all()
            course_ids = [course.id for course in teacher_courses]

            student_grades = db.query(Grade).filter(
                and_(
                    Grade.student_id == student_id,
                    Grade.course_id.in_(course_ids)
                )
            ).first()

            return student_grades is not None

        return False

    def _can_access_class_report(self, db: Session, user_id: int, class_id: str) -> bool:
        """检查是否可以访问班级报告"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 管理员可以查看所有班级
        if user.role == UserRole.ADMIN:
            return True

        # 教师可以查看自己授课的班级
        if user.role == UserRole.TEACHER:
            # 检查是否有该班级的学生选修自己的课程
            class_students = db.query(User).filter(User.class_name == class_id).all()
            student_ids = [student.id for student in class_students]

            teacher_courses = db.query(Course).filter(Course.teacher_id == user_id).all()
            course_ids = [course.id for course in teacher_courses]

            enrollments = db.query(Enrollment).filter(
                and_(
                    Enrollment.student_id.in_(student_ids),
                    Enrollment.course_id.in_(course_ids)
                )
            ).first()

            return enrollments is not None

        return False

    def _can_access_grade_analysis(self, db: Session, user_id: int, request: GradeAnalysisRequest) -> bool:
        """检查是否可以访问成绩分析"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 只有管理员和教师可以请求成绩分析
        if user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            return False

        # 教师只能分析自己授课的课程或班级
        if user.role == UserRole.TEACHER:
            if request.analysis_scope == "course" and request.course_id:
                course = db.query(Course).filter(
                    and_(Course.id == request.course_id, Course.teacher_id == user_id)
                ).first()
                return course is not None

            elif request.analysis_scope == "class" and request.scope_id:
                # 检查是否有该班级的学生选修自己的课程
                class_students = db.query(User).filter(User.class_name == request.scope_id).all()
                student_ids = [student.id for student in class_students]

                teacher_courses = db.query(Course).filter(Course.teacher_id == user_id).all()
                course_ids = [course.id for course in teacher_courses]

                enrollments = db.query(Enrollment).filter(
                    and_(
                        Enrollment.student_id.in_(student_ids),
                        Enrollment.course_id.in_(course_ids)
                    )
                ).first()

                return enrollments is not None

        return True

    def _get_student_transcript_data(self, db: Session, student_id: int) -> Dict[str, Any]:
        """获取学生成绩单数据"""
        # 这里应该查询数据库获取实际数据
        return {
            "student_info": {"id": student_id, "name": "学生姓名"},
            "academic_records": [],
            "gpa_summary": {"gpa": 3.5},
            "generated_at": datetime.utcnow()
        }

    def _get_class_summary_data(self, db: Session, report_id: int) -> Dict[str, Any]:
        """获取班级汇总数据"""
        # 这里应该查询数据库获取实际数据
        return {
            "class_info": {"name": "班级名称"},
            "students": [],
            "statistics": {},
            "generated_at": datetime.utcnow()
        }

    def _get_grade_analysis_data(self, db: Session, report_id: int) -> Dict[str, Any]:
        """获取成绩分析数据"""
        # 这里应该查询数据库获取实际数据
        return {
            "analysis_scope": "course",
            "statistics": {},
            "trends": [],
            "recommendations": [],
            "generated_at": datetime.utcnow()
        }

    async def _generate_transcript_file(self, data: Dict[str, Any], format: ReportFormat) -> str:
        """生成成绩单文件"""
        # 这里应该实现实际的文件生成逻辑
        file_name = f"transcript_{uuid.uuid4().hex[:8]}.{format.value}"
        file_path = os.path.join(self.reports_dir, file_name)

        # 确保目录存在
        os.makedirs(self.reports_dir, exist_ok=True)

        # 生成文件（这里是示例）
        with open(file_path, 'w') as f:
            f.write("成绩单内容")

        return file_path

    async def _generate_class_summary_file(self, data: Dict[str, Any]) -> str:
        """生成班级汇总文件"""
        file_name = f"class_summary_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(self.reports_dir, file_name)

        os.makedirs(self.reports_dir, exist_ok=True)

        with open(file_path, 'w') as f:
            f.write("班级汇总内容")

        return file_path

    async def _generate_grade_analysis_file(self, data: Dict[str, Any]) -> str:
        """生成成绩分析文件"""
        file_name = f"grade_analysis_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(self.reports_dir, file_name)

        os.makedirs(self.reports_dir, exist_ok=True)

        with open(file_path, 'w') as f:
            f.write("成绩分析内容")

        return file_path