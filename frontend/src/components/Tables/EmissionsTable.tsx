import React from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  CircularProgress,
  Box
} from '@mui/material';
import { EmissionRecord } from '../../types/emissions';

interface EmissionsTableProps {
  emissions: EmissionRecord[];
  loading: boolean;
  onEdit: (record: EmissionRecord) => void;
  onDelete: (id: number) => void;
}

export const EmissionsTable: React.FC<EmissionsTableProps> = ({ 
  emissions, 
  loading,
  onEdit,
  onDelete 
}) => {
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Company</TableCell>
              <TableCell>Scope</TableCell>
              <TableCell>Activity Type</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Emissions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {emissions.map((emission) => (
              <TableRow key={emission.id}>
                <TableCell>{emission.company_id}</TableCell>
                <TableCell>{emission.scope}</TableCell>
                <TableCell>{emission.activity_type}</TableCell>
                <TableCell>{emission.activity_amount} {emission.activity_unit}</TableCell>
                <TableCell>{emission.calculated_emission} {emission.emission_unit}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};
