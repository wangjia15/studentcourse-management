import asyncio
import chardet
import pandas as pd
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, text

from app.models.grade import Grade, GradeType, GradeStatus
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus
from app.core.config import get_settings
from app.services.pdf_reports import PDFReportGenerator

settings = get_settings()
logger = logging.getLogger(__name__)


class FileFormat(str, Enum):
    EXCEL = "excel"
    CSV = "csv"
    AUTO = "auto"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationError:
    def __init__(
        self,
        row_number: int,
        field: str,
        message: str,
        level: ValidationLevel = ValidationLevel.ERROR,
        current_value: Any = None,
        suggested_value: Any = None,
    ):
        self.row_number = row_number
        self.field = field
        self.message = message
        self.level = level
        self.current_value = current_value
        self.suggested_value = suggested_value


class BatchProcessingResult:
    def __init__(self):
        self.total_records = 0
        self.processed_records = 0
        self.failed_records = 0
        self.successful_records = 0
        self.duplicate_records = 0
        self.warnings: List[ValidationError] = []
        self.errors: List[ValidationError] = []
        self.processing_time = 0.0
        self.status = ProcessingStatus.PENDING
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.file_path = None
        self.export_file_path = None


class FileProcessor:
    """Excel/CSV文件处理器，支持中文编码和大文件处理"""

    @staticmethod
    def detect_encoding(file_content: bytes) -> str:
        """自动检测文件编码"""
        try:
            result = chardet.detect(file_content)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)

            logger.info(f"Detected encoding: {encoding} with confidence: {confidence}")

            # 常见中文编码处理
            if encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
                return 'gbk'
            elif encoding.lower() in ['utf-8-sig']:
                return 'utf-8-sig'
            else:
                return encoding

        except Exception as e:
            logger.warning(f"Encoding detection failed: {e}, defaulting to utf-8")
            return 'utf-8'

    @staticmethod
    def detect_csv_delimiter(file_content: str, sample_size: int = 1024) -> str:
        """自动检测CSV分隔符"""
        sample = file_content[:sample_size]

        # 计算常见分隔符的出现次数
        delimiters = [',', '\t', ';', '|']
        delimiter_counts = {}

        for delimiter in delimiters:
            delimiter_counts[delimiter] = sample.count(delimiter)

        # 选择出现次数最多的分隔符
        best_delimiter = max(delimiter_counts, key=delimiter_counts.get)

        logger.info(f"Detected delimiter: '{best_delimiter}'")
        return best_delimiter

    @staticmethod
    async def read_excel_file(
        file_content: bytes,
        sheet_name: Optional[str] = None,
        header_row: int = 0,
        chunk_size: Optional[int] = None,
    ) -> Union[pd.DataFrame, List[pd.DataFrame]]:
        """读取Excel文件"""
        try:
            # 使用BytesIO处理文件内容
            excel_file = BytesIO(file_content)

            # 检查是否是多sheet文件
            excel_file.seek(0)
            xl_file = pd.ExcelFile(excel_file)

            if sheet_name:
                # 读取指定sheet
                if chunk_size:
                    chunks = []
                    for chunk in pd.read_excel(
                        excel_file,
                        sheet_name=sheet_name,
                        header=header_row,
                        chunksize=chunk_size
                    ):
                        chunks.append(chunk)
                    return pd.concat(chunks, ignore_index=True)
                else:
                    return pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
            else:
                # 读取所有sheet
                all_sheets = {}
                for sheet in xl_file.sheet_names:
                    if chunk_size:
                        chunks = []
                        for chunk in pd.read_excel(
                            excel_file,
                            sheet_name=sheet,
                            header=header_row,
                            chunksize=chunk_size
                        ):
                            chunks.append(chunk)
                        all_sheets[sheet] = pd.concat(chunks, ignore_index=True)
                    else:
                        all_sheets[sheet] = pd.read_excel(excel_file, sheet_name=sheet, header=header_row)

                return all_sheets

        except Exception as e:
            logger.error(f"Excel file reading failed: {e}")
            raise ValueError(f"Excel文件读取失败: {str(e)}")

    @staticmethod
    async def read_csv_file(
        file_content: bytes,
        delimiter: Optional[str] = None,
        encoding: Optional[str] = None,
        header_row: int = 0,
        chunk_size: Optional[int] = None,
    ) -> Union[pd.DataFrame, List[pd.DataFrame]]:
        """读取CSV文件"""
        try:
            # 检测编码
            if encoding is None:
                encoding = FileProcessor.detect_encoding(file_content)

            # 解码文件内容
            text_content = file_content.decode(encoding)

            # 检测分隔符
            if delimiter is None:
                delimiter = FileProcessor.detect_csv_delimiter(text_content)

            # 创建StringIO对象
            csv_file = text_content.splitlines()

            if chunk_size:
                chunks = []
                for chunk in pd.read_csv(
                    csv_file,
                    sep=delimiter,
                    encoding=encoding,
                    header=header_row,
                    chunksize=chunk_size
                ):
                    chunks.append(chunk)
                return pd.concat(chunks, ignore_index=True)
            else:
                return pd.read_csv(
                    csv_file,
                    sep=delimiter,
                    encoding=encoding,
                    header=header_row
                )

        except Exception as e:
            logger.error(f"CSV file reading failed: {e}")
            raise ValueError(f"CSV文件读取失败: {str(e)}")

    @staticmethod
    async def detect_file_format(file_content: bytes) -> FileFormat:
        """自动检测文件格式"""
        try:
            # 检查Excel文件签名
            excel_signatures = [
                b'\x50\x4B\x03\x04',  # XLSX (Office Open XML)
                b'\xD0\xCF\x11\xE0',  # XLS (Microsoft Office)
            ]

            for signature in excel_signatures:
                if file_content.startswith(signature):
                    return FileFormat.EXCEL

            # 检查是否为CSV格式
            try:
                encoding = FileProcessor.detect_encoding(file_content)
                text_content = file_content.decode(encoding)
                delimiter = FileProcessor.detect_csv_delimiter(text_content)

                # 验证CSV格式
                first_line = text_content.split('\n')[0]
                if delimiter in first_line and ',' in first_line or '\t' in first_line:
                    return FileFormat.CSV
            except:
                pass

            return FileFormat.AUTO

        except Exception as e:
            logger.error(f"File format detection failed: {e}")
            return FileFormat.AUTO


