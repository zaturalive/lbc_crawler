import { useEffect, useState } from 'react';
import { getPatterns } from '../api/client';
import './PatternSelector.css';

export default function PatternSelector({ selected, onChange, customRegex, onCustomRegexChange }) {
  const [patterns, setPatterns] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [regexError, setRegexError] = useState('');

  useEffect(() => {
    getPatterns().then(setPatterns).catch(() => {});
  }, []);

  function togglePattern(id) {
    const next = selected.includes(id) ? selected.filter(x => x !== id) : [...selected, id];
    onChange(next);
  }

  function handleRegexChange(e) {
    const val = e.target.value;
    onCustomRegexChange(val);
    if (!val) { setRegexError(''); return; }
    try { new RegExp(val); setRegexError(''); }
    catch (_) { setRegexError('Expression invalide'); }
  }

  return (
    <div className="pattern-selector">
      <p className="pattern-selector__label">Mots-clés à rechercher dans l'annonce :</p>
      <div className="pattern-selector__checkboxes">
        {patterns.map(p => (
          <label key={p.id} className="pattern-selector__item">
            <input
              type="checkbox"
              checked={selected.includes(p.id)}
              onChange={() => togglePattern(p.id)}
            />
            <span>{p.name}</span>
            {p.description && <small className="pattern-selector__hint">{p.description}</small>}
          </label>
        ))}
      </div>
      <button
        type="button"
        className="pattern-selector__advanced-toggle"
        onClick={() => setShowAdvanced(v => !v)}
      >
        {showAdvanced ? '▲ Masquer le mode avancé' : '▼ Mode avancé (expression personnalisée)'}
      </button>
      {showAdvanced && (
        <div className="pattern-selector__advanced">
          <label>
            <span>Expression régulière personnalisée :</span>
            <input
              type="text"
              value={customRegex}
              onChange={handleRegexChange}
              placeholder="ex: \\bpas\\s+de\\s+rouille\\b"
            />
          </label>
          {regexError && <span className="pattern-selector__error">{regexError}</span>}
        </div>
      )}
    </div>
  );
}
