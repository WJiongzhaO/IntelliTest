import { create } from 'zustand';
import type { RequirementResponse } from '../types';
import * as api from '../api/requirements';

interface RequirementState {
  requirements: RequirementResponse[];
  loading: boolean;
  error: string | null;

  fetchAll: () => Promise<void>;
  addByCsv: (file: File) => Promise<RequirementResponse[]>;
  addByText: (text: string) => Promise<RequirementResponse[]>;
  addByForm: (entries: { raw_text: string }[]) => Promise<RequirementResponse[]>;
  structureOne: (id: string) => Promise<RequirementResponse | null>;
  analyzeRisk: (id: string) => Promise<void>;
  remove: (id: string) => Promise<void>;
  clearError: () => void;
}

export const useRequirementStore = create<RequirementState>((set, get) => ({
  requirements: [],
  loading: false,
  error: null,

  fetchAll: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.listRequirements();
      set({ requirements: data, loading: false });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '需求列表获取失败';
      set({ error: msg, loading: false });
    }
  },

  addByCsv: async (file: File) => {
    set({ loading: true, error: null });
    try {
      const created = await api.uploadCsv(file);
      set({ requirements: [...created, ...get().requirements], loading: false });
      return created;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'CSV 导入失败';
      set({ error: msg, loading: false });
      return [];
    }
  },

  addByText: async (text: string) => {
    set({ loading: true, error: null });
    try {
      const created = await api.ingestText(text);
      set({ requirements: [...created, ...get().requirements], loading: false });
      return created;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '文本解析失败';
      set({ error: msg, loading: false });
      return [];
    }
  },

  addByForm: async (entries) => {
    set({ loading: true, error: null });
    try {
      const created = await api.ingestForm(entries);
      set({ requirements: [...created, ...get().requirements], loading: false });
      return created;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '表单提交失败';
      set({ error: msg, loading: false });
      return [];
    }
  },

  structureOne: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const updated = await api.structureRequirement(id);
      const reqs = get().requirements.map((r) => (r.id === id ? updated : r));
      set({ requirements: reqs, loading: false });
      return updated;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '需求结构化失败';
      set({ error: msg, loading: false });
      return null;
    }
  },

  analyzeRisk: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const assessment = await api.analyzeRequirementRisk(id);
      const reqs = get().requirements.map((r) =>
        r.id === id
          ? {
              ...r,
              risk_impact: assessment.impact,
              risk_likelihood: assessment.likelihood,
              risk_score: assessment.risk_score,
              priority: assessment.priority,
              risk_impact_rationale: assessment.impact_rationale,
              risk_likelihood_rationale: assessment.likelihood_rationale,
            }
          : r,
      );
      set({ requirements: reqs, loading: false });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '风险分析失败';
      set({ error: msg, loading: false });
    }
  },

  remove: async (id: string) => {
    try {
      await api.deleteRequirement(id);
      set({ requirements: get().requirements.filter((r) => r.id !== id) });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '删除失败';
      set({ error: msg });
    }
  },

  clearError: () => set({ error: null }),
}));
