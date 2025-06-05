import axios, { AxiosResponse } from 'axios';
import { EmissionRecord, Company, DashboardData, FormData } from '../types/emissions';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const emissionsAPI = {
  // Emissions
  getAllEmissions: (): Promise<AxiosResponse<EmissionRecord[]>> =>
    apiClient.get('/api/emissions'),
  
  getEmissionById: (id: number): Promise<AxiosResponse<EmissionRecord>> =>
    apiClient.get(`/api/emissions/${id}`),
  
  createEmission: (data: FormData): Promise<AxiosResponse<EmissionRecord>> =>
    apiClient.post('/api/emissions', data),
  
  updateEmission: (id: number, data: Partial<FormData>): Promise<AxiosResponse<EmissionRecord>> =>
    apiClient.put(`/api/emissions/${id}`, data),
  
  deleteEmission: (id: number): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/api/emissions/${id}`),

  // Dashboard
  getDashboardData: (): Promise<AxiosResponse<DashboardData>> =>
    apiClient.get('/api/dashboard'),

  // Companies
  getCompanies: (): Promise<AxiosResponse<Company[]>> =>
    apiClient.get('/api/companies'),
  
  getCompanyById: (id: number): Promise<AxiosResponse<Company>> =>
    apiClient.get(`/api/companies/${id}`),

  // Export
  exportData: (format: 'csv' | 'xlsx' | 'pdf', filters?: any): Promise<AxiosResponse<Blob>> =>
    apiClient.get('/api/export', {
      params: { format, ...filters },
      responseType: 'blob'
    }),

  // Data quality
  validateData: (data: any): Promise<AxiosResponse<any>> =>
    apiClient.post('/api/validate', data),
};

export default apiClient;
