export const EMISSION_SCOPES = [
  { value: 'SCOPE_1', label: 'Scope 1 - Direct Emissions' },
  { value: 'SCOPE_2', label: 'Scope 2 - Indirect Emissions' },
  { value: 'SCOPE_3', label: 'Scope 3 - Value Chain Emissions' }
];

export const ACTIVITY_TYPES = [
  'Stationary Combustion',
  'Mobile Combustion',
  'Electricity Consumption',
  'Business Travel',
  'Employee Commuting',
  'Waste Generation',
  'Water Usage'
];

export const UNITS = [
  'kg CO2e',
  'tonnes CO2e',
  'kWh',
  'MWh',
  'liters',
  'gallons',
  'miles',
  'kilometers'
];

export const CHART_COLORS = {
  scope1: '#FF6B6B',
  scope2: '#4ECDC4',
  scope3: '#45B7D1',
  primary: '#6C5CE7',
  secondary: '#A8E6CF',
  warning: '#FFA726',
  error: '#EF5350',
  success: '#66BB6A'
};

export const API_ENDPOINTS = {
  EMISSIONS: '/api/emissions',
  COMPANIES: '/api/companies',
  DASHBOARD: '/api/dashboard',
  EXPORT: '/api/export',
  WEBSOCKET: '/ws'
};
