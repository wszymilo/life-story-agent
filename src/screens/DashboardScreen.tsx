import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboardStats, DashboardStats } from '../services/evaluation';
import { TopBar } from '../components/TopBar';
import { LoadingScreen } from '../components/LoadingScreen';
import { ErrorFallback } from '../components/ErrorFallback';

export function DashboardScreen() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Evaluations</h2>
          {stats.recent_evaluations.length === 0 ? (
            <p className="text-gray-500">No evaluations yet</p>
          ) : (
            <div className="space-y-2">
              {stats.recent_evaluations.map((eval_) => (
                <div key={eval_.id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <span className="font-medium">{eval_.eval_type}</span>
                    <span className="text-gray-500 text-sm ml-2">
                      {new Date(eval_.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <span className="text-blue-600 font-bold">
                    {eval_.overall_score ?? '-'} / 5
                  </span>
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
