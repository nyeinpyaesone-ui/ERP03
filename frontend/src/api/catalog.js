/* ── Types ── (kept in JS with JSDoc for zero-build TS-like safety) */

/** Product as returned by the ERP03 catalog API. */
export class Product {
  /** @type {string} */
  id;
  /** @type {string} */
  business_id;
  /** @type {string} */
  branch_id;
  /** @type {string} */
  sku;
  /** @type {string | null} */
  barcode;
  /** @type {string} */
  name;
  /** @type {string} */
  unit;
  /** @type {number} */
  sale_price;
  /** @type {number} */
  cost_price;
  /** @type {number} */
  min_stock;
  /** @type {boolean} */
  active;

  constructor(data) {
    this.id = data.id;
    this.business_id = data.business_id;
    this.branch_id = data.branch_id;
    this.sku = data.sku;
    this.barcode = data.barcode ?? null;
    this.name = data.name;
    this.unit = data.unit ?? "pcs";
    this.sale_price = Number(data.sale_price ?? 0);
    this.cost_price = Number(data.cost_price ?? 0);
    this.min_stock = Number(data.min_stock ?? 0);
    this.active = data.active ?? true;
  }
}

/** Paginated product list response. */
export class ProductPage {
  /** @type {Product[]} */
  items;
  /** @type {number} */
  limit;
  /** @type {number} */
  offset;
  /** @type {number} */
  total;
  /** @type {boolean} */
  has_more;

  constructor(data) {
    this.items = (data.items ?? []).map((i) => new Product(i));
    this.limit = data.limit ?? 50;
    this.offset = data.offset ?? 0;
    this.total = data.total ?? 0;
    this.has_more = data.has_more ?? false;
  }
}

/** Payload for creating a product. */
export class ProductCreateInput {
  /** @type {string} */
  branch_id;
  /** @type {string} */
  sku;
  /** @type {string | null} */
  barcode;
  /** @type {string} */
  name;
  /** @type {string} */
  unit;
  /** @type {number} */
  sale_price;
  /** @type {number} */
  cost_price;
  /** @type {number} */
  min_stock;

  constructor(data) {
    this.branch_id = data.branch_id;
    this.sku = data.sku;
    this.barcode = data.barcode ?? null;
    this.name = data.name;
    this.unit = data.unit ?? "pcs";
    this.sale_price = Number(data.sale_price ?? 0);
    this.cost_price = Number(data.cost_price ?? 0);
    this.min_stock = Number(data.min_stock ?? 0);
  }
}

/** Error from the API. */
export class ApiError extends Error {
  /** @type {number} */
  status;
  /** @type {string} */
  code;

  constructor(message, status = 500, code = "ERR") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** ── API client ── */
const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

function money(n) {
  return n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

async function request(path, { method = "GET", body, headers = {}, token } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (!res.ok) {
    const msg =
      data && typeof data === "object" && data.detail
        ? data.detail
        : typeof data === "string"
          ? data
          : res.statusText;
    throw new ApiError(msg, res.status, codeFromStatus(res.status));
  }

  return data;
}

function codeFromStatus(status) {
  if (status === 401) return "UNAUTHORIZED";
  if (status === 403) return "FORBIDDEN";
  if (status === 404) return "NOT_FOUND";
  if (status === 409) return "CONFLICT";
  if (status === 422) return "VALIDATION_ERROR";
  if (status >= 500) return "SERVER_ERROR";
  return "REQUEST_ERROR";
}

export const catalogApi = {
  /** List products with optional search and pagination. */
  async listProducts({ businessId, search, includeInactive, limit = 50, offset = 0, token } = {}) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (search) params.set("search", search);
    if (includeInactive) params.set("include_inactive", "true");

    const data = await request(`/products?${params}`, {
      headers: { business_id: String(businessId) },
      token,
    });
    return new ProductPage(data);
  },

  /** Create a new product. */
  async createProduct({ branchId, sku, barcode, name, unit = "pcs", salePrice, costPrice = 0, minStock = 0, token }) {
    const data = await request("/products", {
      method: "POST",
      body: new ProductCreateInput({
        branch_id: branchId,
        sku,
        barcode,
        name,
        unit,
        sale_price: salePrice,
        cost_price: costPrice,
        min_stock: minStock,
      }),
      token,
    });
    return new Product(data);
  },
};

export { money };
