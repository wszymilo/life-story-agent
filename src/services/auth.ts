import {
  sendEmailLink,
  handleEmailLink,
  signInWithGoogle,
  signOut as firebaseSignOut,
  getIdToken,
} from '../lib/firebase'

export interface AuthResult {
  success: boolean
  error?: string
  token?: string
}

export async function signInWithGoogleAuth(): Promise<AuthResult> {
  try {
    const user = await signInWithGoogle()
    const token = await getIdToken(user)
    return { success: true, token }
  } catch (e) {
    const error = e instanceof Error ? e.message : 'Google sign-in failed'
    return { success: false, error }
  }
}

export async function sendMagicLink(email: string): Promise<AuthResult> {
  try {
    window.localStorage.setItem('emailForSignIn', email)
    await sendEmailLink(email)
    return { success: true }
  } catch (e) {
    window.localStorage.removeItem('emailForSignIn')
    const error = e instanceof Error ? e.message : 'Failed to send magic link'
    return { success: false, error }
  }
}

export async function handleMagicLink(): Promise<AuthResult> {
  try {
    const user = await handleEmailLink()
    const token = await getIdToken(user)
    return { success: true, token }
  } catch (e) {
    const error = e instanceof Error ? e.message : 'Failed to verify magic link'
    return { success: false, error }
  }
}

export async function signOut(): Promise<void> {
  await firebaseSignOut()
}