import { z } from 'zod';

const envSchema = z.object({
  PORT: z.string().default('3000'),
  WEBHOOK_GITHUB_KEY: z.string().min(1, "WEBHOOK_GITHUB_KEY is required"),
  GITHUB_TOKEN: z.string().optional().default('dummy-token-for-startup'),
  ERP_WEBHOOK_URL: z.string().url().default('https://erp.anynoob.com/webhook/'),
  REDIS_URL: z.string().default('redis://localhost:6379'),
});

export const config = envSchema.parse(process.env);
