import { useState, useEffect } from 'react';
import ListingCard from './ListingCard';
import ListingsFilterBar from './ListingsFilterBar';
import { analyzeSearch } from '../api/client';

export default function ResultsGrid({ results, loading, onOpenModal, likedIds = [], onToggleLike, aiMode = false, onAiAnalyze, searchHistoryId = null }) {
  const [filteredListings, setFilteredListings] = useState([]);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  // Réinitialise les listings filtrés à chaque nouvelle recherche
  useEffect(() => {
    setFilteredListings(results?.listings || []);
    setAiAnalysis(null);
  }, [results]);

  async function handleAiAnalyze() {
    if (!searchHistoryId || aiLoading) return;
    setAiLoading(true);
    onAiAnalyze && onAiAnalyze(true);
    try {
      const data = await analyzeSearch(searchHistoryId);
      setAiAnalysis(data);
    } catch (e) {
      console.error('AI analyze failed:', e);
    } finally {
      setAiLoading(false);
      setTimeout(() => onAiAnalyze && onAiAnalyze(false), 2000);
    }
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
      <div className="bg-fmc-surface border-b border-fmc-accent-deep/40 px-4 py-2 flex items-center gap-3 rounded-lg">
        <span className="text-fmc-accent font-mono text-sm font-bold">
          {count} annonce{count > 1 ? 's' : ''} trouvée{count > 1 ? 's' : ''}
        </span>
        {listingsWithScore > 0 && (
          <span className="text-fmc-text-dim text-xs font-mono">
            — {listingsWithScore} avec score fiabilité
          </span>
        )}
        {searchHistoryId && !aiAnalysis && (
          <button
            onClick={handleAiAnalyze}
            disabled={aiLoading}
            className={`ml-auto flex items-center gap-2 px-3 py-1 rounded font-mono text-xs transition-all duration-300 ${
              aiLoading
                ? 'bg-purple-900/50 text-purple-300 border border-purple-500/50 animate-pulse cursor-wait'
                : 'bg-gradient-to-r from-purple-900/40 to-cyan-900/40 text-purple-300 border border-purple-500/40 hover:border-purple-400/70 hover:text-purple-200'
            }`}
          >
            {aiLoading ? '⏳ Analyse en cours...' : '✨ Analyse IA'}
          </button>
        )}
      </div>

      {/* AI analysis panel */}
      {aiAnalysis?.reponse && (
        <div className="fmc-panel p-4 space-y-3 border border-purple-500/30 bg-purple-950/20 animate-fade-in">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono font-bold text-purple-300">✨ Analyse IA de la recherche</h3>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                aiAnalysis.reponse.risk_level === 'low' ? 'bg-green-900/40 text-green-400 border border-green-500/40' :
                aiAnalysis.reponse.risk_level === 'high' ? 'bg-red-900/40 text-red-400 border border-red-500/40' :
                'bg-yellow-900/40 text-yellow-400 border border-yellow-500/40'
              }`}>
                {aiAnalysis.reponse.risk_level === 'low' ? '✅ Risque faible' :
                 aiAnalysis.reponse.risk_level === 'high' ? '⚠️ Risque élevé' : '⚡ Risque modéré'}
              </span>
              <button onClick={() => setAiAnalysis(null)} className="text-fmc-text-dim hover:text-fmc-text text-xs font-mono">✕</button>
            </div>
          </div>

          <p className="text-sm text-fmc-text font-mono leading-relaxed">{aiAnalysis.reponse.synthese_globale}</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {aiAnalysis.reponse.themes_mentionnes?.length > 0 && (
              <div>
                <p className="text-xs text-green-400 font-mono mb-1">✅ Souvent mentionné</p>
                <ul className="space-y-0.5">
                  {aiAnalysis.reponse.themes_mentionnes.map((t, i) => (
                    <li key={i} className="text-xs text-fmc-text-dim font-mono">• {t}</li>
                  ))}
                </ul>
              </div>
            )}
            {aiAnalysis.reponse.themes_absents?.length > 0 && (
              <div>
                <p className="text-xs text-red-400 font-mono mb-1">❌ Jamais mentionné</p>
                <ul className="space-y-0.5">
                  {aiAnalysis.reponse.themes_absents.map((t, i) => (
                    <li key={i} className="text-xs text-fmc-text-dim font-mono">• {t}</li>
                  ))}
                </ul>
              </div>
            )}
            {aiAnalysis.reponse.prochaines_reparations?.length > 0 && (
              <div>
                <p className="text-xs text-yellow-400 font-mono mb-1">🔧 Réparations probables</p>
                <ul className="space-y-0.5">
                  {aiAnalysis.reponse.prochaines_reparations.map((r, i) => (
                    <li key={i} className="text-xs text-fmc-text-dim font-mono">• {r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Barre de filtres client-side */}
      <ListingsFilterBar listings={listings} onFiltered={setFilteredListings} />

      {/* Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 p-1">
        {filteredListings.map(l => (
          <ListingCard
            key={l.lbc_id || l.id}
            listing={l}
            onOpenModal={onOpenModal}
            isLiked={likedIds.includes(l.id)}
            onToggleLike={onToggleLike}
          />
        ))}
      </div>
    </div>
  );
}
