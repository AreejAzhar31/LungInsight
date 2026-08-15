import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { FeedbackForm } from '@/components/feedback/FeedbackForm';

describe('FeedbackForm', () => {
  it('disables submit until a rating is selected', () => {
    renderWithProviders(<FeedbackForm predictionId="pred-1" />);
    expect(screen.getByRole('button', { name: /submit feedback/i })).toBeDisabled();
  });

  it('enables submit once a star rating is chosen', async () => {
    renderWithProviders(<FeedbackForm predictionId="pred-1" />);
    await userEvent.click(screen.getByLabelText('3 stars'));
    expect(screen.getByRole('button', { name: /submit feedback/i })).toBeEnabled();
  });

  it('shows a success message after submitting', async () => {
    renderWithProviders(<FeedbackForm predictionId="pred-1" />);
    await userEvent.click(screen.getByLabelText('4 stars'));
    await userEvent.click(screen.getByRole('button', { name: /submit feedback/i }));
    await waitFor(() => {
      expect(screen.getByText(/feedback has been recorded/i)).toBeInTheDocument();
    });
  });
});
