import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { LoginPage } from '@/pages/LoginPage';

describe('LoginPage', () => {
  it('renders email and password fields', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('requires both fields before submission proceeds', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByLabelText('Email')).toBeRequired();
    expect(screen.getByLabelText('Password')).toBeRequired();
  });

  it('submits the form and shows a loading state', async () => {
    renderWithProviders(<LoginPage />);
    await userEvent.type(screen.getByLabelText('Email'), 'demo@lunginsight.ai');
    await userEvent.type(screen.getByLabelText('Password'), 'SecurePass123');
    await userEvent.click(screen.getByRole('button', { name: /log in/i }));

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /logging in/i })).not.toBeInTheDocument();
    });
  });

  it('links to the register page', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByRole('link', { name: 'Register' })).toHaveAttribute('href', '/register');
  });
});
