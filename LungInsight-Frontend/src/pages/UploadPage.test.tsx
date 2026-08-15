import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { UploadPage } from '@/pages/UploadPage';

function makeFile(name: string, type: string) {
  return new File(['fake image bytes'], name, { type });
}

describe('UploadPage', () => {
  it('shows the dropzone and a placeholder result panel initially', () => {
    renderWithProviders(<UploadPage />);
    expect(screen.getByText(/drop a chest x-ray/i)).toBeInTheDocument();
    expect(screen.getByText(/your prediction result will appear here/i)).toBeInTheDocument();
  });

  it('shows a preview and the run-prediction button after selecting a file', async () => {
    renderWithProviders(<UploadPage />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(input, makeFile('xray.jpg', 'image/jpeg'));

    expect(screen.getByText('xray.jpg')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run prediction/i })).toBeInTheDocument();
  });

  it('runs the full flow: upload -> analyze -> mock prediction result', async () => {
    renderWithProviders(<UploadPage />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(input, makeFile('xray.jpg', 'image/jpeg'));
    await userEvent.click(screen.getByRole('button', { name: /run prediction/i }));

    await waitFor(
      () => {
        expect(screen.getByText('Result')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(screen.getByText(/prediction id/i)).toBeInTheDocument();
    expect(screen.getByText(/this result is from a mock api call/i)).toBeInTheDocument();
  });

  it('allows clearing the selected file before analysis', async () => {
    renderWithProviders(<UploadPage />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(input, makeFile('xray.jpg', 'image/jpeg'));
    await userEvent.click(screen.getByLabelText('Remove selected image'));

    expect(screen.getByText(/drop a chest x-ray/i)).toBeInTheDocument();
  });
});
