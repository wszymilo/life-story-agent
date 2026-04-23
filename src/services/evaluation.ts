import { fetchJson } from './api'

export interface DashboardStats {
  total_evaluations: number;
  avg_factual_accuracy: number | null;
  avg_coherence: number | null;
  avg_completeness: number | null;
  avg_overall_score: number | null;
  recent_evaluations: EvaluationResult[];
}

export interface EvaluationResult {
  id: string;
  event_id: string;
  eval_type: string;
  prompt_text: string | null;
  summary_text: string | null;
  factual_accuracy: number | null;
  coherence: number | null;
  completeness: number | null;
  overall_score: number | null;
  evaluator_model: string;
  created_at: string;
}

export async function getDashboardStats(evalType?: string): Promise<DashboardStats> {
  const url = evalType ? `/api/evaluations/dashboard?eval_type=${encodeURIComponent(evalType)}` : '/api/evaluations/dashboard'
  const data = await fetchJson<DashboardStats>(url)
  return data
}

export interface CreateEvaluationInput {
  event_id: string
  eval_type: string
  prompt_text: string
  summary_text: string
}

export async function createEvaluation(input: CreateEvaluationInput): Promise<void> {
  await fetchJson<void>('/api/evaluations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}
