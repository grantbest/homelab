import { test, expect } from '@playwright/test';

test.use({
  baseURL: 'http://127.0.0.1:80',
});

test('Dashboard Regression: Home Page Loads and shows Title', async ({ page }) => {
  await page.goto('/');
  
  // Verify that the page didn't return a Traefik 404
  const body = await page.content();
  expect(body).not.toContain('404 page not found');
  
  // Check for some text that should definitely be on your dashboard
  // (Adjust this to match what's actually in your Next.js app)
  await expect(page).toHaveTitle(/Betting Engine/);
});
