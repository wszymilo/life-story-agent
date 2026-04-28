import { initializeApp, getApps } from 'firebase/app'
import {
  getAuth,
  isSignInWithEmailLink,
  sendSignInLinkToEmail,
  signInWithEmailLink,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User,
} from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
}

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]

export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()

export function isEmailLink(url: string): boolean {
  return isSignInWithEmailLink(auth, url)
}

export async function sendEmailLink(email: string): Promise<void> {
  const actionCodeSettings = {
    url: `${window.location.origin}/auth/callback`,
    handleCodeInApp: true,
  }
  await sendSignInLinkToEmail(auth, email, actionCodeSettings)
}

export async function handleEmailLink(email?: string): Promise<User> {
  if (!email && typeof window !== 'undefined') {
    email = window.localStorage.getItem('emailForSignIn') || undefined
  }
  if (!email) {
    throw new Error('Email not stored for email link verification')
  }
  const result = await signInWithEmailLink(auth, email, window.location.href)
  window.localStorage.removeItem('emailForSignIn')
  return result.user
}

export async function signInWithGoogle(): Promise<User> {
  const result = await signInWithPopup(auth, googleProvider)
  return result.user
}

export async function signOut(): Promise<void> {
  await firebaseSignOut(auth)
}

export function onAuthChange(callback: (user: User | null) => void): () => void {
  return onAuthStateChanged(auth, callback)
}

export function getIdToken(user: User): Promise<string> {
  return user.getIdToken()
}

export function getCurrentUser(): User | null {
  return auth.currentUser
}

export type { User }