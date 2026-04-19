export function extractErrorMessage(
  error: unknown,
  defaultMessage: string
): string {
  return error instanceof Error ? error.message : defaultMessage
}