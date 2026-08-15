import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PredictionBadge } from '@/components/ui/Badge';

describe('PredictionBadge', () => {
  it('renders the Normal label', () => {
    render(<PredictionBadge label="Normal" />);
    expect(screen.getByText('Normal')).toBeInTheDocument();
  });

  it('renders the Pneumonia label with flag styling', () => {
    render(<PredictionBadge label="Pneumonia" />);
    const badge = screen.getByText('Pneumonia').closest('span');
    expect(badge).toHaveClass('bg-flag-50');
  });

  it('renders confidence when provided', () => {
    render(<PredictionBadge label="Pneumonia" confidence={94.3} />);
    expect(screen.getByText('94.3%')).toBeInTheDocument();
  });

  it('omits confidence when not provided', () => {
    render(<PredictionBadge label="Normal" />);
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });
});
