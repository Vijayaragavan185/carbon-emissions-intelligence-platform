import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { emissionsAPI } from '../services/api';
import { EmissionRecord, DashboardData, FormData } from '../types/emissions';
import { useWebSocket } from './useWebSocket';

export const useEmissionsData = () => {
  const queryClient = useQueryClient();
  const [realTimeData, setRealTimeData] = useState<any>(null);

  // WebSocket for real-time updates
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('emissions_updated', (data) => {
      setRealTimeData(data);
      queryClient.invalidateQueries('emissions');
      queryClient.invalidateQueries('dashboard');
    });

    return unsubscribe;
  }, [subscribe, queryClient]);

  // Queries
  const {
    data: emissions,
    isLoading: emissionsLoading,
    error: emissionsError
  } = useQuery<EmissionRecord[]>('emissions', 
    () => emissionsAPI.getAllEmissions().then(res => res.data)
  );

  const {
    data: dashboardData,
    isLoading: dashboardLoading,
    error: dashboardError
  } = useQuery<DashboardData>('dashboard',
    () => emissionsAPI.getDashboardData().then(res => res.data),
    { refetchInterval: 30000 } // Refetch every 30 seconds
  );

  // Mutations
  const createEmissionMutation = useMutation(
    (data: FormData) => emissionsAPI.createEmission(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('emissions');
        queryClient.invalidateQueries('dashboard');
      }
    }
  );

  const updateEmissionMutation = useMutation(
    ({ id, data }: { id: number; data: Partial<FormData> }) => 
      emissionsAPI.updateEmission(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('emissions');
        queryClient.invalidateQueries('dashboard');
      }
    }
  );

  const deleteEmissionMutation = useMutation(
    (id: number) => emissionsAPI.deleteEmission(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('emissions');
        queryClient.invalidateQueries('dashboard');
      }
    }
  );

  // Helper functions
  const createEmission = useCallback((data: FormData) => {
    return createEmissionMutation.mutate(data);
  }, [createEmissionMutation]);

  const updateEmission = useCallback((id: number, data: Partial<FormData>) => {
    return updateEmissionMutation.mutate({ id, data });
  }, [updateEmissionMutation]);

  const deleteEmission = useCallback((id: number) => {
    return deleteEmissionMutation.mutate(id);
  }, [deleteEmissionMutation]);

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
    
    // Mutations
    createEmission,
    updateEmission,
    deleteEmission,
    
    // Mutation states
    isCreating: createEmissionMutation.isLoading,
    isUpdating: updateEmissionMutation.isLoading,
    isDeleting: deleteEmissionMutation.isLoading,
  };
};
