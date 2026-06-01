// Import a local Markdown file as a Feishu docx, set tenant-readable + owner full_access,
// and print the doc URL. Usage:
//   node feishu_doc.mjs <markdown_path> <doc_title> [owner_open_id]
// Auth: app tenant token from FEISHU_APP_ID / FEISHU_APP_SECRET in ~/zylos/.env.
import fs from 'fs';

const ENV = process.env.HOME + '/zylos/.env';
const g = k => (fs.readFileSync(ENV,'utf8').match(new RegExp('^'+k+'=(.*)$','m'))||[])[1]?.trim();
const [mdPath, title, ownerArg] = process.argv.slice(2);
if (!mdPath || !title) { console.error('usage: node feishu_doc.mjs <md> <title> [owner_open_id]'); process.exit(1); }
const OWNER = ownerArg || g('OWNER_OPEN_ID') || '';
const B = 'https://open.feishu.cn/open-apis';
const j = async (u,o)=> (await (await fetch(u,o)).json());

const tok = (await j(`${B}/auth/v3/tenant_access_token/internal`, {method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({app_id:g('FEISHU_APP_ID'), app_secret:g('FEISHU_APP_SECRET')})})).tenant_access_token;
if (!tok) { console.error('no tenant token'); process.exit(2); }
const H = { Authorization:'Bearer '+tok };

const folder = (await j(`${B}/drive/explorer/v2/root_folder/meta`, {headers:H})).data?.token;
const md = fs.readFileSync(mdPath);
const fname = title.replace(/[\/\\]/g,'_') + '.md';
const fd = new FormData();
fd.append('file_name', fname); fd.append('parent_type','explorer'); fd.append('parent_node', folder);
fd.append('size', String(md.length)); fd.append('file', new Blob([md]), fname);
const file_token = (await (await fetch(`${B}/drive/v1/files/upload_all`, {method:'POST',headers:H,body:fd})).json()).data?.file_token;
if (!file_token) { console.error('upload failed'); process.exit(3); }

const ticket = (await j(`${B}/drive/v1/import_tasks`, {method:'POST', headers:{...H,'Content-Type':'application/json'},
  body:JSON.stringify({file_extension:'md', file_token, type:'docx', file_name:title, point:{mount_type:1, mount_key:folder}})})).data?.ticket;
if (!ticket) { console.error('import task failed'); process.exit(4); }

let docToken, url;
for (let i=0;i<25;i++){
  await new Promise(r=>setTimeout(r,1500));
  const job = (await j(`${B}/drive/v1/import_tasks/${ticket}`, {headers:H})).data?.result;
  if (job && job.job_status===0) { docToken=job.token; url=job.url; break; }
}
if (!docToken) { console.error('import not ready'); process.exit(5); }

const H2 = {...H,'Content-Type':'application/json'};
await j(`${B}/drive/v1/permissions/${docToken}/public?type=docx`, {method:'PATCH', headers:H2,
  body:JSON.stringify({link_share_entity:'tenant_readable'})});
if (OWNER) await j(`${B}/drive/v1/permissions/${docToken}/members?type=docx&need_notification=false`, {method:'POST', headers:H2,
  body:JSON.stringify({member_type:'openid', member_id:OWNER, perm:'full_access'})});

console.log('URL:', url);
