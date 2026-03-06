import { useEffect, useState } from 'react';
import { getPatterns } from '../api/client';
import Input from './ui/Input';
import Button from './ui/Button';
import { ChevronDown, ChevronUp } from 'lucide-react';

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
    <div className="space-y-4">
      <div>
        <p className="text-sm font-semibold text-fmc-text mb-3">Filtrer par mots-clés :</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {patterns.map(p => (
            <label key={p.id} className="flex items-start gap-3 p-3 rounded-md border border-fmc-accent-deep bg-fmc-card hover:bg-fmc-surface hover:border-fmc-border cursor-pointer transition-all duration-200">
              <input
                type="checkbox"
                checked={selected.includes(p.id)}
                onChange={() => togglePattern(p.id)}
                className="mt-1 rounded"
              />
              <div className="flex-1">
                <span className="font-medium text-fmc-text">{p.name}</span>
                {p.description && <p className="text-xs text-fmc-text-muted mt-1">{p.description}</p>}
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="border-t border-fmc-accent-deep/40 pt-4">
        <Button
          type="button"
          variant="ghost"
          onClick={() => setShowAdvanced(v => !v)}
          className="flex items-center gap-2"
        >
          {showAdvanced ? (
            <>
              <ChevronUp className="h-4 w-4" />
              Masquer le mode avancé
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4" />
              Mode avancé (expression personnalisée)
            </>
          )}
        </Button>
      </div>

      {showAdvanced && (
        <div className="space-y-3 p-4 rounded-md bg-fmc-surface border border-fmc-accent-deep">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-fmc-text">Expression régulière personnalisée :</label>
            <Input
              type="text"
              value={customRegex}
              onChange={handleRegexChange}
              placeholder="ex: \\bpas\\s+de\\s+rouille\\b"
            />
          </div>
          {regexError && (
            <div className="rounded-md bg-red-900/20 p-2">
              <p className="text-sm text-red-400">{regexError}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
