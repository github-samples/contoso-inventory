import { test, expect } from '@playwright/test';

test.describe('AssetTrack - Smoke Tests', () => {
  test('home page loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/AssetTrack/);
  });

  test('assets page is accessible', async ({ page }) => {
    await page.goto('/assets');
    await expect(page.getByRole('heading', { level: 1, name: /assets/i })).toBeVisible();
  });

  test('employees page is accessible', async ({ page }) => {
    await page.goto('/employees');
    await expect(page.getByRole('heading', { level: 1, name: /employees/i })).toBeVisible();
  });
});
