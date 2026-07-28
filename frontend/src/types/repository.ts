export type Repository = {
  id: number
  url: string
  full_name: string
  provider: string
  status: string
  clone_path: string
  default_branch: string | null
  created_at: string
  updated_at: string
}
