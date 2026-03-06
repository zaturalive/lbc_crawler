import { useEffect } from 'react';
import { X, ExternalLink } from 'lucide-react';
import Badge from './ui/Badge';
import Button from './ui/Button';

function parseIssue(issue) {
  const clean = issue.replace(/[\t\r\n]+/g, ' ').replace(/\s{2,}/g, ' ').trim();
  const colonIdx = clean.indexOf(':');
  if (colonIdx === -1) return { title: clean, description: '' };
  return {
    title: clean.slice(0, colonIdx).trim(),
    description: clean.slice(colonIdx + 1).trim(),
  };
}

const scoreVariant = (score) => {
  if (score === null || score === undefined) return 'default';
  if (score >= 7) return 'success';
  if (score >= 4) return 'warning';
  return 'danger';
};

export default function ReliabilityModal({ listing, onClose }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!listing) return null;

  const { title, price, year, mileage, location, url, matched_keywords, vehicle, gearbox, horsepower, fuel_type } = listing;
  const issues = vehicle?.common_issues || [];

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-fmc-surface border border-fmc-border rounded-lg max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-neon animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-fmc-panel border-b border-fmc-accent-deep/60 px-6 py-4 sticky top-0 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-mono font-bold text-fmc-text pr-8">{title || 'Annonce'}</h2>
            {price && (
              <p className="text-2xl font-bold text-fmc-accent font-mono mt-1">
                {new Intl.NumberFormat('fr-FR').format(price)}&nbsp;€
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-fmc-text-dim hover:text-fmc-accent transition-colors rounded-full p-1.5 hover:bg-fmc-accent/10"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">

          {/* Caractéristiques */}
          <section>
            <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
              <span className="text-fmc-accent">◈</span> Caractéristiques
            </h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {year && (
                <div>
                  <span className="text-fmc-text-dim text-xs font-mono">Année</span>
                  <p className="font-mono font-semibold text-fmc-text">{year}</p>
                </div>
              )}
              {mileage && (
                <div>
                  <span className="text-fmc-text-dim text-xs font-mono">Kilométrage</span>
                  <p className="font-mono font-semibold text-fmc-text">{new Intl.NumberFormat('fr-FR').format(mileage)} km</p>
                </div>
              )}
              {location && (
                <div>
                  <span className="text-fmc-text-dim text-xs font-mono">Ville</span>
                  <p className="font-mono font-semibold text-fmc-text">{location}</p>
                </div>
              )}
              {gearbox && (
                <div>
                  <span className="text-fmc-text-dim text-xs font-mono">Boîte</span>
                  <p className="font-mono font-semibold text-fmc-text capitalize">
                    {gearbox === 'manual' ? 'Manuelle' : 'Automatique'}
                  </p>
                </div>
              )}
              {fuel_type && (
                <div>
                  <span className="text-fmc-text-dim text-xs font-mono">Carburant</span>
                  <p className="font-mono font-semibold text-fmc-text capitalize">{fuel_type}</p>
                </div>
              )}
              {horsepower && (
                <div>
                  <span className="text-fmc-text-dim text-xs font-mono">Puissance</span>
                  <p className="font-mono font-semibold text-fmc-text">{horsepower} ch</p>
                </div>
              )}
            </div>
          </section>

          {/* Score fiabilité */}
          <section className="border-t border-fmc-accent-deep/30 pt-4">
            <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
              <span className="text-fmc-accent">◈</span> Fiabilité
            </h3>
            {vehicle ? (
              <div className="flex items-center gap-3">
                <Badge variant={scoreVariant(vehicle.reliability_score)} className="text-base px-4 py-1.5 font-mono">
                  {vehicle.reliability_score !== null && vehicle.reliability_score !== undefined
                    ? `${vehicle.reliability_score}/10`
                    : 'N/A'
                  }
                </Badge>
                <span className="text-fmc-text-muted text-xs font-mono">
                  {vehicle.model && `Modèle : ${vehicle.model}`}
                  {vehicle.year_start && vehicle.year_end && ` (${vehicle.year_start}–${vehicle.year_end})`}
                </span>
              </div>
            ) : (
              <p className="text-fmc-text-dim text-xs font-mono">Données non disponibles pour ce modèle.</p>
            )}
          </section>

          {/* Problèmes connus */}
          {issues.length > 0 && (
            <section className="border-t border-fmc-accent-deep/30 pt-4">
              <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                <span className="text-fmc-accent">◈</span> Problèmes connus ({issues.length})
              </h3>
              <ul className="space-y-2">
                {issues.map((issue, i) => {
                  const parsed = parseIssue(issue);
                  return (
                    <li key={i} className="flex gap-2">
                      <span className="text-fmc-accent font-mono text-xs mt-0.5">▸</span>
                      <div>
                        <p className="text-xs text-fmc-text-muted font-mono font-semibold capitalize">{parsed.title}</p>
                        {parsed.description && (
                          <p className="text-xs text-fmc-text-dim font-mono mt-0.5">{parsed.description}</p>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>
          )}

          {/* Mots-clés détectés */}
          {matched_keywords && matched_keywords.length > 0 && (
            <section className="border-t border-fmc-accent-deep/30 pt-4">
              <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                <span className="text-fmc-accent">◈</span> Mots-clés détectés
              </h3>
              <div className="flex flex-wrap gap-2">
                {matched_keywords.map(kw => (
                  <Badge key={kw} variant="success">{kw}</Badge>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="bg-fmc-panel border-t border-fmc-accent-deep/60 px-6 py-4 sticky bottom-0">
          <Button variant="primary" fullWidth asChild>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 font-mono"
            >
              Voir l'annonce LeBonCoin
              <ExternalLink className="h-4 w-4" />
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
}
