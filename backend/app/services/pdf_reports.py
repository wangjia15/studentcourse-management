from datetime import datetime
from typing import Any, Dict, List, Optional
from io import BytesIO
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.models.grade import Grade
from app.models.user import User
from app.models.course import Course

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """PDF报告生成器，支持中文格式化"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_chinese_font()
        self.setup_custom_styles()

    def setup_chinese_font(self):
        """设置中文字体"""
        try:
            # 尝试注册中文字体
            # 在实际部署时需要确保中文字体文件存在
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",  # Windows
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            ]

            for font_path in font_paths:
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    logger.info(f"Successfully registered Chinese font: {font_path}")
                    break
                except:
                    continue
            else:
                logger.warning("No Chinese font found, using default font")
        except Exception as e:
            logger.warning(f"Chinese font setup failed: {e}")

    def setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=self.styles['Title'],
            fontName='ChineseFont',
            fontSize=18,
            leading=22,
            alignment=1  # 居中
        ))

        # 正文样式
        self.styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=self.styles['Normal'],
            fontName='ChineseFont',
            fontSize=10,
            leading=12
        ))

        # 表头样式
        self.styles.add(ParagraphStyle(
            name='ChineseHeader',
            parent=self.styles['Normal'],
            fontName='ChineseFont',
            fontSize=9,
            leading=11,
            alignment=1  # 居中
        ))

    def generate_grade_report(
        self,
        grades_data: List[Dict[str, Any]],
        report_info: Dict[str, Any],
        include_charts: bool = False
    ) -> BytesIO:
        """生成成绩报告"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # 构建报告内容
            story = []

            # 添加标题
            title = Paragraph("成绩报表", self.styles['ChineseTitle'])
            story.append(title)
            story.append(Spacer(1, 12))

            # 添加报告信息
            self._add_report_info(story, report_info)

            # 添加统计摘要
            self._add_statistics_summary(story, grades_data)

            # 添加详细数据表格
            self._add_grades_table(story, grades_data)

            # 生成PDF
            doc.build(story)
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"PDF grade report generation failed: {e}")
            raise

    def generate_class_statistics_report(
        self,
        class_data: Dict[str, Any],
        course_info: Dict[str, Any]
    ) -> BytesIO:
        """生成班级统计报告"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            story = []

            # 标题
            title = Paragraph(f"{course_info['course_name']} - 班级成绩统计", self.styles['ChineseTitle'])
            story.append(title)
            story.append(Spacer(1, 12))

            # 课程信息
            self._add_course_info(story, course_info)

            # 班级统计信息
            self._add_class_statistics(story, class_data)

            # 成绩分布表
            self._add_grade_distribution_table(story, class_data)

            # 生成PDF
            doc.build(story)
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"PDF class statistics report generation failed: {e}")
            raise

    def generate_batch_processing_report(
        self,
        processing_result: Dict[str, Any],
        file_info: Dict[str, Any]
    ) -> BytesIO:
        """生成批量处理报告"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            story = []

            # 标题
            title = Paragraph("批量数据处理报告", self.styles['ChineseTitle'])
            story.append(title)
            story.append(Spacer(1, 12))

            # 文件信息
            self._add_file_info(story, file_info)

            # 处理结果摘要
            self._add_processing_summary(story, processing_result)

            # 错误详情
            if processing_result.get('errors'):
                self._add_error_details(story, processing_result['errors'])

            # 生成PDF
            doc.build(story)
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"PDF batch processing report generation failed: {e}")
            raise

    def _add_report_info(self, story: List, report_info: Dict[str, Any]):
        """添加报告信息"""
        info_data = [
            ['报告生成时间', datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')],
            ['学期', report_info.get('semester', '')],
            ['学年', report_info.get('academic_year', '')],
            ['课程代码', report_info.get('course_code', '')],
            ['课程名称', report_info.get('course_name', '')],
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(info_table)
        story.append(Spacer(1, 12))

    def _add_statistics_summary(self, story: List, grades_data: List[Dict[str, Any]]):
        """添加统计摘要"""
        if not grades_data:
            return

        # 计算统计数据
        total_students = len(grades_data)
        scores = [grade['score'] for grade in grades_data if grade['score'] is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        # 计算及格率
        pass_count = len([s for s in scores if s >= 60])
        pass_rate = (pass_count / len(scores) * 100) if scores else 0

        # 计算优秀率
        excellent_count = len([s for s in scores if s >= 90])
        excellent_rate = (excellent_count / len(scores) * 100) if scores else 0

        stats_data = [
            ['统计项目', '数值'],
            ['学生总数', f"{total_students} 人"],
            ['平均分', f"{average_score:.2f}"],
            ['最高分', f"{max_score:.2f}"],
            ['最低分', f"{min_score:.2f}"],
            ['及格率', f"{pass_rate:.2f}%"],
            ['优秀率', f"{excellent_rate:.2f}%"],
        ]

        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(Paragraph("统计摘要", self.styles['ChineseNormal']))
        story.append(Spacer(1, 6))
        story.append(stats_table)
        story.append(Spacer(1, 12))

    def _add_grades_table(self, story: List, grades_data: List[Dict[str, Any]]):
        """添加成绩表格"""
        if not grades_data:
            return

        # 表头
        headers = ['学号', '姓名', '分数', '等级', 'GPA', '成绩类型']

        # 准备数据
        table_data = [headers]
        for grade in grades_data[:50]:  # 限制显示前50条记录
            row = [
                grade.get('student_id', ''),
                grade.get('student_name', ''),
                f"{grade.get('score', 0):.1f}",
                grade.get('letter_grade', ''),
                f"{grade.get('gpa_points', 0):.2f}",
                grade.get('grade_type', '')
            ]
            table_data.append(row)

        # 创建表格
        table = Table(table_data, colWidths=[1*inch, 1.5*inch, 0.8*inch, 0.6*inch, 0.6*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(Paragraph("详细成绩表 (前50条记录)", self.styles['ChineseNormal']))
        story.append(Spacer(1, 6))
        story.append(table)

        if len(grades_data) > 50:
            story.append(Spacer(1, 6))
            note = Paragraph(f"注: 共{len(grades_data)}条记录，仅显示前50条", self.styles['ChineseNormal'])
            story.append(note)

    def _add_course_info(self, story: List, course_info: Dict[str, Any]):
        """添加课程信息"""
        info_data = [
            ['课程代码', course_info.get('course_code', '')],
            ['课程名称', course_info.get('course_name', '')],
            ['学分', f"{course_info.get('credits', 0)}"],
            ['学时', f"{course_info.get('hours', 0)}"],
            ['授课教师', course_info.get('teacher_name', '')],
            ['学期', course_info.get('semester', '')],
            ['学年', course_info.get('academic_year', '')],
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(Paragraph("课程信息", self.styles['ChineseNormal']))
        story.append(Spacer(1, 6))
        story.append(info_table)
        story.append(Spacer(1, 12))

    def _add_class_statistics(self, story: List, class_data: Dict[str, Any]):
        """添加班级统计信息"""
        stats_data = [
            ['统计项目', '数值'],
            ['班级人数', f"{class_data.get('total_students', 0)} 人"],
            ['平均分', f"{class_data.get('average_score', 0):.2f}"],
            ['最高分', f"{class_data.get('max_score', 0):.2f}"],
            ['最低分', f"{class_data.get('min_score', 0):.2f}"],
            ['标准差', f"{class_data.get('std_deviation', 0):.2f}"],
            ['及格率', f"{class_data.get('pass_rate', 0):.2f}%"],
            ['优秀率', f"{class_data.get('excellent_rate', 0):.2f}%"],
        ]

        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(Paragraph("班级统计", self.styles['ChineseNormal']))
        story.append(Spacer(1, 6))
        story.append(stats_table)
        story.append(Spacer(1, 12))

    def _add_grade_distribution_table(self, story: List, class_data: Dict[str, Any]):
        """添加成绩分布表"""
        distribution = class_data.get('grade_distribution', {})
        if not distribution:
            return

        dist_data = [['成绩等级', '人数', '百分比']]
        total_students = class_data.get('total_students', 0)

        for grade_level, count in distribution.items():
            percentage = (count / total_students * 100) if total_students > 0 else 0
            dist_data.append([grade_level, f"{count} 人", f"{percentage:.2f}%"])

        dist_table = Table(dist_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        dist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(Paragraph("成绩分布", self.styles['ChineseNormal']))
        story.append(Spacer(1, 6))
        story.append(dist_table)

    def _add_file_info(self, story: List, file_info: Dict[str, Any]):
        """添加文件信息"""
        info_data = [
            ['文件名称', file_info.get('filename', '')],
            ['文件格式', file_info.get('format', '')],
            ['文件大小', f"{file_info.get('size', 0)} 字节"],
            ['处理时间', datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')],
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(info_table)
        story.append(Spacer(1, 12))

    def _add_processing_summary(self, story: List, processing_result: Dict[str, Any]):
        """添加处理结果摘要"""
        summary_data = [
            ['统计项目', '数值'],
            ['总记录数', f"{processing_result.get('total_records', 0)} 条"],
            ['成功记录数', f"{processing_result.get('successful_records', 0)} 条"],
            ['失败记录数', f"{processing_result.get('failed_records', 0)} 条"],
            ['重复记录数', f"{processing_result.get('duplicate_records', 0)} 条"],
            ['处理时间', f"{processing_result.get('processing_time', 0):.2f} 秒"],
            ['处理状态', processing_result.get('status', '')],
        ]

        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(Paragraph("处理结果摘要", self.styles['ChineseNormal']))
        story.append(Spacer(1, 6))
        story.append(summary_table)
        story.append(Spacer(1, 12))

    def _add_error_details(self, story: List, errors: List[Dict[str, Any]]):
        """添加错误详情"""
        if not errors:
            return

        # 表头
        error_headers = ['行号', '字段', '错误信息', '当前值', '建议值']

        # 准备数据，只显示前20个错误
        error_data = [error_headers]
        for error in errors[:20]:
            row = [
                str(error.get('row_number', '')),
                error.get('field', ''),
                error.get('message', ''),
                str(error.get('current_value', '')),
                str(error.get('suggested_value', ''))
            ]
            error_data.append(row)

        # 创建表格
        error_table = Table(error_data, colWidths=[0.6*inch, 1*inch, 2*inch, 1*inch, 1*inch])
        error_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(Paragraph("错误详情 (前20条)", self.styles['ChineseNormal']))
        story.append(Spacer(1, 6))
        story.append(error_table)

        if len(errors) > 20:
            story.append(Spacer(1, 6))
            note = Paragraph(f"注: 共{len(errors)}个错误，仅显示前20个", self.styles['ChineseNormal'])
            story.append(note)