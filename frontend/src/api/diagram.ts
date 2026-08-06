import type { DiagramRequest, DiagramResponse } from '@/types/diagram'
import { apiClient, getApiErrorMessage } from '@/lib/axios'

export async function generateRepositoryDiagram(
  repositoryId: number,
  payload: DiagramRequest,
) {
  try {
    const { data } = await apiClient.post<DiagramResponse>(
      `/api/v1/repositories/${repositoryId}/diagram`,
      payload,
    )
    return data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Diagram generation failed'))
  }
}
