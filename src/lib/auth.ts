import { Amplify } from 'aws-amplify'

const COGNITO_REGION = import.meta.env.VITE_COGNITO_REGION || 'eu-west-1'
const COGNITO_USER_POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID || ''
const COGNITO_CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID || ''

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: COGNITO_USER_POOL_ID || 'PLACEHOLDER',
      userPoolClientId: COGNITO_CLIENT_ID || 'PLACEHOLDER',
      loginWith: {
        email: true,
      },
      signUpVerificationMethod: 'code',
      userAttributes: {
        email: { required: true },
      },
      passwordFormat: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialCharacters: false,
      },
    },
  },
})

if (!COGNITO_USER_POOL_ID || !COGNITO_CLIENT_ID) {
  console.warn('[auth] Missing Cognito configuration. Set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID')
}

export const AUTH_CONFIG = {
  region: COGNITO_REGION,
  userPoolId: COGNITO_USER_POOL_ID,
  userPoolClientId: COGNITO_CLIENT_ID,
}

export type CognitoUser = {
  id: string
  email: string
}

export type CognitoSession = {
  accessToken: string
  idToken: string
  refreshToken?: string
  expiresAt: number
}

export { COGNITO_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID }