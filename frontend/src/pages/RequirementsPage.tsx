import { Alert, Space } from 'antd';
import RequirementInputPanel from '../components/RequirementInputPanel';
import RequirementList from '../components/RequirementList';
import { useRequirementStore } from '../stores/requirementStore';

export default function RequirementsPage() {
  const { error, clearError } = useRequirementStore();

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          closable
          onClose={clearError}
          showIcon
        />
      )}

      <RequirementInputPanel />
      <RequirementList />
    </Space>
  );
}
