import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import db
import settings

db.initialize()
settings.load_settings()

HTML = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Component Inventory</title>
<style>
:root{color-scheme:light dark;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;--bg:#0f172a;--card:#172033;--card2:#111827;--line:#334155;--muted:#94a3b8;--text:#e5e7eb;--accent:#03a9f4;--ok:#4ade80;--warn:#fbbf24}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text)}button,input,select,textarea{font:inherit;color:inherit}.wrap{max-width:1280px;margin:auto;padding:18px}.header{display:flex;justify-content:space-between;align-items:center;gap:12px}.header h2{margin:0}.nav{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0}.nav button,.btn{border:1px solid var(--line);background:var(--card);padding:9px 12px;border-radius:9px;cursor:pointer}.nav button.active,.btn.primary{background:#0369a1;border-color:#0ea5e9}.btn.danger{border-color:#7f1d1d}.bar{display:grid;grid-template-columns:minmax(250px,1fr) 220px 160px;gap:8px;margin-bottom:14px}.bar input,.bar select,.field input,.field select,.field textarea{width:100%;border:1px solid var(--line);background:var(--card2);padding:9px 10px;border-radius:8px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}.stat,.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}.stat .n{font-size:1.65rem;font-weight:750}.muted{color:var(--muted);font-size:.9rem}.product-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.product{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;cursor:pointer}.product:hover{border-color:#64748b}.top{display:flex;justify-content:space-between;gap:12px}.name{font-weight:700}.sku{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}.qty{font-size:1.15rem;font-weight:750;white-space:nowrap}.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.chip{background:#243247;border-radius:999px;padding:3px 8px;font-size:.76rem}.purchase{color:#7dd3fc}.hidden{display:none!important}.empty{text-align:center;color:var(--muted);padding:32px}.stock-row{display:grid;grid-template-columns:minmax(260px,1fr) 180px 170px;align-items:center;gap:10px}.stock-actions{display:flex;align-items:center;gap:7px;justify-content:flex-end}.stock-actions button{width:38px}.stock-actions .q{min-width:45px;text-align:center;font-weight:700}.field{margin-bottom:12px}.field label{display:block;font-size:.86rem;color:var(--muted);margin-bottom:5px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.detail-backdrop{position:fixed;inset:0;background:#0009;display:flex;align-items:flex-start;justify-content:center;padding:4vh 16px;z-index:10;overflow:auto}.detail{width:min(900px,100%);background:var(--card2);border:1px solid var(--line);border-radius:14px;padding:18px}.detail-head{display:flex;justify-content:space-between;gap:12px;align-items:start}.detail h2{margin:2px 0}.detail-cols{display:grid;grid-template-columns:1.25fr .75fr;gap:18px}.specs{display:grid;grid-template-columns:180px 1fr;gap:7px 12px;font-size:.9rem}.specs dt{color:var(--muted)}.source{display:grid;grid-template-columns:140px 1fr 150px 48px;gap:7px;margin:7px 0}.source input{border:1px solid var(--line);background:var(--card);padding:8px;border-radius:7px;min-width:0}.section-title{font-weight:700;margin:16px 0 7px}.import-layout{display:grid;grid-template-columns:1fr 1fr;gap:12px}.drop{border:1px dashed #64748b;border-radius:12px;padding:22px;text-align:center;background:var(--card)}.preview{max-height:420px;overflow:auto}.preview-row{display:grid;grid-template-columns:110px 1fr 80px 110px;gap:7px;padding:8px 0;border-bottom:1px solid #283548;font-size:.88rem}.action-create{color:var(--ok)}.action-update,.action-replace{color:#7dd3fc}.action-skip{color:var(--muted)}.action-add_quantity{color:var(--warn)}.code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#0b1220;padding:10px;border-radius:8px;overflow:auto;white-space:pre-wrap}.toast{position:fixed;right:18px;bottom:18px;background:#052e16;border:1px solid #166534;color:#dcfce7;padding:10px 14px;border-radius:10px;z-index:20}.settings-grid{display:grid;grid-template-columns:1fr;gap:12px}.switch{display:flex;gap:10px;align-items:center}.switch input{width:20px;height:20px}.actions{display:flex;gap:8px;flex-wrap:wrap}.help{font-size:.85rem;color:var(--muted);line-height:1.4}
@media(max-width:850px){.bar,.stats,.product-grid,.detail-cols,.grid2,.grid3,.import-layout{grid-template-columns:1fr}.stock-row{grid-template-columns:1fr}.stock-actions{justify-content:flex-start}.source{grid-template-columns:1fr}.preview-row{grid-template-columns:80px 1fr 65px}.preview-row span:last-child{display:none}}
</style></head>
<body><div class="wrap">
<div class="header"><div><h2>Component Inventory</h2><div class="muted">Electronics product catalog and stock</div></div><button class="btn primary" onclick="newProduct()">+ New product</button></div>
<div class="nav"><button id="tab-products" class="active" onclick="showTab('products')">Products</button><button id="tab-stock" onclick="showTab('stock')">Inventory</button><button id="tab-import" onclick="showTab('import')">Import / Export</button><button id="tab-settings" onclick="showTab('settings')">Settings</button></div>

<section id="products-panel">
<div class="stats"><div class="stat"><div class="muted">Products</div><div class="n" id="statProducts">-</div></div><div class="stat"><div class="muted">Units in stock</div><div class="n" id="statUnits">-</div></div><div class="stat"><div class="muted">Categories</div><div class="n" id="statCats">-</div></div><div class="stat"><div class="muted">Low stock (<=2)</div><div class="n" id="statLow">-</div></div></div>
<div class="bar"><input id="q" placeholder="Search products, applications, specs, 433 MHz..."><select id="cat"><option value="">All categories</option></select><select id="stockFilter"><option value="all">All stock</option><option value="in">In stock</option><option value="out">Out of stock</option></select></div>
<div id="products" class="product-grid"></div>
</section>

<section id="stock-panel" class="hidden"><div class="card"><b>Inventory</b><div class="muted">Quick stock adjustments. Product details and purchase links live in the product catalog.</div></div><div id="stockRows"></div></section>

<section id="import-panel" class="hidden">
<div class="import-layout"><div class="card"><h3>Import products</h3><div class="field"><label>File</label><input id="importFile" type="file" accept=".csv,.json,text/csv,application/json"></div><div class="field"><label>When SKU/name already exists</label><select id="importMode"><option value="update_existing">Update existing product</option><option value="skip_existing">Skip existing product</option><option value="add_quantity">Add imported quantity to stock</option><option value="replace">Replace existing product</option></select></div><div class="actions"><button class="btn" onclick="previewImport()">Preview import</button><button id="runImport" class="btn primary" onclick="runImport()" disabled>Import</button></div><p class="help">Matching uses SKU first, then exact product name. Update/replace sets the imported quantity; Add quantity increments stock.</p></div>
<div class="card"><h3>Export inventory</h3><p>Download the complete catalog including specifications, descriptions and purchase sources.</p><div class="actions"><a class="btn" href="api/export.csv" download>Download CSV</a><a class="btn" href="api/export.json" download>Download JSON</a></div><div class="section-title">CSV structured fields</div><div class="code">applications, tags, specifications and purchase_sources are JSON values inside CSV cells.</div></div></div>
<div id="previewCard" class="card hidden"><div class="top"><div><h3 style="margin:0">Import preview</h3><div class="muted" id="previewSummary"></div></div></div><div id="previewRows" class="preview"></div></div>
</section>

<section id="settings-panel" class="hidden"><div class="settings-grid"><div class="card"><h3>Home Assistant MCP (recommended)</h3><div class="field"><label>Home Assistant / Nabu Casa MCP endpoint</label><div class="actions"><input id="haMcpEndpoint" readonly style="flex:1"><button class="btn" onclick="copyValue('haMcpEndpoint')">Copy</button></div></div><p class="help">This endpoint is served by Home Assistant itself. When you open this page through Nabu Casa, the field above automatically uses the same public HTTPS origin. No router port forwarding is required. Requires the companion Component Inventory integration and Home Assistant's Model Context Protocol Server integration.</p><div class="code">/api/mcp/component_inventory</div></div><div class="card"><h3>Local app connection</h3><div class="field"><label>Direct LAN MCP endpoint</label><div class="actions"><input id="endpoint" readonly style="flex:1" value="http://HOME_ASSISTANT_IP:8098/mcp"><button class="btn" onclick="copyValue('endpoint')">Copy</button></div></div><div class="field"><label>Local app API token</label><div class="actions"><input id="token" type="password" readonly style="flex:1"><button class="btn" id="showToken" onclick="toggleToken()">Show</button><button class="btn" onclick="copyValue('token')">Copy</button></div></div><p class="help">The companion Home Assistant integration uses this token to access the app locally. External MCP clients using the Home Assistant endpoint authenticate with Home Assistant OAuth or a Home Assistant access token instead.</p><label class="switch"><input id="writes" type="checkbox" onchange="saveWrites()"><span>Allow inventory quantity changes through MCP</span></label><p class="help">Keep this off if coding agents should only search and plan with available parts.</p><button class="btn danger" onclick="rotateToken()">Generate new local API token</button></div><div class="card"><h3>MCP tools</h3><div class="code">search_inventory
get_inventory_item
get_inventory_item_by_sku
list_inventory
list_inventory_categories
adjust_inventory_quantity</div></div></div></section>
</div>

<div id="detailBackdrop" class="detail-backdrop hidden"><div class="detail"><div class="detail-head"><div><div id="dSku" class="sku"></div><h2 id="dName"></h2><div id="dCategory" class="muted"></div></div><div class="actions"><button class="btn" onclick="editCurrent()">Edit</button><button class="btn" onclick="closeDetail()">Close</button></div></div><div class="detail-cols"><div><div class="section-title">Description</div><div id="dDescription"></div><div class="section-title">Typical applications</div><div id="dApplications" class="chips"></div><div class="section-title">Specifications</div><dl id="dSpecs" class="specs"></dl><div class="section-title">Purchase sources</div><div id="dSources"></div><div class="section-title">Notes</div><div id="dNotes" class="muted"></div></div><div><div class="stat"><div class="muted">On hand</div><div id="dQty" class="n">0</div><div id="dUnit" class="muted">pcs</div></div><div class="card"><div class="muted">Location</div><div id="dLocation">-</div></div><div class="card"><div class="muted">Manufacturer / model</div><div id="dModel">-</div></div><div class="actions"><button class="btn" onclick="quickAdjust(-1)">-1</button><button class="btn" onclick="quickAdjust(1)">+1</button></div></div></div></div></div>

<div id="editBackdrop" class="detail-backdrop hidden"><div class="detail"><div class="detail-head"><div><div class="sku">PRODUCT EDITOR</div><h2 id="editTitle">Product</h2></div><button class="btn" onclick="closeEdit()">Close</button></div><div class="grid2"><div class="field"><label>SKU</label><input id="eSku"></div><div class="field"><label>Product name</label><input id="eName"></div><div class="field"><label>Category</label><input id="eCategory"></div><div class="field"><label>Subcategory</label><input id="eSubcategory"></div><div class="field"><label>Manufacturer</label><input id="eManufacturer"></div><div class="field"><label>Model</label><input id="eModel"></div><div class="field"><label>Quantity</label><input id="eQuantity" type="number" min="0"></div><div class="field"><label>Unit</label><input id="eUnit" value="pcs"></div><div class="field"><label>Location</label><input id="eLocation"></div><div class="field"><label>Product page URL</label><input id="eProductUrl" type="url"></div><div class="field"><label>Datasheet URL</label><input id="eDatasheet" type="url"></div></div><div class="field"><label>Description</label><textarea id="eDescription" rows="3"></textarea></div><div class="field"><label>Applications (one per line)</label><textarea id="eApplications" rows="4"></textarea></div><div class="field"><label>Tags (comma separated)</label><input id="eTags"></div><div class="field"><label>Specifications (one per line: Key: Value)</label><textarea id="eSpecs" rows="7"></textarea></div><div class="field"><label>Notes</label><textarea id="eNotes" rows="3"></textarea></div><div class="section-title">Purchase sources</div><div id="sourceEditor"></div><button class="btn" onclick="addSourceRow()">+ Add purchase source</button><div class="actions" style="margin-top:18px"><button class="btn primary" onclick="saveProduct()">Save product</button></div></div></div>
<div id="toast" class="toast hidden"></div>
<script>
let items=[], current=null, editingId=null, importText='', importFormat='';
const $=id=>document.getElementById(id);
function toast(msg){$('toast').textContent=msg;$('toast').classList.remove('hidden');setTimeout(()=>$('toast').classList.add('hidden'),2200)}
async function api(path, opts={}){const r=await fetch(path,opts);const text=await r.text();let body={};try{body=text?JSON.parse(text):{}}catch{body={error:text}}if(!r.ok)throw new Error(body.error||('HTTP '+r.status));return body}
function showTab(name){['products','stock','import','settings'].forEach(x=>{$(x+'-panel').classList.toggle('hidden',x!==name);$('tab-'+x).classList.toggle('active',x===name)});if(name==='settings')loadSettings()}
function escapeHtml(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function sourceButtons(p){return (p.purchase_sources||[]).filter(s=>s.url).slice(0,3).map(s=>`<a class="chip purchase" href="${escapeHtml(s.url)}" target="_blank" onclick="event.stopPropagation()">${escapeHtml(s.vendor||'Buy')} ↗</a>`).join('')}
function render(){const q=$('q').value.toLowerCase().trim(),cat=$('cat').value,stock=$('stockFilter').value;const shown=items.filter(p=>(!cat||p.category===cat)&&(!q||JSON.stringify(p).toLowerCase().includes(q))&&(stock==='all'||(stock==='in'?p.quantity>0:p.quantity===0)));$('products').innerHTML=shown.length?shown.map(p=>`<div class="product" onclick="openDetail(${p.id})"><div class="top"><div><div class="sku">${escapeHtml(p.sku)}</div><div class="name">${escapeHtml(p.name)}</div><div class="muted">${escapeHtml(p.category)}${p.subcategory?' / '+escapeHtml(p.subcategory):''}</div></div><div class="qty">${p.quantity} <span class="muted">${escapeHtml(p.unit)}</span></div></div><p>${escapeHtml(p.description||'')}</p><div class="chips">${(p.applications||[]).slice(0,3).map(x=>`<span class="chip">${escapeHtml(x)}</span>`).join('')}${sourceButtons(p)}</div></div>`).join(''):'<div class="empty">No products found.</div>';renderStock();updateStats()}
function renderStock(){$('stockRows').innerHTML=items.map(p=>`<div class="card stock-row"><div><div class="sku">${escapeHtml(p.sku)}</div><div class="name">${escapeHtml(p.name)}</div><div class="muted">${escapeHtml(p.location||'No location')}</div></div><div class="muted">${escapeHtml(p.category)}</div><div class="stock-actions"><button class="btn" onclick="adjust(${p.id},-1)">-</button><span class="q">${p.quantity}</span><button class="btn" onclick="adjust(${p.id},1)">+</button><span class="muted">${escapeHtml(p.unit)}</span></div></div>`).join('')}
function updateStats(){$('statProducts').textContent=items.length;$('statUnits').textContent=items.reduce((a,b)=>a+b.quantity,0);$('statCats').textContent=new Set(items.map(x=>x.category).filter(Boolean)).size;$('statLow').textContent=items.filter(x=>x.quantity<=2).length}
async function load(){const data=await api('api/items');items=data.items;const cats=[...new Set(items.map(x=>x.category).filter(Boolean))].sort();$('cat').innerHTML='<option value="">All categories</option>'+cats.map(c=>`<option>${escapeHtml(c)}</option>`).join('');render()}
async function adjust(id,delta){await api(`api/items/${id}/adjust`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({delta,reason:'Web UI'})});await load();if(current&&current.id===id)openDetail(id)}
function openDetail(id){current=items.find(x=>x.id===id);if(!current)return;$('dSku').textContent=current.sku;$('dName').textContent=current.name;$('dCategory').textContent=[current.category,current.subcategory].filter(Boolean).join(' / ');$('dDescription').textContent=current.description||'-';$('dApplications').innerHTML=(current.applications||[]).map(x=>`<span class="chip">${escapeHtml(x)}</span>`).join('')||'<span class="muted">None</span>';$('dSpecs').innerHTML=Object.entries(current.specifications||{}).map(([k,v])=>`<dt>${escapeHtml(k)}</dt><dd>${escapeHtml(v)}</dd>`).join('')||'<span class="muted">No specifications</span>';$('dQty').textContent=current.quantity;$('dUnit').textContent=current.unit;$('dLocation').textContent=current.location||'Not set';$('dModel').textContent=[current.manufacturer,current.model].filter(Boolean).join(' / ')||'Not set';$('dNotes').textContent=current.notes||'-';const src=(current.purchase_sources||[]).map(s=>`<div><a class="purchase" href="${escapeHtml(s.url)}" target="_blank">${escapeHtml(s.vendor||'Purchase link')} ↗</a>${s.part_number?' <span class="muted">'+escapeHtml(s.part_number)+'</span>':''}</div>`).join('');$('dSources').innerHTML=src||'<div class="muted">No purchase links yet.</div>';$('detailBackdrop').classList.remove('hidden')}
function closeDetail(){$('detailBackdrop').classList.add('hidden')}
async function quickAdjust(delta){if(current)await adjust(current.id,delta)}
function linesToSpecs(text){const o={};text.split('\n').map(x=>x.trim()).filter(Boolean).forEach(line=>{const i=line.indexOf(':');if(i>0)o[line.slice(0,i).trim()]=line.slice(i+1).trim()});return o}
function specsToLines(o){return Object.entries(o||{}).map(([k,v])=>`${k}: ${v}`).join('\n')}
function sourceRow(s={}){return `<div class="source"><input class="srcVendor" placeholder="Vendor (AliExpress)" value="${escapeHtml(s.vendor||'')}"><input class="srcUrl" placeholder="https://..." value="${escapeHtml(s.url||'')}"><input class="srcPart" placeholder="Part / listing ID" value="${escapeHtml(s.part_number||'')}"><button class="btn" type="button" onclick="this.parentElement.remove()">x</button></div>`}
function addSourceRow(s={}){$('sourceEditor').insertAdjacentHTML('beforeend',sourceRow(s))}
function newProduct(){editingId=null;current=null;$('editTitle').textContent='New product';['Sku','Name','Category','Subcategory','Manufacturer','Model','Location','ProductUrl','Datasheet','Description','Notes'].forEach(x=>$('e'+x).value='');$('eQuantity').value=0;$('eUnit').value='pcs';$('eApplications').value='';$('eTags').value='';$('eSpecs').value='';$('sourceEditor').innerHTML='';addSourceRow();$('editBackdrop').classList.remove('hidden')}
function editCurrent(){if(!current)return;editingId=current.id;$('editTitle').textContent='Edit product';$('eSku').value=current.sku||'';$('eName').value=current.name||'';$('eCategory').value=current.category||'';$('eSubcategory').value=current.subcategory||'';$('eManufacturer').value=current.manufacturer||'';$('eModel').value=current.model||'';$('eQuantity').value=current.quantity;$('eUnit').value=current.unit||'pcs';$('eLocation').value=current.location||'';$('eProductUrl').value=current.product_url||'';$('eDatasheet').value=current.datasheet_url||'';$('eDescription').value=current.description||'';$('eApplications').value=(current.applications||[]).join('\n');$('eTags').value=(current.tags||[]).join(', ');$('eSpecs').value=specsToLines(current.specifications);$('eNotes').value=current.notes||'';$('sourceEditor').innerHTML='';(current.purchase_sources||[]).forEach(addSourceRow);if(!(current.purchase_sources||[]).length)addSourceRow();closeDetail();$('editBackdrop').classList.remove('hidden')}
function closeEdit(){$('editBackdrop').classList.add('hidden')}
async function saveProduct(){const sources=[...document.querySelectorAll('.source')].map(r=>({vendor:r.querySelector('.srcVendor').value.trim(),url:r.querySelector('.srcUrl').value.trim(),part_number:r.querySelector('.srcPart').value.trim()})).filter(s=>s.vendor||s.url||s.part_number);const data={sku:$('eSku').value.trim(),name:$('eName').value.trim(),category:$('eCategory').value.trim(),subcategory:$('eSubcategory').value.trim(),manufacturer:$('eManufacturer').value.trim(),model:$('eModel').value.trim(),quantity:Number($('eQuantity').value||0),unit:$('eUnit').value.trim()||'pcs',location:$('eLocation').value.trim(),description:$('eDescription').value.trim(),applications:$('eApplications').value.split('\n').map(x=>x.trim()).filter(Boolean),tags:$('eTags').value.split(',').map(x=>x.trim()).filter(Boolean),specifications:linesToSpecs($('eSpecs').value),notes:$('eNotes').value.trim(),datasheet_url:$('eDatasheet').value.trim(),product_url:$('eProductUrl').value.trim(),purchase_sources:sources};if(!data.name){alert('Product name is required');return}const path=editingId?`api/items/${editingId}`:'api/items';await api(path,{method:editingId?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});closeEdit();await load();toast('Product saved')}
async function readImportFile(){const f=$('importFile').files[0];if(!f)throw new Error('Choose a CSV or JSON file first');importText=await f.text();importFormat=f.name.toLowerCase().endsWith('.json')?'json':'csv';return {text:importText,format:importFormat}}
async function previewImport(){try{const f=await readImportFile();const mode=$('importMode').value;const data=await api(`api/import/preview?format=${f.format}&mode=${mode}`,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:f.text});$('previewRows').innerHTML=data.rows.map(r=>`<div class="preview-row"><span class="sku">${escapeHtml(r.sku)}</span><span>${escapeHtml(r.name)}</span><span>${r.quantity}</span><span class="action-${r.action}">${r.action.replace('_',' ')}</span></div>`).join('');const actions={};data.rows.forEach(r=>actions[r.action]=(actions[r.action]||0)+1);$('previewSummary').textContent=data.rows.length+' rows - '+Object.entries(actions).map(([k,v])=>v+' '+k.replace('_',' ')).join(', ');$('previewCard').classList.remove('hidden');$('runImport').disabled=false}catch(e){alert(e.message)}}
async function runImport(){try{if(!importText)await readImportFile();const mode=$('importMode').value;const data=await api(`api/import?format=${importFormat}&mode=${mode}`,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:importText});toast('Import complete');$('previewSummary').textContent='Import complete: '+JSON.stringify(data.result);await load()}catch(e){alert(e.message)}}
async function loadSettings(){const s=await api('api/settings');$('token').value=s.api_token;$('writes').checked=!!s.allow_mcp_writes;$('haMcpEndpoint').value=window.location.origin+'/api/mcp/component_inventory'}
function toggleToken(){const t=$('token');t.type=t.type==='password'?'text':'password';$('showToken').textContent=t.type==='password'?'Show':'Hide'}
async function copyValue(id){await navigator.clipboard.writeText($(id).value);toast('Copied')}
async function saveWrites(){await api('api/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({allow_mcp_writes:$('writes').checked})});toast('Settings saved')}
async function rotateToken(){if(!confirm('Generate a new token? Existing MCP clients will stop working until updated.'))return;const s=await api('api/settings/rotate-token',{method:'POST'});$('token').value=s.api_token;toast('New token generated')}
$('q').addEventListener('input',render);$('cat').addEventListener('change',render);$('stockFilter').addEventListener('change',render);load();
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print('[web] ' + fmt % args)

    def _json(self, status, data, headers=None):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _text(self, status, body, content_type='text/plain; charset=utf-8', headers=None):
        data = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        length = int(self.headers.get('Content-Length', '0') or 0)
        return self.rfile.read(length).decode('utf-8') if length else ''

    def _body_json(self):
        raw = self._body()
        return json.loads(raw or '{}')

    def do_GET(self):
        path = urlparse(self.path).path.lstrip('/')
        if path in ('', 'index.html'):
            return self._text(200, HTML, 'text/html; charset=utf-8')
        if path == 'api/items':
            return self._json(200, {'items': db.list_items(limit=2000)})
        if path == 'api/categories':
            return self._json(200, {'categories': db.categories()})
        if path == 'api/settings':
            return self._json(200, settings.load_settings())
        if path == 'api/export.json':
            return self._text(200, db.export_json(), 'application/json; charset=utf-8', {'Content-Disposition': 'attachment; filename="component_inventory.json"'})
        if path == 'api/export.csv':
            return self._text(200, db.export_csv(), 'text/csv; charset=utf-8', {'Content-Disposition': 'attachment; filename="component_inventory.csv"'})
        if path.startswith('api/items/'):
            parts = path.split('/')
            if len(parts) == 3 and parts[2].isdigit():
                item = db.get_item(int(parts[2]))
                return self._json(200 if item else 404, item or {'error': 'Not found'})
        return self._json(404, {'error': 'Not found'})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.lstrip('/')
        qs = parse_qs(parsed.query)
        try:
            if path == 'api/items':
                return self._json(201, db.create_item(self._body_json()))
            if path.startswith('api/items/') and path.endswith('/adjust'):
                item_id = int(path.split('/')[2])
                data = self._body_json()
                return self._json(200, db.adjust_quantity(item_id, int(data.get('delta', 0)), str(data.get('reason', 'Web UI'))))
            if path == 'api/import/preview':
                fmt = qs.get('format', ['csv'])[0]
                mode = qs.get('mode', ['update_existing'])[0]
                rows = db.parse_import(self._body(), fmt)
                return self._json(200, {'rows': db.preview_import(rows, mode)})
            if path == 'api/import':
                fmt = qs.get('format', ['csv'])[0]
                mode = qs.get('mode', ['update_existing'])[0]
                if mode not in ('update_existing','skip_existing','add_quantity','replace'):
                    raise ValueError('Invalid import mode')
                rows = db.parse_import(self._body(), fmt)
                return self._json(200, {'result': db.import_items(rows, mode), 'rows': len(rows)})
            if path == 'api/settings/rotate-token':
                return self._json(200, settings.rotate_token())
        except Exception as e:
            return self._json(400, {'error': str(e)})
        return self._json(404, {'error': 'Not found'})

    def do_PUT(self):
        path = urlparse(self.path).path.lstrip('/')
        try:
            if path == 'api/settings':
                return self._json(200, settings.update_settings(self._body_json()))
            if path.startswith('api/items/'):
                parts = path.split('/')
                if len(parts) == 3 and parts[2].isdigit():
                    return self._json(200, db.update_item(int(parts[2]), self._body_json()))
        except Exception as e:
            return self._json(400, {'error': str(e)})
        return self._json(404, {'error': 'Not found'})

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8099), Handler).serve_forever()
