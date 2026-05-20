import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  FileTextOutlined,
  ExperimentOutlined,
  BranchesOutlined,
  AuditOutlined,
  DeploymentUnitOutlined,
} from '@ant-design/icons';
import RequirementsPage from './pages/RequirementsPage';
import TestDesignWorkbench from './pages/TestDesignWorkbench';
import WhiteboxWorkbench from './pages/WhiteboxWorkbench';
import OracleEditor from './pages/OracleEditor';

const { Header, Content, Footer, Sider } = Layout;

const navItems = [
  { key: '/', icon: <FileTextOutlined />, label: <Link to="/">Requirements</Link> },
  {
    key: '/test-design',
    icon: <DeploymentUnitOutlined />,
    label: <Link to="/test-design">Test Design (C+D)</Link>,
  },
  {
    key: '/whitebox',
    icon: <BranchesOutlined />,
    label: <Link to="/whitebox">Whitebox (FR 4.0)</Link>,
  },
  { key: '/oracle', icon: <AuditOutlined />, label: <Link to="/oracle">Oracle (FR 5.0)</Link> },
];

function App() {
  const location = useLocation();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <h1 style={{ margin: '0 16px 0 0', fontSize: 20, color: '#fff', whiteSpace: 'nowrap' }}>
          IntelliTest
        </h1>
        <ExperimentOutlined style={{ color: '#fff', marginRight: 8 }} />
        <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: 13 }}>ATCrafters</span>
      </Header>
      <Layout>
        <Sider width={220} theme="light">
          <Menu mode="inline" selectedKeys={[location.pathname]} items={navItems} />
        </Sider>
        <Layout>
          <Content style={{ padding: 24 }}>
            <Routes>
              <Route path="/" element={<RequirementsPage />} />
              <Route path="/test-design" element={<TestDesignWorkbench />} />
              <Route path="/whitebox" element={<WhiteboxWorkbench />} />
              <Route path="/oracle" element={<OracleEditor />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
      <Footer style={{ textAlign: 'center' }}>
        IntelliTest - AI-Driven AutoTestDesign Tool &copy;{new Date().getFullYear()} ATCrafters
      </Footer>
    </Layout>
  );
}

export default App;
