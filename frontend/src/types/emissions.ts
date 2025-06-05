// export interface FormData {
//   company_id: number;
//   scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3' | '';
//   activity_type: string;
//   activity_amount: number;
//   activity_unit: string;
//   reporting_period_start: string;
//   reporting_period_end: string;
//   notes: string; // ← Make this required to match Yup schema
// }

export interface FormData {
  company_id: number;
  scope: string;
  activity_type: string;
  activity_amount: number;
  activity_unit: string;
  reporting_period_start: string;
  reporting_period_end: string;
  notes: string;
}
// export interface Company {
//   id: number;
//   name: string;
//   industry_sector: string;
//   country: string;
//   reporting_year: number;
// }

export interface Company {
  id: number;
  name: string;
  industry_sector: string;
  country: string;
  reporting_year: number;
}
// export interface EmissionRecord {
//   id: number;
//   company_id: number;
//   scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3';
//   activity_type: string;
//   activity_amount: number;
//   activity_unit: string;
//   calculated_emission: number;
//   emission_unit: string;
//   reporting_period_start: string;
//   reporting_period_end: string;
//   created_at: string;
//   updated_at: string;
// }
export interface EmissionRecord {
  id: number;
  company_id: number;
  scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3';
  activity_type: string;
  activity_amount: number;
  activity_unit: string;
  calculated_emission: number;
  emission_unit: string;
  reporting_period_start: string;
  reporting_period_end: string;
  created_at: string;
  updated_at: string;
}
// export interface DashboardData {
//   totalEmissions: number;
//   scopeBreakdown: {
//     scope1: number;
//     scope2: number;
//     scope3: number;
//   };
//   monthlyTrends: Array<{
//     month: string;
//     emissions: number;
//   }>;
// }
export interface DashboardData {
  totalEmissions: number;
  scopeBreakdown: {
    scope1: number;
    scope2: number;
    scope3: number;
  };
  monthlyTrends: Array<{
    month: string;
    emissions: number;
  }>;
}
// export interface EmissionRecord {
//   id: number;
//   company_id: number;
//   scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3';
//   activity_type: string;
//   activity_amount: number;
//   activity_unit: string;
//   calculated_emission: number;
//   emission_unit: string;
//   reporting_period_start: string;
//   reporting_period_end: string;
//   data_quality_score?: number;
//   verification_status: string;
//   created_at: string;
//   updated_at: string;
// }

// export interface Company {
//   id: number;
//   name: string;
//   industry_sector: string;
//   country: string;
//   reporting_year: number;
//   total_emissions?: number;
// }

export interface EmissionFactor {
  id: number;
  name: string;
  scope: string;
  category: string;
  factor_value: number;
  unit: string;
  source: string;
  region: string;
  year: number;
  uncertainty?: number;
  data_quality: number;
}

// export interface DashboardData {
//   totalEmissions: number;
//   scopeBreakdown: {
//     scope1: number;
//     scope2: number;
//     scope3: number;
//   };
//   monthlyTrends: Array<{
//     month: string;
//     emissions: number;
//   }>;
//   topSources: Array<{
//     source: string;
//     emissions: number;
//     percentage: number;
//   }>;
//   recentRecords: EmissionRecord[];
// }

// export interface FormData {
//   company_id: number;
//   scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3'; // ← More specific type
//   activity_type: string;
//   activity_amount: number;
//   activity_unit: string;
//   reporting_period_start: string; // ← Keep as string for form handling
//   reporting_period_end: string;
//   notes?: string;
// }

