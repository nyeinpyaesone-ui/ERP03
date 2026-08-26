import { z } from 'zod';

const envSchema = z.object({
  PORT: z.string().default('3000'),
  WEBHOOK_GITHUB_KEY: z.string().min(10, "Missing Webhook Secret"),
  GITHUB_TOKEN: z.string().min(20, "Missing GitHub Token"),
  ERP_WEBHOOK_URL: z.string().url().default('https://erp.anynoob.com/webhook/'),
  REDIS_URL: z.string().default('redis://localhost:6379'),
  GITHUB_ACTOR: z.string().optional(),
});

export const config = envSchema.parse(process.env);
