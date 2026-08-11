import type { RepositoryOpsRow } from '@/types/admin'

export function formatRepositoryOwnerLabel(
  repo: Pick<RepositoryOpsRow, 'owner_email' | 'user_id'>,
): string {
  if (repo.owner_email) {
    return repo.owner_email
  }
  if (repo.user_id != null) {
    return `User #${repo.user_id}`
  }
  return 'Public'
}

export function formatRepositorySelectLabel(repo: RepositoryOpsRow): string {
  return `${repo.full_name} · ${formatRepositoryOwnerLabel(repo)}`
}
