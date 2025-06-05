import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { emissionsAPI } from '../services/api';
import { EmissionRecord, DashboardData, FormData } from '../types/emissions';
import { useWebSocket } from './useWebSocket';

export const useEmissionsData = () => {
  const queryClient = useQueryClient();
  const [realTimeData, setRealTimeData] = useState<any>(null);

  // WebSocket for real-time updates
  const { subscribe, isConnected, connectionStatus } = useWebSocket(
    process.env.REACT_APP_WS_URL,
    {
      onConnect: () => {
        console.log('Connected to emissions WebSocket');
      },
      onDisconnect: () => {
        console.log('Disconnected from emissions WebSocket');
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
      },
    }
  );

  useEffect(() => {
    const unsubscribeEmissions = subscribe('emissions_updated', (data) => {
      setRealTimeData(data);
      queryClient.invalidateQueries(['emissions']);
      queryClient.invalidateQueries(['dashboard']);
    });

    const unsubscribeDashboard = subscribe('dashboard_update', (data) => {
      queryClient.invalidateQueries(['dashboard']);
    });

    const unsubscribeDataQuality = subscribe('data_quality_alert', (data) => {
      console.log('Data quality alert received:', data);
      // Handle data quality alerts
    });

    return () => {
      unsubscribeEmissions();
      unsubscribeDashboard();
      unsubscribeDataQuality();
    };
  }, [subscribe, queryClient]);

  // Queries
  const {
    data: emissions,
    isLoading: emissionsLoading,
    error: emissionsError,
    refetch: refetchEmissions
  } = useQuery<EmissionRecord[]>(
    ['emissions'],
    () => emissionsAPI.getAllEmissions().then(res => res.data),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    }
  );

  const {
    data: dashboardData,
    isLoading: dashboardLoading,
    error: dashboardError,
    refetch: refetchDashboard
  } = useQuery<DashboardData>(
    ['dashboard'],
    () => emissionsAPI.getDashboardData().then(res => res.data),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 1 * 60 * 1000, // 1 minute
      refetchOnWindowFocus: false,
    }
  );

  // Mutations
  const createEmissionMutation = useMutation(
    (data: FormData) => emissionsAPI.createEmission(data),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['emissions']);
        queryClient.invalidateQueries(['dashboard']);
        console.log('Emission created successfully:', data);
      },
      onError: (error) => {
        console.error('Failed to create emission:', error);
      }
    }
  );

  const updateEmissionMutation = useMutation(
    ({ id, data }: { id: number; data: Partial<FormData> }) => 
      emissionsAPI.updateEmission(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['emissions']);
        queryClient.invalidateQueries(['dashboard']);
      },
      onError: (error) => {
        console.error('Failed to update emission:', error);
      }
    }
  );

  const deleteEmissionMutation = useMutation(
    (id: number) => emissionsAPI.deleteEmission(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['emissions']);
        queryClient.invalidateQueries(['dashboard']);
      },
      onError: (error) => {
        console.error('Failed to delete emission:', error);
      }
    }
  );

  // Helper functions
  const createEmission = useCallback((data: FormData) => {
    return createEmissionMutation.mutateAsync(data);
  }, [createEmissionMutation]);

  const updateEmission = useCallback((id: number, data: Partial<FormData>) => {
    return updateEmissionMutation.mutateAsync({ id, data });
  }, [updateEmissionMutation]);

  const deleteEmission = useCallback((id: number) => {
    return deleteEmissionMutation.mutateAsync(id);
  }, [deleteEmissionMutation]);

  const refreshData = useCallback(() => {
    refetchEmissions();
    refetchDashboard();
  }, [refetchEmissions, refetchDashboard]);

  return {
    // Data
    emissions,
    dashboardData,
    realTimeData,
    
    // Loading states
    emissionsLoading,
    dashboardLoading,
    
    // Errors
    emissionsError,
    dashboardError,
    
    // WebSocket status
    isConnected,
    connectionStatus,
    
    // Mutations
    createEmission,
    updateEmission,
    deleteEmission,
    
    // Mutation states
    isCreating: createEmissionMutation.isLoading,
    isUpdating: updateEmissionMutation.isLoading,
    isDeleting: deleteEmissionMutation.isLoading,
    
    // Utility functions
    refreshData,
  };
};

export default useEmissionsData;
