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

export async function getDashboardStats(): Promise<DashboardStats> {
  const data = await fetchJson<DashboardStats>('/api/evaluations/dashboard')
  return data
}
