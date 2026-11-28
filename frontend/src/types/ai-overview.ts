export interface OverviewSource {
  title: string
  url: string
}

export type OverviewStatus =
  | 'GENERATED_SUCCESSFULLY'
  | 'NOT_GENERATED_DUE_TO_INSUFFICIENT_EVIDENCE'
  | 'NOT_GENERATED_DUE_TO_LLM_ERROR'
  | 'NOT_GENERATED_DUE_TO_EMPTY_QUERY'
  | 'NOT_GENERATED_DUE_TO_RETRIEVAL_ERROR'

export interface AIOverviewResponse {
  status: OverviewStatus
  reason: string | null
  overview: string | null
  sources: OverviewSource[]
}