class GradeBatchProcessor:
    """成绩批量处理器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.result = BatchProcessingResult()

    async def validate_student_exists(self, student_identifier: str) -> Optional[User]:
        """验证学生是否存在"""
        try:
            # 支持学号或ID查询
            if student_identifier.isdigit():
                query = select(User).where(
                    and_(
                        User.role == UserRole.STUDENT,
                        or_(
                            User.student_id == student_identifier,
                            User.id == int(student_identifier)
                        )
                    )
                )
            else:
                query = select(User).where(
                    and_(
                        User.role == UserRole.STUDENT,
                        User.student_id == student_identifier
                    )
                )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Student validation failed: {e}")
            return None

    async def validate_course_exists(self, course_identifier: str) -> Optional[Course]:
        """验证课程是否存在"""
        try:
            # 支持课程代码或ID查询
            if course_identifier.isdigit():
                query = select(Course).where(
                    or_(
                        Course.course_code == course_identifier,
                        Course.id == int(course_identifier)
                    )
                )
            else:
                query = select(Course).where(Course.course_code == course_identifier)

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Course validation failed: {e}")
            return None

    def validate_score_format(self, score: Any) -> Tuple[bool, Optional[float]]:
        """验证分数格式"""
        try:
            if pd.isna(score) or score == '':
                return False, None

            # 转换为数字
            score_float = float(score)

            # 检查范围
            if 0 <= score_float <= 100:
                return True, score_float
            else:
                return False, score_float

        except (ValueError, TypeError):
            return False, None

    def validate_grade_type(self, grade_type: str) -> bool:
        """验证成绩类型"""
        try:
            return grade_type.lower() in [gt.value for gt in GradeType]
        except:
            return False

    def validate_academic_year(self, academic_year: str) -> bool:
        """验证学年格式"""
        try:
            # 格式示例: 2024-2025
            if '-' in academic_year:
                start_year, end_year = academic_year.split('-')
                return len(start_year) == 4 and len(end_year) == 4
            return False
        except:
            return False

    async def validate_grade_record(
        self,
        row_data: Dict[str, Any],
        row_number: int
    ) -> Tuple[bool, List[ValidationError]]:
        """验证单条成绩记录"""
        errors = []
        warnings = []

        # 验证学生ID
        student_id = str(row_data.get('学号', row_data.get('student_id', ''))).strip()
        if not student_id:
            errors.append(ValidationError(
                row_number=row_number,
                field='学号',
                message='学号不能为空',
                current_value=student_id
            ))
        else:
            student = await self.validate_student_exists(student_id)
            if not student:
                errors.append(ValidationError(
                    row_number=row_number,
                    field='学号',
                    message=f'学号 {student_id} 不存在',
                    current_value=student_id
                ))

        # 验证课程代码
        course_code = str(row_data.get('课程代码', row_data.get('course_code', ''))).strip()
        if not course_code:
            errors.append(ValidationError(
                row_number=row_number,
                field='课程代码',
                message='课程代码不能为空',
                current_value=course_code
            ))
        else:
            course = await self.validate_course_exists(course_code)
            if not course:
                errors.append(ValidationError(
                    row_number=row_number,
                    field='课程代码',
                    message=f'课程代码 {course_code} 不存在',
                    current_value=course_code
                ))

        # 验证分数
        score_valid, score_value = self.validate_score_format(
            row_data.get('分数', row_data.get('score', ''))
        )
        if not score_valid:
            errors.append(ValidationError(
                row_number=row_number,
                field='分数',
                message='分数必须是0-100之间的数字',
                current_value=row_data.get('分数', row_data.get('score', ''))
            ))

        # 验证成绩类型
        grade_type = str(row_data.get('成绩类型', row_data.get('grade_type', 'final'))).strip()
        if not self.validate_grade_type(grade_type):
            errors.append(ValidationError(
                row_number=row_number,
                field='成绩类型',
                message=f'成绩类型无效，有效类型: {[gt.value for gt in GradeType]}',
                current_value=grade_type,
                suggested_value='final'
            ))

        # 验证学年
        academic_year = str(row_data.get('学年', row_data.get('academic_year', ''))).strip()
        if academic_year and not self.validate_academic_year(academic_year):
            errors.append(ValidationError(
                row_number=row_number,
                field='学年',
                message='学年格式错误，正确格式: 2024-2025',
                current_value=academic_year
            ))

        # 验证学期
        semester = str(row_data.get('学期', row_data.get('semester', ''))).strip()
        if semester not in ['春季', '秋季', 'Spring', 'Fall', 'summer', 'winter']:
            warnings.append(ValidationError(
                row_number=row_number,
                field='学期',
                message='学期可能不在标准列表中',
                current_value=semester,
                level=ValidationLevel.WARNING
            ))

        # 合并错误和警告
        all_issues = errors + warnings

        return len(errors) == 0, all_issues

    async def check_duplicate_grade(
        self,
        student_id: int,
        course_id: int,
        grade_type: str,
        academic_year: str,
        semester: str
    ) -> bool:
        """检查重复成绩"""
        try:
            query = select(Grade).where(
                and_(
                    Grade.student_id == student_id,
                    Grade.course_id == course_id,
                    Grade.grade_type == grade_type,
                    Grade.academic_year == academic_year,
                    Grade.semester == semester
                )
            )
            result = await self.db.execute(query)
            existing_grade = result.scalar_one_or_none()
            return existing_grade is not None
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False

    def calculate_grade_metrics(self, score: float, max_score: float = 100.0) -> Dict[str, float]:
        """计算成绩相关指标"""
        percentage = (score / max_score) * 100

        # 中国4.0 GPA计算
        if percentage >= 90:
            gpa_points = 4.0
        elif percentage >= 85:
            gpa_points = 3.7
        elif percentage >= 82:
            gpa_points = 3.3
        elif percentage >= 78:
            gpa_points = 3.0
        elif percentage >= 75:
            gpa_points = 2.7
        elif percentage >= 72:
            gpa_points = 2.3
        elif percentage >= 68:
            gpa_points = 2.0
        elif percentage >= 64:
            gpa_points = 1.5
        elif percentage >= 60:
            gpa_points = 1.0
        else:
            gpa_points = 0.0

        # 等级成绩
        if percentage >= 90:
            letter_grade = "A"
        elif percentage >= 80:
            letter_grade = "B"
        elif percentage >= 70:
            letter_grade = "C"
        elif percentage >= 60:
            letter_grade = "D"
        else:
            letter_grade = "F"

        # 绩点计算
        if percentage >= 95:
            grade_points = 4.0
        elif percentage >= 90:
            grade_points = 3.8
        elif percentage >= 85:
            grade_points = 3.6
        elif percentage >= 80:
            grade_points = 3.2
        elif percentage >= 75:
            grade_points = 2.8
        elif percentage >= 70:
            grade_points = 2.4
        elif percentage >= 65:
            grade_points = 2.0
        elif percentage >= 60:
            grade_points = 1.6
        else:
            grade_points = 0.0

        return {
            'percentage': percentage,
            'gpa_points': gpa_points,
            'letter_grade': letter_grade,
            'grade_points': grade_points
        }

    async def process_batch_grades(
        self,
        df: pd.DataFrame,
        submitted_by: int,
        options: Dict[str, Any] = None
    ) -> BatchProcessingResult:
        """批量处理成绩数据"""
        start_time = datetime.utcnow()
        self.result.status = ProcessingStatus.PROCESSING

        try:
            options = options or {}
            skip_duplicates = options.get('skip_duplicates', True)
            validate_only = options.get('validate_only', False)

            self.result.total_records = len(df)

            # 数据清洗和标准化
            df = self.clean_dataframe(df)

            # 验证每条记录
            valid_records = []
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始
                row_dict = row.to_dict()

                is_valid, issues = await self.validate_grade_record(row_dict, row_number)

                if issues:
                    for issue in issues:
                        if issue.level == ValidationLevel.ERROR:
                            self.result.errors.append(issue)
                        else:
                            self.result.warnings.append(issue)

                if is_valid and not validate_only:
                    valid_records.append((row_number, row_dict))

            # 处理有效记录
            if valid_records and not validate_only:
                await self.create_grade_records(valid_records, submitted_by, skip_duplicates)

            # 更新结果
            self.result.processed_records = len(valid_records)
            self.result.successful_records = len(valid_records) - self.result.duplicate_records
            self.result.failed_records = len(self.result.errors)

            self.result.status = ProcessingStatus.COMPLETED
            self.result.completed_at = datetime.utcnow()
            self.result.processing_time = (self.result.completed_at - start_time).total_seconds()

            logger.info(f"Batch processing completed: {self.result.successful_records}/{self.result.total_records} records processed")

            return self.result

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            self.result.status = ProcessingStatus.FAILED
            self.result.completed_at = datetime.utcnow()
            self.result.processing_time = (self.result.completed_at - start_time).total_seconds()
            raise

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗和标准化数据框"""
        # 删除完全为空的行
        df = df.dropna(how='all')

        # 标准化列名
        column_mapping = {
            '学号': 'student_id',
            '学生ID': 'student_id',
            'student_id': 'student_id',
            '课程代码': 'course_code',
            '课程编号': 'course_code',
            'course_code': 'course_code',
            '课程名称': 'course_name',
            'course_name': 'course_name',
            '分数': 'score',
            '成绩': 'score',
            'score': 'score',
            '满分': 'max_score',
            'max_score': 'max_score',
            '成绩类型': 'grade_type',
            'grade_type': 'grade_type',
            '权重': 'weight',
            'weight': 'weight',
            '学年': 'academic_year',
            'academic_year': 'academic_year',
            '学期': 'semester',
            'semester': 'semester',
            '评语': 'comments',
            'comments': 'comments',
            '反馈': 'feedback',
            'feedback': 'feedback'
        }

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 清洗字符串数据
        string_columns = ['student_id', 'course_code', 'course_name', 'grade_type', 'academic_year', 'semester']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        return df

    async def create_grade_records(
        self,
        valid_records: List[Tuple[int, Dict[str, Any]]],
        submitted_by: int,
        skip_duplicates: bool = True
    ):
        """创建成绩记录"""
        try:
            grades_to_create = []

            for row_number, row_data in valid_records:
                # 获取学生和课程信息
                student_id_str = row_data.get('student_id', '')
                course_code = row_data.get('course_code', '')

                student = await self.validate_student_exists(student_id_str)
                course = await self.validate_course_exists(course_code)

                if not student or not course:
                    continue

                # 检查重复
                grade_type = row_data.get('grade_type', 'final')
                academic_year = row_data.get('academic_year', '2024-2025')
                semester = row_data.get('semester', '春季')

                if skip_duplicates and await self.check_duplicate_grade(
                    student.id, course.id, grade_type, academic_year, semester
                ):
                    self.result.duplicate_records += 1
                    continue

                # 计算成绩指标
                score = float(row_data.get('score', 0))
                max_score = float(row_data.get('max_score', 100))
                metrics = self.calculate_grade_metrics(score, max_score)

                # 创建成绩记录
                grade = Grade(
                    student_id=student.id,
                    course_id=course.id,
                    score=score,
                    max_score=max_score,
                    percentage=metrics['percentage'],
                    letter_grade=metrics['letter_grade'],
                    gpa_points=metrics['gpa_points'],
                    grade_points=metrics['grade_points'],
                    grade_type=grade_type,
                    weight=float(row_data.get('weight', 1.0)),
                    academic_year=academic_year,
                    semester=semester,
                    status=GradeStatus.DRAFT.value,
                    is_final=False,
                    is_published=False,
                    submitted_by=submitted_by,
                    comments=row_data.get('comments'),
                    feedback=row_data.get('feedback')
                )

                grades_to_create.append(grade)

            # 批量插入数据库
            if grades_to_create:
                self.db.add_all(grades_to_create)
                await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Grade creation failed: {e}")
            raise


class BatchProcessingService:
    """批量处理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.processor = GradeBatchProcessor(db)
        self.file_processor = FileProcessor()
        self.pdf_generator = PDFReportGenerator()

    async def process_file_upload(
        self,
        file_content: bytes,
        filename: str,
        submitted_by: int,
        options: Dict[str, Any] = None
    ) -> BatchProcessingResult:
        """处理文件上传"""
        try:
            # 检测文件格式
            file_format = await self.file_processor.detect_file_format(file_content)

            if file_format == FileFormat.EXCEL:
                # 读取Excel文件
                df = await self.file_processor.read_excel_file(file_content)
                if isinstance(df, dict):
                    # 如果是多sheet文件，选择第一个sheet
                    sheet_name = list(df.keys())[0]
                    df = df[sheet_name]
            elif file_format == FileFormat.CSV:
                # 读取CSV文件
                df = await self.file_processor.read_csv_file(file_content)
            else:
                raise ValueError("不支持的文件格式")

            # 处理成绩数据
            result = await self.processor.process_batch_grades(df, submitted_by, options)
            result.file_path = filename

            return result

        except Exception as e:
            logger.error(f"File upload processing failed: {e}")
            raise

    async def get_processing_template(self, template_type: str = "basic") -> pd.DataFrame:
        """获取导入模板"""
        if template_type == "basic":
            columns = [
                '学号',
                '课程代码',
                '分数',
                '成绩类型',
                '学年',
                '学期',
                '评语'
            ]
            df = pd.DataFrame(columns=columns)

            # 添加示例数据
            example_data = [
                ['2024001', 'CS101', 85, 'final', '2024-2025', '春季', '表现良好'],
                ['2024002', 'CS101', 92, 'final', '2024-2025', '春季', '优秀'],
            ]
            df = pd.DataFrame(example_data, columns=columns)

            return df
        else:
            raise ValueError(f"Unknown template type: {template_type}")

    async def export_grades_to_excel(
        self,
        course_id: Optional[int] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        grade_type: Optional[str] = None
    ) -> BytesIO:
        """导出成绩到Excel"""
        try:
            # 查询成绩数据
            query = select(Grade, User, Course).join(User, Grade.student_id == User.id).join(Course, Grade.course_id == Course.id)

            conditions = []
            if course_id:
                conditions.append(Grade.course_id == course_id)
            if academic_year:
                conditions.append(Grade.academic_year == academic_year)
            if semester:
                conditions.append(Grade.semester == semester)
            if grade_type:
                conditions.append(Grade.grade_type == grade_type)

            if conditions:
                query = query.where(and_(*conditions))

            result = await self.db.execute(query)
            records = result.all()

            # 创建DataFrame
            data = []
            for grade, user, course in records:
                data.append({
                    '学号': user.student_id,
                    '姓名': user.full_name,
                    '课程代码': course.course_code,
                    '课程名称': course.course_name,
                    '分数': grade.score,
                    '满分': grade.max_score,
                    '百分比': grade.percentage,
                    '等级成绩': grade.letter_grade,
                    'GPA': grade.gpa_points,
                    '绩点': grade.grade_points,
                    '成绩类型': grade.grade_type,
                    '学年': grade.academic_year,
                    '学期': grade.semester,
                    '状态': grade.status,
                    '提交时间': grade.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                    '评语': grade.comments
                })

            df = pd.DataFrame(data)

            # 导出到Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='成绩数据', index=False)

                # 获取工作簿和工作表对象
                workbook = writer.book
                worksheet = writer.sheets['成绩数据']

                # 设置列宽
                for i, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, min(max_len, 50))

            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            raise

    async def generate_error_report(
        self,
        result: BatchProcessingResult
    ) -> BytesIO:
        """生成错误报告"""
        try:
            # 创建错误报告数据
            error_data = []
            for error in result.errors:
                error_data.append({
                    '行号': error.row_number,
                    '字段': error.field,
                    '错误级别': error.level.value,
                    '当前值': error.current_value,
                    '建议值': error.suggested_value,
                    '错误信息': error.message
                })

            df_errors = pd.DataFrame(error_data)

            # 创建处理结果摘要
            summary_data = [{
                '处理状态': result.status.value,
                '总记录数': result.total_records,
                '成功记录数': result.successful_records,
                '失败记录数': result.failed_records,
                '重复记录数': result.duplicate_records,
                '处理时间(秒)': result.processing_time,
                '开始时间': result.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '完成时间': result.completed_at.strftime('%Y-%m-%d %H:%M:%S') if result.completed_at else ''
            }]

            df_summary = pd.DataFrame(summary_data)

            # 导出到Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_summary.to_excel(writer, sheet_name='处理摘要', index=False)
                df_errors.to_excel(writer, sheet_name='错误详情', index=False)

                # 格式化工作表
                workbook = writer.book
                summary_sheet = writer.sheets['处理摘要']
                error_sheet = writer.sheets['错误详情']

                # 设置列宽
                for sheet in [summary_sheet, error_sheet]:
                    for i, col in enumerate(df_summary.columns if sheet == summary_sheet else df_errors.columns):
                        sheet.set_column(i, i, 20)

            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Error report generation failed: {e}")
            raise

    async def generate_pdf_report(
        self,
        course_id: Optional[int] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        grade_type: Optional[str] = None
    ) -> BytesIO:
        """生成PDF成绩报告"""
        try:
            # 查询成绩数据
            query = select(Grade, User, Course).join(User, Grade.student_id == User.id).join(Course, Grade.course_id == Course.id)

            conditions = []
            if course_id:
                conditions.append(Grade.course_id == course_id)
            if academic_year:
                conditions.append(Grade.academic_year == academic_year)
            if semester:
                conditions.append(Grade.semester == semester)
            if grade_type:
                conditions.append(Grade.grade_type == grade_type)

            if conditions:
                query = query.where(and_(*conditions))

            result = await self.db.execute(query)
            records = result.all()

            if not records:
                raise ValueError("没有找到符合条件的成绩数据")

            # 准备报告数据
            grades_data = []
            course_info = {}
            report_info = {}

            for grade, user, course in records:
                grades_data.append({
                    'student_id': user.student_id,
                    'student_name': user.full_name,
                    'score': grade.score,
                    'letter_grade': grade.letter_grade,
                    'gpa_points': grade.gpa_points,
                    'grade_type': grade.grade_type
                })

                if not course_info:
                    course_info = {
                        'course_code': course.course_code,
                        'course_name': course.course_name,
                        'credits': course.credits,
                        'hours': course.hours,
                        'teacher_name': course.teacher.full_name if course.teacher else '',
                        'semester': grade.semester,
                        'academic_year': grade.academic_year
                    }

            report_info = {
                'semester': course_info['semester'],
                'academic_year': course_info['academic_year'],
                'course_code': course_info['course_code'],
                'course_name': course_info['course_name']
            }

            # 生成PDF报告
            pdf_buffer = self.pdf_generator.generate_grade_report(
                grades_data, report_info
            )

            return pdf_buffer

        except Exception as e:
            logger.error(f"PDF report generation failed: {e}")
            raise