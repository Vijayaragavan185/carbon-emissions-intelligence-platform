import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Save,
  Send,
  Preview,
  ExpandMore,
  CheckCircle,
  Warning,
  Error as ErrorIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import { ESGApiService } from '../../services/esgApi';
import { ESGValidationService } from '../../services/esgValidation';

interface ESGReportFormProps {
  reportId?: number;
  onSave?: (reportId: number) => void;
  onSubmit?: (reportId: number) => void;
}

interface ReportData {
  id?: number;
  report_name: string;
  framework: string;
  company_id: number;
  reporting_period_start: Date;
  reporting_period_end: Date;
  report_data: Record<string, any>;
  status?: string;
  compliance_score?: number;
}

interface ValidationResult {
  valid: boolean;
  score: number;
  errors: string[];
  warnings: string[];
  completeness?: number;
}

const frameworks = [
  { value: 'cdp', label: 'CDP (Carbon Disclosure Project)' },
  { value: 'tcfd', label: 'TCFD (Task Force on Climate-related Financial Disclosures)' },
  { value: 'eu_taxonomy', label: 'EU Taxonomy Regulation' }
];

const ESGReportForm: React.FC<ESGReportFormProps> = ({ reportId, onSave, onSubmit }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [reportData, setReportData] = useState<ReportData>({
    report_name: '',
    framework: '',
    company_id: 1, // Would come from context
    reporting_period_start: new Date(),
    reporting_period_end: new Date(),
    report_data: {}
  });
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false);

  const esgApi = new ESGApiService();
  const validator = new ESGValidationService();

  const steps = [
    'Basic Information',
    'Framework Configuration', 
    'Data Entry',
    'Validation & Review',
    'Submit for Approval'
  ];

  useEffect(() => {
    if (reportId) {
      loadReport();
    }
  }, [reportId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const response = await esgApi.getReportDetail(reportId!);
      if (response.success) {
        setReportData({
          ...response.report,
          reporting_period_start: new Date(response.report.reporting_period.start),
          reporting_period_end: new Date(response.report.reporting_period.end)
        });
      }
    } catch (err) {
      setError('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: keyof ReportData, value: any) => {
    setReportData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleReportDataChange = (section: string, field: string, value: any) => {
    setReportData(prev => ({
      ...prev,
      report_data: {
        ...prev.report_data,
        [section]: {
          ...prev.report_data[section],
          [field]: value
        }
      }
    }));
  };

  const validateReport = async () => {
    try {
      setLoading(true);
      const result = await validator.validateReportData(reportData.framework, reportData.report_data);
      setValidationResult(result);
      return result.valid;
    } catch (err) {
      setError('Validation failed');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const saveReport = async () => {
    try {
      setSaving(true);
      setError(null);

      const payload = {
        report_name: reportData.report_name,
        framework: reportData.framework,
        company_id: reportData.company_id,
        reporting_period_start: reportData.reporting_period_start.toISOString(),
        reporting_period_end: reportData.reporting_period_end.toISOString(),
        report_data: reportData.report_data
      };

      let response;
      if (reportId) {
        response = await esgApi.updateReport(reportId, payload);
      } else {
        response = await esgApi.createReport(payload);
      }

      if (response.success) {
        setReportData(prev => ({ ...prev, id: response.report_id || reportId }));
        onSave?.(response.report_id || reportId!);
      } else {
        setError('Failed to save report');
      }
    } catch (err) {
      setError('Save operation failed');
    } finally {
      setSaving(false);
    }
  };

  const submitForApproval = async () => {
    try {
      setLoading(true);
      
      // Validate first
      const isValid = await validateReport();
      if (!isValid) {
        setError('Please fix validation errors before submitting');
        return;
      }

      // Save before submitting
      await saveReport();

      // Submit for approval
      const response = await esgApi.submitForApproval(reportData.id!);
      if (response.success) {
        onSubmit?.(reportData.id!);
        setSubmitDialogOpen(false);
      } else {
        setError('Failed to submit for approval');
      }
    } catch (err) {
      setError('Submission failed');
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (activeStep === 3) {
      // Validation step
      await validateReport();
    }
    setActiveStep(prev => Math.min(prev + 1, steps.length - 1));
  };

  const handleBack = () => {
    setActiveStep(prev => Math.max(prev - 1, 0));
  };

  const renderBasicInformation = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <TextField
          fullWidth
          label="Report Name"
          value={reportData.report_name}
          onChange={(e) => handleFieldChange('report_name', e.target.value)}
          required
          placeholder="e.g., 2024 Annual CDP Climate Report"
        />
      </Grid>
      
      <Grid item xs={12} md={6}>
        <FormControl fullWidth required>
          <InputLabel>ESG Framework</InputLabel>
          <Select
            value={reportData.framework}
            onChange={(e) => handleFieldChange('framework', e.target.value)}
            label="ESG Framework"
          >
            {frameworks.map(fw => (
              <MenuItem key={fw.value} value={fw.value}>
                {fw.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>

      <Grid item xs={12} md={6}>
        <TextField
          fullWidth
          label="Company ID"
          type="number"
          value={reportData.company_id}
          onChange={(e) => handleFieldChange('company_id', parseInt(e.target.value))}
          required
        />
      </Grid>

      <Grid item xs={12} md={6}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DatePicker
            label="Reporting Period Start"
            value={reportData.reporting_period_start}
            onChange={(date) => handleFieldChange('reporting_period_start', date)}
            renderInput={(params) => <TextField {...params} fullWidth required />}
          />
        </LocalizationProvider>
      </Grid>

      <Grid item xs={12} md={6}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DatePicker
            label="Reporting Period End"
            value={reportData.reporting_period_end}
            onChange={(date) => handleFieldChange('reporting_period_end', date)}
            renderInput={(params) => <TextField {...params} fullWidth required />}
          />
        </LocalizationProvider>
      </Grid>
    </Grid>
  );

  const renderFrameworkConfiguration = () => {
    if (!reportData.framework) {
      return (
        <Alert severity="warning">
          Please select a framework in the previous step
        </Alert>
      );
    }

    const frameworkInfo = frameworks.find(fw => fw.value === reportData.framework);

    return (
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="h6">{frameworkInfo?.label}</Typography>
          <Typography variant="body2" mt={1}>
            {reportData.framework === 'cdp' && 
              'The CDP framework focuses on climate change governance, strategy, risk management, and metrics & targets.'
            }
            {reportData.framework === 'tcfd' && 
              'TCFD provides a framework for climate-related financial disclosures across four pillars.'
            }
            {reportData.framework === 'eu_taxonomy' && 
              'EU Taxonomy regulation establishes criteria for environmentally sustainable economic activities.'
            }
          </Typography>
        </Alert>

        <Typography variant="h6" gutterBottom>
          Framework-Specific Configuration
        </Typography>
        
        {/* Framework-specific configuration would go here */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Disclosure Year"
              type="number"
              value={new Date().getFullYear()}
              disabled
            />
          </Grid>
          
          {reportData.framework === 'cdp' && (
            <>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Questionnaire Type</InputLabel>
                  <Select defaultValue="climate_change" label="Questionnaire Type">
                    <MenuItem value="climate_change">Climate Change</MenuItem>
                    <MenuItem value="water_security">Water Security</MenuItem>
                    <MenuItem value="forests">Forests</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </>
          )}
          
          {reportData.framework === 'tcfd' && (
            <>
              <Grid item xs={12}>
                <Alert severity="info">
                  TCFD reporting covers four key areas: Governance, Strategy, Risk Management, and Metrics & Targets
                </Alert>
              </Grid>
            </>
          )}
        </Grid>
      </Box>
    );
  };

  const renderDataEntry = () => {
    if (!reportData.framework) {
      return (
        <Alert severity="warning">
          Please configure the framework first
        </Alert>
      );
    }

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Data Entry - {reportData.framework.toUpperCase()}
        </Typography>
        
        {/* CDP Data Entry */}
        {reportData.framework === 'cdp' && (
          <Box>
            {['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7'].map(section => (
              <Accordion key={section} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    {section}: {section === 'C1' ? 'Governance' : 
                               section === 'C2' ? 'Risks & Opportunities' :
                               section === 'C3' ? 'Business Strategy' :
                               section === 'C4' ? 'Targets & Performance' :
                               section === 'C5' ? 'Emissions Methodology' :
                               section === 'C6' ? 'Emissions Data' :
                               'Emissions Breakdown'}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    {section === 'C6' && (
                      <>
                        <Grid item xs={12} md={4}>
                          <TextField
                            fullWidth
                            label="Scope 1 Emissions (tCO2e)"
                            type="number"
                            value={reportData.report_data[section]?.scope_1_emissions || ''}
                            onChange={(e) => handleReportDataChange(section, 'scope_1_emissions', parseFloat(e.target.value))}
                          />
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            fullWidth
                            label="Scope 2 Emissions (tCO2e)"
                            type="number"
                            value={reportData.report_data[section]?.scope_2_emissions || ''}
                            onChange={(e) => handleReportDataChange(section, 'scope_2_emissions', parseFloat(e.target.value))}
                          />
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            fullWidth
                            label="Scope 3 Emissions (tCO2e)"
                            type="number"
                            value={reportData.report_data[section]?.scope_3_emissions || ''}
                            onChange={(e) => handleReportDataChange(section, 'scope_3_emissions', parseFloat(e.target.value))}
                          />
                        </Grid>
                      </>
                    )}
                    
                    {section === 'C4' && (
                      <>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Emission Reduction Target (%)"
                            type="number"
                            value={reportData.report_data[section]?.reduction_target || ''}
                            onChange={(e) => handleReportDataChange(section, 'reduction_target', parseFloat(e.target.value))}
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Target Year"
                            type="number"
                            value={reportData.report_data[section]?.target_year || ''}
                            onChange={(e) => handleReportDataChange(section, 'target_year', parseInt(e.target.value))}
                          />
                        </Grid>
                      </>
                    )}
                    
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Additional Notes"
                        multiline
                        rows={3}
                        value={reportData.report_data[section]?.notes || ''}
                        onChange={(e) => handleReportDataChange(section, 'notes', e.target.value)}
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        {/* TCFD Data Entry */}
        {reportData.framework === 'tcfd' && (
          <Box>
            {['governance', 'strategy', 'risk_management', 'metrics_targets'].map(pillar => (
              <Accordion key={pillar} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    {pillar.replace('_', ' & ').toUpperCase()}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label={`${pillar} Description`}
                        multiline
                        rows={4}
                        value={reportData.report_data[pillar]?.description || ''}
                        onChange={(e) => handleReportDataChange(pillar, 'description', e.target.value)}
                        placeholder={`Describe your ${pillar.replace('_', ' ')} approach...`}
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        {/* EU Taxonomy Data Entry */}
        {reportData.framework === 'eu_taxonomy' && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Total Revenue (€)"
                  type="number"
                  value={reportData.report_data.total_revenue || ''}
                  onChange={(e) => handleReportDataChange('', 'total_revenue', parseFloat(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Total CapEx (€)"
                  type="number"
                  value={reportData.report_data.total_capex || ''}
                  onChange={(e) => handleReportDataChange('', 'total_capex', parseFloat(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Total OpEx (€)"
                  type="number"
                  value={reportData.report_data.total_opex || ''}
                  onChange={(e) => handleReportDataChange('', 'total_opex', parseFloat(e.target.value))}
                />
              </Grid>
            </Grid>
          </Box>
        )}
      </Box>
    );
  };

  const renderValidationReview = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Validation & Review
      </Typography>
      
      {loading && (
        <Box mb={2}>
          <LinearProgress />
          <Typography variant="body2" color="textSecondary" mt={1}>
            Validating report data...
          </Typography>
        </Box>
      )}

      {validationResult && (
        <Box mb={3}>
          <Alert 
            severity={validationResult.valid ? 'success' : 'error'}
            icon={validationResult.valid ? <CheckCircle /> : <ErrorIcon />}
          >
            <Typography variant="h6">
              Validation {validationResult.valid ? 'Passed' : 'Failed'}
            </Typography>
            <Typography variant="body2" mt={1}>
              Compliance Score: {validationResult.score}%
              {validationResult.completeness && ` • Completeness: ${validationResult.completeness}%`}
            </Typography>
          </Alert>

          {validationResult.errors.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2" color="error" gutterBottom>
                Errors that must be fixed:
              </Typography>
              {validationResult.errors.map((error, index) => (
                <Chip
                  key={index}
                  label={error}
                  color="error"
                  variant="outlined"
                  size="small"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          )}

          {validationResult.warnings.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2" color="warning.main" gutterBottom>
                Warnings:
              </Typography>
              {validationResult.warnings.map((warning, index) => (
                <Chip
                  key={index}
                  label={warning}
                  color="warning"
                  variant="outlined"
                  size="small"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          )}
        </Box>
      )}

      <Box display="flex" gap={2}>
        <Button
          variant="outlined"
          onClick={validateReport}
          disabled={loading}
        >
          Re-validate
        </Button>
        <Button
          variant="outlined"
          startIcon={<Preview />}
          onClick={() => setPreviewOpen(true)}
        >
          Preview Report
        </Button>
      </Box>
    </Box>
  );

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            {reportId ? 'Edit ESG Report' : 'Create New ESG Report'}
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((label, index) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
                <StepContent>
                  <Box mb={2}>
                    {index === 0 && renderBasicInformation()}
                    {index === 1 && renderFrameworkConfiguration()}
                    {index === 2 && renderDataEntry()}
                    {index === 3 && renderValidationReview()}
                    {index === 4 && (
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          Submit for Approval
                        </Typography>
                        <Typography variant="body2" color="textSecondary" mb={2}>
                          Your report will be submitted to the approval workflow. 
                          Make sure all data is accurate as changes will require re-approval.
                        </Typography>
                        <Button
                          variant="contained"
                          color="primary"
                          startIcon={<Send />}
                          onClick={() => setSubmitDialogOpen(true)}
                          disabled={!validationResult?.valid}
                        >
                          Submit for Approval
                        </Button>
                      </Box>
                    )}
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Box display="flex" gap={1}>
                      <Button
                        disabled={index === 0}
                        onClick={handleBack}
                      >
                        Back
                      </Button>
                      {index < steps.length - 1 && (
                        <Button
                          variant="contained"
                          onClick={handleNext}
                          disabled={
                            (index === 0 && (!reportData.report_name || !reportData.framework)) ||
                            (index === 3 && validationResult && !validationResult.valid)
                          }
                        >
                          Next
                        </Button>
                      )}
                      <Button
                        variant="outlined"
                        startIcon={<Save />}
                        onClick={saveReport}
                        disabled={saving || !reportData.report_name || !reportData.framework}
                      >
                        {saving ? 'Saving...' : 'Save Draft'}
                      </Button>
                    </Box>
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Submit Confirmation Dialog */}
      <Dialog open={submitDialogOpen} onClose={() => setSubmitDialogOpen(false)}>
        <DialogTitle>Submit Report for Approval</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to submit this report for approval? 
            Once submitted, the report will enter the approval workflow and cannot be edited until approved or returned for changes.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSubmitDialogOpen(false)}>Cancel</Button>
          <Button onClick={submitForApproval} variant="contained" disabled={loading}>
            {loading ? 'Submitting...' : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Preview Dialog would go here */}
    </Box>
  );
};

export default ESGReportForm;
