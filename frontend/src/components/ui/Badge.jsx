import { clsx } from 'clsx';

const variants = {
  default: 'fmc-badge',
  accent:  'fmc-badge fmc-badge-accent',
  success: 'fmc-badge fmc-badge-success',
  warning: 'fmc-badge fmc-badge-warning',
  danger:  'fmc-badge fmc-badge-danger',
  blue:    'fmc-badge bg-blue-900/30 border border-blue-700/50 text-blue-400',
  purple:  'fmc-badge bg-purple-900/30 border border-purple-700/50 text-purple-400',
};

export default function Badge({ variant = 'default', className, children }) {
  return (
    <span className={clsx(variants[variant] || variants.default, className)}>
      {children}
    </span>
  );
}
