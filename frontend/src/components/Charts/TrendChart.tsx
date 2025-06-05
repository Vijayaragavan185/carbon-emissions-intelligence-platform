import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Box, Paper, Typography, useTheme } from '@mui/material';
import { format, parseISO } from 'date-fns';
import { CHART_COLORS } from '../../utils/constants';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface TrendChartProps {
  data: Array<{
    month: string;
    emissions: number;
    scope1?: number;
    scope2?: number;
    scope3?: number;
  }>;
  height?: number;
  showScopes?: boolean;
}

export const TrendChart: React.FC<TrendChartProps> = ({
  data,
  height = 400,
  showScopes = false
}) => {
  const theme = useTheme();

  const chartData = useMemo(() => {
    const labels = data.map(item => format(parseISO(item.month), 'MMM yyyy'));

    if (showScopes) {
      return {
        labels,
        datasets: [
          {
            label: 'Scope 1',
            data: data.map(item => item.scope1 || 0),
            borderColor: CHART_COLORS.scope1,
            backgroundColor: `${CHART_COLORS.scope1}20`,
            fill: false,
            tension: 0.4,
          },
          {
            label: 'Scope 2',
            data: data.map(item => item.scope2 || 0),
            borderColor: CHART_COLORS.scope2,
            backgroundColor: `${CHART_COLORS.scope2}20`,
            fill: false,
            tension: 0.4,
          },
          {
            label: 'Scope 3',
            data: data.map(item => item.scope3 || 0),
            borderColor: CHART_COLORS.scope3,
            backgroundColor: `${CHART_COLORS.scope3}20`,
            fill: false,
            tension: 0.4,
          },
        ],
      };
    }

    return {
      labels,
      datasets: [
        {
          label: 'Total Emissions',
          data: data.map(item => item.emissions),
          borderColor: CHART_COLORS.primary,
          backgroundColor: `${CHART_COLORS.primary}20`,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: CHART_COLORS.primary,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
        },
      ],
    };
  }, [data, showScopes]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Emissions Trend Over Time',
        font: {
          size: 16,
          weight: 'bold' as const, // Fixed: Add 'as const'
        },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()} tonnes CO2e`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Month',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Emissions (tonnes CO2e)',
        },
        beginAtZero: true,
        ticks: {
          callback: (value: any) => `${value} tonnes`,
        },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  };

  return (
    <Paper elevation={3} sx={{ p: 3, height: height + 100 }}>
      <Box sx={{ height: height, position: 'relative' }}>
        <Line data={chartData} options={options} />
      </Box>
    </Paper>
  );
};
