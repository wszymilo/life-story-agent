/// <reference types="vite/client" />

declare module 'unidecode' {
  function unidecode(str: string): string
  export = unidecode
}