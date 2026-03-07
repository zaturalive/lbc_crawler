import { useEffect, useState } from 'react';
import { X, ExternalLink, AlertTriangle } from 'lucide-react';
import Badge from './ui/Badge';
import { analyzeListingAI, getAiQuota } from '../api/client';

function parseIssue(issue) {
  const clean = issue.replace(/[\t\r\n]+/g, ' ').replace(/\s{2,}/g, ' ').trim();
  const colonIdx = clean.indexOf(':');
  if (colonIdx === -1) return { title: clean, description: '' };
  return {
    title: clean.slice(0, colonIdx).trim(),
    description: clean.slice(colonIdx + 1).trim(),
  };
}

/**
 * Parse a detailed issue block like:
 * "Embrayage : texte... Bruits parasites : texte... GPS/électronique : texte..."
 * Strategy: split on ". " followed by a title-like pattern (short phrase + " : ")
 * Returns array of { subtitle, text }
 */
function parseDetailedIssue(raw) {
  // Normalize line breaks and extra spaces
  const clean = raw.replace(/\r\n|\r/g, ' ').replace(/\s{2,}/g, ' ').trim();

  // Split on sentence boundary before a new "Title : " pattern
  // A title is: 2-60 chars with no colon, followed by " : "
  // We split on ". " or ". \n" right before such a title
  const parts = clean.split(/\.\s+(?=[^.:]{2,60}?\s*:\s)/);

  const bullets = parts
    .map(part => {
      const colonPos = part.indexOf(' : ');
      if (colonPos === -1 || colonPos > 70) {
        // No clear title — keep as plain text if substantial
        return part.trim().length > 15 ? { subtitle: '', text: part.trim().replace(/\.$/, '') } : null;
      }
      const subtitle = part.slice(0, colonPos).trim();
      const text = part.slice(colonPos + 3).trim().replace(/\.$/, '');
      // Reject if "subtitle" looks like mid-sentence (contains '. ' or is too long)
      if (subtitle.includes('. ') || subtitle.length > 60) {
        return { subtitle: '', text: part.trim().replace(/\.$/, '') };
      }
      return text.length > 5 ? { subtitle, text } : null;
    })
    .filter(Boolean);

  return bullets.length > 0 ? bullets : [{ subtitle: '', text: clean }];
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
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [aiQuota, setAiQuota] = useState(null);

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

  async function handleAnalyze() {
    if (aiAnalysis?.reponse) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const data = await analyzeListingAI(listing.id);
      if (data && data.status === 'error') {
        setAiError("L'analyse a échoué. Réessayez.");
        setAiAnalysis(null);
      } else {
        setAiAnalysis(data);
      }
    } catch (err) {
      if (err?.status === 429) {
        setAiError(err.message || 'Quota IA dépassé');
      } else {
        setAiError(err.message || 'Analyse IA indisponible');
      }
    } finally {
      setAiLoading(false);
    }
  }

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
          <button
            onClick={() => { setActiveTab('analyse-ia'); handleAnalyze(); }}
            disabled={aiQuota && aiQuota.listing_analyses_used >= aiQuota.listing_analyses_max}
            className={`px-4 py-2.5 text-xs font-mono font-semibold transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
              aiQuota && aiQuota.listing_analyses_used >= aiQuota.listing_analyses_max
                ? 'text-zinc-500 border-transparent cursor-not-allowed'
                : activeTab === 'analyse-ia'
                  ? 'text-fmc-accent border-fmc-accent'
                  : 'text-fmc-text-dim border-transparent hover:text-fmc-text'
            }`}
          >
            ✨ Analyse IA
            {aiQuota && aiQuota.listing_analyses_used >= aiQuota.listing_analyses_max ? (
              <span className="px-1.5 py-0.5 text-xs font-mono rounded-full bg-red-900/30 border border-red-500/50 text-red-400 leading-none">
                {aiQuota.listing_analyses_max}/{aiQuota.listing_analyses_max}
              </span>
            ) : (
              <span className="px-1.5 py-0.5 text-xs font-mono rounded-full bg-green-900/30 border border-green-500/50 text-green-400 leading-none">
                {aiQuota ? `${aiQuota.listing_analyses_used}/${aiQuota.listing_analyses_max}` : 'Gratuit'}
              </span>
            )}
          </button>
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
                    {vehicle.reliability_rank && (
                      <div className="flex items-center gap-2 p-2 rounded bg-zinc-800 border border-zinc-700">
                        <span className="text-xs text-zinc-400">Classement fiabilite :</span>
                        <span className="text-sm font-semibold text-green-400 font-mono">{vehicle.reliability_rank}</span>
                      </div>
                    )}
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
                  <div className="space-y-2">
                    {knownIssuesText.flatMap((paragraph, i) => {
                      const bullets = parseDetailedIssue(paragraph);
                      return bullets.map((bullet, j) => (
                        <div key={`${i}-${j}`} className="rounded border border-fmc-accent-deep/30 bg-fmc-panel/60 overflow-hidden">
                          {bullet.subtitle && (
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-fmc-accent-deep/20 border-b border-fmc-accent-deep/30">
                              <AlertTriangle className="h-3 w-3 text-fmc-accent flex-shrink-0" />
                              <span className="text-xs font-mono font-semibold text-fmc-accent">{bullet.subtitle}</span>
                            </div>
                          )}
                          <p className="px-3 py-2 text-xs text-fmc-text-dim leading-relaxed">{bullet.text}</p>
                        </div>
                      ));
                    })}
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
          {/* Tab 4 — Analyse IA */}
          {activeTab === 'analyse-ia' && (
            <div className="space-y-4">
              {/* Header avec badge gratuit */}
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-mono font-semibold text-fmc-text flex items-center gap-2">
                  <span className="text-fmc-accent">✨</span> Analyse IA de l'annonce
                </h3>
                <span className="px-2 py-0.5 text-xs font-mono rounded-full bg-green-900/30 border border-green-500/50 text-green-400">
                  ✓ Gratuit
                </span>
              </div>

              {/* Etat: pas encore charge */}
              {!aiLoading && !aiAnalysis?.reponse && !aiError && (
                <div className="text-center py-6">
                  <p className="text-fmc-text-dim text-xs font-mono mb-3">
                    L'IA va analyser la description de cette annonce pour trouver les réparations effectuées,
                    estimer les prochaines révisions et évaluer le risque.
                  </p>
                  {aiQuota && aiQuota.listing_analyses_used >= aiQuota.listing_analyses_max ? (
                    <div className="space-y-2">
                      <button disabled className="fmc-btn-primary text-sm px-6 py-2 opacity-40 cursor-not-allowed">
                        ✨ Lancer l'analyse IA
                      </button>
                      <p className="text-red-400 text-xs font-mono">
                        Quota atteint ({aiQuota.listing_analyses_max}/{aiQuota.listing_analyses_max})
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <button
                        onClick={handleAnalyze}
                        className="fmc-btn-primary text-sm px-6 py-2"
                      >
                        ✨ Lancer l'analyse IA
                      </button>
                      {aiQuota && (
                        <p className="text-fmc-text-dim text-xs font-mono">
                          ({aiQuota.listing_analyses_max - aiQuota.listing_analyses_used}/{aiQuota.listing_analyses_max} restantes)
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Loading */}
              {aiLoading && (
                <div className="flex flex-col items-center justify-center py-8 gap-3">
                  <div className="w-8 h-8 border-2 border-fmc-accent border-t-transparent rounded-full animate-spin" />
                  <p className="text-fmc-text-dim text-xs font-mono">Analyse en cours…</p>
                </div>
              )}

              {/* Erreur — toast inline dans la modal */}
              {aiError && (
                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] bg-red-900/90 border border-red-500/50 text-red-200 font-mono text-sm px-5 py-3 rounded-lg shadow-xl">
                  {aiError}
                </div>
              )}

              {/* Resultats */}
              {aiAnalysis?.reponse && (
                <div className="space-y-4">
                  {/* Niveau de risque */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-fmc-text-dim">Risque global :</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                      aiAnalysis.reponse?.risk_level === 'low'  ? 'bg-green-900/30 text-green-400 border border-green-500/50' :
                      aiAnalysis.reponse?.risk_level === 'high' ? 'bg-red-900/30 text-red-400 border border-red-500/50' :
                                                         'bg-yellow-900/30 text-yellow-400 border border-yellow-500/50'
                    }`}>
                      {aiAnalysis.reponse?.risk_level === 'low' ? '✓ Faible' : aiAnalysis.reponse?.risk_level === 'high' ? '⚠ Élevé' : '~ Modéré'}
                    </span>
                    {aiAnalysis.cached && (
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-900/40 border border-cyan-500/40 text-cyan-400">
                        ⚡ Analyse déjà en cache
                      </span>
                    )}
                    {aiAnalysis.model && (
                      <span className="text-xs text-fmc-text-dim font-mono ml-auto opacity-60">via {aiAnalysis.model}</span>
                    )}
                  </div>

                  {/* Resume */}
                  {aiAnalysis.reponse?.condition_summary && (
                    <div className="fmc-card p-3 space-y-1">
                      <p className="text-xs font-mono font-semibold text-fmc-accent">📋 État général</p>
                      <p className="text-xs text-fmc-text leading-relaxed">{aiAnalysis.reponse?.condition_summary}</p>
                    </div>
                  )}

                  {/* Reparations effectuees */}
                  {aiAnalysis.reponse?.repairs_found && aiAnalysis.reponse?.repairs_found.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-xs font-mono font-semibold text-fmc-accent">🔧 Réparations effectuées</p>
                      <ul className="space-y-1">
                        {aiAnalysis.reponse?.repairs_found.map((r, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-fmc-text font-mono">
                            <span className="text-green-400 mt-0.5">✓</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Revisions a venir */}
                  {aiAnalysis.reponse?.upcoming_maintenance && aiAnalysis.reponse?.upcoming_maintenance.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-xs font-mono font-semibold text-fmc-accent">🔮 Révisions probables à prévoir</p>
                      <ul className="space-y-1">
                        {aiAnalysis.reponse?.upcoming_maintenance.map((m, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-fmc-text font-mono">
                            <span className="text-yellow-400 mt-0.5">→</span>
                            <span>{m}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Aucune reparation trouvee */}
                  {aiAnalysis.reponse?.repairs_found && aiAnalysis.reponse?.repairs_found.length === 0 && (
                    <p className="text-xs text-fmc-text-dim font-mono italic">Aucune réparation mentionnée dans l'annonce.</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
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
