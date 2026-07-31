import type { RetrievalCompareRequest, RetrievalCompareResponse } from '@/types/retrievalLab'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function compareRetrievalModes(
  repositoryId: number,
  payload: RetrievalCompareRequest,
) {
  try {
    const { data } = await apiClient.post<RetrievalCompareResponse>(
      `/api/v1/repositories/${repositoryId}/retrieval/compare`,
      payload,
    )
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Retrieval comparison failed'))
  }
}
