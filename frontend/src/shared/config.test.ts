import { describe, expect, it } from "vitest";

import { normalizeApiUrl } from "./config";

describe("normalizeApiUrl", () => {
  it("removes trailing slashes", () => {
    expect(normalizeApiUrl("http://localhost:8000/api///")).toBe(
      "http://localhost:8000/api",
    );
  });
});
