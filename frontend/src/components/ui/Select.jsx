import * as SelectPrimitive from '@radix-ui/react-select';
import { ChevronDown, Check } from 'lucide-react';
import clsx from 'clsx';
import './Select.css';

export const Select = SelectPrimitive.Root;
export const SelectGroup = SelectPrimitive.Group;
export const SelectValue = SelectPrimitive.Value;

export const SelectTrigger = ({
  className,
  children,
  ...props
}) => (
  <SelectPrimitive.Trigger
    className={clsx(
      'inline-flex h-10 items-center justify-between rounded-md border border-fmc-border bg-fmc-surface px-3 py-2 text-base text-fmc-text placeholder:text-fmc-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fmc-border focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
      className
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="h-4 w-4 opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
);

export const SelectContent = ({
  className,
  children,
  position = 'popper',
  ...props
}) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      className={clsx(
        'relative z-50 w-full min-w-[8rem] overflow-hidden rounded-md border border-fmc-border bg-fmc-surface shadow-md',
        position === 'popper' && 'w-[var(--radix-select-trigger-width)] data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1',
        className
      )}
      position={position}
      {...props}
    >
      <SelectPrimitive.Viewport className={clsx('p-1', position === 'popper' && 'h-[var(--radix-select-content-available-height)]')}>
        {children}
      </SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
);

export const SelectItem = ({
  className,
  children,
  ...props
}) => (
  <SelectPrimitive.Item
    className={clsx(
      'relative flex cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-base text-fmc-text outline-none focus:bg-fmc-panel focus:text-fmc-text data-[disabled]:pointer-events-none data-[disabled]:opacity-50 hover:bg-fmc-panel transition-colors duration-150',
      className
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4 text-fmc-accent" />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
);

export const SelectSeparator = ({
  className,
  ...props
}) => (
  <SelectPrimitive.Separator
    className={clsx('-mx-1 my-1 h-px bg-fmc-card', className)}
    {...props}
  />
);
