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
    title: '综合测试设计',
    desc: '统一生成黑盒测试、白盒建模和测试预言结果',
    href: '/test-design',
    icon: <ArrowRightOutlined />,
  },
  {
    title: '审查导出',
    desc: '默认优先审查并导出综合设计产出的测试资产',
    href: '/review-export',
    icon: <DownloadOutlined />,
  },
];

const moduleLinks = [
  {
    title: '黑盒测试',
    desc: '单独调试等价类、边界值和判定表用例',
    href: '/blackbox',
    icon: <ApartmentOutlined />,
  },
  {
    title: '白盒建模',
    desc: '单独生成状态模型、覆盖序列和白盒用例',
    href: '/whitebox',
    icon: <BranchesOutlined />,
  },
  {
    title: '测试预言',
    desc: '单独生成、校验并审查预期结果',
    href: '/oracle',
    icon: <AuditOutlined />,
  },
];

export default function DashboardPage() {
  return (
    <div className="workspace-hero">
      <div className="ai-mark">IT</div>
      <Title level={2}>IntelliTest 测试工作台</Title>
      <Text className="muted-text">从需求到测试资产导出的统一入口</Text>
      <Text className="muted-text">
        默认流程：需求输入 → 需求结构化 → 风险分析 → 综合设计 → 审查导出。
      </Text>
      <Text className="muted-text">
        综合设计集成黑盒测试、白盒建模和测试预言；审查导出默认优先使用综合设计结果。
      </Text>

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

      <Text className="muted-text">综合设计子功能可单独进入调试，也可直接运行综合流程。</Text>
      <div className="feature-grid" aria-label="综合设计子功能入口">
        {moduleLinks.map((item) => (
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
