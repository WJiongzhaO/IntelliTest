import { Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import RequirementsPage from './pages/RequirementsPage';

const { Header, Content, Footer } = Layout;

const navItems = [
  { key: '/', icon: <FileTextOutlined />, label: <Link to="/">Requirements</Link> },
];

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <h1 style={{ margin: '0 24px 0 0', fontSize: 20, color: '#fff', whiteSpace: 'nowrap' }}>
          IntelliTest
        </h1>
        <Menu
          theme="dark"
          mode="horizontal"
          selectable={false}
          items={navItems}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ padding: 24 }}>
        <Routes>
          <Route path="/" element={<RequirementsPage />} />
        </Routes>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        IntelliTest - AI-Driven AutoTestDesign Tool &copy;{new Date().getFullYear()} ATCrafters
      </Footer>
    </Layout>
  );
}

export default App;
