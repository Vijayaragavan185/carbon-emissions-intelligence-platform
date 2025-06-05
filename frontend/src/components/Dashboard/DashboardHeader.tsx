import React from 'react';
import { Typography, Box } from '@mui/material';

interface DashboardHeaderProps {
  title: string;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ title }) => {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h6" noWrap component="div">
        {title}
      </Typography>
    </Box>
  );
};
