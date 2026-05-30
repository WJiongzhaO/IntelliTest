import { create } from 'zustand';
import { generateBlackboxWithCoverage } from '../api/blackbox';
import { createWhiteboxModel } from '../api/whitebox';
import { runCombinedDesign } from '../api/testDesign';
import type {
  BlackBoxGenerationResult,
  BlackBoxTechnique,
  CoverageCriterion,
  StructuredRequirement,
  TestSuite,
} from '../types/models';
import type { WhiteboxModelResponse } from '../api/whitebox';

export type TestDesignJobKind = 'blackbox' | 'whitebox' | 'combined';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface BlackboxJobOptions {
  techniques: BlackBoxTechnique[];
}

export interface WhiteboxJobOptions {
  coverage: CoverageCriterion;
  useLlm: boolean;
}

export interface CombinedJobOptions {
  techniques: string[];
  coverage: CoverageCriterion;
  useLlm: boolean;
  synthesizeOracles: boolean;
}

export type TestDesignJobOptions = BlackboxJobOptions | WhiteboxJobOptions | CombinedJobOptions;

export interface TestDesignJob {
  id: string;
  requirementId: string;
  requirementTitle: string;
  requirement: StructuredRequirement;
  kind: TestDesignJobKind;
  options: TestDesignJobOptions;
  status: JobStatus;
  error?: string;
  startedAt?: number;
  finishedAt?: number;
}

interface EnqueueItem {
  internalId: string;
  requirement: StructuredRequirement;
  title: string;
}

interface TestDesignJobState {
  jobs: TestDesignJob[];
  blackboxResults: Record<string, BlackBoxGenerationResult>;
  whiteboxResults: Record<string, WhiteboxModelResponse>;
  combinedResults: Record<string, TestSuite>;
  enqueueBlackbox: (items: EnqueueItem[], options: BlackboxJobOptions) => void;
  enqueueWhitebox: (items: EnqueueItem[], options: WhiteboxJobOptions) => void;
  enqueueCombined: (items: EnqueueItem[], options: CombinedJobOptions) => void;
  isRequirementBusy: (requirementId: string, kind?: TestDesignJobKind) => boolean;
  clearFinished: () => void;
  cancelPending: () => void;
  retryFailed: (jobId: string) => void;
  clearResults: (kind: TestDesignJobKind) => void;
}

const kindLabels: Record<TestDesignJobKind, string> = {
  blackbox: '黑盒生成',
  whitebox: '白盒建模',
  combined: '综合设计',
};

export function getTestDesignJobKindLabel(kind: TestDesignJobKind): string {
  return kindLabels[kind];
}

let processing = false;

async function runJob(job: TestDesignJob): Promise<void> {
  if (job.kind === 'blackbox') {
    const options = job.options as BlackboxJobOptions;
    const result = await generateBlackboxWithCoverage(
      job.requirement,
      options.techniques,
      job.requirementId,
    );
    useTestDesignJobStore.setState((state) => ({
      blackboxResults: { ...state.blackboxResults, [job.requirementId]: result },
    }));
    return;
  }

  if (job.kind === 'whitebox') {
    const options = job.options as WhiteboxJobOptions;
    const result = await createWhiteboxModel({
      requirement_id: job.requirementId,
      requirement: job.requirement,
      coverage: options.coverage,
      use_llm: options.useLlm,
    });
    useTestDesignJobStore.setState((state) => ({
      whiteboxResults: { ...state.whiteboxResults, [job.requirementId]: result },
    }));
    return;
  }

  const options = job.options as CombinedJobOptions;
  const result = await runCombinedDesign({
    requirement_id: job.requirementId,
    requirement: job.requirement,
    techniques: options.techniques,
    coverage: options.coverage,
    synthesize_oracles: options.synthesizeOracles,
    use_llm: options.useLlm,
  });
  useTestDesignJobStore.setState((state) => ({
    combinedResults: { ...state.combinedResults, [job.requirementId]: result },
  }));
}

async function processQueue(): Promise<void> {
  if (processing) return;
  processing = true;

  try {
    while (true) {
      const { jobs } = useTestDesignJobStore.getState();
      const next = jobs.find((job) => job.status === 'pending');
      if (!next) break;

      useTestDesignJobStore.setState({
        jobs: jobs.map((job) =>
          job.id === next.id ? { ...job, status: 'running', startedAt: Date.now() } : job,
        ),
      });

      try {
        await runJob(next);
        useTestDesignJobStore.setState((state) => ({
          jobs: state.jobs.map((job) =>
            job.id === next.id
              ? { ...job, status: 'completed', finishedAt: Date.now(), error: undefined }
              : job,
          ),
        }));
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : '生成失败';
        useTestDesignJobStore.setState((state) => ({
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

function enqueue(
  kind: TestDesignJobKind,
  items: EnqueueItem[],
  options: TestDesignJobOptions,
): void {
  const activeIds = new Set(
    useTestDesignJobStore
      .getState()
      .jobs.filter(
        (job) =>
          job.kind === kind && (job.status === 'pending' || job.status === 'running'),
      )
      .map((job) => job.requirementId),
  );

  const newJobs: TestDesignJob[] = items
    .filter((item) => !activeIds.has(item.internalId))
    .map((item) => ({
      id: `${kind}-${item.internalId}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      requirementId: item.internalId,
      requirementTitle: item.title,
      requirement: item.requirement,
      kind,
      options,
      status: 'pending',
    }));

  if (newJobs.length === 0) return;

  useTestDesignJobStore.setState((state) => ({ jobs: [...state.jobs, ...newJobs] }));
  void processQueue();
}

export const useTestDesignJobStore = create<TestDesignJobState>((set, get) => ({
  jobs: [],
  blackboxResults: {},
  whiteboxResults: {},
  combinedResults: {},

  enqueueBlackbox: (items, options) => enqueue('blackbox', items, options),

  enqueueWhitebox: (items, options) => enqueue('whitebox', items, options),

  enqueueCombined: (items, options) => enqueue('combined', items, options),

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

  clearResults: (kind) => {
    if (kind === 'blackbox') set({ blackboxResults: {} });
    if (kind === 'whitebox') set({ whiteboxResults: {} });
    if (kind === 'combined') set({ combinedResults: {} });
  },
}));
