import { clsx } from 'clsx';

export function Card({ className, onClick, children }) {
  return (
    <div
      onClick={onClick}
      className={clsx('fmc-card', onClick && 'cursor-pointer', className)}
    >
      {children}
    </div>
  );
}

export function CardContent({ className, children }) {
  return (
    <div className={clsx('p-4', className)}>
      {children}
    </div>
  );
}
