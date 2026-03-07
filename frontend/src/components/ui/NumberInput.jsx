import { Minus, Plus } from 'lucide-react';

export default function NumberInput({ value, onChange, placeholder, min, max, step = 1, className = '' }) {
  const num = value === '' || value === null || value === undefined ? '' : Number(value);

  const increment = () => {
    const next = num === '' ? (min ?? 0) : num + step;
    if (max === undefined || next <= max) onChange(String(next));
  };

  const decrement = () => {
    const next = num === '' ? (min ?? 0) : num - step;
    if (min === undefined || next >= min) onChange(String(next));
  };

  return (
    <div className={`flex items-stretch rounded border border-fmc-border bg-fmc-surface overflow-hidden focus-within:border-fmc-accent transition-colors ${className}`}>
      <button
        type="button"
        onClick={decrement}
        className="px-2 text-fmc-text-dim hover:text-fmc-accent hover:bg-fmc-accent/10 transition-colors border-r border-fmc-border flex items-center"
        tabIndex={-1}
      >
        <Minus className="h-3 w-3" />
      </button>
      <input
        type="number"
        value={value ?? ''}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        onChange={e => onChange(e.target.value)}
        className="flex-1 bg-transparent px-2 py-1.5 text-sm font-mono text-fmc-text placeholder-fmc-text-dim outline-none min-w-0 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
      />
      <button
        type="button"
        onClick={increment}
        className="px-2 text-fmc-text-dim hover:text-fmc-accent hover:bg-fmc-accent/10 transition-colors border-l border-fmc-border flex items-center"
        tabIndex={-1}
      >
        <Plus className="h-3 w-3" />
      </button>
    </div>
  );
}
