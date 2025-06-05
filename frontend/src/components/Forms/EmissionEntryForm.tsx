import React, { useState, useEffect, useCallback } from 'react';
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
  Chip,
  Divider,
  IconButton,
  Tooltip,
  Snackbar,
} from '@mui/material';
import {
  Save as SaveIcon,
  Clear as ClearIcon,
  Calculate as CalculateIcon,
  Info as InfoIcon,
  AutoMode as AutoModeIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format, parseISO, isValid } from 'date-fns';
import { FormData, Company, EmissionFactor } from '../../types/emissions';
import { EMISSION_SCOPES, ACTIVITY_TYPES, UNITS } from '../../utils/constants';

// Enhanced validation schema
const schema = yup.object({
  company_id: yup.number().positive('Please select a company').required('Company is required'),
  scope: yup.string().oneOf(['SCOPE_1', 'SCOPE_2', 'SCOPE_3'], 'Invalid scope').required('Scope is required'),
  activity_type: yup.string().required('Activity type is required'),
  activity_amount: yup.number()
    .positive('Amount must be positive')
    .max(1000000, 'Amount seems too large')
    .required('Amount is required'),
  activity_unit: yup.string().required('Unit is required'),
  reporting_period_start: yup.date().required('Start date is required'),
  reporting_period_end: yup.date()
    .required('End date is required')
    .test('is-after-start', 'End date must be after start date', function(value) {
      const { reporting_period_start } = this.parent;
      if (!reporting_period_start || !value) return true;
      return new Date(value) > new Date(reporting_period_start);
    }),
  notes: yup.string().max(500, 'Notes must be less than 500 characters'),
});

interface EmissionCalculation {
  emission: number;
  factor: number;
  factorSource: string;
  uncertainty?: number;
  confidence: 'high' | 'medium' | 'low';
}

interface EmissionEntryFormProps {
  companies: Company[];
  onSubmit: (data: FormData) => void;
  onCancel?: () => void;
  initialData?: Partial<FormData>;
  isLoading?: boolean;
  emissionFactors?: EmissionFactor[];
}

