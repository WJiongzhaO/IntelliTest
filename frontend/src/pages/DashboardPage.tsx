import { Button, Typography } from 'antd';
import {
  ArrowRightOutlined,
  ApartmentOutlined,
  AuditOutlined,
  BranchesOutlined,
  DownloadOutlined,
  FileTextOutlined,
  RadarChartOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';

const { Title, Text } = Typography;

const featureLinks = [
  {
    title: '需求输入',
    desc: '录入、导入并结构化原始需求',
    href: '/requirements',
    icon: <FileTextOutlined />,
  },
  {
    title: '风险分析',
    desc: '查看需求风险分数与优先级',
    href: '/risk',
    icon: <RadarChartOutlined />,
  },
  {
    title: '黑盒测试',
    desc: '按等价类、边界值和判定表生成用例',
    href: '/blackbox',
    icon: <ApartmentOutlined />,
  },
  {
    title: '综合测试设计',
    desc: '整合黑盒、白盒和预言生成流程',
    href: '/test-design',
    icon: <ArrowRightOutlined />,
  },
  {
    title: '白盒建模',
    desc: '生成状态模型、覆盖序列和测试用例',
    href: '/whitebox',
    icon: <BranchesOutlined />,
  },
  {
    title: '测试预言',
    desc: '生成、校验并审查预期结果',
    href: '/oracle',
    icon: <AuditOutlined />,
  },
  {
    title: '审查导出',
    desc: '人工审查测试资产并导出交付物',
    href: '/review-export',
    icon: <DownloadOutlined />,
  },
];

export default function DashboardPage() {
  return (
    <div className="workspace-hero">
      <div className="ai-mark">IT</div>
      <Title level={2}>IntelliTest 测试工作台</Title>
      <Text className="muted-text">从需求到测试资产导出的统一入口</Text>

      <div className="feature-grid" aria-label="功能入口">
        {featureLinks.map((item) => (
          <Link className="feature-link-card" to={item.href} key={item.href}>
            <span className="workflow-icon">{item.icon}</span>
            <span>
              <strong>{item.title}</strong>
              <Text className="muted-text">{item.desc}</Text>
            </span>
          </Link>
        ))}
      </div>

      <Button type="primary" icon={<FileTextOutlined />}>
        <Link to="/requirements">开始录入需求</Link>
      </Button>
    </div>
  );
}
