import { config } from "../utils/config.js";

class RefeeError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function httpGet<T>(pathOrUrl: string): Promise<T> {
  const url = pathOrUrl.startsWith("http") ? new URL(pathOrUrl) : new URL(pathOrUrl, config.refeeApiBaseUrl);
  if (!url.searchParams.get("token")) {
    url.searchParams.set("token", config.refeeToken);
  }
  const res = await fetch(url.toString(), { method: "GET" });
  const text = await res.text();
  let data: any;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
  if (!res.ok) {
    throw new RefeeError(res.status, (data?.message ?? data?.error ?? "Request failed") as string);
  }
  return data as T;
}

export async function getRefillAddress() {
  return httpGet<{ address: string }>("/refill");
}

export async function getRefeeBalance() {
  return httpGet<{ balance: number }>("/balance");
}

export async function buyEnergy(params: { days: string; volume: number; target: string }) {
  const url = new URL("/buyenergy", config.refeeApiBaseUrl);
  url.searchParams.set("days", params.days);
  url.searchParams.set("volume", String(params.volume));
  url.searchParams.set("target", params.target);
  url.searchParams.set("token", config.refeeToken);
  return httpGet<{ ok: boolean; orderId?: string }>(url.toString());
}

export async function buyBandwidth(params: { days: string; volume: number; target: string }) {
  const url = new URL("/buybandwidth", config.refeeApiBaseUrl);
  url.searchParams.set("days", params.days);
  url.searchParams.set("volume", String(params.volume));
  url.searchParams.set("target", params.target);
  url.searchParams.set("token", config.refeeToken);
  return httpGet<{ ok: boolean; orderId?: string }>(url.toString());
}

export async function calcCost(targets: string[]) {
  const url = new URL("/cost", config.refeeApiBaseUrl);
  url.searchParams.set("targets", targets.join(","));
  url.searchParams.set("token", config.refeeToken);
  return httpGet<any>(url.toString());
}

export { RefeeError };
