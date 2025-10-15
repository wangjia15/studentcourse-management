import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  FormControl,
  FormControlLabel,
  FormLabel,
  Grid,
  MenuItem,
  Select,
  TextField,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  CloudUpload,
  Download,
  Error,
  CheckCircle,
  Info,
  Refresh,
  Visibility
} from '@mui/icons-material';
import axios from 'axios';

interface ProcessingOptions {
  skip_duplicates: boolean;
  validate_only: boolean;
  auto_detect_format: boolean;
}

interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  current_stage: string;
  estimated_remaining_time?: number;
  error_message?: string;
  result?: ProcessingResult;
}

interface ProcessingResult {
  task_id: string;
  status: string;
  total_records: number;
  processed_records: number;
  successful_records: number;
  failed_records: number;
  duplicate_records: number;
  warnings: ValidationError[];
  errors: ValidationError[];
  processing_time: number;
  created_at: string;
  completed_at?: string;
  file_path: string;
}

interface ValidationError {
  row_number: number;
  field: string;
  message: string;
  level: 'error' | 'warning' | 'info';
  current_value?: any;
  suggested_value?: any;
}

const BatchUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null);
  const [results, setResults] = useState<ProcessingResult[]>([]);
  const [options, setOptions] = useState<ProcessingOptions>({
    skip_duplicates: true,
    validate_only: false,
    auto_detect_format: true
  });
  const [error, setError] = useState<string | null>(null);
  const [detailsDialog, setDetailsDialog] = useState<ProcessingResult | null>(null);

  // 文件选择处理
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      // 检查文件大小 (100MB)
      if (selectedFile.size > 100 * 1024 * 1024) {
        setError('文件大小超过限制 (100MB)');
        return;
      }

      // 检查文件类型
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv',
        'application/csv'
      ];

      if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(xlsx|xls|csv)$/i)) {
        setError('不支持的文件格式，请上传 Excel (.xlsx, .xls) 或 CSV 文件');
        return;
      }

      setFile(selectedFile);
      setError(null);
    }
  }, []);

  // 上传文件
  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('options', JSON.stringify(options));

      const response = await axios.post('/api/v1/batch/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const task = response.data;
      setCurrentTask(task);

      // 开始轮询任务状态
      pollTaskStatus(task.task_id);

    } catch (err: any) {
      setError(err.response?.data?.detail || '上传失败');
      setUploading(false);
    }
  }, [file, options]);

  // 轮询任务状态
  const pollTaskStatus = useCallback(async (taskId: string) => {
    try {
      const response = await axios.get(`/api/v1/batch/task/${taskId}/status`);
      const task = response.data;

      setCurrentTask(task);

      if (task.status === 'completed') {
        setUploading(false);
        if (task.result) {
          setResults(prev => [task.result!, ...prev]);
        }
      } else if (task.status === 'failed') {
        setUploading(false);
        setError(task.error_message || '处理失败');
      } else {
        // 继续轮询
        setTimeout(() => pollTaskStatus(taskId), 2000);
      }
    } catch (err) {
      console.error('Failed to poll task status:', err);
      setUploading(false);
    }
  }, []);

  // 下载模板
  const downloadTemplate = useCallback(async () => {
    try {
      const response = await axios.get('/api/v1/batch/template/basic', {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '成绩导入模板.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('下载模板失败');
    }
  }, []);

  // 下载错误报告
  const downloadErrorReport = useCallback(async (taskId: string) => {
    try {
      const response = await axios.get(`/api/v1/batch/error-report/${taskId}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `错误报告_${taskId}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('下载错误报告失败');
    }
  }, []);

  // 重新上传
  const resetUpload = useCallback(() => {
    setFile(null);
    setCurrentTask(null);
    setError(null);
    setUploading(false);
  }, []);

  // 查看详情
  const viewDetails = useCallback((result: ProcessingResult) => {
    setDetailsDialog(result);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle />;
      case 'failed': return <Error />;
      case 'processing': return <CircularProgress size={20} />;
      default: return <Info />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        批量成绩处理
      </Typography>

      {/* 上传区域 */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="文件上传"
          action={
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={downloadTemplate}
            >
              下载模板
            </Button>
          }
        />
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Box
                sx={{
                  border: '2px dashed #ccc',
                  borderRadius: 2,
                  p: 3,
                  textAlign: 'center',
                  bgcolor: '#fafafa',
                  '&:hover': { borderColor: '#999', bgcolor: '#f5f5f5' }
                }}
              >
                <input
                  type="file"
                  id="file-upload"
                  style={{ display: 'none' }}
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileSelect}
                  disabled={uploading}
                />
                <label htmlFor="file-upload">
                  <Button
                    variant="contained"
                    component="span"
                    startIcon={<CloudUpload />}
                    disabled={uploading}
                  >
                    选择文件
                  </Button>
                </label>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  支持 Excel (.xlsx, .xls) 和 CSV 文件，最大 100MB
                </Typography>
                {file && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    已选择: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </Typography>
                )}
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControl fullWidth margin="normal">
                <FormLabel>处理选项</FormLabel>
                <FormControlLabel
                  control={
                    <input
                      type="checkbox"
                      checked={options.skip_duplicates}
                      onChange={(e) => setOptions(prev => ({
                        ...prev,
                        skip_duplicates: e.target.checked
                      }))}
                    />
                  }
                  label="跳过重复记录"
                />
                <FormControlLabel
                  control={
                    <input
                      type="checkbox"
                      checked={options.validate_only}
                      onChange={(e) => setOptions(prev => ({
                        ...prev,
                        validate_only: e.target.checked
                      }))}
                    />
                  }
                  label="仅验证数据"
                />
                <FormControlLabel
                  control={
                    <input
                      type="checkbox"
                      checked={options.auto_detect_format}
                      onChange={(e) => setOptions(prev => ({
                        ...prev,
                        auto_detect_format: e.target.checked
                      }))}
                    />
                  }
                  label="自动检测格式"
                />
              </FormControl>

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
                >
                  {uploading ? '处理中...' : '开始上传'}
                </Button>
                {file && (
                  <Button
                    variant="text"
                    fullWidth
                    onClick={resetUpload}
                    sx={{ mt: 1 }}
                    startIcon={<Refresh />}
                  >
                    重新选择
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 错误提示 */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 当前任务状态 */}
      {currentTask && (
        <Card sx={{ mb: 3 }}>
          <CardHeader
            title="处理进度"
            action={
              <Chip
                icon={getStatusIcon(currentTask.status)}
                label={currentTask.status}
                color={getStatusColor(currentTask.status)}
              />
            }
          />
          <CardContent>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                {currentTask.current_stage}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={currentTask.progress}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
                进度: {currentTask.progress.toFixed(1)}%
              </Typography>
            </Box>

            {currentTask.result && (
              <Grid container spacing={2}>
                <Grid item xs={6} md={2}>
                  <Typography variant="body2" color="textSecondary">
                    总记录数
                  </Typography>
                  <Typography variant="h6">
                    {currentTask.result.total_records}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={2}>
                  <Typography variant="body2" color="textSecondary">
                    成功记录
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {currentTask.result.successful_records}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={2}>
                  <Typography variant="body2" color="textSecondary">
                    失败记录
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {currentTask.result.failed_records}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={2}>
                  <Typography variant="body2" color="textSecondary">
                    重复记录
                  </Typography>
                  <Typography variant="h6" color="warning.main">
                    {currentTask.result.duplicate_records}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      startIcon={<Visibility />}
                      onClick={() => viewDetails(currentTask.result!)}
                    >
                      查看详情
                    </Button>
                    {currentTask.result.errors.length > 0 && (
                      <Button
                        size="small"
                        color="error"
                        onClick={() => downloadErrorReport(currentTask.result!.task_id)}
                      >
                        下载错误报告
                      </Button>
                    )}
                  </Box>
                </Grid>
              </Grid>
            )}
          </CardContent>
        </Card>
      )}

      {/* 历史记录 */}
      {results.length > 0 && (
        <Card>
          <CardHeader title="处理历史" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>文件名</TableCell>
                    <TableCell>状态</TableCell>
                    <TableCell>处理时间</TableCell>
                    <TableCell>成功/失败</TableCell>
                    <TableCell>操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.map((result) => (
                    <TableRow key={result.task_id}>
                      <TableCell>{result.file_path}</TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(result.status)}
                          label={result.status}
                          color={getStatusColor(result.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(result.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        {result.successful_records}/{result.failed_records}
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => viewDetails(result)}
                        >
                          <Visibility />
                        </IconButton>
                        {result.errors.length > 0 && (
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => downloadErrorReport(result.task_id)}
                          >
                            <Error />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* 详情对话框 */}
      <Dialog
        open={!!detailsDialog}
        onClose={() => setDetailsDialog(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>处理详情</DialogTitle>
        <DialogContent>
          {detailsDialog && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    文件名
                  </Typography>
                  <Typography variant="body1">
                    {detailsDialog.file_path}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    处理时间
                  </Typography>
                  <Typography variant="body1">
                    {detailsDialog.processing_time.toFixed(2)} 秒
                  </Typography>
                </Grid>
              </Grid>

              {/* 错误列表 */}
              {detailsDialog.errors.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    错误详情 ({detailsDialog.errors.length})
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>行号</TableCell>
                          <TableCell>字段</TableCell>
                          <TableCell>错误信息</TableCell>
                          <TableCell>当前值</TableCell>
                          <TableCell>建议值</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {detailsDialog.errors.slice(0, 10).map((error, index) => (
                          <TableRow key={index}>
                            <TableCell>{error.row_number}</TableCell>
                            <TableCell>{error.field}</TableCell>
                            <TableCell>{error.message}</TableCell>
                            <TableCell>{error.current_value || '-'}</TableCell>
                            <TableCell>{error.suggested_value || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  {detailsDialog.errors.length > 10 && (
                    <Typography variant="caption" color="textSecondary">
                      显示前 10 条错误，共 {detailsDialog.errors.length} 条
                    </Typography>
                  )}
                </Box>
              )}

              {/* 警告列表 */}
              {detailsDialog.warnings.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    警告信息 ({detailsDialog.warnings.length})
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>行号</TableCell>
                          <TableCell>字段</TableCell>
                          <TableCell>警告信息</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {detailsDialog.warnings.slice(0, 10).map((warning, index) => (
                          <TableRow key={index}>
                            <TableCell>{warning.row_number}</TableCell>
                            <TableCell>{warning.field}</TableCell>
                            <TableCell>{warning.message}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialog(null)}>
            关闭
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BatchUpload;