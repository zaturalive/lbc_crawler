import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ListingCard from './ListingCard';
import ListingsFilterBar from './ListingsFilterBar';
import { analyzeListingAI, getCachedAnalyses, getAiQuota } from '../api/client';

export default function ResultsGrid({ results, loading, onOpenModal, likedIds = [], onToggleLike, aiMode = false, onAiAnalyze, searchHistoryId = null, token = null, onClearSearch = null, viewedIds = new Set() }) {
  const navigate = useNavigate();
  const [filteredListings, setFilteredListings] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [aiQuota, setAiQuota] = useState(null);
  const [cols, setCols] = useState(3);
  const [batchProgress, setBatchProgress] = useState(null);
  const [cardAnalyses, setCardAnalyses] = useState({});
  const [currentlyAnalyzing, setCurrentlyAnalyzing] = useState(null);

  // Charge le quota IA au montage (silencieux si indisponible)
  useEffect(() => {
    getAiQuota(token).then(setAiQuota).catch(() => {});
  }, [token]);

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

  // Charge automatiquement les analyses déjà payées par l'user au montage
  useEffect(() => {
    if (!token || !results?.listings?.length) return;
    const ids = results.listings.map(l => l.id);
    getCachedAnalyses(ids, token)
      .then(cached => {
        if (cached && typeof cached === 'object' && Object.keys(cached).length > 0) {
          const parsed = {};
          for (const [k, v] of Object.entries(cached)) parsed[parseInt(k)] = v;
          setCardAnalyses(prev => ({ ...prev, ...parsed }));
        }
      })
      .catch(() => {});
  }, [results, token]);

  async function handleAiAnalyze(e) {
    if (aiLoading) return;
    const coords = e ? { x: e.clientX, y: e.clientY } : null;
    setAiLoading(true);
    onAiAnalyze && onAiAnalyze(true, coords);

    const toAnalyze = filteredListings.slice(0, 50);

    // Pré-charger les analyses déjà en cache
    let alreadyCached = {};
    try {
      const ids = toAnalyze.map(l => l.id);
      const cached = await getCachedAnalyses(ids, token);
      if (cached && typeof cached === 'object') {
        for (const [k, v] of Object.entries(cached)) alreadyCached[parseInt(k)] = v;
        setCardAnalyses(prev => ({ ...prev, ...alreadyCached }));
      }
    } catch (_) { /* silencieux */ }

    // Séparer les cards à analyser (non cachées) des cards déjà prêtes
    const needsAnalysis = toAnalyze.filter(l => !alreadyCached[l.id]);
    const cachedCount   = toAnalyze.length - needsAnalysis.length;

    setBatchProgress({ done: cachedCount, total: toAnalyze.length, cached: cachedCount, newCount: 0 });

    let done = cachedCount;
    let newCount = 0;
    for (const listing of needsAnalysis) {
      setCurrentlyAnalyzing(listing.id);
      try {
        const result = await analyzeListingAI(listing.id, token);
        setCardAnalyses(prev => ({ ...prev, [listing.id]: result }));
        if (!result?.cached) newCount++;
      } catch (err) {
        if (err?.status === 402) {
          navigate('/credits');
          break;
        }
        if (err?.status === 429) {
          setAiError(err?.message || 'Quota IA dépassé (10/10)');
          break;
        }
        // autres erreurs: skip silencieusement
      }
      done++;
      setBatchProgress({ done, total: toAnalyze.length, cached: cachedCount, newCount });
    }

    setCurrentlyAnalyzing(null);
    setAiLoading(false);
    setBatchProgress(null);
    // Rafraîchir le quota après le batch
    getAiQuota(token).then(setAiQuota).catch(() => {});
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

        {/* Bouton fermer recherche */}
        {onClearSearch && (
          <button
            onClick={onClearSearch}
            className="flex items-center gap-1 px-2 py-1 rounded font-mono text-xs text-fmc-text-dim border border-fmc-accent-deep/30 hover:text-red-400 hover:border-red-500/50 transition-colors"
            title="Fermer la recherche et revenir à l'accueil"
          >
            ✕ Fermer
          </button>
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
          const quotaReached = aiQuota && aiQuota.listing_analyses_used >= aiQuota.listing_analyses_max;
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
                    ? `⏳ ${batchProgress.done}/${batchProgress.total} · ${batchProgress.newCount ?? 0} nouvelles · ⚡${batchProgress.cached ?? 0} cache`
                    : '⏳ Préparation...'
                ) : `✨ Analyse IA des cards`}
              </button>
              {aiQuota && (
                <span className="text-fmc-text-dim text-xs font-mono">
                  ({aiQuota.listing_analyses_used}/{aiQuota.listing_analyses_max} analyses utilisées)
                </span>
              )}
            </div>
          );
        })()}
      </div>

      {/* Barre de filtres client-side */}
      <ListingsFilterBar
        listings={listings}
        onFiltered={setFilteredListings}
        analyzedIds={new Set(Object.keys(cardAnalyses).map(Number))}
      />

      {/* Grid */}
      <div className={`grid grid-cols-1 gap-4 p-1 ${cols === 2 ? 'sm:grid-cols-2' : 'sm:grid-cols-2 lg:grid-cols-3'}`}>
        {filteredListings.map(l => (
          <ListingCard
            key={l.lbc_id || l.id}
            listing={l}
            onOpenModal={(listing) => onOpenModal(listing, cardAnalyses[listing.id] || null)}
            isLiked={likedIds.includes(l.id)}
            onToggleLike={onToggleLike}
            aiMode={aiMode}
            aiAnalysis={cardAnalyses[l.id] || null}
            isAnalyzing={currentlyAnalyzing === l.id}
            isViewed={viewedIds.has(l.id)}
            hasAiAnalysis={!!cardAnalyses[l.id]?.reponse}
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
