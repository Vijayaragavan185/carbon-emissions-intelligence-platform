import React from 'react';
import { Snackbar, Alert } from '@mui/material';

interface NotificationToastProps {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
  onClose: () => void;
}

export const NotificationToast: React.FC<NotificationToastProps> = ({
  open,
  message,
  severity,
  onClose
}) => {
  return (
    <Snackbar open={open} autoHideDuration={6000} onClose={onClose}>
      <Alert onClose={onClose} severity={severity} sx={{ width: '100%' }}>
        {message}
      </Alert>
    </Snackbar>
  );
};
