import { clsx } from 'clsx';

const variants = {
  primary: 'fmc-btn-primary',
  ghost:   'fmc-btn-ghost',
  outline: 'border border-fmc-border text-fmc-text hover:bg-fmc-surface transition-all duration-200 rounded-md px-4 py-2 text-sm',
  danger:  'bg-red-900/30 border border-red-700/50 text-red-400 hover:bg-red-900/50 rounded-md px-4 py-2 text-sm transition-all',
};

const sizes = {
  sm:  'px-3 py-1.5 text-xs',
  md:  'px-4 py-2 text-sm',
  lg:  'px-5 py-2.5 text-base',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  asChild = false,
  disabled = false,
  className,
  children,
  ...props
}) {
  const classes = clsx(
    variants[variant] || variants.primary,
    !['sm', 'md', 'lg'].some(s => (variants[variant] || '').includes('px-')) && sizes[size],
    fullWidth && 'w-full',
    disabled && 'opacity-40 cursor-not-allowed pointer-events-none',
    className,
  );

  if (asChild) {
    return <span className={classes} {...props}>{children}</span>;
  }

  return (
    <button className={classes} disabled={disabled} {...props}>
      {children}
    </button>
  );
}
