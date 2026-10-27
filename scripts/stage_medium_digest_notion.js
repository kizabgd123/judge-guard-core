#!/usr/bin/env node
/**
 * stage_medium_digest_notion.js
 * 
 * Stages the Medium Daily Digest into the Notion database 'Agent Taming Research Pipeline'
 * under Platform: 'Medium' and Status: 'In Review' (pre-publication verification gate).
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const DIGEST_MARKDOWN = fs.readFileSync(path.join(__dirname, 'medium_daily_digest.md'), 'utf8');
const DIGEST_TITLE = DIGEST_MARKDOWN.split(/\r?\n/).find(line => line.startsWith('# '))?.slice(2) || 'Medium Daily Digest';

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

if (!NOTION_TOKEN) {
  console.error('❌ Missing NOTION_API_KEY in environment');
  process.exit(1);
}

function notionRequest(method, reqPath, body) {
  return new Promise((resolve, reject) => {
    const bodyStr = body ? JSON.stringify(body) : null;
    const req = https.request({
      hostname: 'api.notion.com',
      path: `/v1${reqPath}`,
      method,
      headers: {
        'Authorization': `Bearer ${NOTION_TOKEN}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
        ...(bodyStr ? { 'Content-Length': Buffer.byteLength(bodyStr) } : {})
      }
    }, (res) => {
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

async function ensureMediumPlatformOption() {
  console.log('🔄 Checking Notion database schema for Platform: Medium...');
  const db = await notionRequest('GET', `/databases/${DATABASE_ID}`);
  const platformProp = db.properties?.['Platform'];
  if (platformProp && platformProp.select) {
    const existingOptions = platformProp.select.options || [];
    const hasMedium = existingOptions.some(o => o.name.toLowerCase() === 'medium');
    if (!hasMedium) {
      console.log('➕ Adding Medium option to Platform property...');
      const updatedOptions = [...existingOptions, { name: 'Medium', color: 'green' }];
      await notionRequest('PATCH', `/databases/${DATABASE_ID}`, {
        properties: {
          'Platform': {
            select: { options: updatedOptions }
          }
        }
      });
      console.log('✅ Added Medium to Platform property.');
    } else {
      console.log('✅ Medium option already present.');
    }
  }
}

async function stageDigest() {
  await ensureMediumPlatformOption();

  const title = DIGEST_TITLE;
  const excerpt = DIGEST_MARKDOWN.replace(/^# .*\r?\n/, '').slice(0, 900);
  const children = [];
  for (let offset = 0; offset < DIGEST_MARKDOWN.length; offset += 1800) {
    children.push({
      object: 'block',
      type: 'code',
      code: {
        rich_text: [{ type: 'text', text: { content: DIGEST_MARKDOWN.slice(offset, offset + 1800) } }],
        language: 'markdown'
      }
    });
  }

  console.log(`📝 Inserting Medium Daily Digest into Notion database ${DATABASE_ID}...`);
  const response = await notionRequest('POST', '/pages', {
    parent: { database_id: DATABASE_ID },
    properties: {
      'Action': {
        title: [{ text: { content: title } }]
      },
      'Status': {
        select: { name: 'In Progress' }
      },
      'Platform': {
        select: { name: 'Medium' }
      },
      'Post Type': {
        select: { name: 'article' }
      },
      'Details': {
        rich_text: [{ text: { content: excerpt } }]
      }
    },
    children: children
  });

  console.log(`🎉 Page created successfully in Notion!`);
  console.log(`Page ID: ${response.id}`);
  console.log(`URL: ${response.url}`);
  return response;
}

if (require.main === module) {
  stageDigest().catch(err => {
    console.error('Fatal error staging digest:', err);
    process.exit(1);
  });
}

module.exports = { stageDigest };
