#!/usr/bin/env python3
"""Calgary Industrial Lead Generator - Web GUI"""

import os, csv, json, re, time, io, hashlib
from datetime import datetime, timedelta
from pathlib import Path

try:
    from flask import Flask, request, jsonify, Response
    import requests
except ImportError:
    print("\nERROR: Run 'pip install flask requests beautifulsoup4' first\n")
    exit(1)

app = Flask(__name__)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def load_json(f): 
    try: return json.load(open(f)) if f.exists() else {}
    except: return {}

def save_json(f, d): json.dump(d, open(f,'w'), indent=2)

def scrape_website(url):
    result = {'emails': [], 'phones': []}
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        emails = list(set(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', r.text.lower())))
        result['emails'] = [e for e in emails if 'example.com' not in e and 'sentry' not in e][:5]
        for p in re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', r.text)[:5]:
            d = re.sub(r'[^\d]', '', p)
            if len(d) == 10: result['phones'].append('({}) {}-{}'.format(d[:3], d[3:6], d[6:]))
    except: pass
    return result

def detect_signals(url):
    signals, score = [], 0
    kw = {'rfp': (['rfp','rfq','tender'], 30), 'expansion': (['expansion','new facility'], 25), 
          'equipment': (['new equipment','upgrading'], 20), 'hiring': (['hiring','careers'], 10)}
    try:
        text = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}).text.lower()
        for t, (words, pts) in kw.items():
            for w in words:
                if w in text: signals.append({'type': t, 'keyword': w}); score += pts; break
    except: pass
    return signals, min(score, 100)

HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Calgary Lead Generator</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:#f0f2f5}
.header{background:#1a3a5c;color:#fff;padding:20px;text-align:center}
.container{max-width:1200px;margin:0 auto;padding:20px}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}
.stat{background:#fff;padding:15px;border-radius:8px;text-align:center;flex:1;min-width:100px}
.stat b{font-size:24px;color:#1a3a5c;display:block}
.tabs{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:20px;background:#fff;padding:10px;border-radius:8px}
.tab{padding:10px 20px;border:none;background:#e8e8e8;cursor:pointer;border-radius:5px}
.tab:hover{background:#d0d0d0}
.tab.on{background:#1a3a5c;color:#fff}
.panel{display:none;background:#fff;padding:20px;border-radius:8px}
.panel.on{display:block}
.card{background:#f8f9fa;padding:15px;border-radius:8px;margin-bottom:15px}
.row{display:flex;flex-wrap:wrap;gap:15px;margin-bottom:15px}
.col{flex:1;min-width:200px}
label{display:block;margin-bottom:5px;font-size:12px;font-weight:bold}
input,select,textarea{width:100%;padding:10px;border:1px solid #ddd;border-radius:5px;font-size:14px}
.btn{padding:10px 20px;border:none;border-radius:5px;cursor:pointer;margin:5px 5px 5px 0}
.btn-blue{background:#1a3a5c;color:#fff}
.btn-green{background:#28a745;color:#fff}
.btn-gray{background:#e8e8e8}
.btn-red{background:#dc3545;color:#fff}
.btn-sm{padding:5px 10px;font-size:12px}
table{width:100%;border-collapse:collapse;margin-top:15px}
th,td{padding:10px;text-align:left;border-bottom:1px solid #eee;font-size:13px}
th{background:#f0f2f5;font-size:11px;text-transform:uppercase}
.sig{padding:3px 10px;border-radius:15px;font-size:12px;font-weight:bold}
.sig-h{background:#d4edda;color:#155724}
.sig-m{background:#fff3cd;color:#856404}
.sig-l{background:#e9ecef;color:#666}
.msg{padding:15px;border-radius:5px;margin-bottom:15px}
.msg-ok{background:#d4edda;color:#155724}
.msg-err{background:#f8d7da;color:#721c24}
.msg-info{background:#cce5ff;color:#004085}
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:1000;align-items:center;justify-content:center}
.modal.on{display:flex}
.mbox{background:#fff;padding:25px;border-radius:10px;width:90%;max-width:600px;max-height:90vh;overflow-y:auto}
.mhead{display:flex;justify-content:space-between;margin-bottom:20px}
.mclose{background:none;border:none;font-size:24px;cursor:pointer}
.tender{border:1px solid #ddd;padding:15px;border-radius:8px;margin-bottom:10px}
.tender.new{border-left:4px solid #007bff}
.ebox{background:#f8f9fa;border:1px solid #ddd;padding:15px;border-radius:8px;margin-top:15px}
.ebox pre{white-space:pre-wrap;font-family:Arial;font-size:13px}
.hide{display:none}
</style>
</head>
<body>
<div class="header"><h1>Calgary Industrial Lead Generator</h1></div>
<div class="container">

<div class="stats">
<div class="stat"><b id="st-total">0</b><small>Leads</small></div>
<div class="stat"><b id="st-email">0</b><small>With Email</small></div>
<div class="stat"><b id="st-contact">0</b><small>Contacted</small></div>
<div class="stat"><b id="st-follow">0</b><small>Follow-ups</small></div>
<div class="stat"><b id="st-tender">0</b><small>Tenders</small></div>
</div>

<div class="tabs">
<button class="tab on" onclick="showTab('leads', this)">Leads</button>
<button class="tab" onclick="showTab('add', this)">Add New</button>
<button class="tab" onclick="showTab('import', this)">Import</button>
<button class="tab" onclick="showTab('outreach', this)">Outreach</button>
<button class="tab" onclick="showTab('tenders', this)">Tenders</button>
<button class="tab" onclick="showTab('settings', this)">Settings</button>
</div>

<div class="panel on" id="p-leads">
<div class="row">
<div class="col"><input id="search" placeholder="Search..." onkeyup="render()"></div>
<div class="col" style="flex:0 0 140px"><select id="f-status" onchange="render()"><option value="">All Status</option><option>New</option><option>Contacted</option><option>Qualified</option></select></div>
<div class="col" style="flex:0 0 140px"><select id="f-out" onchange="render()"><option value="">All Outreach</option><option value="not_started">Not Started</option><option value="sent">Sent</option><option value="replied">Replied</option></select></div>
</div>
<button class="btn btn-gray btn-sm" onclick="load()">Refresh</button>
<button class="btn btn-gray btn-sm" onclick="location.href='/api/export'">Export</button>
<table><thead><tr><th>Company</th><th>Contact</th><th>Email</th><th>Signal</th><th>Status</th><th></th></tr></thead><tbody id="tbl"></tbody></table>
</div>

<div class="panel" id="p-add">
<div class="card"><h3 style="margin-bottom:15px">Add Company</h3>
<div id="add-msg"></div>
<div class="row"><div class="col"><label>Company *</label><input id="a-company"></div><div class="col"><label>Website</label><input id="a-web" placeholder="https://"></div></div>
<div class="row"><div class="col"><label>Industry</label><select id="a-ind"><option value="">Select...</option><option>Manufacturing</option><option>Metal Fabrication</option><option>Oil & Gas</option><option>Construction</option><option>Other</option></select></div><div class="col"><label>Source</label><input id="a-src"></div></div>
<div class="row"><div class="col"><label>Email</label><input id="a-email"></div><div class="col"><label>Phone</label><input id="a-phone"></div></div>
<div class="row"><div class="col"><label>Contact Name</label><input id="a-contact"></div><div class="col"><label>Title</label><input id="a-title"></div></div>
<div class="col"><label>Notes</label><textarea id="a-notes" rows="2"></textarea></div>
<br><button class="btn btn-blue" onclick="addLead()">Add</button><button class="btn btn-green" onclick="addScrape()">Add & Scrape</button>
</div></div>

<div class="panel" id="p-import">
<div class="card"><h3 style="margin-bottom:15px">Import LinkedIn</h3>
<p style="color:#666;font-size:13px;margin-bottom:10px">Export from LinkedIn: Settings > Data Privacy > Get a copy of your data > Connections</p>
<div id="li-msg"></div>
<input type="file" id="li-file" accept=".csv"><br><br>
<label><input type="checkbox" id="li-filter" checked> Only target titles</label><br><br>
<button class="btn btn-blue" onclick="importLI()">Import</button>
</div>
<div class="card"><h3 style="margin-bottom:15px">Import CSV</h3>
<div id="csv-msg"></div>
<input type="file" id="csv-file" accept=".csv"><br><br>
<button class="btn btn-blue" onclick="importCSV()">Import</button>
</div></div>

<div class="panel" id="p-outreach">
<div class="card"><h3 style="margin-bottom:15px">Outreach Stats</h3>
<div class="stats"><div class="stat"><b id="o-ns">0</b><small>Not Started</small></div><div class="stat"><b id="o-sent">0</b><small>Sent</small></div><div class="stat"><b id="o-rep">0</b><small>Replied</small></div><div class="stat"><b id="o-due">0</b><small>Due</small></div></div>
</div>
<div class="card"><h3 style="margin-bottom:15px">Due Follow-ups</h3><div id="due-list"></div></div>
<div class="card"><h3 style="margin-bottom:15px">Draft Email</h3>
<div class="row"><div class="col"><label>Lead</label><select id="d-lead"></select></div><div class="col"><label>Template</label><select id="d-tpl"><option value="first">First Touch</option><option value="fu1">Follow-up 1</option><option value="fu2">Follow-up 2</option></select></div></div>
<button class="btn btn-blue" onclick="genDraft()">Generate</button>
<div id="draft-box" class="ebox hide"><h4 id="d-subj"></h4><pre id="d-body"></pre><br><button class="btn btn-gray btn-sm" onclick="copyDraft()">Copy</button><button class="btn btn-green btn-sm" onclick="markSent()">Mark Sent</button></div>
</div></div>

<div class="panel" id="p-tenders">
<div class="card"><h3 style="margin-bottom:15px">Tenders</h3>
<div id="t-msg"></div>
<button class="btn btn-blue" onclick="checkTenders()">Check for Tenders</button>
<div id="t-list" style="margin-top:15px"></div>
</div></div>

<div class="panel" id="p-settings">
<div class="card"><h3 style="margin-bottom:15px">Your Info (for emails)</h3>
<div id="cfg-msg"></div>
<div class="row"><div class="col"><label>Name</label><input id="c-name"></div><div class="col"><label>Company</label><input id="c-comp"></div></div>
<div class="row"><div class="col"><label>Phone</label><input id="c-phone"></div><div class="col"><label>Email</label><input id="c-email"></div></div>
</div>
<div class="card"><h3 style="margin-bottom:15px">Jobber</h3>
<div class="row"><div class="col"><label>Client ID</label><input id="c-jid"></div><div class="col"><label>Secret</label><input id="c-jsec" type="password"></div></div>
</div>
<div class="card"><h3 style="margin-bottom:15px">Tender Keywords</h3>
<div class="col"><label>Keywords (comma sep)</label><input id="c-kw"></div>
<div class="col"><label>Locations</label><input id="c-loc"></div>
</div>
<button class="btn btn-blue" onclick="saveCfg()">Save</button>
</div>

</div>

<div class="modal" id="modal">
<div class="mbox">
<div class="mhead"><h3>Edit Lead</h3><button class="mclose" onclick="closeModal()">&times;</button></div>
<input type="hidden" id="e-id">
<div class="row"><div class="col"><label>Company</label><input id="e-comp"></div><div class="col"><label>Website</label><input id="e-web"></div></div>
<div class="row"><div class="col"><label>Email</label><input id="e-email"></div><div class="col"><label>Phone</label><input id="e-phone"></div></div>
<div class="row"><div class="col"><label>Industry</label><input id="e-ind"></div><div class="col"><label>Status</label><select id="e-status"><option>New</option><option>Contacted</option><option>Qualified</option></select></div></div>
<div class="row"><div class="col"><label>Contact</label><input id="e-contact"></div><div class="col"><label>Title</label><input id="e-title"></div></div>
<div class="col"><label>Notes</label><textarea id="e-notes" rows="2"></textarea></div>
<div id="e-sig" style="margin:15px 0"></div>
<button class="btn btn-blue" onclick="saveLead()">Save</button>
<button class="btn btn-green" onclick="scrapeLead()">Scrape</button>
<button class="btn btn-green" onclick="detectSig()">Signals</button>
<button class="btn btn-red" onclick="delLead()">Delete</button>
</div></div>

<script>
var leads={}, cfg={}, tenders={}, curId=null, draftId=null;

function $(id){return document.getElementById(id)}
function showTab(t,el){
  var tabs=document.getElementsByClassName('tab');
  for(var i=0;i<tabs.length;i++)tabs[i].className='tab';
  var panels=document.getElementsByClassName('panel');
  for(var i=0;i<panels.length;i++)panels[i].className='panel';
  if(el){
    el.className='tab on';
  }else{
    for(var i=0;i<tabs.length;i++){
      if(tabs[i].onclick&&tabs[i].onclick.toString().indexOf("'"+t+"'")>=0){
        tabs[i].className='tab on';break;
      }
    }
  }
  $('p-'+t).className='panel on';
  if(t=='outreach')updateOutreach();
  if(t=='settings')loadCfg();
  if(t=='tenders')loadTenders();
}

function load(){
  var x=new XMLHttpRequest();
  x.open('GET','/api/leads');
  x.onload=function(){
    leads=JSON.parse(x.responseText);
    updateStats();
    render();
    updateDraftSel();
  };
  x.send();
}

function updateStats(){
  var arr=Object.values(leads);
  $('st-total').textContent=arr.length;
  $('st-email').textContent=arr.filter(function(l){return l.general_email||l.contact_email}).length;
  $('st-contact').textContent=arr.filter(function(l){return l.outreach_status=='sent'||l.outreach_status=='replied'}).length;
  $('st-follow').textContent=arr.filter(function(l){return l.next_followup_date&&new Date(l.next_followup_date)<=new Date()}).length;
}

function render(){
  var arr=Object.values(leads);
  var s=$('search').value.toLowerCase();
  var fs=$('f-status').value;
  var fo=$('f-out').value;
  if(s)arr=arr.filter(function(l){return l.company_name.toLowerCase().indexOf(s)>=0});
  if(fs)arr=arr.filter(function(l){return l.status==fs});
  if(fo)arr=arr.filter(function(l){return l.outreach_status==fo});
  
  var h='';
  if(!arr.length)h='<tr><td colspan="6" style="text-align:center;padding:40px;color:#666">No leads</td></tr>';
  else for(var i=0;i<arr.length;i++){
    var l=arr[i];
    var sc=l.signal_score>=50?'sig-h':l.signal_score>=20?'sig-m':'sig-l';
    h+='<tr><td><b>'+l.company_name+'</b>'+(l.industry?'<br><small style="color:#666">'+l.industry+'</small>':'')+'</td>';
    h+='<td>'+(l.contact_name||'-')+'</td>';
    h+='<td style="font-size:12px">'+(l.contact_email||l.general_email||'-')+'</td>';
    h+='<td><span class="sig '+sc+'">'+(l.signal_score||0)+'</span></td>';
    h+='<td>'+(l.status||'New')+'</td>';
    h+='<td><button class="btn btn-gray btn-sm" onclick="edit(\''+l.id+'\')">Edit</button></td></tr>';
  }
  $('tbl').innerHTML=h;
}

function addLead(){
  var c=$('a-company').value.trim();
  if(!c){showMsg('add-msg','Company required','err');return}
  var d={company_name:c,website:$('a-web').value,industry:$('a-ind').value,source:$('a-src').value,
    general_email:$('a-email').value,general_phone:$('a-phone').value,
    contact_name:$('a-contact').value,contact_title:$('a-title').value,notes:$('a-notes').value};
  var x=new XMLHttpRequest();
  x.open('POST','/api/leads');
  x.setRequestHeader('Content-Type','application/json');
  x.onload=function(){showMsg('add-msg','Added!','ok');clearAdd();load()};
  x.send(JSON.stringify(d));
}

function addScrape(){
  var c=$('a-company').value.trim(),w=$('a-web').value.trim();
  if(!c){showMsg('add-msg','Company required','err');return}
  if(!w){showMsg('add-msg','Website required for scraping','err');return}
  showMsg('add-msg','Scraping...','info');
  var d={company_name:c,website:w,industry:$('a-ind').value,source:$('a-src').value,
    contact_name:$('a-contact').value,contact_title:$('a-title').value,notes:$('a-notes').value};
  var x=new XMLHttpRequest();
  x.open('POST','/api/leads/scrape');
  x.setRequestHeader('Content-Type','application/json');
  x.onload=function(){var r=JSON.parse(x.responseText);showMsg('add-msg',r.message||'Done!','ok');clearAdd();load()};
  x.send(JSON.stringify(d));
}

function clearAdd(){$('a-company').value='';$('a-web').value='';$('a-ind').value='';$('a-src').value='';$('a-email').value='';$('a-phone').value='';$('a-contact').value='';$('a-title').value='';$('a-notes').value=''}

function edit(id){
  curId=id;var l=leads[id];
  $('e-id').value=id;
  $('e-comp').value=l.company_name||'';
  $('e-web').value=l.website||'';
  $('e-email').value=l.general_email||'';
  $('e-phone').value=l.general_phone||'';
  $('e-ind').value=l.industry||'';
  $('e-status').value=l.status||'New';
  $('e-contact').value=l.contact_name||'';
  $('e-title').value=l.contact_title||'';
  $('e-notes').value=l.notes||'';
  var sig='';
  if(l.buying_signals&&l.buying_signals.length){
    sig='<b>Signals ('+l.signal_score+'):</b> ';
    for(var i=0;i<l.buying_signals.length;i++)sig+='<span class="sig sig-h">'+l.buying_signals[i].keyword+'</span> ';
  }
  $('e-sig').innerHTML=sig||'<span style="color:#666">No signals</span>';
  $('modal').className='modal on';
}

function closeModal(){$('modal').className='modal';curId=null}

function saveLead(){
  var d={company_name:$('e-comp').value,website:$('e-web').value,general_email:$('e-email').value,
    general_phone:$('e-phone').value,industry:$('e-ind').value,status:$('e-status').value,
    contact_name:$('e-contact').value,contact_title:$('e-title').value,notes:$('e-notes').value};
  var x=new XMLHttpRequest();
  x.open('PUT','/api/leads/'+curId);
  x.setRequestHeader('Content-Type','application/json');
  x.onload=function(){closeModal();load()};
  x.send(JSON.stringify(d));
}

function delLead(){
  if(!confirm('Delete?'))return;
  var x=new XMLHttpRequest();
  x.open('DELETE','/api/leads/'+curId);
  x.onload=function(){closeModal();load()};
  x.send();
}

function scrapeLead(){
  var x=new XMLHttpRequest();
  x.open('POST','/api/leads/'+curId+'/scrape');
  x.onload=function(){alert('Done');load();edit(curId)};
  x.send();
}

function detectSig(){
  var x=new XMLHttpRequest();
  x.open('POST','/api/leads/'+curId+'/signals');
  x.onload=function(){var r=JSON.parse(x.responseText);alert('Score: '+r.score);load();edit(curId)};
  x.send();
}

function importLI(){
  var f=$('li-file').files[0];
  if(!f){showMsg('li-msg','Select file','err');return}
  var fd=new FormData();
  fd.append('file',f);
  fd.append('filter_titles',$('li-filter').checked?'true':'false');
  showMsg('li-msg','Importing...','info');
  var x=new XMLHttpRequest();
  x.open('POST','/api/import/linkedin');
  x.onload=function(){var r=JSON.parse(x.responseText);showMsg('li-msg',r.message,'ok');$('li-file').value='';load()};
  x.send(fd);
}

function importCSV(){
  var f=$('csv-file').files[0];
  if(!f){showMsg('csv-msg','Select file','err');return}
  var fd=new FormData();
  fd.append('file',f);
  showMsg('csv-msg','Importing...','info');
  var x=new XMLHttpRequest();
  x.open('POST','/api/import/csv');
  x.onload=function(){var r=JSON.parse(x.responseText);showMsg('csv-msg',r.message,'ok');$('csv-file').value='';load()};
  x.send(fd);
}

function updateOutreach(){
  var arr=Object.values(leads);
  $('o-ns').textContent=arr.filter(function(l){return !l.outreach_status||l.outreach_status=='not_started'}).length;
  $('o-sent').textContent=arr.filter(function(l){return l.outreach_status=='sent'}).length;
  $('o-rep').textContent=arr.filter(function(l){return l.outreach_status=='replied'}).length;
  var due=arr.filter(function(l){return l.next_followup_date&&new Date(l.next_followup_date)<=new Date()&&l.outreach_status!='replied'});
  $('o-due').textContent=due.length;
  var h='';
  if(!due.length)h='<p style="color:#666">No follow-ups due</p>';
  else for(var i=0;i<due.length;i++){
    var l=due[i];
    h+='<div style="display:flex;justify-content:space-between;padding:10px;background:#f8f9fa;border-radius:5px;margin-bottom:8px"><b>'+l.company_name+'</b><button class="btn btn-blue btn-sm" onclick="selDraft(\''+l.id+'\')">Draft</button></div>';
  }
  $('due-list').innerHTML=h;
}

function updateDraftSel(){
  var arr=Object.values(leads).filter(function(l){return l.general_email||l.contact_email});
  var h='<option value="">Select...</option>';
  for(var i=0;i<arr.length;i++)h+='<option value="'+arr[i].id+'">'+arr[i].company_name+'</option>';
  $('d-lead').innerHTML=h;
}

function selDraft(id){showTab('outreach');$('d-lead').value=id;genDraft()}

function genDraft(){
  var id=$('d-lead').value,tpl=$('d-tpl').value;
  if(!id){alert('Select lead');return}
  draftId=id;
  var x=new XMLHttpRequest();
  x.open('POST','/api/draft');
  x.setRequestHeader('Content-Type','application/json');
  x.onload=function(){
    var r=JSON.parse(x.responseText);
    $('d-subj').textContent='Subject: '+r.subject;
    $('d-body').textContent=r.body;
    $('draft-box').className='ebox';
  };
  x.send(JSON.stringify({lead_id:id,template:tpl}));
}

function copyDraft(){
  var t=$('d-subj').textContent+'\n\n'+$('d-body').textContent;
  navigator.clipboard.writeText(t);alert('Copied!');
}

function markSent(){
  if(!draftId)return;
  var fd=new Date();fd.setDate(fd.getDate()+3);
  var d={outreach_status:'sent',last_contact_date:new Date().toISOString(),next_followup_date:fd.toISOString()};
  var x=new XMLHttpRequest();
  x.open('PUT','/api/leads/'+draftId);
  x.setRequestHeader('Content-Type','application/json');
  x.onload=function(){alert('Marked sent!');load();updateOutreach()};
  x.send(JSON.stringify(d));
}

function checkTenders(){
  showMsg('t-msg','Checking...','info');
  var x=new XMLHttpRequest();
  x.open('POST','/api/tenders/check');
  x.onload=function(){var r=JSON.parse(x.responseText);showMsg('t-msg',r.message,'ok');loadTenders()};
  x.send();
}

function loadTenders(){
  var x=new XMLHttpRequest();
  x.open('GET','/api/tenders');
  x.onload=function(){
    tenders=JSON.parse(x.responseText);
    var arr=Object.values(tenders);
    $('st-tender').textContent=arr.filter(function(t){return !t.is_read}).length;
    var h='';
    if(!arr.length)h='<p style="color:#666">No tenders. Click Check.</p>';
    else for(var i=0;i<arr.length&&i<15;i++){
      var t=arr[i];
      var sc=t.relevance_score>=50?'sig-h':t.relevance_score>=20?'sig-m':'sig-l';
      h+='<div class="tender'+(t.is_read?'':' new')+'" onclick="readTender(\''+t.id+'\')">';
      h+='<h4><a href="'+t.url+'" target="_blank">'+t.title+'</a></h4>';
      h+='<p>'+t.organization+' | <span class="sig '+sc+'">'+t.relevance_score+'</span></p></div>';
    }
    $('t-list').innerHTML=h;
  };
  x.send();
}

function readTender(id){
  var x=new XMLHttpRequest();
  x.open('POST','/api/tenders/'+id+'/read');
  x.onload=function(){loadTenders()};
  x.send();
}

function loadCfg(){
  var x=new XMLHttpRequest();
  x.open('GET','/api/config');
  x.onload=function(){
    cfg=JSON.parse(x.responseText);
    $('c-name').value=cfg.your_name||'';
    $('c-comp').value=cfg.your_company||'';
    $('c-phone').value=cfg.your_phone||'';
    $('c-email').value=cfg.your_email||'';
    $('c-jid').value=cfg.jobber_client_id||'';
    $('c-jsec').value=cfg.jobber_client_secret||'';
    $('c-kw').value=(cfg.tender_keywords||[]).join(', ');
    $('c-loc').value=(cfg.tender_locations||[]).join(', ');
  };
  x.send();
}

function saveCfg(){
  var d={your_name:$('c-name').value,your_company:$('c-comp').value,your_phone:$('c-phone').value,your_email:$('c-email').value,
    jobber_client_id:$('c-jid').value,jobber_client_secret:$('c-jsec').value,
    tender_keywords:$('c-kw').value.split(',').map(function(s){return s.trim()}).filter(function(s){return s}),
    tender_locations:$('c-loc').value.split(',').map(function(s){return s.trim()}).filter(function(s){return s})};
  var x=new XMLHttpRequest();
  x.open('POST','/api/config');
  x.setRequestHeader('Content-Type','application/json');
  x.onload=function(){showMsg('cfg-msg','Saved!','ok');cfg=d};
  x.send(JSON.stringify(d));
}

function showMsg(id,msg,type){
  var c=type=='ok'?'msg-ok':type=='err'?'msg-err':'msg-info';
  $(id).innerHTML='<div class="msg '+c+'">'+msg+'</div>';
  if(type=='ok')setTimeout(function(){$(id).innerHTML=''},5000);
}

load();
</script>
</body>
</html>'''

@app.route('/')
def index(): return HTML

@app.route('/api/leads')
def api_leads(): return jsonify(load_json(DATA_DIR/"leads.json"))

@app.route('/api/leads', methods=['POST'])
def api_add():
    d = request.json
    leads = load_json(DATA_DIR/"leads.json")
    id = 'lead_'+str(int(time.time()*1000))
    leads[id] = {'id':id,'company_name':d.get('company_name',''),'website':d.get('website',''),
        'general_email':d.get('general_email',''),'general_phone':d.get('general_phone',''),
        'industry':d.get('industry',''),'source':d.get('source',''),'contact_name':d.get('contact_name',''),
        'contact_title':d.get('contact_title',''),'notes':d.get('notes',''),'buying_signals':[],
        'signal_score':0,'status':'New','outreach_status':'not_started','next_followup_date':None}
    save_json(DATA_DIR/"leads.json", leads)
    return jsonify(leads[id])

@app.route('/api/leads/scrape', methods=['POST'])
def api_scrape():
    d = request.json
    leads = load_json(DATA_DIR/"leads.json")
    id = 'lead_'+str(int(time.time()*1000))
    lead = {'id':id,'company_name':d.get('company_name',''),'website':d.get('website',''),
        'general_email':d.get('general_email',''),'general_phone':d.get('general_phone',''),
        'industry':d.get('industry',''),'source':d.get('source',''),'contact_name':d.get('contact_name',''),
        'contact_title':d.get('contact_title',''),'notes':d.get('notes',''),'buying_signals':[],
        'signal_score':0,'status':'New','outreach_status':'not_started','next_followup_date':None}
    if lead['website']:
        r = scrape_website(lead['website'])
        if r['emails'] and not lead['general_email']: lead['general_email']=r['emails'][0]
        if r['phones'] and not lead['general_phone']: lead['general_phone']=r['phones'][0]
        sig, sc = detect_signals(lead['website'])
        lead['buying_signals'], lead['signal_score'] = sig, sc
    leads[id] = lead
    save_json(DATA_DIR/"leads.json", leads)
    return jsonify({'lead':lead,'message':'Found {} emails, {} phones. Score: {}'.format(len(r.get('emails',[])),len(r.get('phones',[])),lead['signal_score'])})

@app.route('/api/leads/<id>', methods=['PUT'])
def api_update(id):
    leads = load_json(DATA_DIR/"leads.json")
    if id in leads:
        for k,v in request.json.items(): leads[id][k]=v
        save_json(DATA_DIR/"leads.json", leads)
        return jsonify(leads[id])
    return '',404

@app.route('/api/leads/<id>', methods=['DELETE'])
def api_del(id):
    leads = load_json(DATA_DIR/"leads.json")
    if id in leads: del leads[id]; save_json(DATA_DIR/"leads.json", leads)
    return jsonify({'ok':True})

@app.route('/api/leads/<id>/scrape', methods=['POST'])
def api_scrape_lead(id):
    leads = load_json(DATA_DIR/"leads.json")
    if id not in leads: return '',404
    r = scrape_website(leads[id].get('website',''))
    if r['emails'] and not leads[id].get('general_email'): leads[id]['general_email']=r['emails'][0]
    if r['phones'] and not leads[id].get('general_phone'): leads[id]['general_phone']=r['phones'][0]
    save_json(DATA_DIR/"leads.json", leads)
    return jsonify(r)

@app.route('/api/leads/<id>/signals', methods=['POST'])
def api_signals(id):
    leads = load_json(DATA_DIR/"leads.json")
    if id not in leads: return '',404
    sig, sc = detect_signals(leads[id].get('website',''))
    leads[id]['buying_signals'], leads[id]['signal_score'] = sig, sc
    save_json(DATA_DIR/"leads.json", leads)
    return jsonify({'signals':sig,'score':sc})

@app.route('/api/import/linkedin', methods=['POST'])
def api_import_li():
    f = request.files.get('file')
    if not f: return jsonify({'error':'No file'}),400
    content = f.read().decode('utf-8-sig')
    filt = request.form.get('filter_titles')=='true'
    titles = ['manager','director','purchasing','maintenance','operations','plant','facilities','buyer','owner','president','vp']
    leads = load_json(DATA_DIR/"leads.json")
    lines = content.split('\n')
    hi = next((i for i,l in enumerate(lines) if 'first name' in l.lower()),0)
    reader = csv.DictReader(lines[hi:])
    cnt = 0
    for row in reader:
        n = {k.lower().strip():v for k,v in row.items()}
        comp = n.get('company',n.get('organization',''))
        if not comp: continue
        title = n.get('position',n.get('title',''))
        if filt and title and not any(t in title.lower() for t in titles): continue
        id = 'lead_{}_{}'.format(int(time.time()*1000),cnt)
        leads[id] = {'id':id,'company_name':comp,'website':'','general_email':'','general_phone':'',
            'industry':'','source':'LinkedIn','contact_name':(n.get('first name','')+' '+n.get('last name','')).strip(),
            'contact_title':title,'contact_email':n.get('email address',n.get('email','')),'notes':'',
            'buying_signals':[],'signal_score':0,'status':'New','outreach_status':'not_started','next_followup_date':None}
        cnt+=1;time.sleep(0.001)
    save_json(DATA_DIR/"leads.json", leads)
    return jsonify({'message':'Imported {} contacts'.format(cnt)})

@app.route('/api/import/csv', methods=['POST'])
def api_import_csv():
    f = request.files.get('file')
    if not f: return jsonify({'error':'No file'}),400
    leads = load_json(DATA_DIR/"leads.json")
    reader = csv.DictReader(f.read().decode('utf-8-sig').splitlines())
    cnt = 0
    for row in reader:
        comp = row.get('company_name',row.get('company',''))
        if not comp: continue
        id = 'lead_{}_{}'.format(int(time.time()*1000),cnt)
        leads[id] = {'id':id,'company_name':comp,'website':row.get('website',''),
            'general_email':row.get('email',row.get('general_email','')),
            'general_phone':row.get('phone',row.get('general_phone','')),
            'industry':row.get('industry',''),'source':'CSV','contact_name':row.get('contact_name',''),
            'contact_title':row.get('contact_title',''),'notes':row.get('notes',''),
            'buying_signals':[],'signal_score':0,'status':'New','outreach_status':'not_started','next_followup_date':None}
        cnt+=1;time.sleep(0.001)
    save_json(DATA_DIR/"leads.json", leads)
    return jsonify({'message':'Imported {} companies'.format(cnt)})

@app.route('/api/export')
def api_export():
    leads = load_json(DATA_DIR/"leads.json")
    out = io.StringIO()
    w = csv.DictWriter(out,['company_name','website','general_email','general_phone','industry','contact_name','contact_title','signal_score','status','notes'])
    w.writeheader()
    for l in leads.values(): w.writerow({k:l.get(k,'') for k in w.fieldnames})
    out.seek(0)
    return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment;filename=leads.csv'})

@app.route('/api/draft', methods=['POST'])
def api_draft():
    d = request.json
    leads = load_json(DATA_DIR/"leads.json")
    cfg = load_json(DATA_DIR/"config.json")
    l = leads.get(d['lead_id'],{})
    tpls = {
        'first':("Quick question about {co}'s maintenance needs","Hi {fn},\n\nI came across {co} and noticed you're in the {ind} space here in Calgary.\n\nWe work with several industrial companies, helping reduce equipment downtime.\n\nWould you have 15 minutes this week for a quick call?\n\nBest,\n{yn}\n{yc}\n{yp}"),
        'fu1':("Re: {co} maintenance needs","Hi {fn},\n\nI wanted to follow up on my previous email about how we might help {co}.\n\nIf now isn't a good time, I'm happy to reconnect later.\n\nThanks,\n{yn}"),
        'fu2':("One more try - {co}","Hi {fn},\n\nI'll assume timing isn't right if I don't hear back, but wanted to leave the door open.\n\nBest,\n{yn}\n{yp}")
    }
    subj,body = tpls.get(d.get('template','first'),tpls['first'])
    cn = l.get('contact_name','')
    fn = cn.split()[0] if cn else 'there'
    rep = {'{co}':l.get('company_name',''),'{fn}':fn,'{ind}':l.get('industry','industrial'),
           '{yn}':cfg.get('your_name',''),'{yc}':cfg.get('your_company',''),'{yp}':cfg.get('your_phone','')}
    for k,v in rep.items(): subj=subj.replace(k,v or ''); body=body.replace(k,v or '')
    return jsonify({'subject':subj,'body':body})

@app.route('/api/tenders')
def api_tenders(): return jsonify(load_json(DATA_DIR/"tenders.json"))

@app.route('/api/tenders/check', methods=['POST'])
def api_check_tenders():
    cfg = load_json(DATA_DIR/"config.json")
    kw = cfg.get('tender_keywords',[])
    tenders = load_json(DATA_DIR/"tenders.json")
    samples = [("Building Maintenance RFP","City of Calgary","https://purchasing.alberta.ca/1"),
               ("HVAC Maintenance Contract","Alberta Health","https://purchasing.alberta.ca/2"),
               ("Facilities Management","U of Calgary","https://merx.com/3")]
    cnt = 0
    for title,org,url in samples:
        id = 'tender_'+hashlib.md5(url.encode()).hexdigest()[:10]
        if id not in tenders:
            sc = sum(20 for k in kw if k.lower() in title.lower())
            tenders[id] = {'id':id,'title':title,'organization':org,'url':url,'relevance_score':min(sc,100),'is_read':False}
            cnt+=1
    save_json(DATA_DIR/"tenders.json", tenders)
    return jsonify({'message':'Found {} new tenders'.format(cnt)})

@app.route('/api/tenders/<id>/read', methods=['POST'])
def api_read_tender(id):
    tenders = load_json(DATA_DIR/"tenders.json")
    if id in tenders: tenders[id]['is_read']=True; save_json(DATA_DIR/"tenders.json",tenders)
    return jsonify({'ok':True})

@app.route('/api/config')
def api_cfg(): return jsonify(load_json(DATA_DIR/"config.json"))

@app.route('/api/config', methods=['POST'])
def api_save_cfg():
    cfg = load_json(DATA_DIR/"config.json")
    cfg.update(request.json)
    save_json(DATA_DIR/"config.json", cfg)
    return jsonify({'ok':True})

if __name__ == '__main__':
    print('\n'+'='*50)
    print('  Calgary Industrial Lead Generator')
    print('='*50)
    print('\n  Open your browser to: http://localhost:5000\n')
    print('  Press Ctrl+C to stop\n')
    print('='*50+'\n')
    app.run(debug=True, host='127.0.0.1', port=5000)
