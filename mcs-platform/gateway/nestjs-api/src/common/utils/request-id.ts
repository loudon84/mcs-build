import { v4 as uuidv4 } from 'uuid';

/**
 * Generate or extract request ID from header
 */
export function getOrGenerateRequestId(existingRequestId?: string): string {
  return existingRequestId || uuidv4();
}

