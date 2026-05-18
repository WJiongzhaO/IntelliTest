import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';

const { Header, Content, Footer } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', color: '#fff' }}>
        <h1 style={{ margin: 0, fontSize: 20 }}>IntelliTest</h1>
      </Header>
      <Content style={{ padding: 24 }}>
        <Routes>
          <Route path="/" element={<div>Welcome to IntelliTest</div>} />
        </Routes>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        IntelliTest - AI-Driven AutoTestDesign Tool ©{new Date().getFullYear()} ATCrafters
      </Footer>
    </Layout>
  );
}

export default App;
