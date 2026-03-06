import { useEffect, useState } from 'react';
import { X, ExternalLink } from 'lucide-react';
import Badge from './ui/Badge';

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

function formatScrapedAt(raw) {
  if (!raw) return null;
  const d = new Date(raw);
  if (isNaN(d)) return raw;
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

const TABS = [
  { id: 'annonce',    label: 'Annonce' },
  { id: 'fiabilite',  label: 'Fiabilite' },
  { id: 'liens',      label: 'Liens' },
];

export default function ReliabilityModal({ listing, onClose }) {
  const [activeTab, setActiveTab] = useState('annonce');

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!listing) return null;

  const {
    title, price, year, mileage, location, url,
    matched_keywords, vehicle, gearbox, horsepower, fuel_type,
    doors, seats, color, description, scraped_at,
  } = listing;

  const issues = vehicle?.common_issues || [];
  const knownIssuesText = vehicle?.known_issues_text || [];

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-fmc-surface border border-fmc-border rounded-lg max-w-2xl w-full max-h-[85vh] flex flex-col shadow-neon animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Sticky header */}
        <div className="bg-fmc-panel border-b border-fmc-accent-deep/60 px-6 py-4 flex-shrink-0 flex items-start justify-between">
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

        {/* Tab bar */}
        <div className="flex border-b border-fmc-accent-deep/40 px-6 flex-shrink-0">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-xs font-mono font-semibold transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? 'text-fmc-accent border-fmc-accent'
                  : 'text-fmc-text-dim border-transparent hover:text-fmc-text'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-6 py-4">

          {/* Tab 1 — Annonce */}
          {activeTab === 'annonce' && (
            <div className="space-y-4">
              <section>
                <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                  <span className="text-fmc-accent">◈</span> Caracteristiques
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {year && (
                    <div>
                      <span className="text-fmc-text-dim text-xs font-mono">Annee</span>
                      <p className="font-mono font-semibold text-fmc-text">{year}</p>
                    </div>
                  )}
                  {mileage && (
                    <div>
                      <span className="text-fmc-text-dim text-xs font-mono">Kilometrage</span>
                      <p className="font-mono font-semibold text-fmc-text">{new Intl.NumberFormat('fr-FR').format(mileage)} km</p>
                    </div>
                  )}
                  {gearbox && (
                    <div>
                      <span className="text-fmc-text-dim text-xs font-mono">Boite</span>
                      <p className="font-mono font-semibold text-fmc-text">
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
                  {doors > 0 && (
                    <div>
                      <span className="text-fmc-text-dim text-xs font-mono">Portes</span>
                      <p className="font-mono font-semibold text-fmc-text">{doors}</p>
                    </div>
                  )}
                  {seats > 0 && (
                    <div>
                      <span className="text-fmc-text-dim text-xs font-mono">Places</span>
                      <p className="font-mono font-semibold text-fmc-text">{seats}</p>
                    </div>
                  )}
                  {color && (
                    <div>
                      <span className="text-fmc-text-dim text-xs font-mono">Couleur</span>
                      <p className="font-mono font-semibold text-fmc-text capitalize">{color}</p>
                    </div>
                  )}
                  {location && (
                    <div>
                      <span className="text-fmc-text-dim text-xs font-mono">Ville</span>
                      <p className="font-mono font-semibold text-fmc-text">{location}</p>
                    </div>
                  )}
                </div>
              </section>

              {matched_keywords && matched_keywords.length > 0 && (
                <section className="border-t border-fmc-accent-deep/30 pt-4">
                  <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                    <span className="text-fmc-accent">◈</span> Mots-cles detectes
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {matched_keywords.map(kw => (
                      <Badge key={kw} variant="success">{kw}</Badge>
                    ))}
                  </div>
                </section>
              )}

              {description && (
                <section className="border-t border-fmc-accent-deep/30 pt-4">
                  <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                    <span className="text-fmc-accent">◈</span> Description
                  </h3>
                  <div className="max-h-48 overflow-y-auto bg-fmc-panel rounded border border-fmc-accent-deep/20 p-3">
                    <p className="text-xs font-mono text-fmc-text-dim whitespace-pre-wrap leading-relaxed">{description}</p>
                  </div>
                </section>
              )}
            </div>
          )}

          {/* Tab 2 — Fiabilite */}
          {activeTab === 'fiabilite' && (
            <div className="space-y-4">
              <section>
                <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                  <span className="text-fmc-accent">◈</span> Score de fiabilite
                </h3>
                {vehicle ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <Badge variant={scoreVariant(vehicle.reliability_score)} className="text-base px-4 py-1.5 font-mono">
                        {vehicle.reliability_score !== null && vehicle.reliability_score !== undefined
                          ? `${vehicle.reliability_score}/10`
                          : 'N/A'
                        }
                      </Badge>
                      {vehicle.total_testimonials != null && (
                        <span className="text-fmc-text-dim text-xs font-mono">
                          {vehicle.total_testimonials} temoignages
                        </span>
                      )}
                    </div>
                    {vehicle.model && (
                      <p className="text-fmc-text-muted text-xs font-mono">
                        Modele : {vehicle.model}
                        {vehicle.year_start && vehicle.year_end && ` (${vehicle.year_start}–${vehicle.year_end})`}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-fmc-text-dim text-xs font-mono">Donnees non disponibles pour ce modele.</p>
                )}
              </section>

              {issues.length > 0 && (
                <section className="border-t border-fmc-accent-deep/30 pt-4">
                  <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                    <span className="text-fmc-accent">◈</span> Problemes connus ({issues.length})
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

              {knownIssuesText.length > 0 && (
                <section className="border-t border-fmc-accent-deep/30 pt-4">
                  <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                    <span className="text-fmc-accent">◈</span> Analyse detaillee
                  </h3>
                  <div className="space-y-3">
                    {knownIssuesText.map((paragraph, i) => (
                      <p key={i} className="text-xs text-fmc-text-dim leading-relaxed">{paragraph}</p>
                    ))}
                  </div>
                </section>
              )}

              {!vehicle && (
                <p className="text-fmc-text-dim text-xs font-mono pt-2">Donnees non disponibles pour ce modele.</p>
              )}
            </div>
          )}

          {/* Tab 3 — Liens */}
          {activeTab === 'liens' && (
            <div className="space-y-4">
              {vehicle?.source_url && (
                <section>
                  <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                    <span className="text-fmc-accent">◈</span> Fiche fiabilite
                  </h3>
                  <a
                    href={vehicle.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-xs font-mono text-fmc-accent hover:text-fmc-glow underline underline-offset-2 transition-colors"
                  >
                    Voir la fiche fiches-auto.fr
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </section>
              )}

              <section className={vehicle?.source_url ? 'border-t border-fmc-accent-deep/30 pt-4' : ''}>
                <h3 className="text-xs font-mono font-semibold text-fmc-text-dim uppercase tracking-widest mb-3">
                  <span className="text-fmc-accent">◈</span> Annonce LeBonCoin
                </h3>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="fmc-btn-primary inline-flex items-center gap-2 font-mono text-sm"
                >
                  Voir l'annonce LeBonCoin
                  <ExternalLink className="h-4 w-4" />
                </a>
              </section>

              {scraped_at && (
                <section className="border-t border-fmc-accent-deep/30 pt-4">
                  <p className="text-xs font-mono text-fmc-text-dim">
                    Scrappe le {formatScrapedAt(scraped_at)}
                  </p>
                </section>
              )}
            </div>
          )}
        </div>

        {/* Sticky footer — quick access LBC button */}
        <div className="bg-fmc-panel border-t border-fmc-accent-deep/60 px-6 py-3 flex-shrink-0">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="fmc-btn-primary w-full flex items-center justify-center gap-2 font-mono"
          >
            Voir l'annonce LeBonCoin
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
