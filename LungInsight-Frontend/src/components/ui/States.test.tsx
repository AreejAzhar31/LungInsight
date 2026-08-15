import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorState, EmptyState } from '@/components/ui/States';

describe('ErrorState', () => {
  it('renders the message', () => {
    render(<ErrorState message="Something failed." />);
    expect(screen.getByText('Something failed.')).toBeInTheDocument();
  });

  it('renders a retry button when onRetry is provided and calls it on click', async () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Failed." onRetry={onRetry} />);
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('does not render a retry button when onRetry is omitted', () => {
    render(<ErrorState message="Failed." />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('renders title and message', () => {
    render(<EmptyState title="No data" message="Nothing to show yet." />);
    expect(screen.getByText('No data')).toBeInTheDocument();
    expect(screen.getByText('Nothing to show yet.')).toBeInTheDocument();
  });

  it('renders custom action content', () => {
    render(<EmptyState title="No data" message="Empty." action={<button>Add item</button>} />);
    expect(screen.getByRole('button', { name: 'Add item' })).toBeInTheDocument();
  });
});
