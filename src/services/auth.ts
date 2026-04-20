import { supabase } from '../lib/supabase'

export interface AuthResult {
  success: boolean
  error?: string
}

export async function signInWithMagicLink(email: string): Promise<AuthResult> {
  try {
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: window.location.origin,
      },
    })

    if (error) {
      return { success: false, error: error.message }
    }

    return { success: true }
  } catch {
    return { success: false, error: 'An unexpected error occurred' }
  }
}