import React, { useState, useEffect } from 'react';
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
  Alert,
  CircularProgress,
  FormHelperText,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { FormData, Company } from '../../types/emissions';
import { EMISSION_SCOPES, ACTIVITY_TYPES, UNITS } from '../../utils/constants';
import { useEmissionsData } from '../../hooks/useEmissionsData';

const schema = yup.object({
  company_id: yup.number().required('Company is required'),
  scope: yup.string().required('Scope is required'),
  activity_type: yup.string().required('Activity type is required'),
  activity_amount: yup.number().positive('Amount must be positive').required('Amount is required'),
  activity_unit: yup.string().required('Unit is required'),
  reporting_period_start: yup.date().required('Start date is required'),
  reporting_period_end: yup.date().required('End date is required'),
  notes: yup.string(),
});

interface EmissionEntryFormProps {
  companies: Company[];
  onSubmit: (data: FormData) => void;
  initialData?: Partial<FormData>;
  isLoading?: boolean;
}

export const EmissionEntryForm: React.FC<EmissionEntryFormProps> = ({
  companies,
  onSubmit,
  initialData,
  isLoading = false
}) => {
  const [calculatedEmission, setCalculatedEmission] = useState<number | null>(null);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors, isDirty },
    reset,
    getValues,
  } = useForm<FormData>({
    resolver: yupResolver(schema),
    defaultValues: initialData || {
      company_id: 0,
      scope: '',
      activity_type: '',
      activity_amount: 0,
      activity_unit: '',
      reporting_period_start: '',
      reporting_period_end: '',
      notes: '',
    },
  });

  // Watch form values for auto-calculation
  const watchedValues = watch(['activity_amount', 'activity_type', 'scope']);

  // Auto-save functionality
  useEffect(() => {
    if (autoSaveEnabled && isDirty) {
      const timer = setTimeout(() => {
        const values = getValues();
        localStorage.setItem('emission_form_draft', JSON.stringify(values));
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [watchedValues, isDirty, autoSaveEnabled, getValues]);

  // Calculate emissions based on activity
  useEffect(() => {
    const [amount, activityType, scope] = watchedValues;
    if (amount > 0 && activityType && scope) {
      // Mock calculation - in real app, this would call an API
      const mockFactor = getEmissionFactor(activityType, scope);
      setCalculatedEmission(amount * mockFactor);
    } else {
      setCalculatedEmission(null);
    }
  }, [watchedValues]);

  // Load draft from localStorage
  useEffect(() => {
    const draft = localStorage.getItem('emission_form_draft');
    if (draft && !initialData) {
      try {
        const parsedDraft = JSON.parse(draft);
        reset(parsedDraft);
      } catch (error) {
        console.error('Error loading draft:', error);
      }
    }
  }, [reset, initialData]);

  const getEmissionFactor = (activityType: string, scope: string): number => {
    // Mock emission factors - in real app, fetch from API
    const factors: Record<string, number> = {
      'Stationary Combustion': 0.2,
      'Mobile Combustion': 0.3,
      'Electricity Consumption': 0.4,
      'Business Travel': 0.15,
      'Employee Commuting': 0.1,
      'Waste Generation': 0.05,
      'Water Usage': 0.02,
    };
    return factors[activityType] || 0.2;
  };

  const onFormSubmit = (data: FormData) => {
    onSubmit(data);
    localStorage.removeItem('emission_form_draft');
  };

  const clearDraft = () => {
    localStorage.removeItem('emission_form_draft');
    reset();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Paper elevation={3} sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
        <Typography variant="h5" gutterBottom>
          Add Emission Record
        </Typography>

        {calculatedEmission && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Estimated Emission: {calculatedEmission.toFixed(2)} kg CO2e
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onFormSubmit)}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Controller
                name="company_id"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.company_id}>
                    <InputLabel>Company</InputLabel>
                    <Select {...field} label="Company">
                      {companies.map((company) => (
                        <MenuItem key={company.id} value={company.id}>
                          {company.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>{errors.company_id?.message}</FormHelperText>
                  </FormControl>
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="scope"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.scope}>
                    <InputLabel>Emission Scope</InputLabel>
                    <Select {...field} label="Emission Scope">
                      {EMISSION_SCOPES.map((scope) => (
                        <MenuItem key={scope.value} value={scope.value}>
                          {scope.label}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>{errors.scope?.message}</FormHelperText>
                  </FormControl>
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="activity_type"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.activity_type}>
                    <InputLabel>Activity Type</InputLabel>
                    <Select {...field} label="Activity Type">
                      {ACTIVITY_TYPES.map((type) => (
                        <MenuItem key={type} value={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>{errors.activity_type?.message}</FormHelperText>
                  </FormControl>
                )}
              />
            </Grid>

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
                    error={!!errors.activity_amount}
                    helperText={errors.activity_amount?.message}
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <Controller
                name="activity_unit"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.activity_unit}>
                    <InputLabel>Unit</InputLabel>
                    <Select {...field} label="Unit">
                      {UNITS.map((unit) => (
                        <MenuItem key={unit} value={unit}>
                          {unit}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>{errors.activity_unit?.message}</FormHelperText>
                  </FormControl>
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="reporting_period_start"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    label="Reporting Period Start"
                    value={field.value ? new Date(field.value) : null}
                    onChange={(date) => field.onChange(date?.toISOString().split('T')[0])}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={!!errors.reporting_period_start}
                        helperText={errors.reporting_period_start?.message}
                      />
                    )}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="reporting_period_end"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    label="Reporting Period End"
                    value={field.value ? new Date(field.value) : null}
                    onChange={(date) => field.onChange(date?.toISOString().split('T')[0])}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={!!errors.reporting_period_end}
                        helperText={errors.reporting_period_end?.message}
                      />
                    )}
                  />
                )}
              />
            </Grid>

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
            <Button
              variant="outlined"
              onClick={clearDraft}
              disabled={isLoading}
            >
              Clear Form
            </Button>

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
    </LocalizationProvider>
  );
};
