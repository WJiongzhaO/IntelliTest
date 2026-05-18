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
      const msg = err instanceof Error ? err.message : 'Failed to fetch requirements';
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
      const msg = err instanceof Error ? err.message : 'CSV upload failed';
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
      const msg = err instanceof Error ? err.message : 'Text parsing failed';
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
      const msg = err instanceof Error ? err.message : 'Form submission failed';
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
      const msg = err instanceof Error ? err.message : 'Structuring failed';
      set({ error: msg, loading: false });
      return null;
    }
  },

  remove: async (id: string) => {
    try {
      await api.deleteRequirement(id);
      set({ requirements: get().requirements.filter((r) => r.id !== id) });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Delete failed';
      set({ error: msg });
    }
  },

  clearError: () => set({ error: null }),
}));
