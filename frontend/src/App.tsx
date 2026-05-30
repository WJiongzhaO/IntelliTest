import { useState } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { Badge, Button, Layout, Space } from 'antd';
import {
  AppstoreOutlined,
  FileTextOutlined,
  RadarChartOutlined,
  BranchesOutlined,
  AuditOutlined,
  DeploymentUnitOutlined,
  DownloadOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ApartmentOutlined,
  DownOutlined,
} from '@ant-design/icons';
import DashboardPage from './pages/DashboardPage';
import RequirementsPage from './pages/RequirementsPage';
import RiskDashboardPage from './pages/RiskDashboardPage';
import TestDesignWorkbench from './pages/TestDesignWorkbench';
import WhiteboxWorkbench from './pages/WhiteboxWorkbench';
import OracleEditor from './pages/OracleEditor';
import ReviewExportPage from './pages/ReviewExportPage';
import BlackboxWorkbench from './pages/BlackboxWorkbench';
import JobQueuePanel from './components/JobQueuePanel';

const { Header, Content, Sider } = Layout;

const navTitles: Record<string, string> = {
  '/': '总览',
  '/requirements': '需求输入',
  '/risk': '风险分析',
  '/blackbox': '黑盒测试',
  '/test-design': '综合测试设计',
  '/whitebox': '白盒建模',
  '/oracle': '测试预言',
  '/review-export': '审查导出',
};

const standaloneNavItems = [
  { path: '/', icon: <AppstoreOutlined />, label: '工作台' },
  { path: '/requirements', icon: <FileTextOutlined />, label: '需求输入' },
  { path: '/risk', icon: <RadarChartOutlined />, label: '风险分析' },
];

const designSubItems = [
  { path: '/blackbox', icon: <ApartmentOutlined />, label: '黑盒测试' },
  { path: '/whitebox', icon: <BranchesOutlined />, label: '白盒建模' },
  { path: '/oracle', icon: <AuditOutlined />, label: '测试预言' },
];

function App() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [designOpen, setDesignOpen] = useState(true);
  const isActive = (path: string) => location.pathname === path;

  return (
    <Layout className="app-shell">
      <Sider
        width={252}
        collapsedWidth={76}
        collapsed={collapsed}
        className="dark-sider"
        trigger={null}
      >
        <div className="brand-lockup">
          <div className="brand-logo">I</div>
          <div>
            <strong>IntelliTest</strong>
            <span>ATCrafters</span>
          </div>
        </div>
        <span className="sider-caption">功能导航</span>
        <nav className="sider-nav" aria-label="功能导航">
          {standaloneNavItems.map((item) => (
            <Link
              className={`sider-nav-link${isActive(item.path) ? ' active' : ''}`}
              to={item.path}
              key={item.path}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          ))}

          <div className={`sider-nav-group${isActive('/test-design') ? ' active' : ''}`}>
            <Link className="sider-nav-link sider-nav-parent-link" to="/test-design">
              <DeploymentUnitOutlined />
              <span>综合设计</span>
            </Link>
            <button
              className={`sider-nav-toggle${designOpen ? ' open' : ''}`}
              type="button"
              aria-label={designOpen ? '收起综合设计子功能' : '展开综合设计子功能'}
              aria-expanded={designOpen}
              onClick={() => setDesignOpen((value) => !value)}
            >
              <DownOutlined />
            </button>
          </div>

          <div className={`sider-subnav${designOpen && !collapsed ? ' open' : ''}`}>
            {designSubItems.map((item) => (
              <Link
                className={`sider-nav-link sider-subnav-link${isActive(item.path) ? ' active' : ''}`}
                to={item.path}
                key={item.path}
                tabIndex={designOpen && !collapsed ? 0 : -1}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          <Link
            className={`sider-nav-link${isActive('/review-export') ? ' active' : ''}`}
            to="/review-export"
          >
            <DownloadOutlined />
            <span>审查导出</span>
          </Link>
        </nav>
      </Sider>
      <Layout className="main-layout">
        <Header className="top-bar">
          <Space>
            <Button
              type="text"
              className="sidebar-toggle"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed((value) => !value)}
              aria-label={collapsed ? '展开侧边栏' : '隐藏侧边栏'}
            />
            <strong>{navTitles[location.pathname] ?? 'IntelliTest'}</strong>
          </Space>
          <Space>
            <Badge status="success" text="在线" />
          </Space>
        </Header>
        <Content className="workspace">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/requirements" element={<RequirementsPage />} />
            <Route path="/risk" element={<RiskDashboardPage />} />
            <Route path="/blackbox" element={<BlackboxWorkbench />} />
            <Route path="/test-design" element={<TestDesignWorkbench />} />
            <Route path="/whitebox" element={<WhiteboxWorkbench />} />
            <Route path="/oracle" element={<OracleEditor />} />
            <Route path="/review-export" element={<ReviewExportPage />} />
          </Routes>
        </Content>
      </Layout>
      <JobQueuePanel />
    </Layout>
  );
}

export default App;
