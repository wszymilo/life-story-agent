import { signIn, signOut, fetchAuthSession } from 'aws-amplify/auth'

export interface AuthResult {
  success: boolean
  error?: string
}

export async function signInWithPassword(email: string, password: string): Promise<AuthResult> {
  try {
    await signIn({
      username: email,
      password,
    })
    return { success: true }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'An unexpected error occurred'
    return { success: false, error: message }
  }
}

export async function signOutUser(): Promise<void> {
  await signOut()
}

export async function getSession() {
  return fetchAuthSession()
}