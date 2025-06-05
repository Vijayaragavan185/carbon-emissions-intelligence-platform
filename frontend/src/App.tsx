import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Typography, Paper, Box } from '@mui/material';

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

// Simple Dashboard Component for now
const SimpleDashboard: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h3" component="h1" gutterBottom color="primary">
            Carbon Emissions Intelligence Platform
          </Typography>
          <Typography variant="h6" color="textSecondary">
            Dashboard is loading...
          </Typography>
          <Typography variant="body1" sx={{ mt: 2 }}>
            Welcome to your Carbon Emissions tracking dashboard.
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <SimpleDashboard />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
