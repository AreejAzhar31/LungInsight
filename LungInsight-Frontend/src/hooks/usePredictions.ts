import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as predictionsApi from '@/api/predictions';

export function usePredictions(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['predictions', page, pageSize],
    queryFn: () => predictionsApi.listPredictions(page, pageSize),
  });
}

export function usePrediction(id: string | undefined) {
  return useQuery({
    queryKey: ['prediction', id],
    queryFn: () => predictionsApi.getPrediction(id as string),
    enabled: Boolean(id),
  });
}

export function usePredictionImageUrl(id: string | undefined) {
  return useQuery({
    queryKey: ['prediction-image-url', id],
    queryFn: () => predictionsApi.getPredictionImageUrl(id as string),
    enabled: Boolean(id),
    // Supabase signed URLs are time-limited (1 hour) -- don't let React
    // Query treat a stale one as still fresh indefinitely.
    staleTime: 30 * 60 * 1000,
  });
}

export function useCreatePrediction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => predictionsApi.createPrediction(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['predictions'] });
      queryClient.invalidateQueries({ queryKey: ['history'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
