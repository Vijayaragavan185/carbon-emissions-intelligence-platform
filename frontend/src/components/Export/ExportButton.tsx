import React from 'react';
import { Button } from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';

export const ExportButton: React.FC = () => {
  const handleExport = () => {
    console.log('Export functionality');
  };

  return (
    <Button
      variant="outlined"
      startIcon={<DownloadIcon />}
      onClick={handleExport}
    >
      Export
    </Button>
  );
};
