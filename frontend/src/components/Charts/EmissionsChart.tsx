import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { Box, Paper, Typography, useTheme, useMediaQuery } from '@mui/material';
import { CHART_COLORS } from '../../utils/constants';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface EmissionsChartProps {
  data: {
    scope1: number;
    scope2: number;
    scope3: number;
  };
  type?: 'bar' | 'doughnut';
  height?: number;
}

export const EmissionsChart: React.FC<EmissionsChartProps> = ({
  data,
  type = 'doughnut',
  height = 400
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const chartData = useMemo(() => {
    const scopeData = [data.scope1, data.scope2, data.scope3];
    const total = scopeData.reduce((sum, value) => sum + value, 0);
    
    return {
      labels: ['Scope 1', 'Scope 2', 'Scope 3'],
      datasets: [
        {
          label: 'CO2e Emissions (tonnes)',
          data: scopeData,
          backgroundColor: [
            CHART_COLORS.scope1,
            CHART_COLORS.scope2,
            CHART_COLORS.scope3,
          ],
          borderColor: [
            CHART_COLORS.scope1,
            CHART_COLORS.scope2,
            CHART_COLORS.scope3,
          ],
          borderWidth: 2,
        },
      ],
    };
  }, [data]);

    const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
        position: isMobile ? 'bottom' as const : 'right' as const,
        labels: {
            usePointStyle: true,
            padding: 20,
        },
        },
        title: {
        display: true,
        text: 'Emissions by Scope',
        font: {
            size: 16,
            weight: 'bold' as const, // Add 'as const'
        },
        },
        tooltip: {
        callbacks: {
            label: (context: any) => {
            const value = context.parsed || context.raw;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${context.label}: ${value.toLocaleString()} tonnes CO2e (${percentage}%)`;
            },
        },
        },
    },
    scales: type === 'bar' ? {
        y: {
        beginAtZero: true,
        ticks: {
            callback: (value: any) => `${value} tonnes`,
        },
        },
    } : undefined,
    };

return (
    <Paper elevation={3} sx={{ p: 3, height: height + 100 }}>
      <Box sx={{ height: height, position: 'relative' }}>
        {type === 'bar' ? (
          <Bar data={chartData} options={options} />
        ) : (
          <Doughnut data={chartData} options={options} />
        )}
      </Box>
    </Paper>
  );
};
