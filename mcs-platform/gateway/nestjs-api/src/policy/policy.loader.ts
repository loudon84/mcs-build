import { Injectable } from '@nestjs/common';
import { readFileSync, watchFile } from 'fs';
import { join } from 'path';
import * as yaml from 'js-yaml';
import { ConfigService } from '../config/config.service';
import { PolicyConfig } from '../common/types';
import { PolicyLoader } from './policy.types';

@Injectable()
export class YamlPolicyLoader implements PolicyLoader {
  private policyCache: PolicyConfig | null = null;
  private watchEnabled: boolean;

  constructor(private configService: ConfigService) {
    this.watchEnabled = !configService.isProduction;
  }

  async load(): Promise<PolicyConfig> {
    if (this.policyCache) {
      return this.policyCache;
    }

    return this.reload();
  }

  async reload(): Promise<PolicyConfig> {
    try {
      const policyPath = this.configService.policyPath;
      const fullPath = join(process.cwd(), policyPath);
      const fileContent = readFileSync(fullPath, 'utf-8');
      const policy = yaml.load(fileContent) as PolicyConfig;

      // Validate policy structure
      this.validatePolicy(policy);

      this.policyCache = policy;

      // Watch for changes in development
      if (this.watchEnabled) {
        watchFile(fullPath, { interval: 5000 }, () => {
          console.log('Policy file changed, reloading...');
          this.reload().catch((err) => {
            console.error('Failed to reload policy:', err);
          });
        });
      }

      return policy;
    } catch (error) {
      throw new Error(`Failed to load policy: ${error.message}`);
    }
  }

  private validatePolicy(policy: PolicyConfig): void {
    if (!policy.default || !policy.default.graphs) {
      throw new Error('Policy must have default.graphs');
    }

    if (!policy.routing || !policy.routing.orchestrator_base_url) {
      throw new Error('Policy must have routing.orchestrator_base_url');
    }

    // Validate graph structure
    for (const graph of policy.default.graphs) {
      if (!graph.name || !graph.versions || !graph.default_version) {
        throw new Error('Graph must have name, versions, and default_version');
      }
    }
  }
}

