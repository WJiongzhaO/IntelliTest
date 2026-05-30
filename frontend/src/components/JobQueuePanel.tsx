import { Button, Card, List, Progress, Space, Tag, Typography } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  StopOutlined,
} from '@ant-design/icons';
import {
  getJobKindLabel,
  useRequirementJobStore,
  type JobStatus as ReqJobStatus,
  type RequirementJob,
} from '../stores/requirementJobStore';
import {
  getTestDesignJobKindLabel,
  useTestDesignJobStore,
  type TestDesignJob,
} from '../stores/testDesignJobStore';

const { Text } = Typography;

type UnifiedJobStatus = ReqJobStatus;
type UnifiedJob =
  | { source: 'requirement'; job: RequirementJob }
  | { source: 'testDesign'; job: TestDesignJob };

const statusIcons: Record<UnifiedJobStatus, React.ReactNode> = {
  pending: <ClockCircleOutlined style={{ color: '#8c8c8c' }} />,
  running: <LoadingOutlined style={{ color: '#1677ff' }} />,
  completed: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  failed: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
};

const statusLabels: Record<UnifiedJobStatus, string> = {
  pending: '等待中',
  running: '处理中',
  completed: '已完成',
  failed: '失败',
};

function getKindLabel(item: UnifiedJob): string {
  if (item.source === 'requirement') return getJobKindLabel(item.job.kind);
  return getTestDesignJobKindLabel(item.job.kind);
}

function JobListItem({
  item,
  onRetry,
}: {
  item: UnifiedJob;
  onRetry: (item: UnifiedJob) => void;
}) {
  const job = item.job;

  return (
    <List.Item
      actions={
        job.status === 'failed'
          ? [
              <Button key="retry" type="link" size="small" onClick={() => onRetry(item)}>
                重试
              </Button>,
            ]
          : undefined
      }
    >
      <List.Item.Meta
        avatar={statusIcons[job.status]}
        title={
          <Space size={4} wrap>
            <Text ellipsis style={{ maxWidth: 180 }}>
              {job.requirementTitle}
            </Text>
            <Tag>{getKindLabel(item)}</Tag>
            <Tag color={job.status === 'failed' ? 'error' : 'default'}>
              {statusLabels[job.status]}
            </Tag>
          </Space>
        }
        description={
          job.error ? (
            <Text type="danger" style={{ fontSize: 12 }}>
              {job.error}
            </Text>
          ) : null
        }
      />
    </List.Item>
  );
}

export default function JobQueuePanel() {
  const reqJobs = useRequirementJobStore((s) => s.jobs);
  const reqClearFinished = useRequirementJobStore((s) => s.clearFinished);
  const reqCancelPending = useRequirementJobStore((s) => s.cancelPending);
  const reqRetryFailed = useRequirementJobStore((s) => s.retryFailed);

  const tdJobs = useTestDesignJobStore((s) => s.jobs);
  const tdClearFinished = useTestDesignJobStore((s) => s.clearFinished);
  const tdCancelPending = useTestDesignJobStore((s) => s.cancelPending);
  const tdRetryFailed = useTestDesignJobStore((s) => s.retryFailed);

  const jobs: UnifiedJob[] = [
    ...reqJobs.map((job) => ({ source: 'requirement' as const, job })),
    ...tdJobs.map((job) => ({ source: 'testDesign' as const, job })),
  ];

  if (jobs.length === 0) return null;

  const completed = jobs.filter((j) => j.job.status === 'completed').length;
  const failed = jobs.filter((j) => j.job.status === 'failed').length;
  const active = jobs.filter(
    (j) => j.job.status === 'pending' || j.job.status === 'running',
  ).length;
  const running = jobs.find((j) => j.job.status === 'running');
  const progress = Math.round(((completed + failed) / jobs.length) * 100);
  const hasPending = jobs.some((j) => j.job.status === 'pending');
  const hasFinished = jobs.some(
    (j) => j.job.status === 'completed' || j.job.status === 'failed',
  );

  const handleClearFinished = () => {
    reqClearFinished();
    tdClearFinished();
  };

  const handleCancelPending = () => {
    reqCancelPending();
    tdCancelPending();
  };

  const handleRetry = (item: UnifiedJob) => {
    if (item.source === 'requirement') reqRetryFailed(item.job.id);
    else tdRetryFailed(item.job.id);
  };

  return (
    <Card
      className="job-queue-panel"
      size="small"
      title={
        <Space direction="vertical" size={0} style={{ width: '100%' }}>
          <Text strong>处理队列</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {active > 0
              ? `进行中 ${completed + failed}/${jobs.length}${running ? ` · 当前：${running.job.requirementTitle}` : ''}`
              : `全部完成（成功 ${completed}，失败 ${failed}）`}
          </Text>
        </Space>
      }
      extra={
        <Space size={4}>
          {hasPending && (
            <Button size="small" icon={<StopOutlined />} onClick={handleCancelPending}>
              取消等待
            </Button>
          )}
          {hasFinished && (
            <Button size="small" onClick={handleClearFinished}>
              清除记录
            </Button>
          )}
        </Space>
      }
    >
      <Progress
        percent={progress}
        size="small"
        status={failed > 0 && active === 0 ? 'exception' : 'active'}
      />
      <List
        className="job-queue-list"
        size="small"
        dataSource={jobs}
        renderItem={(item) => <JobListItem key={item.job.id} item={item} onRetry={handleRetry} />}
      />
      {active > 0 && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          任务在后台执行，可继续浏览其他页面。
        </Text>
      )}
    </Card>
  );
}
