import React from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Grid,
  CircularProgress,
  FormHelperText,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { FormData, Company } from '../../types/emissions';
import { EMISSION_SCOPES, ACTIVITY_TYPES, UNITS } from '../../utils/constants';

interface EmissionEntryFormProps {
  companies: Company[];
  onSubmit: (data: FormData) => void;
  onCancel?: () => void;
  initialData?: Partial<FormData>;
  isLoading?: boolean;
}

export const EmissionEntryForm: React.FC<EmissionEntryFormProps> = ({
  companies,
  onSubmit,
  onCancel,
  initialData,
  isLoading = false
}) => {
  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm({
    defaultValues: {
      company_id: initialData?.company_id || 0,
      scope: initialData?.scope || '',
      activity_type: initialData?.activity_type || '',
      activity_amount: initialData?.activity_amount || 0,
      activity_unit: initialData?.activity_unit || '',
      reporting_period_start: initialData?.reporting_period_start || '',
      reporting_period_end: initialData?.reporting_period_end || '',
      notes: initialData?.notes || '',
    },
  });

  const onFormSubmit = (data: any) => {
    // Basic validation
    if (data.company_id === 0) {
      alert('Please select a company');
      return;
    }
    if (!data.scope) {
      alert('Please select an emission scope');
      return;
    }
    if (!data.activity_type) {
      alert('Please select an activity type');
      return;
    }
    if (data.activity_amount <= 0) {
      alert('Please enter a valid activity amount');
      return;
    }
    if (!data.activity_unit) {
      alert('Please select a unit');
      return;
    }
    if (!data.reporting_period_start || !data.reporting_period_end) {
      alert('Please select reporting period dates');
      return;
    }

    onSubmit(data as FormData);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Add Emission Record
      </Typography>

      <Box component="form" onSubmit={handleSubmit(onFormSubmit)}>
        <Grid container spacing={3}>
          {/* Company Selection */}
          <Grid item xs={12} md={6}>
            <Controller
              name="company_id"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Company</InputLabel>
                  <Select {...field} label="Company">
                    <MenuItem value={0} disabled>
                      Select a company
                    </MenuItem>
                    {companies.map((company) => (
                      <MenuItem key={company.id} value={company.id}>
                        {company.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
          </Grid>

          {/* Scope Selection */}
          <Grid item xs={12} md={6}>
            <Controller
              name="scope"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Emission Scope</InputLabel>
                  <Select {...field} label="Emission Scope">
                    <MenuItem value="" disabled>
                      Select a scope
                    </MenuItem>
                    {EMISSION_SCOPES.map((scope) => (
                      <MenuItem key={scope.value} value={scope.value}>
                        {scope.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
          </Grid>

          {/* Activity Type */}
          <Grid item xs={12} md={6}>
            <Controller
              name="activity_type"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Activity Type</InputLabel>
                  <Select {...field} label="Activity Type">
                    <MenuItem value="" disabled>
                      Select an activity type
                    </MenuItem>
                    {ACTIVITY_TYPES.map((type) => (
                      <MenuItem key={type} value={type}>
                        {type}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
          </Grid>

          {/* Activity Amount */}
          <Grid item xs={12} md={3}>
            <Controller
              name="activity_amount"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Activity Amount"
                  type="number"
                  inputProps={{ min: 0, step: 0.01 }}
                />
              )}
            />
          </Grid>

          {/* Activity Unit */}
          <Grid item xs={12} md={3}>
            <Controller
              name="activity_unit"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Unit</InputLabel>
                  <Select {...field} label="Unit">
                    <MenuItem value="" disabled>
                      Select a unit
                    </MenuItem>
                    {UNITS.map((unit) => (
                      <MenuItem key={unit} value={unit}>
                        {unit}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
          </Grid>

          {/* Date Fields */}
          <Grid item xs={12} md={6}>
            <Controller
              name="reporting_period_start"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Reporting Period Start"
                  type="date"
                  InputLabelProps={{ shrink: true }}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Controller
              name="reporting_period_end"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Reporting Period End"
                  type="date"
                  InputLabelProps={{ shrink: true }}
                />
              )}
            />
          </Grid>

          {/* Notes */}
          <Grid item xs={12}>
            <Controller
              name="notes"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Notes (Optional)"
                  multiline
                  rows={3}
                  placeholder="Additional information about this emission record..."
                />
              )}
            />
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          {onCancel && (
            <Button
              variant="outlined"
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>
          )}

          <Button
            type="submit"
            variant="contained"
            disabled={isLoading}
            startIcon={isLoading ? <CircularProgress size={20} /> : null}
          >
            {isLoading ? 'Saving...' : 'Save Emission Record'}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default EmissionEntryForm;
