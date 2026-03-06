import ListingCard from './ListingCard';
import './ResultsGrid.css';

export default function ResultsGrid({ results, loading }) {
  if (loading) {
    return (
      <div className="results-grid__loading">
        <div className="results-grid__spinner" />
        <p>Recherche en cours sur LeBonCoin...</p>
      </div>
    );
  }
  if (!results) return null;

  const { count, listings } = results;

  if (count === 0 || !listings?.length) {
    return (
      <div className="results-grid__empty">
        <p>Aucune annonce trouvée — essayez d'élargir vos critères.</p>
      </div>
    );
  }

  return (
    <div className="results-grid">
      <p className="results-grid__count">{count} annonce{count > 1 ? 's' : ''} trouvée{count > 1 ? 's' : ''}</p>
      <div className="results-grid__grid">
        {listings.map(l => <ListingCard key={l.lbc_id || l.id} listing={l} />)}
      </div>
    </div>
  );
}
