import { useState } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { Badge, Button, Layout, Menu, Space } from 'antd';
import {
  AppstoreOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  RadarChartOutlined,
  BranchesOutlined,
  AuditOutlined,
  DeploymentUnitOutlined,
  DownloadOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ApartmentOutlined,
} from '@ant-design/icons';
import DashboardPage from './pages/DashboardPage';
import RequirementsPage from './pages/RequirementsPage';
import RiskDashboardPage from './pages/RiskDashboardPage';
import TestDesignWorkbench from './pages/TestDesignWorkbench';
import WhiteboxWorkbench from './pages/WhiteboxWorkbench';
import OracleEditor from './pages/OracleEditor';
import ReviewExportPage from './pages/ReviewExportPage';
import BlackboxWorkbench from './pages/BlackboxWorkbench';

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

const navItems = [
  { key: '/', icon: <AppstoreOutlined />, label: <Link to="/">工作台</Link> },
  {
    key: '/requirements',
    icon: <FileTextOutlined />,
    label: <Link to="/requirements">需求输入</Link>,
  },
  { key: '/risk', icon: <RadarChartOutlined />, label: <Link to="/risk">风险分析</Link> },
  {
    key: '/blackbox',
    icon: <ApartmentOutlined />,
    label: <Link to="/blackbox">黑盒测试</Link>,
  },
  {
    key: '/test-design',
    icon: <DeploymentUnitOutlined />,
    label: <Link to="/test-design">综合设计</Link>,
  },
  {
    key: '/whitebox',
    icon: <BranchesOutlined />,
    label: <Link to="/whitebox">白盒建模</Link>,
  },
  { key: '/oracle', icon: <AuditOutlined />, label: <Link to="/oracle">测试预言</Link> },
  {
    key: '/review-export',
    icon: <DownloadOutlined />,
    label: <Link to="/review-export">审查导出</Link>,
  },
];

function App() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

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
        <Button className="new-run-button" icon={<ExperimentOutlined />}>
          新建测试流程
        </Button>
        <span className="sider-caption">功能导航</span>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={navItems}
          className="sider-menu"
        />
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
    </Layout>
  );
}

export default App;
