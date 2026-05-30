import type { RequirementReviewBundle } from '../api/artifacts';
import type { ExportFormat } from '../types/models';

const INVALID_FILENAME_CHARS = /[<>:"/\\|?*\x00-\x1f]/g;

export function sanitizeExportBasename(name: string): string {
  return name.replace(INVALID_FILENAME_CHARS, '_').replace(/\s+/g, ' ').trim();
}

export function defaultExportBasename(bundle: RequirementReviewBundle): string {
  const ref = bundle.external_id?.trim() || bundle.requirement_ref;
  const title = bundle.title?.trim();
  if (title) return sanitizeExportBasename(`${ref}_${title}`);
  return sanitizeExportBasename(ref);
}

export function isDirectoryPickerSupported(): boolean {
  return typeof window.showDirectoryPicker === 'function';
}

export async function pickExportDirectory(): Promise<FileSystemDirectoryHandle> {
  if (!isDirectoryPickerSupported()) {
    throw new Error('当前浏览器不支持选择文件夹批量保存，请使用 Chrome 或 Edge');
  }
  return window.showDirectoryPicker({ mode: 'readwrite' });
}

export async function writeBlobToDirectory(
  dirHandle: FileSystemDirectoryHandle,
  filename: string,
  blob: Blob,
): Promise<void> {
  const fileHandle = await dirHandle.getFileHandle(filename, { create: true });
  const writable = await fileHandle.createWritable();
  await writable.write(blob);
  await writable.close();
}

export const EXPORT_FORMAT_LABELS: Record<ExportFormat, string> = {
  json: 'JSON',
  csv: 'CSV',
  xlsx: 'Excel',
};
