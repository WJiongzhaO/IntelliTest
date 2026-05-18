import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import WhiteboxWorkbench from './pages/WhiteboxWorkbench';
import OracleEditor from './pages/OracleEditor';

const { Header, Content, Footer, Sider } = Layout;

const navItems = [
  { key: '/', label: <Link to="/">Home</Link> },
  { key: '/whitebox', label: <Link to="/whitebox">Whitebox (FR 4.0)</Link> },
  { key: '/oracle', label: <Link to="/oracle">Oracle (FR 5.0)</Link> },
];

function App() {
  const location = useLocation();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', color: '#fff' }}>
        <h1 style={{ margin: 0, fontSize: 20, color: '#fff' }}>IntelliTest</h1>
      </Header>
      <Layout>
        <Sider width={220} theme="light">
          <Menu mode="inline" selectedKeys={[location.pathname]} items={navItems} />
        </Sider>
        <Layout>
          <Content style={{ padding: 24 }}>
            <Routes>
              <Route
                path="/"
                element={
                  <div>
                    <p>Welcome to IntelliTest — Member D deliverables:</p>
                    <ul>
                      <li>
                        <Link to="/whitebox">Whitebox workbench</Link> — state models & coverage
                      </li>
                      <li>
                        <Link to="/oracle">Oracle editor</Link> — CoT synthesis & review
                      </li>
                    </ul>
                  </div>
                }
              />
              <Route path="/whitebox" element={<WhiteboxWorkbench />} />
              <Route path="/oracle" element={<OracleEditor />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
      <Footer style={{ textAlign: 'center' }}>
        IntelliTest - AI-Driven AutoTestDesign Tool ©{new Date().getFullYear()} ATCrafters
      </Footer>
    </Layout>
  );
}

export default App;
