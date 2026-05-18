import apiClient from './client';
import type {
  CoverageCriterion,
  StateMachineModel,
  StructuredRequirement,
  TestCase,
  TestSequence,
} from '../types/models';

export interface WhiteboxModelRequest {
  requirement_id?: string;
  requirement?: StructuredRequirement;
  coverage: CoverageCriterion;
  use_llm?: boolean;
}

export interface WhiteboxModelResponse {
  model: StateMachineModel;
  sequences: TestSequence[];
  test_cases: TestCase[];
  coverage: CoverageCriterion;
}

export interface MermaidRegenerateRequest {
  initial_state: string;
  states: string[];
  transitions: StateMachineModel['transitions'];
}

export async function createWhiteboxModel(
  body: WhiteboxModelRequest,
): Promise<WhiteboxModelResponse> {
  const { data } = await apiClient.post<WhiteboxModelResponse>('/whitebox/model', body);
  return data;
}

export async function getWhiteboxModel(modelId: string): Promise<StateMachineModel> {
  const { data } = await apiClient.get<StateMachineModel>(`/whitebox/model/${modelId}`);
  return data;
}

export async function updateWhiteboxModel(
  modelId: string,
  body: Partial<StateMachineModel> & { coverage: CoverageCriterion },
): Promise<WhiteboxModelResponse> {
  const { data } = await apiClient.put<WhiteboxModelResponse>(`/whitebox/model/${modelId}`, body);
  return data;
}

export async function regenerateMermaid(
  body: MermaidRegenerateRequest,
): Promise<{ mermaid_diagram: string }> {
  const { data } = await apiClient.post<{ mermaid_diagram: string }>(
    '/whitebox/regenerate-mermaid',
    body,
  );
  return data;
}
