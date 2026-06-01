// Fetch plain text of a Feishu docx OR wiki node.
// Usage: node fetch_feishu.mjs <docx_token_or_wiki_node_token> [outfile]
// Note: a wiki node token usually works directly as the docx document_id for raw_content.
// Auth: refreshes FEISHU_USER_ACCESS_TOKEN via the user-token refresher if available, else
//       uses the token already in ~/zylos/.env. Needs scope docx:document:readonly.
import fs from 'fs';
import { execSync } from 'child_process';

const ENV = process.env.HOME + '/zylos/.env';
const token = process.argv[2];
const out = process.argv[3] || '/tmp/sp_source.txt';
if (!token) { console.error('usage: node fetch_feishu.mjs <token> [outfile]'); process.exit(1); }

const getEnv = k => (fs.readFileSync(ENV,'utf8').match(new RegExp('^'+k+'=(.*)$','m'))||[])[1]?.trim();

// best-effort token refresh (script lives alongside the minutes-digest refresher in this workspace)
try {
  const refresher = process.env.HOME + '/zylos/workspace/minutes-digest/refresh-token.mjs';
  if (fs.existsSync(refresher)) execSync(`node ${refresher}`, {stdio:'ignore'});
} catch {}

const tok = getEnv('FEISHU_USER_ACCESS_TOKEN');
if (!tok) { console.error('No FEISHU_USER_ACCESS_TOKEN'); process.exit(2); }

const r = await fetch(`https://open.feishu.cn/open-apis/docx/v1/documents/${token}/raw_content`,
                      { headers: { Authorization: 'Bearer ' + tok } });
const j = await r.json();
if (j.code !== 0) { console.error('fetch failed:', j.code, j.msg); process.exit(3); }
fs.writeFileSync(out, j.data.content);
console.log(`OK chars=${j.data.content.length} -> ${out}`);
