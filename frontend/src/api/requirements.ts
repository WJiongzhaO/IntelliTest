import apiClient from './client';
import type { FormEntry, RequirementResponse } from '../types';

export async function uploadCsv(file: File): Promise<RequirementResponse[]> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post('/requirements/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function ingestText(text: string): Promise<RequirementResponse[]> {
  const { data } = await apiClient.post('/requirements/text', { text });
  return data;
}

export async function ingestForm(entries: FormEntry[]): Promise<RequirementResponse[]> {
  const { data } = await apiClient.post('/requirements', { entries });
  return data;
}

export async function listRequirements(): Promise<RequirementResponse[]> {
  const { data } = await apiClient.get('/requirements');
  return data;
}

export async function getRequirement(id: string): Promise<RequirementResponse> {
  const { data } = await apiClient.get(`/requirements/${id}`);
  return data;
}

export async function updateRequirement(
  id: string,
  fields: Partial<RequirementResponse>,
): Promise<RequirementResponse> {
  const { data } = await apiClient.put(`/requirements/${id}`, fields);
  return data;
}

export async function deleteRequirement(id: string): Promise<void> {
  await apiClient.delete(`/requirements/${id}`);
}

export async function structureRequirement(id: string): Promise<RequirementResponse> {
  const { data } = await apiClient.post(`/requirements/${id}/structure`);
  return data;
}
