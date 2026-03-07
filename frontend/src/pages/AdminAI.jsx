import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAdminAiAnalyses } from '../api/client';
import { useAuth } from '../context/AuthContext';

const ADMIN_USER_IDS = [1, 6];

const RISK_COLORS = {
  low:    'text-green-400',
  medium: 'text-yellow-400',
  high:   'text-red-400',
};
const RISK_ICONS = { low: '✅', medium: '⚡', high: '⚠️' };
const STATUS_COLORS = {
  done:    'bg-green-900/40 text-green-300',
  error:   'bg-red-900/40 text-red-300',
  pending: 'bg-yellow-900/40 text-yellow-300',
};

export default function AdminAI() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  // Redirection si pas admin
  useEffect(() => {
    if (user !== null && !ADMIN_USER_IDS.includes(user?.id)) {
      navigate('/', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    if (!token) return;
    getAdminAiAnalyses(token)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  function refresh() {
    setLoading(true);
    setError(null);
    getAdminAiAnalyses(token)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  const filtered = data?.analyses?.filter(a =>
    filter === 'all' || a.status === filter
  ) || [];

  return (
    <div className="min-h-screen bg-fmc-bg text-fmc-text font-mono p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-fmc-text flex items-center gap-2">
              <span className="text-purple-400">✨</span> Admin — Requêtes IA
            </h1>
            <p className="text-fmc-text-muted text-xs mt-0.5">
              Toutes les analyses IA effectuées sur les annonces
            </p>
          </div>
          <div className="flex gap-2">
            <a href="/" className="px-3 py-1.5 text-xs border border-fmc-border rounded hover:bg-fmc-surface transition-colors">
              ← Accueil
            </a>
            <button
              onClick={refresh}
              className="px-3 py-1.5 text-xs bg-purple-900/40 border border-purple-500/40 text-purple-300 rounded hover:bg-purple-900/60 transition-colors"
            >
              ↻ Rafraîchir
            </button>
          </div>
        </div>

        {/* Stats cards */}
        {data && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Total', value: data.total, color: 'text-fmc-text', bg: 'bg-fmc-surface' },
              { label: '✅ Réussies', value: data.done, color: 'text-green-400', bg: 'bg-green-900/20' },
              { label: '❌ Erreurs', value: data.errors, color: 'text-red-400', bg: 'bg-red-900/20' },
              { label: '⏳ En cours', value: data.pending, color: 'text-yellow-400', bg: 'bg-yellow-900/20' },
            ].map(s => (
              <div key={s.label} className={`${s.bg} border border-fmc-border rounded-lg p-4 text-center`}>
                <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                <div className="text-fmc-text-muted text-xs mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Filter buttons */}
        <div className="flex gap-2">
          {['all', 'done', 'error', 'pending'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded border transition-colors ${
                filter === f
                  ? 'bg-fmc-accent text-white border-fmc-accent'
                  : 'border-fmc-border text-fmc-text-muted hover:text-fmc-text hover:bg-fmc-surface'
              }`}
            >
              {f === 'all' ? 'Tous' : f === 'done' ? '✅ Réussies' : f === 'error' ? '❌ Erreurs' : '⏳ En cours'}
            </button>
          ))}
          <span className="ml-auto text-fmc-text-muted text-xs self-center">
            {filtered.length} résultat{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Loading / Error */}
        {loading && (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 rounded-full border-2 border-purple-500 border-t-transparent animate-spin" />
          </div>
        )}
        {error && (
          <div className="bg-red-900/30 border border-red-500/40 text-red-300 rounded p-4 text-sm">
            ❌ {error}
          </div>
        )}

        {/* Table */}
        {!loading && !error && (
          <div className="overflow-x-auto rounded-lg border border-fmc-border">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-fmc-surface border-b border-fmc-border">
                  <th className="text-left px-3 py-2 text-fmc-text-muted">ID</th>
                  <th className="text-left px-3 py-2 text-fmc-text-muted">Annonce</th>
                  <th className="text-left px-3 py-2 text-fmc-text-muted">User</th>
                  <th className="text-left px-3 py-2 text-fmc-text-muted">Modèle</th>
                  <th className="text-left px-3 py-2 text-fmc-text-muted">Statut</th>
                  <th className="text-left px-3 py-2 text-fmc-text-muted">Risque</th>
                  <th className="text-left px-3 py-2 text-fmc-text-muted">Résumé</th>
                  <th className="text-left px-3 py-2 text-fmc-text-muted">Date</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-fmc-text-muted">
                      Aucune analyse trouvée
                    </td>
                  </tr>
                )}
                {filtered.map((a, i) => (
                  <tr
                    key={a.id}
                    className={`border-b border-fmc-border/50 hover:bg-fmc-surface/50 transition-colors ${
                      i % 2 === 0 ? '' : 'bg-fmc-surface/20'
                    }`}
                  >
                    <td className="px-3 py-2 text-fmc-text-dim">{a.id}</td>
                    <td className="px-3 py-2">
                      <a
                        href={`/?listing=${a.listing_id}`}
                        className="text-fmc-accent hover:underline"
                        title={`Listing #${a.listing_id}`}
                      >
                        #{a.listing_id}
                      </a>
                    </td>
                    <td className="px-3 py-2 text-fmc-text-dim">user {a.user_id ?? 1}</td>
                    <td className="px-3 py-2 text-fmc-text-dim truncate max-w-[100px]" title={a.model}>
                      {a.model}
                    </td>
                    <td className="px-3 py-2">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${STATUS_COLORS[a.status] || 'bg-zinc-800 text-zinc-400'}`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      {a.risk_level ? (
                        <span className={`font-medium ${RISK_COLORS[a.risk_level] || 'text-fmc-text'}`}>
                          {RISK_ICONS[a.risk_level]} {a.risk_level}
                        </span>
                      ) : (
                        <span className="text-fmc-text-dim">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-fmc-text-dim max-w-[280px] truncate" title={a.condition_summary || ''}>
                      {a.condition_summary || '—'}
                    </td>
                    <td className="px-3 py-2 text-fmc-text-dim whitespace-nowrap">
                      {a.created_at
                        ? new Date(a.created_at).toLocaleString('fr-FR', {
                            day: '2-digit', month: '2-digit', year: '2-digit',
                            hour: '2-digit', minute: '2-digit',
                          })
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
