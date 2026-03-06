import { clsx } from 'clsx';

export default function Input({ className, ...props }) {
  return (
    <input
      className={clsx('fmc-input', className)}
      {...props}
    />
  );
}
