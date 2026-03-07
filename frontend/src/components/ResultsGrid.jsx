import { useState, useEffect } from 'react';
import ListingCard from './ListingCard';
import ListingsFilterBar from './ListingsFilterBar';
import { analyzeListingAI, getAiQuota } from '../api/client';

export default function ResultsGrid({ results, loading, onOpenModal, likedIds = [], onToggleLike, aiMode = false, onAiAnalyze, searchHistoryId = null }) {
  const [filteredListings, setFilteredListings] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [aiQuota, setAiQuota] = useState(null);
  const [cols, setCols] = useState(3);
  const [batchProgress, setBatchProgress] = useState(null);
  const [cardAnalyses, setCardAnalyses] = useState({});

  // Charge le quota IA au montage (silencieux si indisponible)
  useEffect(() => {
    getAiQuota().then(setAiQuota).catch(() => {});
  }, []);

  // Auto-dismiss du toast d'erreur après 5s
  useEffect(() => {
    if (!aiError) return;
    const t = setTimeout(() => setAiError(null), 5000);
    return () => clearTimeout(t);
  }, [aiError]);

  // Réinitialise les listings filtrés à chaque nouvelle recherche
  useEffect(() => {
    setFilteredListings(results?.listings || []);
    setCardAnalyses({});
  }, [results]);

  async function handleAiAnalyze(e) {
    if (aiLoading) return;
    const coords = e ? { x: e.clientX, y: e.clientY } : null;
    setAiLoading(true);
    onAiAnalyze && onAiAnalyze(true, coords);

    const toAnalyze = filteredListings.slice(0, 50);
    setBatchProgress({ done: 0, total: toAnalyze.length });

    let done = 0;
    for (const listing of toAnalyze) {
      try {
        const result = await analyzeListingAI(listing.id);
        setCardAnalyses(prev => ({ ...prev, [listing.id]: result }));
      } catch (err) {
        if (err?.status === 429) {
          setAiError(err?.message || 'Quota IA dépassé');
          break;
        }
        // autres erreurs: skip this card silently
      }
      done++;
      setBatchProgress({ done, total: toAnalyze.length });
    }

    setAiLoading(false);
    setBatchProgress(null);
    setTimeout(() => onAiAnalyze && onAiAnalyze(false, null), 2000);
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <div className="w-8 h-8 rounded-full border-2 border-fmc-accent-deep border-t-fmc-accent animate-spin"
          style={{ boxShadow: '0 0 8px #DC586D50' }}
        />
        <p className="text-fmc-text-muted font-mono text-sm">
          Recherche en cours sur LeBonCoin…
        </p>
      </div>
    );
  }

  if (!results) return null;

  const { count, listings } = results;

  if (count === 0 || !listings?.length) {
    return (
      <div className="fmc-panel p-8 text-center">
        <p className="text-fmc-text-muted font-mono text-sm">
          Aucune annonce trouvée avec vos critères.<br />
          Essayez d'élargir votre recherche.
        </p>
      </div>
    );
  }

  const listingsWithScore = listings.filter(
    l => l.vehicle?.reliability_score !== null && l.vehicle?.reliability_score !== undefined
  ).length;

  return (
    <div className="space-y-4">
      {/* Stats bar */}
      <div className={`px-4 py-2 flex items-center gap-3 rounded-lg ${aiMode ? 'ai-mode-statsbar' : 'bg-fmc-surface border-b border-fmc-accent-deep/40'}`}>
        <span className="text-fmc-accent font-mono text-sm font-bold">
          {count} annonce{count > 1 ? 's' : ''} trouvée{count > 1 ? 's' : ''}
        </span>
        {listingsWithScore > 0 && (
          <span className="text-fmc-text-dim text-xs font-mono">
            — {listingsWithScore} avec score fiabilité
          </span>
        )}
        {/* Toggle colonnes */}
        <div className="flex items-center gap-1 ml-auto border border-fmc-accent-deep/40 rounded overflow-hidden">
          {[2, 3].map(n => (
            <button
              key={n}
              onClick={() => setCols(n)}
              title={`${n} colonnes`}
              className={`px-2 py-1 font-mono text-xs transition-colors duration-150 ${
                cols === n
                  ? 'bg-fmc-accent-deep text-white'
                  : 'text-fmc-text-dim hover:text-fmc-text hover:bg-fmc-surface'
              }`}
            >
              {'▪'.repeat(n)}
            </button>
          ))}
        </div>

        {(() => {
          const quotaReached = aiQuota && aiQuota.search_analyses_used >= aiQuota.search_analyses_max;
          return (
            <div className="flex flex-col items-end gap-0.5">
              <button
                onClick={(e) => handleAiAnalyze(e)}
                disabled={aiLoading || quotaReached}
                className={`flex items-center gap-2 px-3 py-1 rounded font-mono text-xs transition-all duration-300 ${
                  quotaReached
                    ? 'bg-zinc-800/60 text-zinc-500 border border-zinc-600/40 cursor-not-allowed'
                    : aiLoading
                      ? 'bg-purple-900/50 text-purple-300 border border-purple-500/50 animate-pulse cursor-wait'
                      : 'bg-gradient-to-r from-purple-900/40 to-cyan-900/40 text-purple-300 border border-purple-500/40 hover:border-purple-400/70 hover:text-purple-200'
                }`}
              >
                {quotaReached ? '✨ Quota atteint' : aiLoading ? (
                  batchProgress
                    ? `⏳ Analyse ${batchProgress.done}/${batchProgress.total}...`
                    : '⏳ Préparation...'
                ) : '✨ Analyse IA des cards'}
              </button>
              {aiQuota && (
                <span className="text-fmc-text-dim text-xs font-mono">
                  ({aiQuota.search_analyses_used}/{aiQuota.search_analyses_max} utilisées)
                </span>
              )}
            </div>
          );
        })()}
      </div>

      {/* Barre de filtres client-side */}
      <ListingsFilterBar listings={listings} onFiltered={setFilteredListings} />

      {/* Grid */}
      <div className={`grid grid-cols-1 gap-4 p-1 ${cols === 2 ? 'sm:grid-cols-2' : 'sm:grid-cols-2 lg:grid-cols-3'}`}>
        {filteredListings.map(l => (
          <ListingCard
            key={l.lbc_id || l.id}
            listing={l}
            onOpenModal={onOpenModal}
            isLiked={likedIds.includes(l.id)}
            onToggleLike={onToggleLike}
            aiMode={aiMode}
            aiAnalysis={cardAnalyses[l.id] || null}
          />
        ))}
      </div>

      {/* Toast erreur quota IA */}
      {aiError && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-red-900/90 border border-red-500/50 text-red-200 font-mono text-sm px-5 py-3 rounded-lg shadow-xl">
          {aiError}
        </div>
      )}
    </div>
  );
}
