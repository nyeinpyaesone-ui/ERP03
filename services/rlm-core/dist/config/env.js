"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.config = void 0;
const zod_1 = require("zod");
const envSchema = zod_1.z.object({
    PORT: zod_1.z.string().default('3000'),
    WEBHOOK_GITHUB_KEY: zod_1.z.string().min(10, "Missing Webhook Secret"),
    GITHUB_TOKEN: zod_1.z.string().min(20, "Missing GitHub Token"),
    ERP_WEBHOOK_URL: zod_1.z.string().url().default('https://erp.anynoob.com/webhook/'),
    REDIS_URL: zod_1.z.string().default('redis://localhost:6379'),
    GITHUB_ACTOR: zod_1.z.string().optional(),
});
exports.config = envSchema.parse(process.env);
//# sourceMappingURL=env.js.map