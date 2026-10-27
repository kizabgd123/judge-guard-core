#!/usr/bin/env node
/**
 * medium_digest_publisher.js
 * 
 * Automation Publisher for Medium Daily Digest:
 * 1. Queries Notion for scheduled Medium articles (or reads local draft).
 * 2. Implements Zero-Simulation & Pre-Flight Gating (always defaults to publishStatus: 'draft').
 * 3. Dispatches to Medium API when MEDIUM_INTEGRATION_TOKEN is present, or stages
 *    verified artifact at /tmp/medium_drafts/ for manual web publishing / review.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const crypto = require('crypto');

function loadEnv() {
  const envPaths = [path.resolve(__dirname, '../.env')];
  for (const envPath of envPaths) {
    if (fs.existsSync(envPath)) {
      const lines = fs.readFileSync(envPath, 'utf8').split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
          const eqIdx = trimmed.indexOf('=');
          if (eqIdx !== -1) {
            const key = trimmed.substring(0, eqIdx).trim();
            const val = trimmed.substring(eqIdx + 1).trim();
            if (!process.env[key]) {
              process.env[key] = val;
            }
          }
        }
      }
    }
  }
}
loadEnv();

const NOTION_TOKEN = process.env.NOTION_API_KEY;
const DATABASE_ID = process.env.NOTION_DATABASE_ID || '3ae97963-e5cf-81d5-b932-d67d93ae2d5a';
const MEDIUM_TOKEN = process.env.MEDIUM_INTEGRATION_TOKEN;

function httpsRequest(options, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = body ? (typeof body === 'string' ? body : JSON.stringify(body)) : null;
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try { resolve(JSON.parse(data)); } catch { resolve({ status: 'ok', raw: data }); }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 300)}`));
        }
      });
    });
    req.on('error', reject);
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

async function getMediumUser(token) {
  return httpsRequest({
    hostname: 'api.medium.com',
    path: '/v1/me',
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
      'Accept-Charset': 'utf-8'
    }
  });
}

async function createMediumPost(token, userId, postData) {
  return httpsRequest({
    hostname: 'api.medium.com',
    path: `/v1/users/${userId}/posts`,
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Accept-Charset': 'utf-8'
    }
  }, postData);
}

async function updateNotionPageStatus(pageId, status) {
  if (!NOTION_TOKEN) return;
  await httpsRequest({
    hostname: 'api.notion.com',
    path: `/v1/pages/${pageId}`,
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${NOTION_TOKEN}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    }
  }, {
    properties: {
      'Status': {
        select: { name: status }
      }
    }
  });
}

async function getNotionPageMarkdown(pageId) {
  const chunks = [];
  let cursor = null;
  do {
    const query = cursor ? `?start_cursor=${encodeURIComponent(cursor)}&page_size=100` : '?page_size=100';
    const result = await httpsRequest({
      hostname: 'api.notion.com',
      path: `/v1/blocks/${encodeURIComponent(pageId)}/children${query}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${NOTION_TOKEN}`,
        'Notion-Version': '2022-06-28',
        'Accept': 'application/json'
      }
    });
    for (const block of result.results || []) {
      if (block.type === 'code') {
        chunks.push((block.code.rich_text || []).map(item => item.plain_text || item.text?.content || '').join(''));
      }
    }
    cursor = result.has_more ? result.next_cursor : null;
  } while (cursor);
  return chunks.join('');
}

async function runPublisher(options = {}) {
  const publicRequested = options.public === true;
  const publishStatus = 'draft';

  console.log('==================================================');
  console.log('📰 Medium Daily Digest Publisher');
  console.log(`Mode: ${publishStatus.toUpperCase()}`);
  if (publicRequested) {
    console.log('Public dispatch is disabled until an approved Notion record and JudgeGuard ticket are verified; continuing with draft staging only.');
  }
  console.log('==================================================');

  const draftDir = '/tmp/medium_drafts';
  if (!fs.existsSync(draftDir)) {
    fs.mkdirSync(draftDir, { recursive: true });
  }

  const articleContent = fs.readFileSync(path.join(__dirname, 'medium_daily_digest.md'), 'utf8');
  const articleTitle = articleContent.split(/\r?\n/).find(line => line.startsWith('# '))?.slice(2) || 'Medium Daily Digest';
  const tags = ['Software Architecture', 'Artificial Intelligence', 'DevOps', 'Python', 'Cybersecurity'];

  const payload = {
    title: articleTitle,
    contentFormat: 'markdown',
    content: articleContent,
    tags: tags,
    publishStatus: publishStatus
  };

  // 1. Stage local verified artifacts
  const draftPath = path.join(draftDir, 'medium_daily_digest.md');
  const payloadPath = path.join(draftDir, 'medium_payload.json');
  fs.writeFileSync(draftPath, articleContent, 'utf8');
  fs.writeFileSync(payloadPath, JSON.stringify(payload, null, 2), 'utf8');
  console.log(`✅ [Local Staging] Markdown saved to ${draftPath}`);
  console.log(`✅ [Local Staging] Medium API Payload saved to ${payloadPath}`);

  // 2. Publish or report token status
  if (MEDIUM_TOKEN) {
    const notionPageId = process.env.NOTION_PAGE_ID;
    if (!NOTION_TOKEN || !notionPageId) {
      return {
        success: false,
        staged: true,
        mode: 'local_staged',
        draftPath,
        error: 'Medium dispatch requires NOTION_API_KEY and NOTION_PAGE_ID so the staged review copy can be verified.'
      };
    }
    let stagedDraft;
    try {
      stagedDraft = await getNotionPageMarkdown(notionPageId);
    } catch (err) {
      return { success: false, staged: true, draftPath, error: `Could not read Notion review draft: ${err.message}` };
    }
    if (stagedDraft !== articleContent) {
      return { success: false, staged: true, draftPath, error: 'Notion review content does not match the local Medium draft.' };
    }
    const dispatchRecordPath = path.join(draftDir, 'medium_dispatch.json');
    const contentHash = crypto.createHash('sha256').update(articleContent).digest('hex');
    if (fs.existsSync(dispatchRecordPath)) {
      const previous = JSON.parse(fs.readFileSync(dispatchRecordPath, 'utf8'));
      if (previous.contentHash === contentHash) {
        return {
          success: false,
          error: `A Medium draft dispatch is already recorded (${previous.status}); refusing to retry without reconciliation.`,
          postId: previous.postId,
          url: previous.url
        };
      }
    }
    const dispatchRecord = { status: 'dispatching', contentHash, notionPageId, startedAt: new Date().toISOString() };
    fs.writeFileSync(dispatchRecordPath, JSON.stringify(dispatchRecord, null, 2), { mode: 0o600 });
    try {
      console.log('🔑 Authenticating with Medium API...');
      const userRes = await getMediumUser(MEDIUM_TOKEN);
      const userId = userRes.data?.id;
      console.log(`👤 Authenticated Medium user: ${userRes.data?.username} (ID: ${userId})`);

      console.log(`🚀 Dispatching post to Medium (${publishStatus})...`);
      const postRes = await createMediumPost(MEDIUM_TOKEN, userId, payload);
      const postUrl = postRes.data?.url;
      Object.assign(dispatchRecord, {
        status: 'created',
        postId: postRes.data?.id,
        url: postUrl,
        completedAt: new Date().toISOString()
      });
      fs.writeFileSync(dispatchRecordPath, JSON.stringify(dispatchRecord, null, 2), { mode: 0o600 });
      if (NOTION_TOKEN && notionPageId) {
        await updateNotionPageStatus(notionPageId, 'In Progress');
      }
      console.log(`🎉 Medium draft created. URL: ${postUrl}`);
      return { success: true, postId: postRes.data?.id, url: postUrl, mode: publishStatus };
    } catch (err) {
      dispatchRecord.status = 'dispatch_unknown';
      dispatchRecord.completedAt = new Date().toISOString();
      fs.writeFileSync(dispatchRecordPath, JSON.stringify(dispatchRecord, null, 2), { mode: 0o600 });
      console.error(`❌ Medium API publication failed: ${err.message}`);
      return { success: false, error: err.message };
    }
  } else {
    console.log('ℹ️ MEDIUM_INTEGRATION_TOKEN is not configured in .env.');
    console.log('🛡️ Local draft saved at /tmp/medium_drafts/. No Notion request was made.');
    console.log('   To publish live, add MEDIUM_INTEGRATION_TOKEN to your .env or copy the staged markdown to medium.com/new-story.');
    return { success: true, staged: true, mode: 'local_staged', draftPath };
  }
}

if (require.main === module) {
  const isPublic = process.argv.includes('--public');
  runPublisher({ public: isPublic }).catch(err => {
    console.error('Fatal publisher error:', err);
    process.exit(1);
  });
}

module.exports = { runPublisher };
