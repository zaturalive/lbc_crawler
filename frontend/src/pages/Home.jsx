import { useState, useEffect } from 'react';
import ResultsGrid from '../components/ResultsGrid';
import SearchForm from '../components/SearchForm';
import Header from '../components/Header';
import ReliabilityModal from '../components/ReliabilityModal';

export default function Home() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedListing, setSelectedListing] = useState(null);
  const [likedIds, setLikedIds] = useState([]);

  // Charge les likes au démarrage (fail silently si l'API ne répond pas)
  useEffect(() => {
    import('../api/client').then(({ getLikes }) => {
      getLikes()
        .then(data => {
          if (Array.isArray(data)) setLikedIds(data);
        })
        .catch(() => {});
    });
  }, []);

  async function handleToggleLike(listingId) {
    const { addLike, removeLike } = await import('../api/client');
    const isCurrentlyLiked = likedIds.includes(listingId);
    // Optimistic update
    setLikedIds(prev =>
      isCurrentlyLiked
        ? prev.filter(id => id !== listingId)
        : [...prev, listingId]
    );
    // API call with revert on error
    const apiCall = isCurrentlyLiked ? removeLike : addLike;
    apiCall(listingId).catch(() => {
      setLikedIds(prev =>
        isCurrentlyLiked
          ? [...prev, listingId]
          : prev.filter(id => id !== listingId)
      );
    });
  }

  return (
    <div className="flex flex-col h-full bg-fmc-bg">
      <Header />

      {/* LAYOUT: centered form when no results, split scroll when results */}
      {results === null ? (
        <main className="flex-1 flex items-start justify-center overflow-y-auto px-6 py-10">
          <div className="w-full max-w-2xl animate-fade-in">
            {/* Hero */}
            <div className="text-center mb-8">
              <h1 className="text-4xl font-mono font-bold text-neon mb-2 tracking-tight">
                <span className="text-fmc-accent">▸</span> find_my_car
              </h1>
              <p className="text-fmc-text-muted text-sm font-mono">
                Scannez LeBonCoin — filtrez par fiabilité, mots-clés, zone géographique
              </p>
            </div>

            {/* Form panel */}
            <div className="fmc-panel p-6 border-fmc-accent-deep animate-slide-in">
              <h2 className="fmc-title text-base mb-5 flex items-center gap-2">
                <span className="text-fmc-accent text-xs">◈</span>
                CRITÈRES DE RECHERCHE
              </h2>
              <SearchForm onResults={setResults} onLoading={setLoading} />
            </div>
          </div>
        </main>
      ) : (
        /* SPLIT LAYOUT — independent scrolling */
        <div className="flex flex-1 overflow-hidden gap-0">
          {/* LEFT SIDEBAR — form with its own scroll */}
          <aside className="w-80 flex-shrink-0 overflow-y-auto bg-fmc-panel border-r border-fmc-accent-deep/40 px-4 py-5">
            <h2 className="fmc-title text-sm mb-4 flex items-center gap-2">
              <span className="text-fmc-accent">◈</span>
              FILTRES
            </h2>
            <SearchForm onResults={setResults} onLoading={setLoading} />
            <button
              onClick={() => setResults(null)}
              className="mt-4 w-full text-xs text-fmc-text-dim hover:text-fmc-text-muted font-mono underline underline-offset-2 transition-colors"
            >
              ← Nouvelle recherche
            </button>
          </aside>

          {/* RIGHT RESULTS — its own scroll */}
          <main className="flex-1 overflow-y-auto px-6 py-5">
            <ResultsGrid
              results={results}
              loading={loading}
              onOpenModal={setSelectedListing}
              likedIds={likedIds}
              onToggleLike={handleToggleLike}
            />
          </main>
        </div>
      )}

      {selectedListing && (
        <ReliabilityModal
          listing={selectedListing}
          onClose={() => setSelectedListing(null)}
        />
      )}
    </div>
  );
}
