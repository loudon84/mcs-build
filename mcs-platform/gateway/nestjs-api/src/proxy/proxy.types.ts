export interface ProxyOptions {
  timeout?: number;
  retry?: {
    enabled: boolean;
    maxRetries: number;
    retryableStatuses: number[];
  };
}

