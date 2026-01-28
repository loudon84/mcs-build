import { MCSRequestContext } from '../common/types';

declare global {
  namespace Express {
    interface Request {
      mcs?: MCSRequestContext;
      upstreamHeaders?: Record<string, string>;
    }
  }
}

export {};

