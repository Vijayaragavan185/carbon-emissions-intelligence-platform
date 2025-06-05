import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { EmissionsDashboard } from '../../components/EmissionsDashboard';

// Mock the hooks
jest.mock('../../hooks/useEmissionsData', () => ({
  useEmissionsData: () => ({
    dashboardData: {
      totalEmissions: 1000,
      scopeBreakdown: { scope1: 300, scope2: 400, scope3: 300 },
      monthlyTrends: [],
    },
    emissions: [],
    dashboardLoading: false,
    emissionsLoading: false,
    createEmission: jest.fn(),
    isCreating: false,
  }),
}));

jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: () => true,
    subscribe: jest.fn(),
    emit: jest.fn(),
  }),
}));

const theme = createTheme();
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider theme={theme}>
      {children}
    </ThemeProvider>
  </QueryClientProvider>
);

describe('EmissionsDashboard', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  test('renders dashboard with key metrics', async () => {
    render(
      <TestWrapper>
        <EmissionsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
      expect(screen.getByText('1,000')).toBeInTheDocument(); // Total emissions
      expect(screen.getByText('300')).toBeInTheDocument(); // Scope 1
    });
  });

  test('shows live connection status', async () => {
    render(
      <TestWrapper>
        <EmissionsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Live')).toBeInTheDocument();
    });
  });
});
