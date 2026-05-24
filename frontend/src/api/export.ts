import apiClient from './client';
import type { ExportArtifact, ExportFormat } from '../types/models';

export async function exportArtifact(
  artifact: ExportArtifact,
  fileFormat: ExportFormat,
): Promise<Blob> {
  const { data } = await apiClient.post('/export/artifact', artifact, {
    params: { format: fileFormat },
    responseType: 'blob',
  });
  return data;
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
