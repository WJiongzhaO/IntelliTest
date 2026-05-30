import { create } from 'zustand';
import * as api from '../api/requirements';
import { useRequirementStore } from './requirementStore';

export type JobKind = 'structure' | 'risk';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface RequirementJob {
  id: string;
  requirementId: string;
  requirementTitle: string;
  kind: JobKind;
  status: JobStatus;
  error?: string;
  startedAt?: number;
  finishedAt?: number;
}

interface JobItem {
  id: string;
  title: string;
}

interface RequirementJobState {
  jobs: RequirementJob[];
  enqueueStructure: (items: JobItem[]) => void;
  enqueueRisk: (items: JobItem[]) => void;
  isRequirementBusy: (requirementId: string, kind?: JobKind) => boolean;
  clearFinished: () => void;
  cancelPending: () => void;
  retryFailed: (jobId: string) => void;
}

const kindLabels: Record<JobKind, string> = {
  structure: '结构化',
  risk: '风险分析',
};

export function getJobKindLabel(kind: JobKind): string {
  return kindLabels[kind];
}

let processing = false;

async function processQueue(): Promise<void> {
  if (processing) return;
  processing = true;

  try {
    while (true) {
      const { jobs } = useRequirementJobStore.getState();
      const next = jobs.find((job) => job.status === 'pending');
      if (!next) break;

      useRequirementJobStore.setState({
        jobs: jobs.map((job) =>
          job.id === next.id ? { ...job, status: 'running', startedAt: Date.now() } : job,
        ),
      });

      try {
        if (next.kind === 'structure') {
          const updated = await api.structureRequirement(next.requirementId);
          useRequirementStore.getState().patchRequirement(next.requirementId, updated);
        } else {
          const assessment = await api.analyzeRequirementRisk(next.requirementId);
          useRequirementStore.getState().applyRiskAssessment(next.requirementId, assessment);
        }

        useRequirementJobStore.setState((state) => ({
          jobs: state.jobs.map((job) =>
            job.id === next.id
              ? { ...job, status: 'completed', finishedAt: Date.now(), error: undefined }
              : job,
          ),
        }));
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : '处理失败';
        useRequirementJobStore.setState((state) => ({
          jobs: state.jobs.map((job) =>
            job.id === next.id ? { ...job, status: 'failed', error: msg, finishedAt: Date.now() } : job,
          ),
        }));
      }
    }
  } finally {
    processing = false;
  }
}

function enqueue(kind: JobKind, items: JobItem[]): void {
  const activeIds = new Set(
    useRequirementJobStore
      .getState()
      .jobs.filter(
        (job) =>
          job.kind === kind && (job.status === 'pending' || job.status === 'running'),
      )
      .map((job) => job.requirementId),
  );

  const newJobs: RequirementJob[] = items
    .filter((item) => !activeIds.has(item.id))
    .map((item) => ({
      id: `${kind}-${item.id}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      requirementId: item.id,
      requirementTitle: item.title,
      kind,
      status: 'pending',
    }));

  if (newJobs.length === 0) return;

  useRequirementJobStore.setState((state) => ({ jobs: [...state.jobs, ...newJobs] }));
  void processQueue();
}

export const useRequirementJobStore = create<RequirementJobState>((set, get) => ({
  jobs: [],

  enqueueStructure: (items) => enqueue('structure', items),

  enqueueRisk: (items) => enqueue('risk', items),

  isRequirementBusy: (requirementId, kind) =>
    get().jobs.some(
      (job) =>
        job.requirementId === requirementId &&
        (job.status === 'pending' || job.status === 'running') &&
        (kind === undefined || job.kind === kind),
    ),

  clearFinished: () =>
    set((state) => ({
      jobs: state.jobs.filter(
        (job) => job.status === 'pending' || job.status === 'running',
      ),
    })),

  cancelPending: () =>
    set((state) => ({
      jobs: state.jobs.filter((job) => job.status !== 'pending'),
    })),

  retryFailed: (jobId) => {
    const target = get().jobs.find((job) => job.id === jobId);
    if (!target || target.status !== 'failed') return;

    set((state) => ({
      jobs: state.jobs.map((job) =>
        job.id === jobId
          ? { ...job, status: 'pending', error: undefined, startedAt: undefined, finishedAt: undefined }
          : job,
      ),
    }));
    void processQueue();
  },
}));
