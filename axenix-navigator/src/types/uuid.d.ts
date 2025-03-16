declare module "uuid" { 
  export function v4(): string; 
  export function v4(options: any): string; 
  export function v4(options: any, buffer: any, offset?: number): any; 
} 