import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Checkbox, Input, Modal, Space, Table, Typography, message } from 'antd';
import { FolderOpenOutlined } from '@ant-design/icons';
import type { RequirementReviewBundle } from '../api/artifacts';
import { exportArtifact } from '../api/export';
import type { ExportArtifact, ExportFormat } from '../types/models';
import {
  EXPORT_FORMAT_LABELS,
  defaultExportBasename,
  isDirectoryPickerSupported,
  pickExportDirectory,
  writeBlobToDirectory,
} from '../utils/directoryExport';

const { Text } = Typography;

export interface BulkExportEntry {
  requirementId: string;
  requirementRef: string;
  title: string;
  basename: string;
}

interface BulkExportModalProps {
  open: boolean;
  bundles: RequirementReviewBundle[];
  buildArtifact: (bundle: RequirementReviewBundle, basename: string) => ExportArtifact;
  onClose: () => void;
}

const ALL_FORMATS: ExportFormat[] = ['json', 'csv', 'xlsx'];

function buildEntries(bundles: RequirementReviewBundle[]): BulkExportEntry[] {
  return bundles.map((bundle) => ({
    requirementId: bundle.requirement_id,
    requirementRef: bundle.external_id?.trim() || bundle.requirement_ref,
    title: bundle.title?.trim() ?? '',
    basename: defaultExportBasename(bundle),
  }));
}

export default function BulkExportModal({
  open,
  bundles,
  buildArtifact,
  onClose,
}: BulkExportModalProps) {
  const [entries, setEntries] = useState<BulkExportEntry[]>([]);
  const [formats, setFormats] = useState<ExportFormat[]>(['json', 'csv', 'xlsx']);
  const [dirHandle, setDirHandle] = useState<FileSystemDirectoryHandle | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (open) {
      setEntries(buildEntries(bundles));
      setFormats(['json', 'csv', 'xlsx']);
      setDirHandle(null);
    }
  }, [open, bundles]);

  const duplicateBasenames = useMemo(() => {
    const seen = new Map<string, number>();
    for (const entry of entries) {
      const key = entry.basename.trim().toLowerCase();
      if (!key) continue;
      seen.set(key, (seen.get(key) ?? 0) + 1);
    }
    return [...seen.entries()].filter(([, count]) => count > 1).map(([name]) => name);
  }, [entries]);

  const updateBasename = (requirementId: string, basename: string) => {
    setEntries((prev) =>
      prev.map((entry) => (entry.requirementId === requirementId ? { ...entry, basename } : entry)),
    );
  };

  const handlePickDirectory = async () => {
    try {
      const handle = await pickExportDirectory();
      setDirHandle(handle);
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      message.error(error instanceof Error ? error.message : '选择文件夹失败');
    }
  };

  const handleExport = async () => {
    if (formats.length === 0) {
      message.warning('请至少选择一种导出格式');
      return;
    }
    if (!dirHandle) {
      message.warning('请先选择保存文件夹');
      return;
    }
    if (entries.some((entry) => !entry.basename.trim())) {
      message.warning('文件名不能为空');
      return;
    }
    if (duplicateBasenames.length > 0) {
      message.warning('存在重复的文件名，请修改后再导出');
      return;
    }

    const bundleById = new Map(bundles.map((bundle) => [bundle.requirement_id, bundle]));
    setExporting(true);
    let fileCount = 0;
    try {
      for (const entry of entries) {
        const bundle = bundleById.get(entry.requirementId);
        if (!bundle) continue;
        const basename = entry.basename.trim();
        for (const format of formats) {
          const blob = await exportArtifact(buildArtifact(bundle, basename), format);
          await writeBlobToDirectory(dirHandle, `${basename}.${format}`, blob);
          fileCount += 1;
        }
      }
      message.success(`已导出 ${fileCount} 个文件到「${dirHandle.name}」`);
      onClose();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '批量导出失败');
    } finally {
      setExporting(false);
    }
  };

  return (
    <Modal
      title="批量导出"
      open={open}
      width={720}
      onCancel={onClose}
      destroyOnClose
      footer={[
        <Button key="cancel" onClick={onClose} disabled={exporting}>
          取消
        </Button>,
        <Button key="export" type="primary" loading={exporting} onClick={() => void handleExport()}>
          导出到文件夹
        </Button>,
      ]}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {!isDirectoryPickerSupported() && (
          <Alert
            type="warning"
            showIcon
            message="当前浏览器不支持选择文件夹，请使用 Chrome 或 Edge 进行批量导出"
          />
        )}

        <div>
          <Text strong>导出格式</Text>
          <div style={{ marginTop: 8 }}>
            <Checkbox.Group
              value={formats}
              options={ALL_FORMATS.map((format) => ({
                label: EXPORT_FORMAT_LABELS[format],
                value: format,
              }))}
              onChange={(values) => setFormats(values as ExportFormat[])}
            />
          </div>
        </div>

        <div>
          <Text strong>保存路径</Text>
          <Space style={{ marginTop: 8, width: '100%' }} align="start">
            <Input
              readOnly
              style={{ width: 480 }}
              placeholder="点击右侧按钮选择保存文件夹"
              value={dirHandle ? dirHandle.name : ''}
            />
            <Button icon={<FolderOpenOutlined />} onClick={() => void handlePickDirectory()}>
              选择文件夹
            </Button>
          </Space>
          {dirHandle && (
            <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
              所有文件将保存到所选文件夹内
            </Text>
          )}
        </div>

        <div>
          <Text strong>文件名（编号 + 需求名，可修改）</Text>
          {duplicateBasenames.length > 0 && (
            <Alert
              type="error"
              showIcon
              style={{ marginTop: 8, marginBottom: 8 }}
              message={`存在重复文件名：${duplicateBasenames.join('、')}`}
            />
          )}
          <Table<BulkExportEntry>
            size="small"
            rowKey="requirementId"
            pagination={false}
            scroll={{ y: 280 }}
            style={{ marginTop: 8 }}
            dataSource={entries}
            columns={[
              {
                title: '需求编号',
                dataIndex: 'requirementRef',
                width: 120,
              },
              {
                title: '需求名',
                dataIndex: 'title',
                width: 180,
                render: (title: string) => title || '—',
              },
              {
                title: '导出文件名',
                dataIndex: 'basename',
                render: (_, row) => (
                  <Input
                    value={row.basename}
                    onChange={(e) => updateBasename(row.requirementId, e.target.value)}
                  />
                ),
              },
            ]}
          />
          <Text type="secondary">
            共 {entries.length} 条需求，将生成 {entries.length * formats.length} 个文件
          </Text>
        </div>
      </Space>
    </Modal>
  );
}
