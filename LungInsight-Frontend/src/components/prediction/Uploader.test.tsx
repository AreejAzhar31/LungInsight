import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Uploader } from '@/components/prediction/Uploader';

function makeFile(name: string, type: string) {
  return new File(['fake image bytes'], name, { type });
}

describe('Uploader', () => {
  it('shows the dropzone when no file is selected', () => {
    render(<Uploader onFileSelected={vi.fn()} selectedFile={null} onClear={vi.fn()} />);
    expect(screen.getByText(/drop a chest x-ray/i)).toBeInTheDocument();
  });

  it('calls onFileSelected with a valid image file', async () => {
    const onFileSelected = vi.fn();
    render(<Uploader onFileSelected={onFileSelected} selectedFile={null} onClear={vi.fn()} />);

    const file = makeFile('xray.jpg', 'image/jpeg');
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(input, file);

    expect(onFileSelected).toHaveBeenCalledWith(file);
  });

  it('rejects a non-image file with an error message', () => {
    // userEvent.upload correctly respects the input's `accept` attribute
    // (like a real browser file picker) and won't deliver a disallowed
    // file at all. Drag-and-drop bypasses that browser-level filter, so
    // this exercises the same code path a dropped file would hit, via a
    // raw change event instead.
    const onFileSelected = vi.fn();
    render(<Uploader onFileSelected={onFileSelected} selectedFile={null} onClear={vi.fn()} />);

    const file = makeFile('notes.txt', 'text/plain');
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    Object.defineProperty(input, 'files', { value: [file] });
    fireEvent.change(input);

    expect(onFileSelected).not.toHaveBeenCalled();
    expect(screen.getByText(/please upload a jpeg or png/i)).toBeInTheDocument();
  });

  it('shows the preview and filename when a file is selected', () => {
    const file = makeFile('xray.jpg', 'image/jpeg');
    render(<Uploader onFileSelected={vi.fn()} selectedFile={file} onClear={vi.fn()} />);
    expect(screen.getByText('xray.jpg')).toBeInTheDocument();
    expect(screen.getByAltText('Chest X-ray preview')).toBeInTheDocument();
  });

  it('calls onClear when the remove button is clicked', async () => {
    const onClear = vi.fn();
    const file = makeFile('xray.jpg', 'image/jpeg');
    render(<Uploader onFileSelected={vi.fn()} selectedFile={file} onClear={onClear} />);
    await userEvent.click(screen.getByLabelText('Remove selected image'));
    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
