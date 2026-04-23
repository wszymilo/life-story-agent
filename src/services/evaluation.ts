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

export interface EvaluationScores {
  factual_accuracy: number;
  coherence: number;
  completeness: number;
  overall_score: number;
}

export async function storeEvaluationScores(
  eventId: string,
  evalType: string,
  scores: EvaluationScores,
): Promise<void> {
  await fetchJson<void>('/api/evaluations/scores', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_id: eventId, eval_type: evalType, ...scores }),
  })
}
