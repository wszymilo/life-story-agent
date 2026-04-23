import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboardStats, DashboardStats } from '../services/evaluation'
import { TopBar } from '../components/TopBar'
import { LoadingScreen } from '../components/LoadingScreen'
import { ErrorFallback } from '../components/ErrorFallback'
import { extractErrorMessage } from '../lib/errors'

const EVAL_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'summary', label: 'Summary' },
  { value: 'meta_story', label: 'Meta Story' },
  { value: 'question', label: 'Question' },
]

export function DashboardScreen() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null)
  const [evalType, setEvalType] = useState('')

  useEffect(() => {
    setLoading(true)
    getDashboardStats(evalType || undefined)
      .then(setStats)
      .catch((err) => setError(extractErrorMessage(err, 'Failed to load dashboard')))
      .finally(() => setLoading(false))
  }, [evalType])

  if (loading) {
    return <LoadingScreen message="Loading dashboard..." />;
  }

  if (error) {
    return (
      <ErrorFallback
        message={error}
        onRetry={() => navigate('/')}
        retryLabel="Back to Timeline"
      />
    );
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">No data available</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar title="Evaluation Dashboard" back={{ href: '/' }} />
      <div className="max-w-2xl mx-auto p-4">

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Total Evaluations</h2>
          <p className="text-4xl font-bold text-blue-600">{stats.total_evaluations}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Average Scores</h2>
          <div className="grid grid-cols-4 gap-4">
            <ScoreCard label="Accuracy" value={stats.avg_factual_accuracy} />
            <ScoreCard label="Coherence" value={stats.avg_coherence} />
            <ScoreCard label="Completeness" value={stats.avg_completeness} />
            <ScoreCard label="Overall" value={stats.avg_overall_score} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Filter by Type</h2>
            <select
              value={evalType}
              onChange={(e) => setEvalType(e.target.value)}
              className="px-4 py-2 border rounded-lg text-lg bg-white"
            >
              {EVAL_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Evaluations (last 10)</h2>
          {stats.recent_evaluations.length === 0 ? (
            <p className="text-gray-500">No evaluations yet</p>
          ) : (
            <div className="space-y-3">
              {stats.recent_evaluations.map((eval_) => (
                <div key={eval_.id} className="border-b pb-3">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="font-medium capitalize">{eval_.eval_type.replace('_', ' ')}</span>
                      <span className="text-gray-500 text-sm ml-2">
                        {new Date(eval_.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-sm">
                    <ScoreBadge label="Acc" value={eval_.factual_accuracy} />
                    <ScoreBadge label="Coh" value={eval_.coherence} />
                    <ScoreBadge label="Comp" value={eval_.completeness} />
                    <ScoreBadge label="Overall" value={eval_.overall_score} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ScoreCard({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="text-center">
      <div className="text-sm text-gray-600">{label}</div>
      <div className="text-2xl font-bold text-green-600">
        {value?.toFixed(1) ?? '-'}
      </div>
    </div>
  );
}

function ScoreBadge({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="text-center bg-gray-100 rounded py-1">
      <span className="text-gray-500 text-xs block">{label}</span>
      <span className="font-bold text-blue-600">{value ?? '-'}</span>
    </div>
  );
}
