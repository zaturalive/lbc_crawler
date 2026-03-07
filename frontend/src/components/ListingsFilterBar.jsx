import { useState, useEffect, useMemo, useRef } from 'react';
import { Search, X, SlidersHorizontal } from 'lucide-react';
import NumberInput from './ui/NumberInput';

export default function ListingsFilterBar({ listings, onFiltered, analyzedIds = new Set() }) {
  const [titleSearch, setTitleSearch]       = useState('');
  const [checkedKeywords, setCheckedKeywords] = useState([]);
  const [kmMin, setKmMin]                   = useState('');
  const [onlyWithFiche, setOnlyWithFiche]   = useState(false);
  const [onlyWithAI, setOnlyWithAI]         = useState(false);

  // Stable ref to avoid stale-closure issues with the callback
  const onFilteredRef = useRef(onFiltered);
  useEffect(() => { onFilteredRef.current = onFiltered; });

  // All unique keywords present in the current result set
  const allKeywords = useMemo(() => {
    const s = new Set();
    listings?.forEach(l => l.matched_keywords?.forEach(kw => s.add(kw)));
    return [...s].sort();
  }, [listings]);

  // Derive filtered array from current state
  const filtered = useMemo(() => {
    if (!listings) return [];
    let r = listings;
    if (titleSearch.trim()) {
      const q = titleSearch.toLowerCase();
      r = r.filter(l => l.title?.toLowerCase().includes(q));
    }
    if (checkedKeywords.length > 0) {
      r = r.filter(l =>
        checkedKeywords.every(kw => l.matched_keywords?.includes(kw))
      );
    }
    if (kmMin !== '' && !isNaN(Number(kmMin)) && Number(kmMin) > 0) {
      r = r.filter(l => l.mileage >= Number(kmMin));
    }
    if (onlyWithFiche) {
      r = r.filter(l => l.vehicle?.source_url);
    }
    if (onlyWithAI) {
      r = r.filter(l => analyzedIds.has(l.id));
    }
    return r;
  }, [listings, titleSearch, checkedKeywords, kmMin, onlyWithFiche, onlyWithAI, analyzedIds]);

  // Notify parent on every change
  useEffect(() => {
    onFilteredRef.current(filtered);
  }, [filtered]);

  function toggleKeyword(kw) {
    setCheckedKeywords(prev =>
      prev.includes(kw) ? prev.filter(k => k !== kw) : [...prev, kw]
    );
  }

  function reset() {
    setTitleSearch('');
    setCheckedKeywords([]);
    setKmMin('');
    setOnlyWithFiche(false);
    setOnlyWithAI(false);
  }

  const hasActiveFilters = titleSearch || checkedKeywords.length > 0 || kmMin || onlyWithFiche || onlyWithAI;
  const total = listings?.length ?? 0;
  const filteredCount = filtered.length;

  return (
    <div className="fmc-panel px-3 py-2 flex flex-wrap items-center gap-3 text-xs font-mono">

      {/* Icône filtre */}
      <SlidersHorizontal className="h-3.5 w-3.5 text-fmc-accent flex-shrink-0" />

      {/* Recherche titre */}
      <div className="relative flex-1 min-w-[140px]">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-fmc-text-dim pointer-events-none" />
        <input
          type="text"
          value={titleSearch}
          onChange={e => setTitleSearch(e.target.value)}
          placeholder="Filtrer par titre…"
          className="fmc-input pl-6 py-1 text-xs"
          style={{ height: '28px' }}
        />
      </div>

      {/* km min */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <span className="text-fmc-text-dim whitespace-nowrap text-xs">km min</span>
        <NumberInput
          min={0}
          step={10000}
          value={kmMin}
          onChange={v => setKmMin(v)}
          placeholder="0"
          className="w-32 text-xs"
        />
      </div>

      {/* Checkboxes keywords */}
      {allKeywords.length > 0 && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          {allKeywords.map(kw => (
            <label key={kw} className="flex items-center gap-1.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={checkedKeywords.includes(kw)}
                onChange={() => toggleKeyword(kw)}
              />
              <span className="text-fmc-text-dim">{kw}</span>
            </label>
          ))}
        </div>
      )}

      {/* Filtre fiche fiabilité */}
      <label className="flex items-center gap-1.5 cursor-pointer select-none flex-shrink-0">
        <input
          type="checkbox"
          checked={onlyWithFiche}
          onChange={e => setOnlyWithFiche(e.target.checked)}
        />
        <span className={onlyWithFiche ? 'text-fmc-accent' : 'text-fmc-text-dim'}>
          Avec fiche fiabilité
        </span>
      </label>

      {/* Filtre analyse IA */}
      <label className="flex items-center gap-1.5 cursor-pointer select-none flex-shrink-0">
        <input
          type="checkbox"
          checked={onlyWithAI}
          onChange={e => setOnlyWithAI(e.target.checked)}
        />
        <span className={onlyWithAI ? 'text-purple-300' : 'text-fmc-text-dim'}>
          ✨ Déjà analysée IA
        </span>
      </label>

      {/* Compteur + reset — poussé à droite */}
      <div className="flex items-center gap-2 ml-auto flex-shrink-0">
        <span className={`whitespace-nowrap ${filteredCount < total ? 'text-fmc-accent' : 'text-fmc-text-dim'}`}>
          {filteredCount}&nbsp;/&nbsp;{total} annonces
        </span>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={reset}
            title="Effacer les filtres de la barre"
            className="fmc-btn-ghost py-0.5 px-2 flex items-center gap-1"
          >
            <X className="h-3 w-3" />
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
