import { test, expect } from '@playwright/test';

// QR support: the asset detail page renders a server-generated QR code as an
// accessible image. Requires the full stack running (web + assets-svc).
test.describe('AssetTrack - QR code feature', () => {
  test('asset detail page shows an accessible QR code', async ({ page }) => {
    // Land on the assets list and open the first asset's detail page.
    await page.goto('/assets');
    const firstAsset = page.locator('a[href^="/assets/"]').first();
    await firstAsset.click();

    // The QR card heading and the accessible QR image are present.
    await expect(page.getByRole('heading', { name: /qr code/i })).toBeVisible();
    const qr = page.getByRole('img', { name: /qr code linking to the detail page/i });
    await expect(qr).toBeVisible();
    // The inline SVG actually rendered.
    await expect(qr.locator('svg')).toBeVisible();
  });
});
