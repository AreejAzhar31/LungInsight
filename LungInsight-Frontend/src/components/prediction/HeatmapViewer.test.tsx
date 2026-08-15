import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HeatmapViewer } from '@/components/prediction/HeatmapViewer';

describe('HeatmapViewer', () => {
  it('renders the original image', () => {
    render(<HeatmapViewer originalImageUrl="/xray.jpg" heatmapUrl={null} label="Normal" />);
    expect(screen.getByAltText('Chest X-ray')).toBeInTheDocument();
  });

  it('shows a message when no heatmap is available', () => {
    render(<HeatmapViewer originalImageUrl="/xray.jpg" heatmapUrl={null} label="Normal" />);
    expect(screen.getByText(/no grad-cam heatmap available/i)).toBeInTheDocument();
  });

  it('renders overlay controls when a heatmap is available', () => {
    render(<HeatmapViewer originalImageUrl="/xray.jpg" heatmapUrl="/heatmap.png" label="Pneumonia" />);
    expect(screen.getByAltText('Grad-CAM attention heatmap overlay')).toBeInTheDocument();
    expect(screen.getByLabelText('Heatmap overlay opacity')).toBeInTheDocument();
  });

  it('toggles the heatmap visibility via the checkbox', async () => {
    render(<HeatmapViewer originalImageUrl="/xray.jpg" heatmapUrl="/heatmap.png" label="Pneumonia" />);
    const checkbox = screen.getByLabelText('Show attention heatmap');
    expect(checkbox).toBeChecked();
    await userEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
    expect(screen.queryByAltText('Grad-CAM attention heatmap overlay')).not.toBeInTheDocument();
  });
});
