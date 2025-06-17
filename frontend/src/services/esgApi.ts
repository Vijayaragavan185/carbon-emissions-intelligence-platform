class ESGApiService {
  private baseUrl = '/api/esg';

  async getDashboardOverview(params: {
    company_id?: number;
    time_period?: string;
  }): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params.company_id) searchParams.append('company_id', params.company_id.toString());
    if (params.time_period) searchParams.append('time_period', params.time_period);
    
    const response = await fetch(`${this.baseUrl}/dashboard/overview?${searchParams}`);
    return response.json();
  }

  async getReports(params: {
    company_id?: number;
    framework?: string;
    status_filter?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<any> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.append(key, value.toString());
    });
    
    const response = await fetch(`${this.baseUrl}/reports?${searchParams}`);
    return response.json();
  }

  async getReportDetail(reportId: number): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports/${reportId}`);
    return response.json();
  }

  async createReport(reportData: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reportData)
    });
    return response.json();
  }

  async updateReport(reportId: number, reportData: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports/${reportId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reportData)
    });
    return response.json();
  }

  async submitForApproval(reportId: number): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports/${reportId}/submit`, {
      method: 'POST'
    });
    return response.json();
  }

  async approveReport(reportId: number, approvalData: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports/${reportId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(approvalData)
    });
    return response.json();
  }

  async exportToPdf(reportId: number, options: any = {}): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports/${reportId}/export/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options)
    });
    return response.json();
  }

  async publishToExternalPlatforms(reportId: number, publicationData: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports/${reportId}/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(publicationData)
    });
    return response.json();
  }

  async getAuditTrail(reportId: number, params: any = {}): Promise<any> {
    const searchParams = new URLSearchParams(params);
    const response = await fetch(`${this.baseUrl}/reports/${reportId}/audit-trail?${searchParams}`);
    return response.json();
  }

  async getPendingApprovals(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/pending-approvals`);
    return response.json();
  }

  async validateReportData(framework: string, data: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ framework, data })
    });
    return response.json();
  }

  async getIntegrationHealth(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/integration-health`);
    return response.json();
  }

  async getSupportedFrameworks(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/frameworks`);
    return response.json();
  }
}

export { ESGApiService };
