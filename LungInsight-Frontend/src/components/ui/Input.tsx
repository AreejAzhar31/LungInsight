import { type InputHTMLAttributes, type TextareaHTMLAttributes, forwardRef } from 'react';
import clsx from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={id} className="text-sm font-medium text-ink">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={clsx(
            'rounded-md border border-line bg-white px-3.5 py-2.5 text-sm text-ink placeholder:text-steel-light',
            'focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500',
            error && 'border-flag-500 focus:border-flag-500 focus:ring-flag-500',
            className
          )}
          aria-invalid={Boolean(error)}
          {...props}
        />
        {error && <p className="text-xs text-flag-600">{error}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, className, id, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={id} className="text-sm font-medium text-ink">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={id}
          className={clsx(
            'rounded-md border border-line bg-white px-3.5 py-2.5 text-sm text-ink placeholder:text-steel-light',
            'focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500',
            className
          )}
          {...props}
        />
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';
