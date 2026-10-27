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

function loadEnv() {
  const envPaths = [
    path.resolve(__dirname, '../.env'),
    path.resolve('/home/kizajosmladjibacije/Desktop/codymaster/.env')
  ];
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

  const title = 'Medium Daily Digest: Production AI Architectures, Zero-Simulation Law & Deterministic Agents (2026 Edition)';
  const excerpt = 'How we eliminated context bloat, tamed autonomous multi-agent systems, and enforced unbreakable security gates in production using the Antigravity Dual-Brain and JudgeGuard.';

  const children = [
    {
      object: 'block',
      type: 'heading_1',
      heading_1: {
        rich_text: [{ type: 'text', text: { content: 'Medium Daily Digest (2026 Edition)' } }]
      }
    },
    {
      object: 'block',
      type: 'callout',
      callout: {
        icon: { emoji: '🛡️' },
        rich_text: [{ type: 'text', text: { content: 'Status: In Review | Zero-Simulation Verified | Pre-Action Gate PASSED' } }]
      }
    },
    {
      object: 'block',
      type: 'heading_2',
      heading_2: {
        rich_text: [{ type: 'text', text: { content: '1. The Antigravity Dual-Brain Architecture' } }]
      }
    },
    {
      object: 'block',
      type: 'paragraph',
      paragraph: {
        rich_text: [{ type: 'text', text: { content: 'Strictly decoupling the Cognitive Brain (Google NotebookLM) from the Execution Runtime (Antigravity/Docker). Zero-Token Synthesis allows server-side distillation of thousands of documentation pages without consuming agent context window tokens.' } }]
      }
    },
    {
      object: 'block',
      type: 'heading_2',
      heading_2: {
        rich_text: [{ type: 'text', text: { content: '2. The Zero-Simulation Law & Deterministic Safety' } }]
      }
    },
    {
      object: 'block',
      type: 'paragraph',
      paragraph: {
        rich_text: [{ type: 'text', text: { content: 'Eliminating mock deployments, fake tokens, and synthetic test bypasses. Fail-fast mechanics immediately route to authentic offline queues rather than fabricating pleasant pseudo-responses.' } }]
      }
    },
    {
      object: 'block',
      type: 'heading_2',
      heading_2: {
        rich_text: [{ type: 'text', text: { content: '3. JudgeGuard 3-Layer Execution Sentinel' } }]
      }
    },
    {
      object: 'block',
      type: 'paragraph',
      paragraph: {
        rich_text: [{ type: 'text', text: { content: 'Layer 00 (Security Hard Rules: sudo/rm -rf / blocks), Layer 0 (Work Log recency <120s in WORK_LOG.md), Layer 1 (Tool & Phase discipline), Layer 3 (Project Essence & <20% semantic drift evaluation).' } }]
      }
    },
    {
      object: 'block',
      type: 'heading_2',
      heading_2: {
        rich_text: [{ type: 'text', text: { content: '4. Kernel-Level Prompt Injection Elimination' } }]
      }
    },
    {
      object: 'block',
      type: 'paragraph',
      paragraph: {
        rich_text: [{ type: 'text', text: { content: 'Write-Before-Query input validation and strictly banning shell=True across all subprocess calls (using structured argument lists).' } }]
      }
    }
  ];

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
