import { test, expect } from '@playwright/test';

test.use({
  baseURL: 'http://127.0.0.1:80',
});

test('Chat Regression: Send Message and Receive Acknowledgment', async ({ page }) => {
  // 1. Go to Chat Page
  await page.goto('/chat');
  
  // 2. Check for the header text
  await expect(page.locator('h1')).toContainText('BestFam Agent');
  
  // 3. Send a unique message
  const testMessage = `Ping ${Date.now()}`;
  await page.fill('input[placeholder="Message BestFam Agent..."]', testMessage);
  await page.press('input[placeholder="Message BestFam Agent..."]', 'Enter');
  
  // 4. Verify message appears in chat
  await expect(page.locator('body')).toContainText(testMessage);
  
  // 5. Wait for the agent to reply (Acknowledged: ...)
  const replyText = `Acknowledged: ${testMessage}`;
  await expect(page.locator('body')).toContainText(replyText, { timeout: 15000 });
  
  console.log(`✅ Chat regression passed: Sent "${testMessage}", Received "${replyText}"`);
});
