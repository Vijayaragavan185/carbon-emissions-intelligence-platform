import React, { useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Fab,
  Dialog,
  useTheme,
  useMediaQuery,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  TrendingUp,
  TrendingDown,
  Factory,
  Assessment,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { DashboardLayout } from './Dashboard/DashboardLayout';
import { EmissionsChart } from './Charts/EmissionsChart';
import { TrendChart } from './Charts/TrendChart';
import { EmissionEntryForm } from './Forms/EmissionEntryForm';
import { EmissionsTable } from './Tables/EmissionsTable';
import { ExportButton } from './Export/ExportButton';
import { LoadingSpinner } from './UI/LoadingSpinner';
import { NotificationToast } from './UI/NotificationToast';
import { useEmissionsData } from '../hooks/useEmissionsData';
import { useWebSocket } from '../hooks/useWebSocket';

export const EmissionsDashboard: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [formOpen, setFormOpen] = useState(false);
  const [notification, setNotification] = useState<{
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);

  const {
    dashboardData,
    emissions,
    dashboardLoading,
    emissionsLoading,
    createEmission,
    isCreating,
    realTimeData,
  } = useEmissionsData();

  // WebSocket connection status - Fixed: pass URL first, then options
  const { isConnected } = useWebSocket(
    process.env.REACT_APP_WS_URL,
    {
      onConnect: () => {
        setNotification({
          message: 'Real-time updates connected',
          severity: 'success'
        });
      },
      onDisconnect: () => {
        setNotification({
          message: 'Real-time updates disconnected',
          severity: 'warning'
        });
      },
    }
  );

  const handleFormSubmit = async (data: any) => {
    try {
      await createEmission(data);
      setFormOpen(false);
      setNotification({
        message: 'Emission record created successfully',
        severity: 'success'
      });
    } catch (error) {
      setNotification({
        message: 'Failed to create emission record',
        severity: 'error'
      });
    }
  };

  const mockCompanies = [
    { id: 1, name: 'EcoTech Industries', industry_sector: 'Technology', country: 'US', reporting_year: 2023 }
  ];

  if (dashboardLoading) {
    return (
      <DashboardLayout>
        <LoadingSpinner />
      </DashboardLayout>
    );
  }

  const scopeBreakdown = dashboardData?.scopeBreakdown || { scope1: 0, scope2: 0, scope3: 0 };
  const totalEmissions = dashboardData?.totalEmissions || 0;
  const monthlyTrends = dashboardData?.monthlyTrends || [];

  return (
    <DashboardLayout title="Carbon Emissions Intelligence Platform">
      <AnimatePresence>
        {dashboardLoading && (
          <Box sx={{ width: '100%', mb: 2 }}>
            <LinearProgress />
          </Box>
        )}
      </AnimatePresence>

      {/* Real-time connection indicator */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard Overview
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={isConnected ? 'Live' : 'Offline'} // Fixed: Remove function call
            color={isConnected ? 'success' : 'default'} // Fixed: Remove function call
            size="small"
            variant="outlined"
          />
          <ExportButton />
          <IconButton onClick={() => window.location.reload()}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="overline">
                      Total Emissions
                    </Typography>
                    <Typography variant="h4">
                      {totalEmissions.toLocaleString()}
                    </Typography>
                    <Typography color="textSecondary" variant="body2">
                      tonnes CO2e
                    </Typography>
                  </Box>
                  <Factory color="primary" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="overline">
                      Scope 1 Emissions
                    </Typography>
                    <Typography variant="h4">
                      {scopeBreakdown.scope1.toLocaleString()}
                    </Typography>
                    <Typography color="textSecondary" variant="body2">
                      Direct emissions
                    </Typography>
                  </Box>
                  <TrendingUp color="error" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="overline">
                      Scope 2 Emissions
                    </Typography>
                    <Typography variant="h4">
                      {scopeBreakdown.scope2.toLocaleString()}
                    </Typography>
                    <Typography color="textSecondary" variant="body2">
                      Indirect emissions
                    </Typography>
                  </Box>
                  <TrendingDown color="warning" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="overline">
                      Scope 3 Emissions
                    </Typography>
                    <Typography variant="h4">
                      {scopeBreakdown.scope3.toLocaleString()}
                    </Typography>
                    <Typography color="textSecondary" variant="body2">
                      Value chain emissions
                    </Typography>
                  </Box>
                  <Assessment color="info" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <EmissionsChart
              data={scopeBreakdown}
              type={isMobile ? 'bar' : 'doughnut'}
              height={isMobile ? 300 : 400}
            />
          </motion.div>
        </Grid>

        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 }}
          >
            <TrendChart
              data={monthlyTrends}
              height={isMobile ? 300 : 400}
              showScopes={!isMobile}
            />
          </motion.div>
        </Grid>
      </Grid>

      {/* Recent Records Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <EmissionsTable
          emissions={emissions || []}
          loading={emissionsLoading}
          onEdit={(record) => console.log('Edit:', record)}
          onDelete={(id) => console.log('Delete:', id)}
        />
      </motion.div>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add emission record"
        sx={{
          position: 'fixed',
          bottom: isMobile ? 16 : 32,
          right: isMobile ? 16 : 32,
        }}
        onClick={() => setFormOpen(true)}
      >
        <AddIcon />
      </Fab>

      {/* Form Dialog */}
      <Dialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        maxWidth="md"
        fullWidth
        fullScreen={isMobile}
      >
        <EmissionEntryForm
          companies={mockCompanies}
          onSubmit={handleFormSubmit}
          onCancel={() => setFormOpen(false)} // Added onCancel prop
          isLoading={isCreating}
        />
      </Dialog>

      {/* Notification Toast */}
      {notification && (
        <NotificationToast
          message={notification.message}
          severity={notification.severity}
          open={!!notification}
          onClose={() => setNotification(null)}
        />
      )}
    </DashboardLayout>
  );
};
