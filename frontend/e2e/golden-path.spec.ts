import { test, expect } from "@playwright/test";

test("golden path: login, SOS, fusion sitrep, clock isolation, assign", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("aashray.lang", "en");
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Sign in/i })).toBeVisible();
  await page.getByRole("button", { name: "Enter AASHRAY" }).click();
  await expect(page).toHaveURL(/\/c/);

  await page.getByPlaceholder("Short description").fill("Landslide on the hill road, rocks");
  await page.getByRole("button", { name: "Send SOS" }).first().click();
  await expect(page.getByText(/Linked to A/i)).toBeVisible({ timeout: 20_000 });

  await page.getByRole("button", { name: "I’m safe" }).click();
  await expect(page.getByText(/Safety status saved/i)).toBeVisible({ timeout: 15_000 });

  await page.getByRole("button", { name: "Log out" }).click();
  await page.getByRole("button", { name: /Responder/ }).click();
  await page.getByRole("button", { name: "Enter AASHRAY" }).click();
  await expect(page).toHaveURL(/\/ops/);

  await expect(page.getByText(/FUSED from/)).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/PRECOMPUTED|precomputed/i).first()).toBeVisible();
  await expect(page.getByText(/SIMULATED/i).first()).toBeVisible();

  for (let i = 1; i <= 7; i += 1) {
    const tickWait = page.waitForResponse(
      (r) => r.url().includes("/demo/tick") && r.request().method() === "POST" && r.ok(),
    );
    await page.getByRole("button", { name: "Advance clock" }).click();
    const tickRes = await tickWait;
    expect((await tickRes.json()).tick).toBe(i);
  }
  await expect(page.getByText("Village isolated: Gahar hamlet")).toBeVisible({ timeout: 20_000 });

  await page.getByRole("button", { name: /Assign team/ }).click();
  await expect(page.getByText(/assigned/i).first()).toBeVisible({ timeout: 15_000 });
});
