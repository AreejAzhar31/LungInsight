import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from '@/components/ui/Input';

describe('Input', () => {
  it('renders a label associated with the input', () => {
    render(<Input id="email" label="Email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('shows an error message and sets aria-invalid', () => {
    render(<Input id="email" label="Email" error="Email is required" />);
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true');
  });

  it('calls onChange as the user types', async () => {
    const handleChange = vi.fn();
    render(<Input id="name" label="Name" onChange={handleChange} />);
    await userEvent.type(screen.getByLabelText('Name'), 'Jane');
    expect(handleChange).toHaveBeenCalledTimes(4);
  });
});
