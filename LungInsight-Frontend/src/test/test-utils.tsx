import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/context/AuthContext';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

interface WrapperProps {
  children: ReactNode;
  initialRoute?: string;
}

function AllProviders({ children, initialRoute = '/' }: WrapperProps) {
  return (
    <QueryClientProvider client={createTestQueryClient()}>
      <AuthProvider>
        <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export function renderWithProviders(
  ui: ReactElement,
  options?: { initialRoute?: string } & Omit<RenderOptions, 'wrapper'>
) {
  const { initialRoute, ...renderOptions } = options ?? {};
  return render(ui, {
    wrapper: ({ children }) => <AllProviders initialRoute={initialRoute}>{children}</AllProviders>,
    ...renderOptions,
  });
}

export * from '@testing-library/react';
