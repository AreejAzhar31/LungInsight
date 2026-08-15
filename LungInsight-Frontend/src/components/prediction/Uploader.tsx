import { useCallback, useRef, useState, type DragEvent } from 'react';
import { UploadCloud, X } from 'lucide-react';
import clsx from 'clsx';

interface UploaderProps {
  onFileSelected: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
  disabled?: boolean;
}

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/jpg'];

export function Uploader({ onFileSelected, selectedFile, onClear, disabled }: UploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const previewUrl = selectedFile ? URL.createObjectURL(selectedFile) : null;

  const validateAndSelect = useCallback(
    (file: File) => {
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError('Please upload a JPEG or PNG chest X-ray image.');
        return;
      }
      setError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndSelect(file);
  }

  if (selectedFile && previewUrl) {
    return (
      <div className="viewbox-frame rounded-lg p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-ink">{selectedFile.name}</p>
          <button
            type="button"
            onClick={onClear}
            disabled={disabled}
            className="rounded-md p-1 text-steel hover:bg-lightbox-dim hover:text-ink disabled:opacity-50"
            aria-label="Remove selected image"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <img
          src={previewUrl}
          alt="Chest X-ray preview"
          className="mt-3 max-h-96 w-full rounded-md bg-lightbox-dim object-contain"
        />
      </div>
    );
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={clsx(
          'viewbox-frame flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg px-6 py-16 text-center transition-colors',
          isDragging && 'bg-cyan-50',
          disabled && 'cursor-not-allowed opacity-60'
        )}
      >
        <UploadCloud className="h-10 w-10 text-cyan-500" aria-hidden />
        <div>
          <p className="font-display font-medium text-ink">Drop a chest X-ray, or click to browse</p>
          <p className="mt-1 text-sm text-steel">JPEG or PNG, up to 10MB</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/jpg"
          className="sr-only"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) validateAndSelect(file);
          }}
        />
      </div>
      {error && <p className="mt-2 text-sm text-flag-600">{error}</p>}
    </div>
  );
}
