import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { EmissionsDashboard } from './components/EmissionsDashboard'; // Import the full dashboard
import './index.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#6C5CE7',
    },
    secondary: {
      main: '#A8E6CF',
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <EmissionsDashboard /> {/* Use the full dashboard instead of SimpleDashboard */}
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
