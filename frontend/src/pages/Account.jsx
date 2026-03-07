import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, ExternalLink, Car } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getSavedSearches, getLikedListings, removeLike } from '../api/client';
import Header from '../components/Header';

export default function Account() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('searches');
  const [searches, setSearches] = useState([]);
  const [likes, setLikes] = useState([]);
  const [loadingSearches, setLoadingSearches] = useState(false);
  const [loadingLikes, setLoadingLikes] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    fetchSearches();
    fetchLikes();
  }, [token]);

  async function fetchSearches() {
    setLoadingSearches(true);
    try {
      const data = await getSavedSearches(token);
      setSearches(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSearches(false);
    }
  }

  async function fetchLikes() {
    setLoadingLikes(true);
    try {
      const data = await getLikedListings();
      setLikes(Array.isArray(data) ? data : []);
    } catch (err) {
      // fail silently for likes
    } finally {
      setLoadingLikes(false);
    }
  }

  async function handleUnlike(listingId) {
    // Optimistic remove
    setLikes(prev => prev.filter(l => l.id !== listingId));
    try {
      await removeLike(listingId);
    } catch {
      // revert on error
      fetchLikes();
    }
  }

  function loadSearch(filters) {
    navigate('/', { state: { loadSearch: filters } });
  }

  return (
    <div className="flex flex-col h-full bg-fmc-bg">
      <Header />
      <main className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-3xl mx-auto">
          {/* Page header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-mono font-bold text-fmc-text">
              <span className="text-fmc-accent">◈</span> Mon compte
            </h2>
            <div className="flex items-center gap-4">
              <span className="text-xs font-mono text-fmc-text-dim">{user?.email}</span>
              <button
                onClick={() => { logout(); navigate('/'); }}
                className="fmc-btn-ghost text-xs px-3 py-1.5"
              >
                Déconnexion
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-6 border-b border-fmc-accent-deep/30">
            {[
              { id: 'searches', label: 'Mes Recherches' },
              { id: 'likes',    label: 'Mes Favoris' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 text-xs font-mono border-b-2 transition-colors -mb-px ${
                  activeTab === tab.id
                    ? 'border-fmc-accent text-fmc-accent'
                    : 'border-transparent text-fmc-text-dim hover:text-fmc-text'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'searches' && (
            <div>
              {loadingSearches ? (
                <p className="text-xs font-mono text-fmc-text-dim">Chargement…</p>
              ) : searches.length === 0 ? (
                <p className="text-xs font-mono text-fmc-text-dim">Aucune recherche sauvegardée.</p>
              ) : (
                <ul className="space-y-3">
                  {searches.map((s, i) => (
                    <li key={s.id || i} className="fmc-card p-4 flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-mono text-fmc-text-dim mb-1">
                          {s.created_at ? new Date(s.created_at).toLocaleDateString('fr-FR') : '—'}
                          {s.results_count != null && ` · ${s.results_count} résultats`}
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {s.filters && Object.entries(s.filters)
                            .filter(([, v]) => v !== null && v !== '' && v !== undefined)
                            .map(([k, v]) => (
                              <span key={k} className="px-2 py-0.5 bg-fmc-accent/10 border border-fmc-accent-deep/40 rounded text-xs font-mono text-fmc-accent">
                                {k}: {String(v)}
                              </span>
                            ))
                          }
                        </div>
                      </div>
                      <button
                        onClick={() => loadSearch(s.filters)}
                        className="fmc-btn-ghost text-xs px-3 py-1.5 whitespace-nowrap flex-shrink-0"
                      >
                        Charger
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {activeTab === 'likes' && (
            <div>
              {loadingLikes ? (
                <p className="text-xs font-mono text-fmc-text-dim">Chargement…</p>
              ) : likes.length === 0 ? (
                <p className="text-xs font-mono text-fmc-text-dim">Aucun favori enregistré.</p>
              ) : (
                <ul className="space-y-3">
                  {likes.map((item, i) => (
                    <li key={item.id || i} className="fmc-card p-4">
                      <div className="flex items-start gap-3">
                        {/* Main content — clickable → ouvre LBC */}
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-1 min-w-0 group block"
                        >
                          <h3 className="text-sm font-mono font-semibold text-fmc-text group-hover:text-fmc-accent transition-colors line-clamp-2">
                            {item.title || 'Annonce sans titre'}
                          </h3>
                          <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1 text-xs font-mono text-fmc-text-dim">
                            {item.price   && <span className="text-fmc-accent font-bold">{new Intl.NumberFormat('fr-FR').format(item.price)} €</span>}
                            {item.year    && <span>{item.year}</span>}
                            {item.mileage && <span>{new Intl.NumberFormat('fr-FR').format(item.mileage)} km</span>}
                            {item.horsepower && <span>{item.horsepower} ch</span>}
                            {item.gearbox && <span>{item.gearbox === 'automatic' ? 'Auto' : 'Manuelle'}</span>}
                            {item.fuel_type && <span>{item.fuel_type}</span>}
                            {item.location && <span>📍 {item.location}</span>}
                          </div>
                          {item.vehicle && (
                            <div className="flex items-center gap-1.5 mt-1.5">
                              <Car className="h-3 w-3 text-fmc-text-dim" />
                              <span className="text-xs font-mono text-fmc-text-dim">
                                {item.vehicle.brand} {item.vehicle.model}
                                {item.vehicle.reliability_score != null && (
                                  <span className="ml-2 text-green-400">⚡ {item.vehicle.reliability_score}/100</span>
                                )}
                              </span>
                            </div>
                          )}
                        </a>

                        {/* Actions */}
                        <div className="flex flex-col items-end gap-2 flex-shrink-0">
                          {/* Unlike button */}
                          <button
                            onClick={() => handleUnlike(item.id)}
                            title="Retirer des favoris"
                            className="p-1.5 rounded-md border border-red-500/70 text-red-400 bg-red-900/20 hover:bg-red-900/40 transition-colors"
                          >
                            <Heart className="h-3.5 w-3.5 fill-current" />
                          </button>
                          {/* Lien LBC */}
                          {item.url && (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1.5 rounded-md border border-fmc-accent-deep/50 text-fmc-text-dim hover:text-fmc-accent hover:border-fmc-accent/50 transition-colors"
                              title="Voir l'annonce LBC"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
