import { useState, useEffect } from 'react';
import ListingCard from './ListingCard';
import ListingsFilterBar from './ListingsFilterBar';

export default function ResultsGrid({ results, loading, onOpenModal, likedIds = [], onToggleLike }) {
  const [filteredListings, setFilteredListings] = useState([]);

  // Réinitialise les listings filtrés à chaque nouvelle recherche
  useEffect(() => {
    setFilteredListings(results?.listings || []);
  }, [results]);

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
      </div>

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