export const EmissionEntryForm: React.FC<EmissionEntryFormProps> = ({
  companies,
  onSubmit,
  onCancel,
  initialData,
  isLoading = false,
  emissionFactors = []
}) => {
  const [calculatedEmission, setCalculatedEmission] = useState<EmissionCalculation | null>(null);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [draftSaved, setDraftSaved] = useState(false);
  const [calculationLoading, setCalculationLoading] = useState(false);
  const [showCalculationDetails, setShowCalculationDetails] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors, isDirty, isValid: formIsValid },
    reset,
    getValues,
    setValue,
    trigger,
  } = useForm<FormData>({
    resolver: yupResolver(schema),
    mode: 'onChange',
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

  // Watch form values for auto-calculation and validation
  const watchedValues = watch(['activity_amount', 'activity_type', 'scope', 'activity_unit']);
  const [amount, activityType, scope, unit] = watchedValues;

  // Auto-save functionality with debouncing
  useEffect(() => {
    if (autoSaveEnabled && isDirty && formIsValid) {
      const timer = setTimeout(() => {
        const values = getValues();
        try {
          localStorage.setItem('emission_form_draft', JSON.stringify({
            ...values,
            timestamp: new Date().toISOString()
          }));
          setDraftSaved(true);
          setTimeout(() => setDraftSaved(false), 2000);
        } catch (error) {
          console.error('Error saving draft:', error);
        }
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [watchedValues, isDirty, formIsValid, autoSaveEnabled, getValues]);

  // Enhanced emission calculation with multiple factors
  const calculateEmissions = useCallback(async (
    amount: number,
    activityType: string,
    scope: string,
    unit: string
  ) => {
    if (amount <= 0 || !activityType || !scope || !unit) {
      setCalculatedEmission(null);
      return;
    }

    setCalculationLoading(true);

    try {
      // Find matching emission factor from props or use mock data
      let factor = emissionFactors.find(f => 
        f.category === activityType && 
        f.scope === scope &&
        f.unit.toLowerCase().includes(unit.toLowerCase())
      );

      if (!factor) {
        // Use mock factors if no real factors available
        factor = getMockEmissionFactor(activityType, scope, unit);
      }

      if (factor) {
        const emission = amount * factor.factor_value;
        const uncertainty = factor.uncertainty || 10;
        
        const calculation: EmissionCalculation = {
          emission,
          factor: factor.factor_value,
          factorSource: factor.source || 'Mock Data',
          uncertainty,
          confidence: uncertainty < 5 ? 'high' : uncertainty < 15 ? 'medium' : 'low'
        };

        setCalculatedEmission(calculation);
      } else {
        setCalculatedEmission(null);
        setSnackbarMessage('No emission factor found for this activity');
        setSnackbarOpen(true);
      }
    } catch (error) {
      console.error('Error calculating emissions:', error);
      setSnackbarMessage('Error calculating emissions');
      setSnackbarOpen(true);
    } finally {
      setCalculationLoading(false);
    }
  }, [emissionFactors]);

  // Trigger calculation when relevant fields change
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      calculateEmissions(amount, activityType, scope, unit);
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [amount, activityType, scope, unit, calculateEmissions]);

  // Load draft from localStorage on component mount
  useEffect(() => {
    const draft = localStorage.getItem('emission_form_draft');
    if (draft && !initialData) {
      try {
        const parsedDraft = JSON.parse(draft);
        const draftAge = new Date().getTime() - new Date(parsedDraft.timestamp || 0).getTime();
        
        // Only load draft if it's less than 24 hours old
        if (draftAge < 24 * 60 * 60 * 1000) {
          const { timestamp, ...draftData } = parsedDraft;
          reset(draftData);
          setSnackbarMessage('Draft loaded from previous session');
          setSnackbarOpen(true);
        } else {
          localStorage.removeItem('emission_form_draft');
        }
      } catch (error) {
        console.error('Error loading draft:', error);
        localStorage.removeItem('emission_form_draft');
      }
    }
  }, [reset, initialData]);

  const getMockEmissionFactor = (activityType: string, scope: string, unit: string) => {
    // Enhanced mock emission factors with realistic values
    const mockFactors: Record<string, { factor: number; source: string; uncertainty: number }> = {
      'Stationary Combustion': { factor: 0.2034, source: 'EPA', uncertainty: 5 },
      'Mobile Combustion': { factor: 0.3142, source: 'DEFRA', uncertainty: 8 },
      'Electricity Consumption': { factor: 0.4091, source: 'eGRID', uncertainty: 12 },
      'Business Travel': { factor: 0.1521, source: 'IPCC', uncertainty: 15 },
      'Employee Commuting': { factor: 0.1203, source: 'EPA', uncertainty: 20 },
      'Waste Generation': { factor: 0.0543, source: 'EPA', uncertainty: 25 },
      'Water Usage': { factor: 0.0234, source: 'Local Authority', uncertainty: 30 },
    };

    const mockData = mockFactors[activityType] || { factor: 0.2, source: 'Default', uncertainty: 50 };
    
    return {
      id: 0,
      name: `${activityType} - ${scope}`,
      scope,
      category: activityType,
      factor_value: mockData.factor,
      unit: 'kg CO2e/unit',
      source: mockData.source,
      region: 'Default',
      year: new Date().getFullYear(),
      uncertainty: mockData.uncertainty,
      data_quality: 3.0,
    };
  };

  const onFormSubmit = (data: FormData) => {
    // Add calculated emission to form data
    const submissionData = {
      ...data,
      calculated_emission: calculatedEmission?.emission || 0,
    };
    
    onSubmit(submissionData);
    localStorage.removeItem('emission_form_draft');
  };

  const clearDraft = () => {
    localStorage.removeItem('emission_form_draft');
    reset();
    setCalculatedEmission(null);
    setSnackbarMessage('Form cleared');
    setSnackbarOpen(true);
  };

  const fillSampleData = () => {
    const sampleData = {
      company_id: companies[0]?.id || 1,
      scope: 'SCOPE_1',
      activity_type: 'Stationary Combustion',
      activity_amount: 1000,
      activity_unit: 'kWh',
      reporting_period_start: format(new Date(new Date().getFullYear(), 0, 1), 'yyyy-MM-dd'),
      reporting_period_end: format(new Date(new Date().getFullYear(), 11, 31), 'yyyy-MM-dd'),
      notes: 'Sample emission record for testing purposes',
    };

    Object.entries(sampleData).forEach(([key, value]) => {
      setValue(key as keyof FormData, value);
    });
    
    trigger(); // Trigger validation
    setSnackbarMessage('Sample data filled');
    setSnackbarOpen(true);
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Paper elevation={3} sx={{ p: 3, maxWidth: 900, mx: 'auto' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h2">
            Add Emission Record
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Tooltip title="Auto-save enabled">
              <Chip
                icon={<AutoModeIcon />}
                label={draftSaved ? 'Saved' : 'Auto-save'}
                color={draftSaved ? 'success' : 'default'}
                size="small"
                variant={autoSaveEnabled ? 'filled' : 'outlined'}
              />
            </Tooltip>
            <Button size="small" onClick={fillSampleData} variant="outlined">
              Sample Data
            </Button>
          </Box>
        </Box>

        {calculatedEmission && (
          <Alert 
            severity="info" 
            sx={{ mb: 2 }}
            action={
              <IconButton
                color="inherit"
                size="small"
                onClick={() => setShowCalculationDetails(!showCalculationDetails)}
              >
                <InfoIcon />
              </IconButton>
            }
          >
            <Box>
              <Typography variant="body2">
                <strong>Estimated Emission: {calculatedEmission.emission.toFixed(2)} kg CO2e</strong>
              </Typography>
              {showCalculationDetails && (
                <Box sx={{ mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="caption" display="block">
                    Factor: {calculatedEmission.factor} kg CO2e/unit
                  </Typography>
                  <Typography variant="caption" display="block">
                    Source: {calculatedEmission.factorSource}
                  </Typography>
                  <Typography variant="caption" display="block">
                    Confidence: {calculatedEmission.confidence}
                    {calculatedEmission.uncertainty && ` (±${calculatedEmission.uncertainty}%)`}
                  </Typography>
                </Box>
              )}
            </Box>
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onFormSubmit)}>
          <Grid container spacing={3}>
            {/* Company Selection */}
            <Grid item xs={12} md={6}>
              <Controller
                name="company_id"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.company_id}>
                    <InputLabel>Company *</InputLabel>
                    <Select {...field} label="Company *">
                      <MenuItem value={0} disabled>
                        <em>Select a company</em>
                      </MenuItem>
                      {companies.map((company) => (
                        <MenuItem key={company.id} value={company.id}>
                          {company.name} ({company.country})
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>{errors.company_id?.message}</FormHelperText>
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
                  <FormControl fullWidth error={!!errors.scope}>
                    <InputLabel>Emission Scope *</InputLabel>
                    <Select {...field} label="Emission Scope *">
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

            {/* Activity Type */}
            <Grid item xs={12} md={6}>
              <Controller
                name="activity_type"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.activity_type}>
                    <InputLabel>Activity Type *</InputLabel>
                    <Select {...field} label="Activity Type *">
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

            {/* Activity Amount */}
            <Grid item xs={12} md={3}>
              <Controller
                name="activity_amount"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Activity Amount *"
                    type="number"
                    error={!!errors.activity_amount}
                    helperText={errors.activity_amount?.message}
                    inputProps={{ min: 0, step: 0.01 }}
                    InputProps={{
                      endAdornment: calculationLoading && <CircularProgress size={20} />,
                    }}
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
                  <FormControl fullWidth error={!!errors.activity_unit}>
                    <InputLabel>Unit *</InputLabel>
                    <Select {...field} label="Unit *">
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

            {/* Date Range */}
            <Grid item xs={12} md={6}>
              <Controller
                name="reporting_period_start"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    label="Reporting Period Start *"
                    value={field.value ? new Date(field.value) : null}
                    onChange={(date) => {
                      field.onChange(date ? format(date, 'yyyy-MM-dd') : '');
                    }}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: !!errors.reporting_period_start,
                        helperText: errors.reporting_period_start?.message,
                      },
                    }}
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
                    label="Reporting Period End *"
                    value={field.value ? new Date(field.value) : null}
                    onChange={(date) => {
                      field.onChange(date ? format(date, 'yyyy-MM-dd') : '');
                    }}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: !!errors.reporting_period_end,
                        helperText: errors.reporting_period_end?.message,
                      },
                    }}
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
                    error={!!errors.notes}
                    helperText={errors.notes?.message}
                  />
                )}
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                onClick={clearDraft}
                disabled={isLoading}
                startIcon={<ClearIcon />}
              >
                Clear Form
              </Button>
              {onCancel && (
                <Button
                  variant="outlined"
                  onClick={onCancel}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
              )}
            </Box>

            <Button
              type="submit"
              variant="contained"
              disabled={isLoading || !formIsValid}
              startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
              size="large"
            >
              {isLoading ? 'Saving...' : 'Save Emission Record'}
            </Button>
          </Box>
        </Box>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbarOpen}
          autoHideDuration={3000}
          onClose={() => setSnackbarOpen(false)}
          message={snackbarMessage}
        />
      </Paper>
    </LocalizationProvider>
  );
};

export default EmissionEntryForm;
