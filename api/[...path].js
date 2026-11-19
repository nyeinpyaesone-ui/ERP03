import { Readable } from 'node:stream';

const MAX_REQUEST_BYTES = 4 * 1024 * 1024;
const TIMEOUT_MS = 30_000;
const FORWARDED_REQUEST_HEADERS = [
  'accept',
  'authorization',
  'content-type',
  'x-request-id',
  'x-idempotency-key',
];
const FORWARDED_RESPONSE_HEADERS = [
  'cache-control',
  'content-type',
  'retry-after',
  'x-request-id',
];

function getBackendUrl(req) {
  const configuredOrigin = process.env.ERP03_BACKEND_ORIGIN;
  if (!configuredOrigin) {
    const error = new Error('Backend API is not configured.');
    error.statusCode = 503;
    throw error;
  }

  let origin;
  try {
    origin = new URL(configuredOrigin);
  } catch {
    const error = new Error('Backend API configuration is invalid.');
    error.statusCode = 500;
    throw error;
  }

  if (
    origin.protocol !== 'https:' ||
    origin.username ||
    origin.password ||
    (origin.pathname !== '/' && origin.pathname !== '') ||
    origin.search ||
    origin.hash
  ) {
    const error = new Error('Backend API configuration must be an HTTPS origin.');
    error.statusCode = 500;
    throw error;
  }

  const requestUrl = new URL(req.url, 'https://erp03.invalid');
  const apiPath = requestUrl.pathname.replace(/^\/api\/?/, '');
  const target = new URL(origin.origin);
  target.pathname = `/api/v1/${apiPath}`.replace(/\/{2,}/g, '/');
  target.search = requestUrl.search;
  return target;
}

async function readRequestBody(req) {
  if (req.method === 'GET' || req.method === 'HEAD') return undefined;

  const chunks = [];
  let totalBytes = 0;
  for await (const chunk of req) {
    totalBytes += chunk.length;
    if (totalBytes > MAX_REQUEST_BYTES) {
      const error = new Error('Request body exceeds the 4 MiB proxy limit.');
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

export default async function handler(req, res) {
  if (!['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'].includes(req.method)) {
    res.setHeader('Allow', 'GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS');
    res.status(405).json({ detail: 'Method not allowed' });
    return;
  }

  try {
    const target = getBackendUrl(req);
    const headers = new Headers();
    for (const name of FORWARDED_REQUEST_HEADERS) {
      const value = req.headers[name];
      if (typeof value === 'string') headers.set(name, value);
    }

    const body = await readRequestBody(req);
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      signal: AbortSignal.timeout(TIMEOUT_MS),
      redirect: 'manual',
    });

    res.statusCode = upstream.status;
    for (const name of FORWARDED_RESPONSE_HEADERS) {
      const value = upstream.headers.get(name);
      if (value) res.setHeader(name, value);
    }
    res.setHeader('Cache-Control', 'no-store');

    if (!upstream.body || req.method === 'HEAD') {
      res.end();
      return;
    }

    Readable.fromWeb(upstream.body).pipe(res);
  } catch (error) {
    const statusCode = Number.isInteger(error.statusCode)
      ? error.statusCode
      : error.name === 'TimeoutError'
        ? 504
        : 502;

    if (!res.headersSent) {
      res.status(statusCode).json({
        detail:
          statusCode === 503 || statusCode === 500 || statusCode === 413
            ? error.message
            : 'Backend service is temporarily unavailable.',
      });
    } else {
      res.destroy(error);
    }
  }
}
