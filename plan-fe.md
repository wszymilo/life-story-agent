# Frontend AWS Refactor Plan

## Objective

Replace Supabase authentication and client SDK with AWS Cognito + Amplify to prepare the frontend for deployment to AWS S3/CloudFront.

## Status: ✅ COMPLETE

All migration steps completed and verified.

---

## Migration Summary

| Step | Status | Notes |
|------|--------|-------|
| 1. Install Amplify dependencies | ✅ | `npm install @aws-amplify/ui-react aws-amplify` |
| 2. Create `src/lib/auth.ts` | ✅ | Amplify.configure with Cognito User Pool |
| 3. Create `src/lib/cognito.ts` | ✅ | Created (config object) |
| 4. Create `src/context/AuthContext.tsx` | ✅ | Amplify Hub.listen('auth') for state |
| 5. Update `src/services/api.ts` | ✅ | fetchAuthSession for JWT |
| 6. Update `.env.example` | ✅ | VITE_COGNITO_* vars added |
| 7. Update `LoginScreen.tsx` | ✅ | Password form + updated i18n |
| 8. Replace signOut in TimelineScreen | ✅ | Dynamic import of signOutUser |
| 9. Replace supabase in DebugScreen | ✅ | fetchAuthSession + signOut |
| 10. Remove @supabase/supabase-js | ✅ | Dependency removed |
| 11. Run typecheck | ✅ | No errors |
| 12. Run lint | ✅ | 1 warning (acceptable) |
| 13. Verify build | ✅ | Built successfully |

---

## Verification Results

| Check | Result |
|-------|--------|
| `npm run typecheck` | ✅ Pass |
| `npm run lint` | ✅ Pass (1 warning) |
| `npm run build` | ✅ Pass |
| `npm run test:run` | ✅ 96 passed |

---

## Files Changed

### Created
- `src/lib/auth.ts` - Amplify configuration + Cognito setup
- `src/lib/cognito.ts` - Amplify config object

### Modified
- `src/context/AuthContext.tsx` - Amplify Hub listener
- `src/services/api.ts` - fetchAuthSession for JWT
- `src/services/auth.ts` - signInWithPassword
- `src/components/LoginScreen.tsx` - Password form
- `src/screens/TimelineScreen.tsx` - Removed supabase import
- `src/components/DebugScreen.tsx` - Cognito auth
- `.env.example` - Added VITE_COGNITO_* vars
- `src/i18n/locales/en.json` - Added password fields
- `src/i18n/locales/pl.json` - Added password fields

### Tests Updated
- `src/services/auth.test.ts`
- `src/services/api.test.ts`
- `src/components/LoginScreen.test.tsx`
- `src/App.complete.test.tsx`
- `src/App.incomplete.test.tsx`
- `src/hooks/useEncryption.ts` - Uses user.userId

---

## Environment Variables Required

```bash
VITE_API_URL=https://d2pahmt9j4e9bl.cloudfront.net
VITE_COGNITO_REGION=eu-west-1
VITE_COGNITO_USER_POOL_ID=eu-west-1_aiTrkzI1V
VITE_COGNITO_CLIENT_ID=12og6q3ci7vu94v3i342d9tapf
```

---

## Next Steps

1. **Deploy to S3/CloudFront** - Trigger `frontend.yml` GitHub Action
2. **Test end-to-end** - User registration/login via Cognito
3. **Remove old supabase.ts** - Can be deleted since no longer used

---

## Phase 2: Sign-Up Flow (User Registration)

### Objective

Add user registration (sign-up) to the app since currently only login exists with no way to create new accounts.

### Status: ✅ COMPLETE

### Scope

| Component | Description |
|-----------|-------------|
| SignUpScreen | New page with email, password, confirm password |
| Email Verification | Cognito sends code, user verifies |
| Auto-redirect | After verification → login screen |

### Implementation Plan

#### Step 1: Create SignUpScreen component
- Create `src/components/SignUpScreen.tsx`
- Fields: email, password, confirmPassword (with validation)
- Show password requirements from Cognito (8+ chars, lowercase, uppercase, number)
- After submit → call `signUp` from `aws-amplify/auth`
- On success → show "Check your email for verification code" message

#### Step 2: Add verification screen
- Create `src/components/VerifyEmailScreen.tsx`
- Single field: 6-digit code
- Call `confirmSignUp` from `aws-amplify/auth`
- On success → redirect to login

#### Step 3: Add routes
- Add `/signup` route in `App.tsx`
- Add `/verify-email` route in `App.tsx`

#### Step 4: Update LoginScreen
- Add "Don't have an account? Sign up" link
- Link to `/signup`

#### Step 5: Update i18n
- Add translations for:
  - `signup.title`, `signup.emailLabel`, `signup.passwordLabel`, `signup.confirmPasswordLabel`
  - `signup.submit`, `signup.successMessage`
  - `verify.title`, `verify.codeLabel`, `verify.submit`, `verify.successMessage`

### Files to Create
- `src/components/SignUpScreen.tsx`
- `src/components/VerifyEmailScreen.tsx`

### Files to Modify
- `src/App.tsx` - Add routes
- `src/components/LoginScreen.tsx` - Add sign-up link
- `src/i18n/locales/en.json` - Add translations
- `src/i18n/locales/pl.json` - Add translations

### Cognito Configuration Check
- Ensure Cognito App Client has `ALLOW_SIGN_UP` enabled
- Check if email verification is required

### Verification
- [x] Build succeeds
- [x] Lint passes (1 warning - pre-existing)
- [x] Tests pass (96 passed)
- [ ] Manual test: sign up with test email, verify code, log in

### Cognito App Client Note
The app client (`12og6q3ci7vu94v3i342d9tapf`) supports:
- `ALLOW_USER_PASSWORD_AUTH` - for sign in
- `ALLOW_REFRESH_TOKEN_AUTH` - for token refresh

Sign-up should work via the `signUp` API call. If sign-up fails, check Cognito console to ensure "Enable Sign-Up" is checked in the app client settings.

---

*Document version: 2.2 | Updated: 2026-04-27*