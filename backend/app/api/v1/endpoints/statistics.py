from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.services.analytics import AnalyticsService

router = APIRouter()

# 初始化增强分析服务
analytics_service = AnalyticsService()


@router.get("/gpa/student/{student_id}")
def calculate_student_gpa(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    use_optimized: bool = Query(True, description="使用性能优化的计算方法")
) -> Dict[str, Any]:
    """
    计算学生GPA

    支持中国教育部4.0标准，包含详细的GPA计算和统计信息
    """
    # 权限检查
    if (current_user.role == UserRole.STUDENT and current_user.id != student_id) or \
       (current_user.role == UserRole.TEACHER and not analytics_service.can_teacher_access_student_gpa(db, current_user.id, student_id)):
        raise HTTPException(status_code=403, detail="没有权限查看该学生的GPA")

    try:
        result = analytics_service.calculate_student_gpa(
            db, student_id, academic_year, semester, use_optimized
        )
        return {
            "success": True,
            "data": result.dict(),
            "message": "GPA计算成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPA计算失败: {str(e)}")


@router.get("/gpa/student/{student_id}/detailed")
def calculate_detailed_student_gpa(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    include_retake: bool = Query(True, description="包含重修课程处理")
) -> Dict[str, Any]:
    """
    计算详细学生GPA

    包含课程明细、等级分布、不及格课程等完整信息
    """
    # 权限检查
    if (current_user.role == UserRole.STUDENT and current_user.id != student_id) or \
       (current_user.role == UserRole.TEACHER and not analytics_service.can_teacher_access_student_gpa(db, current_user.id, student_id)):
        raise HTTPException(status_code=403, detail="没有权限查看该学生的详细GPA")

    try:
        result = analytics_service.calculate_detailed_student_gpa(
            db, student_id, academic_year, semester, include_retake
        )
        return {
            "success": True,
            "data": result,
            "message": "详细GPA计算成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"详细GPA计算失败: {str(e)}")


@router.get("/gpa/student/{student_id}/cumulative")
def calculate_cumulative_gpa(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    up_to_academic_year: Optional[str] = Query(None),
    up_to_semester: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    计算累计GPA

    支持历史累计计算，包含每学期GPA明细
    """
    # 权限检查
    if (current_user.role == UserRole.STUDENT and current_user.id != student_id) or \
       (current_user.role == UserRole.TEACHER and not analytics_service.can_teacher_access_student_gpa(db, current_user.id, student_id)):
        raise HTTPException(status_code=403, detail="没有权限查看该学生的累计GPA")

    try:
        result = analytics_service.calculate_cumulative_gpa(
            db, student_id, up_to_academic_year, up_to_semester
        )
        return {
            "success": True,
            "data": result,
            "message": "累计GPA计算成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"累计GPA计算失败: {str(e)}")


@router.post("/gpa/student/{student_id}/predict")
def predict_graduation_gpa(
    student_id: int,
    prediction_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    预测毕业GPA

    基于当前成绩和剩余学分预测毕业GPA
    """
    # 权限检查
    if (current_user.role == UserRole.STUDENT and current_user.id != student_id) or \
       (current_user.role == UserRole.TEACHER and not analytics_service.can_teacher_access_student_gpa(db, current_user.id, student_id)):
        raise HTTPException(status_code=403, detail="没有权限预测该学生的毕业GPA")

    try:
        remaining_credits = prediction_data.get("remaining_credits")
        expected_gpa = prediction_data.get("expected_gpa")

        if not remaining_credits or remaining_credits <= 0:
            raise HTTPException(status_code=400, detail="剩余学分必须大于0")

        result = analytics_service.predict_graduation_gpa(
            db, student_id, remaining_credits, expected_gpa
        )
        return {
            "success": True,
            "data": result,
            "message": "毕业GPA预测成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"毕业GPA预测失败: {str(e)}")


@router.get("/distribution/course/{course_id}")
def analyze_course_grade_distribution(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    include_details: bool = Query(False, description="包含学生详情")
) -> Dict[str, Any]:
    """
    分析课程成绩分布

    包含统计指标、分布分析、异常值检测等
    """
    # 权限检查
    if not analytics_service.can_access_course_distribution(db, current_user.id, course_id):
        raise HTTPException(status_code=403, detail="没有权限查看该课程的成绩分布")

    try:
        result = analytics_service.analyze_course_grade_distribution(
            db, course_id, academic_year, semester, include_details
        )
        return {
            "success": True,
            "data": result,
            "message": "课程成绩分布分析成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"课程成绩分布分析失败: {str(e)}")


@router.get("/distribution/class/{class_name}")
def analyze_class_grade_distribution(
    class_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    course_types: Optional[List[str]] = Query(None, description="课程类型过滤")
) -> Dict[str, Any]:
    """
    分析班级成绩分布

    支持不同课程类型的成绩分布分析
    """
    # 权限检查 - 只有教师和管理员可以查看班级分布
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="没有权限查看班级成绩分布")

    try:
        result = analytics_service.analyze_class_grade_distribution(
            db, class_name, academic_year, semester, course_types
        )
        return {
            "success": True,
            "data": result,
            "message": "班级成绩分布分析成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"班级成绩分布分析失败: {str(e)}")


@router.post("/distribution/class-compare")
def compare_class_performance(
    comparison_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    班级成绩对比分析

    支持多个班级的横向对比分析
    """
    # 权限检查
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="没有权限进行班级对比分析")

    try:
        class_names = comparison_data.get("class_names", [])
        academic_year = comparison_data.get("academic_year")
        semester = comparison_data.get("semester")

        if not class_names:
            raise HTTPException(status_code=400, detail="班级名称列表不能为空")

        result = analytics_service.compare_class_performance(
            db, class_names, academic_year, semester
        )
        return {
            "success": True,
            "data": result,
            "message": "班级对比分析成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"班级对比分析失败: {str(e)}")


@router.get("/trend/student/{student_id}")
def analyze_student_grade_trend(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_years: Optional[List[str]] = Query(None, description="学年列表"),
    prediction_enabled: bool = Query(True, description="启用预测分析")
) -> Dict[str, Any]:
    """
    分析学生成绩趋势

    包含历史趋势、风险分析、学习建议等
    """
    # 权限检查
    if (current_user.role == UserRole.STUDENT and current_user.id != student_id) or \
       (current_user.role == UserRole.TEACHER and not analytics_service.can_teacher_access_student_gpa(db, current_user.id, student_id)):
        raise HTTPException(status_code=403, detail="没有权限分析该学生的成绩趋势")

    try:
        result = analytics_service.analyze_student_grade_trend(
            db, student_id, academic_years, prediction_enabled
        )
        return {
            "success": True,
            "data": result,
            "message": "学生成绩趋势分析成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学生成绩趋势分析失败: {str(e)}")


@router.get("/trend/class/{class_name}")
def analyze_class_trend(
    class_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_years: Optional[List[str]] = Query(None, description="学年列表"),
    comparison_enabled: bool = Query(True, description="启用对比分析")
) -> Dict[str, Any]:
    """
    分析班级成绩趋势

    支持历史趋势分析和同级对比
    """
    # 权限检查
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="没有权限分析班级成绩趋势")

    try:
        result = analytics_service.analyze_class_trend(
            db, class_name, academic_years, comparison_enabled
        )
        return {
            "success": True,
            "data": result,
            "message": "班级成绩趋势分析成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"班级成绩趋势分析失败: {str(e)}")


@router.get("/trend/course/{course_id}")
def analyze_course_trend(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_years: Optional[List[str]] = Query(None, description="学年列表"),
    teacher_comparison: bool = Query(True, description="启用教师对比")
) -> Dict[str, Any]:
    """
    分析课程成绩趋势

    支持课程表现趋势和教师教学效果分析
    """
    # 权限检查
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="学生没有权限分析课程趋势")
    elif current_user.role == UserRole.TEACHER:
        # 检查是否为课程教师
        from app.models.course import Course
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course or course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="只有课程教师可以分析该课程趋势")

    try:
        result = analytics_service.analyze_course_trend(
            db, course_id, academic_years, teacher_comparison
        )
        return {
            "success": True,
            "data": result,
            "message": "课程成绩趋势分析成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"课程成绩趋势分析失败: {str(e)}")


@router.get("/ranking/class/{class_name}")
def get_class_ranking(
    class_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    获取班级GPA排名

    包含详细排名信息和统计数据
    """
    # 权限检查
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="没有权限查看班级排名")

    try:
        result = analytics_service.calculate_class_ranking(
            db, class_name, academic_year, semester
        )
        return {
            "success": True,
            "data": result,
            "message": "班级排名计算成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"班级排名计算失败: {str(e)}")


@router.get("/reports/personal/{student_id}")
def generate_personal_report(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    format_type: str = Query("detailed", description="报表格式")
) -> Dict[str, Any]:
    """
    生成个人统计报表

    包含成绩汇总、趋势分析、学习建议等完整信息
    """
    # 权限检查
    if (current_user.role == UserRole.STUDENT and current_user.id != student_id) or \
       (current_user.role == UserRole.TEACHER and not analytics_service.can_teacher_access_student_gpa(db, current_user.id, student_id)):
        raise HTTPException(status_code=403, detail="没有权限生成该学生的个人报表")

    try:
        result = analytics_service.generate_personal_statistical_report(
            db, student_id, academic_year, semester, format_type
        )
        return {
            "success": True,
            "data": result,
            "message": "个人报表生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"个人报表生成失败: {str(e)}")


@router.get("/reports/class/{class_name}")
def generate_class_report(
    class_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    include_individual_details: bool = Query(False, description="包含个人详情")
) -> Dict[str, Any]:
    """
    生成班级统计报表

    包含班级概况、成绩分析、教学建议等
    """
    # 权限检查
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="没有权限生成班级报表")

    try:
        result = analytics_service.generate_class_statistical_report(
            db, class_name, academic_year, semester, include_individual_details
        )
        return {
            "success": True,
            "data": result,
            "message": "班级报表生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"班级报表生成失败: {str(e)}")


@router.get("/reports/system")
def generate_system_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    scope: str = Query("university", description="报表范围")
) -> Dict[str, Any]:
    """
    生成系统统计报表

    只有管理员可以生成系统级报表
    """
    # 权限检查
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以生成系统报表")

    try:
        result = analytics_service.generate_system_statistical_report(
            db, academic_year, semester, scope
        )
        return {
            "success": True,
            "data": result,
            "message": "系统报表生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统报表生成失败: {str(e)}")


@router.get("/visualization/charts")
def get_visualization_data(
    chart_type: str = Query(..., description="图表类型"),
    chart_subtype: str = Query(..., description="图表子类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    entity_id: Optional[int] = Query(None),
    entity_name: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    **kwargs
) -> Dict[str, Any]:
    """
    获取可视化数据

    支持多种图表类型的数据接口
    """
    try:
        result = analytics_service.get_visualization_data(
            db, chart_type, chart_subtype, entity_id, entity_name,
            academic_year, semester, **kwargs
        )
        return {
            "success": True,
            "data": result,
            "message": "可视化数据获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"可视化数据获取失败: {str(e)}")


@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    获取仪表板数据

    根据用户角色返回相应的仪表板数据
    """
    try:
        result = analytics_service.get_dashboard_data(
            db, current_user.id, current_user.role.value, academic_year, semester
        )
        return {
            "success": True,
            "data": result,
            "message": "仪表板数据获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"仪表板数据获取失败: {str(e)}")


@router.post("/batch/analyze")
def batch_analyze(
    batch_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    批量分析

    支持批量GPA计算等操作
    """
    # 权限检查
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="没有权限进行批量分析")

    try:
        student_ids = batch_data.get("student_ids", [])
        analysis_type = batch_data.get("analysis_type", "gpa")
        academic_year = batch_data.get("academic_year")
        semester = batch_data.get("semester")

        if not student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")

        result = analytics_service.parallel_batch_analyze(
            db, student_ids, analysis_type, academic_year, semester
        )
        return {
            "success": True,
            "data": result,
            "message": "批量分析完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")


@router.post("/performance/optimize")
def optimize_performance(
    optimization_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    性能优化操作

    只有管理员可以进行性能优化操作
    """
    # 权限检查
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以进行性能优化操作")

    try:
        operation = optimization_data.get("operation")
        if not operation:
            raise HTTPException(status_code=400, detail="操作类型不能为空")

        result = analytics_service.optimize_performance(db, operation, **optimization_data)
        return {
            "success": True,
            "data": result,
            "message": "性能优化操作完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能优化操作失败: {str(e)}")


@router.get("/performance/metrics")
def get_performance_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取性能指标

    只有管理员可以查看性能指标
    """
    # 权限检查
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以查看性能指标")

    try:
        result = analytics_service.optimize_performance(None, "performance_metrics")
        return {
            "success": True,
            "data": result,
            "message": "性能指标获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能指标获取失败: {str(e)}")