export type User = {
  id: number
  email: string
  created_at: string
}

export type AuthTokenResponse = {
  access_token: string
  token_type: string
  user: User
}
