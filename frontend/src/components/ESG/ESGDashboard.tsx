import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Tabs,
  Tab,
  Chip,
  Button,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Assessment,
  TrendingUp,
  Assignment,
  CheckCircle,
  Warning,
  Error,
  Refresh,
  Download,
  Upload
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';

import { ESGApiService } from '../../services/esgApi';
import { formatDate, formatPercentage } from '../../utils/formatters';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement
);

interface ESGDashboardProps {
  companyId?: number;
}

interface DashboardData {
  overview: {
    total_reports: number;
    recent_reports: number;
    average_compliance_score: number;
    time_period: string;
  };
  status_breakdown: Record<string, number>;
  framework_breakdown: Record<string, number>;
  trends: {
    monthly_reports: Array<{ month: string; reports: number }>;
    compliance_scores: Array<{ date: string; score: number; framework: string }>;
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`esg-tabpanel-${index}`}
    aria-labelledby={`esg-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const ESGDashboard: React.FC<ESGDashboardProps> = ({ companyId }) => {
  const [tabValue, setTabValue] = useState(0);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timePeriod, setTimePeriod] = useState('12m');

  const esgApi = new ESGApiService();

  useEffect(() => {
    loadDashboardData();
  }, [companyId, timePeriod]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await esgApi.getDashboardOverview({
        company_id: companyId,
        time_period: timePeriod
      });
      
      if (response.success) {
        setDashboardData(response);
      } else {
        setError('Failed to load dashboard data');
      }
    } catch (err) {
      setError('Error loading dashboard data');
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
      'approved': 'success',
      'published': 'success',
      'under_review': 'warning',
      'draft': 'info',
      'rejected': 'error'
    };
    return colors[status] || 'default';
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, React.ReactNode> = {
      'approved': <CheckCircle fontSize="small" />,
      'published': <CheckCircle fontSize="small" />,
      'under_review': <Warning fontSize="small" />,
      'draft': <Assignment fontSize="small" />,
      'rejected': <Error fontSize="small" />
    };
    return icons[status] || <Assignment fontSize="small" />;
  };

  const prepareComplianceScoreChart = () => {
    if (!dashboardData?.trends.compliance_scores) return null;

    const data = dashboardData.trends.compliance_scores.slice(-12); // Last 12 data points
    
    return {
      labels: data.map(item => formatDate(item.date)),
      datasets: [
        {
          label: 'Compliance Score',
          data: data.map(item => item.score),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderWidth: 2,
          fill: true,
          tension: 0.4
        }
      ]
    };
  };

  const prepareStatusBreakdownChart = () => {
    if (!dashboardData?.status_breakdown) return null;

    const labels = Object.keys(dashboardData.status_breakdown);
    const data = Object.values(dashboardData.status_breakdown);
    
    return {
      labels: labels.map(label => label.replace('_', ' ').toUpperCase()),
      datasets: [
        {
          data,
          backgroundColor: [
            '#4CAF50', // approved - green
            '#FF9800', // under_review - orange  
            '#2196F3', // draft - blue
            '#F44336', // rejected - red
            '#9C27B0'  // published - purple
          ],
          borderWidth: 2,
          borderColor: '#fff'
        }
      ]
    };
  };

  const prepareFrameworkChart = () => {
    if (!dashboardData?.framework_breakdown) return null;

    const labels = Object.keys(dashboardData.framework_breakdown);
    const data = Object.values(dashboardData.framework_breakdown);
    
    return {
      labels: labels.map(label => label.toUpperCase()),
      datasets: [
        {
          label: 'Reports by Framework',
          data,
          backgroundColor: ['#3f51b5', '#009688', '#ff5722'],
          borderWidth: 1
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        action={
          <Button color="inherit" size="small" onClick={loadDashboardData}>
            Retry
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  if (!dashboardData) {
    return (
      <Alert severity="info">
        No dashboard data available
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          ESG Reporting Dashboard
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={loadDashboardData} color="primary">
              <Refresh />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => window.open('/api/esg/reports/export/dashboard', '_blank')}
          >
            Export
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Assessment color="primary" fontSize="large" />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Reports
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardData.overview.total_reports}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <TrendingUp color="success" fontSize="large" />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Recent Reports
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardData.overview.recent_reports}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Last 30 days
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <CheckCircle color="success" fontSize="large" />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Avg Compliance
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardData.overview.average_compliance_score}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Assignment color="info" fontSize="large" />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Status Overview
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                    {Object.entries(dashboardData.status_breakdown).map(([status, count]) => (
                      <Chip
                        key={status}
                        label={`${status}: ${count}`}
                        size="small"
                        color={getStatusColor(status)}
                        icon={getStatusIcon(status)}
                      />
                    ))}
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for detailed views */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="ESG dashboard tabs">
            <Tab label="Compliance Trends" />
            <Tab label="Status Breakdown" />
            <Tab label="Framework Analysis" />
            <Tab label="Performance Analytics" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Compliance Score Trends
          </Typography>
          <Box height={400}>
            {prepareComplianceScoreChart() && (
              <Line data={prepareComplianceScoreChart()!} options={chartOptions} />
            )}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Report Status Distribution
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box height={300}>
                {prepareStatusBreakdownChart() && (
                  <Doughnut 
                    data={prepareStatusBreakdownChart()!} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom'
                        }
                      }
                    }} 
                  />
                )}
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box mt={2}>
                {Object.entries(dashboardData.status_breakdown).map(([status, count]) => (
                  <Box key={status} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Chip
                      label={status.replace('_', ' ').toUpperCase()}
                      color={getStatusColor(status)}
                      icon={getStatusIcon(status)}
                      variant="outlined"
                    />
                    <Typography variant="h6">{count}</Typography>
                  </Box>
                ))}
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Reports by Framework
          </Typography>
          <Box height={400}>
            {prepareFrameworkChart() && (
              <Bar data={prepareFrameworkChart()!} options={chartOptions} />
            )}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Performance Analytics
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Monthly Report Volume
                  </Typography>
                  <Box height={250}>
                    {dashboardData.trends.monthly_reports && (
                      <Line
                        data={{
                          labels: dashboardData.trends.monthly_reports.map(item => item.month),
                          datasets: [{
                            label: 'Reports Created',
                            data: dashboardData.trends.monthly_reports.map(item => item.reports),
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderWidth: 2,
                            fill: true
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: { legend: { display: false } }
                        }}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Framework Performance
                  </Typography>
                  <Box mt={2}>
                    {Object.entries(dashboardData.framework_breakdown).map(([framework, count]) => (
                      <Box key={framework} mb={2}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="body2">{framework.toUpperCase()}</Typography>
                          <Typography variant="body2" fontWeight="bold">{count} reports</Typography>
                        </Box>
                        <Box
                          height={8}
                          bgcolor="grey.200"
                          borderRadius={1}
                          overflow="hidden"
                        >
                          <Box
                            height="100%"
                            bgcolor="primary.main"
                            borderRadius={1}
                            width={`${(count / dashboardData.overview.total_reports) * 100}%`}
                          />
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>
    </Box>
  );
};

export default ESGDashboard;
