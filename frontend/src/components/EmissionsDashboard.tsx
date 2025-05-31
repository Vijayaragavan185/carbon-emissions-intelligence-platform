import React, { useEffect, useState } from 'react';
import { Box, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import axios from 'axios';

interface Emission {
  id: number;
  source: string;
  value: number;
  unit: string;
  timestamp: string;
}

export const EmissionsDashboard = () => {
  const [emissions, setEmissions] = useState<Emission[]>([]);

  useEffect(() => {
    axios.get('/api/v1/emissions/1').then((res) => {
      setEmissions([res.data]);
    });
  }, []);

  return (
    <Box>
      <Typography variant="h4">Emissions Dashboard</Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Source</TableCell>
            <TableCell>Value</TableCell>
            <TableCell>Unit</TableCell>
            <TableCell>Timestamp</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {emissions.map((emission) => (
            <TableRow key={emission.id}>
              <TableCell>{emission.source}</TableCell>
              <TableCell>{emission.value}</TableCell>
              <TableCell>{emission.unit}</TableCell>
              <TableCell>{emission.timestamp}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
};
