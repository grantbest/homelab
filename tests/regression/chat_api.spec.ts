import { test, expect } from '@playwright/test';

test('Chat API & Bridge Verification', async ({ request }) => {
  // 1. Send message to API directly
  const testMessage = `APIPing ${Date.now()}`;
  
  const postRes = await request.post('http://127.0.0.1:80/api/chat', {
    headers: { 'Host': 'bestfam.us' },
    data: { role: 'user', content: testMessage }
  });
  
  if (!postRes.ok()) {
    console.log(`❌ POST failed: ${postRes.status()} - ${await postRes.text()}`);
  }
  expect(postRes.ok()).toBeTruthy();
  console.log(`✅ Message sent to API: ${testMessage}`);

  // 2. Poll for reply from the bridge
  let replied = false;
  for (let i = 0; i < 10; i++) {
    await new Promise(r => setTimeout(r, 2000));
    
    const getRes = await request.get('http://127.0.0.1:80/api/chat', {
      headers: { 'Host': 'bestfam.us' }
    });
    
    expect(getRes.ok()).toBeTruthy();
    const messages = await getRes.json();
    
    if (messages.some((m: any) => m.role === 'agent' && m.content === `Acknowledged: ${testMessage}`)) {
      replied = true;
      break;
    }
    console.log(`... Waiting for bridge reply (attempt ${i+1}/10)`);
  }
  
  expect(replied).toBeTruthy();
  console.log(`✅ Bridge acknowledged the message!`);
});
