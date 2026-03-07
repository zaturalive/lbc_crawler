import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import {
  getSearchHistory,
  getViewedListings,
  clearSearchHistory,
  clearViewedHistory,
} from '../api/client';

export default function History() {
  const [tab, setTab] = useState('searches');
  const [searches, setSearches] = useState([]);
  const [viewed, setViewed] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getSearchHistory(), getViewedListings()])
      .then(([s, v]) => {
        setSearches(s || []);
        setViewed(v || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleClearSearches() {
    await clearSearchHistory();
    setSearches([]);
  }

  async function handleClearViewed() {
    await clearViewedHistory();
    setViewed([]);
  }

  return (
    <div className="flex flex-col h-full bg-fmc-bg">
      <Header />

      <div className="min-h-screen bg-fmc-bg text-fmc-text font-mono px-4 py-8 max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-lg font-bold text-fmc-accent tracking-wider">
            Historique
          </h1>
          <Link to="/" className="text-xs text-fmc-text-dim hover:text-fmc-text font-mono transition-colors">
            Retour
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-fmc-border">
          <button
            onClick={() => setTab('searches')}
            className={`px-4 py-2 text-xs font-mono transition-colors ${
              tab === 'searches'
                ? 'text-fmc-accent border-b-2 border-fmc-accent'
                : 'text-fmc-text-dim hover:text-fmc-text'
            }`}
          >
            Recherches ({searches.length})
          </button>
          <button
            onClick={() => setTab('viewed')}
            className={`px-4 py-2 text-xs font-mono transition-colors ${
              tab === 'viewed'
                ? 'text-fmc-accent border-b-2 border-fmc-accent'
                : 'text-fmc-text-dim hover:text-fmc-text'
            }`}
          >
            Consultees ({viewed.length})
          </button>
        </div>

        {loading && (
          <div className="text-center text-fmc-text-dim text-xs py-12">
            Chargement…
          </div>
        )}

        {/* Onglet recherches */}
        {!loading && tab === 'searches' && (
          <div className="space-y-3">
            {searches.length === 0 ? (
              <p className="text-fmc-text-dim text-xs text-center py-12">
                Aucune recherche enregistree.
              </p>
            ) : (
              <>
                <div className="flex justify-end">
                  <button
                    onClick={handleClearSearches}
                    className="text-xs text-red-400 hover:text-red-300 font-mono"
                  >
                    Tout effacer
                  </button>
                </div>
                {searches.map((s) => (
                  <SearchHistoryCard key={s.id} item={s} />
                ))}
              </>
            )}
          </div>
        )}

        {/* Onglet annonces consultees */}
        {!loading && tab === 'viewed' && (
          <div className="space-y-3">
            {viewed.length === 0 ? (
              <p className="text-fmc-text-dim text-xs text-center py-12">
                Aucune annonce consultee.
              </p>
            ) : (
              <>
                <div className="flex justify-end">
                  <button
                    onClick={handleClearViewed}
                    className="text-xs text-red-400 hover:text-red-300 font-mono"
                  >
                    Tout effacer
                  </button>
                </div>
                {viewed.map((v) =>
                  v.listing && <ViewedListingCard key={v.id} item={v} />
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Carte d'une recherche passee
function SearchHistoryCard({ item }) {
  const navigate = useNavigate();
  const p = item.params || {};

  const numFields = ['price_min', 'price_max', 'km_min', 'km_max', 'mileage_min', 'mileage_max', 'year_min', 'year_max', 'radius', 'limit'];
  // Normalise les valeurs : convertir les champs numeriques
  const normalizedParams = Object.fromEntries(
    Object.entries(p)
      .filter(([, v]) => v != null)
      .map(([k, v]) => [k, numFields.includes(k) ? Number(v) : v])
  );

  const labels = [
    p.brand && `${p.brand}${p.model ? ` ${p.model}` : ''}`,
    p.city && `${p.city}${p.radius ? ` +${p.radius}km` : ''}`,
    p.price_max && `<= ${Number(p.price_max).toLocaleString()}EUR`,
    (p.km_max || p.mileage_max) && `<= ${Number(p.km_max || p.mileage_max).toLocaleString()} km`,
    p.year_min && `>= ${p.year_min}`,
  ].filter(Boolean);

  const date = item.created_at
    ? new Date(item.created_at).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  function handleRelaunch() {
    navigate('/', { state: { loadSearch: normalizedParams, autoSubmit: true } });
  }

  return (
    <div className="fmc-card p-3 flex items-center justify-between gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap gap-1.5 mb-1">
          {labels.length > 0 ? (
            labels.map((l, i) => (
              <span
                key={i}
                className="px-1.5 py-0.5 bg-fmc-surface border border-fmc-border rounded text-xs text-fmc-text"
              >
                {l}
              </span>
            ))
          ) : (
            <span className="text-xs text-fmc-text-dim italic">
              Recherche sans filtre
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-fmc-text-dim">
          <span>
            {item.result_count} annonce{item.result_count !== 1 ? 's' : ''}
          </span>
          <span>·</span>
          <span>{date}</span>
        </div>
      </div>
      <button
        onClick={handleRelaunch}
        className="shrink-0 text-xs text-fmc-accent hover:underline font-mono"
      >
        Relancer
      </button>
    </div>
  );
}

// Carte d'une annonce consultee
function ViewedListingCard({ item }) {
  const l = item.listing;
  const date = item.viewed_at
    ? new Date(item.viewed_at).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  return (
    <div className="fmc-card p-3 flex items-center gap-3">
      {l.image_url && (
        <img
          src={l.image_url}
          alt={l.title}
          className="w-16 h-12 object-cover rounded shrink-0"
        />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-fmc-text truncate">{l.title}</p>
        <div className="flex items-center gap-2 text-xs text-fmc-text-dim mt-0.5">
          {l.price && (
            <span className="text-fmc-accent font-bold">
              {l.price.toLocaleString()}EUR
            </span>
          )}
          {l.mileage && <span>{l.mileage.toLocaleString()} km</span>}
          {l.year && <span>{l.year}</span>}
          <span>· vu {date}</span>
        </div>
      </div>
      {l.url && (
        <a
          href={l.url}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 text-xs text-fmc-accent hover:underline font-mono"
        >
          Voir
        </a>
      )}
    </div>
  );
}
