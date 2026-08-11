export const ADMIN_EMAIL = 'admin@gmail.com'

export function isAdminEmail(email: string): boolean {
  return email.trim().toLowerCase() === ADMIN_EMAIL
}
