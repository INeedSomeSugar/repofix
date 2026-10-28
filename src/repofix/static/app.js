const $ = id => document.getElementById(id);
const stateNames = {created:'已创建',queued:'排队中',running:'修复中',paused:'已暂停',verified:'验证通过',failed:'验证未通过',error:'执行错误',budget_exhausted:'达到预算',invalid_task:'基线无效',stalled:'重复状态已停止',needs_review:'新增断言待核查'};
const toolNames = {list_files:'查看仓库结构',read_file:'读取代码',search_code:'搜索相关代码',replace_text:'修改源码',write_test:'补充回归测试',run_tests:'分层执行测试',restore_checkpoint:'回退源码检查点'};
let cases = [], currentRun = null, timer = null, currentPatch = '';
async function api(path, method='GET', body) {
  const response = await fetch(path, {method, headers: {'Content-Type':'application/json'}, body:body === undefined ? undefined : JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `请求失败 (${response.status})`);
  return data;
}
function notice(message) { $('notice').textContent=message; $('notice').hidden=!message; }
function chosenCase() {
  const item=cases.find(item=>item.id===$('case').value);
  $('issue').textContent=item?.issue || '';
  $('case-category').textContent=item?.category || '开发样例';
}
function updateMode() { $('mode-note').textContent=$('provider').value==='deepseek' ? '使用服务器环境中的 DeepSeek 凭据，执行将产生实际 API 用量。' : '回放使用已知修复脚本，用于检查工程流程。'; }
async function history() {
  const runs=await api('/api/runs');
  const nodes=runs.map(run=>{
    const button=document.createElement('button');
    button.classList.toggle('active',run.run_id===currentRun);
    button.append(document.createTextNode(cases.find(item=>item.id===run.case_id)?.title || run.case_id));
    const small=document.createElement('small');
    small.textContent=`${run.provider==='replay'?'REPLAY':'DEEPSEEK'} · ${stateNames[run.status] || run.status}`;
    button.append(small);button.addEventListener('click',()=>selectRun(run.run_id));return button;
  });
  if(!nodes.length){const p=document.createElement('p');p.className='muted';p.textContent='还没有运行记录';nodes.push(p);}
  $('history').replaceChildren(...nodes);
}
function renderPatch(patch) {
  currentPatch=patch;$('copy-patch').disabled=!patch;
  const code=document.createElement('code');
  if(!patch){code.textContent='补丁将在修改源码后显示。';}
  else for(const line of patch.split('\n')){
    const span=document.createElement('span');span.className='diff-line';
    if(line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@'))span.classList.add('diff-head');
    else if(line.startsWith('+'))span.classList.add('diff-add');
    else if(line.startsWith('-'))span.classList.add('diff-del');
    span.textContent=line;code.append(span);
  }
  $('patch').replaceChildren(code);
}
function renderEvent(event, provider) {
  const node=document.createElement('div');node.className='event';
  const title=document.createElement('h4');
  const decision=provider==='replay'?'回放步骤':'模型决策';
  const label={created:'创建独立工作副本',baseline:'复现原始测试失败',model:`${decision} · 第 ${event.turn} 轮`,tool:toolNames[event.name]||event.name,grade:'执行独立评分',paused:'保存检查点',error:'执行中断',stopped:'重复状态达到阈值，停止调用'};
  title.textContent=label[event.kind] || event.kind;
  const time=document.createElement('time');time.textContent=new Date(event.time).toLocaleTimeString('zh-CN',{hour12:false,timeZone:'Asia/Shanghai'});time.title='北京时间';title.append(time);node.append(title);
  const p=document.createElement('p');
  if(event.kind==='model')p.textContent=event.content || (event.tool_names||[]).map(name=>toolNames[name]||name).join(' → ');
  else if(event.kind==='tool')p.textContent=event.result?.ok===false ? `工具未执行：${event.result.detail||event.result.error}` : (event.result?.path|| (event.result?.passed===true?'测试通过':event.result?.passed===false?'测试失败，返回反馈':'执行完成'));
  else if(event.kind==='baseline')p.textContent=`${event.result?.tests_run||0} 项公开测试，${event.result?.failures||0} 失败，${event.result?.errors||0} 错误`;
  else if(event.kind==='grade')p.textContent=`${testDescription(event.public)}；独立测试：${event.independent?.passed?'通过':'失败'}`;
  else if(event.kind==='created')p.textContent=event.provider==='replay'?'固定回放 · 非模型效果':'DeepSeek 真实模型 · 保留实际调用记录';
  else p.textContent=event.code||'状态已持久化，可继续查看或恢复。';
  if(event.kind==='tool' && event.result?.test_policy==='layered_v1')p.textContent=testDescription(event.result)+(event.result.checkpoint_id?`；源码检查点 ${event.result.checkpoint_id.slice(0,8)}`:'');
  node.append(p);
  if(event.result || event.independent){const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='查看执行结果';const pre=document.createElement('pre');pre.textContent=JSON.stringify(event.result||event.independent,null,2);details.append(summary,pre);node.append(details);}
  return node;
}
function testDescription(result) {
  if(result?.test_policy!=='layered_v1')return `公开测试：${result?.passed?'通过':'失败'}`;
  const generated=result.agent_generated;
  return `原始测试：${result.trusted.passed?'通过':'失败'}；模型新增：${generated?(generated.passed?'通过':'未通过，需核对规范'):'无'}`;
}
async function refreshRun() {
  const id=currentRun;if(!id)return;
  const [run,events]=await Promise.all([api(`/api/runs/${id}`),api(`/api/runs/${id}/events`)]);
  if(id!==currentRun)return;
  $('status').textContent=stateNames[run.status]||run.status;$('status').className=`status ${run.status}`;
  $('public-stat').textContent=run.baseline ? `${run.baseline.passed?'通过':'失败'} → ${run.final_public ? (run.final_public.passed?'通过':'失败'):'待验证'}` : '—';
  $('grade-stat').textContent=run.grade ? `${run.grade.passed?'通过':'失败'} · ${run.grade.tests_run} 项` : '等待评分';
  $('calls-stat').textContent=`${run.turns} / ${run.tool_calls}`;$('model-name').textContent=run.model||'模型尚未启动';
  $('cost-stat').textContent=`${run.provider==='replay'?'N/A':run.token_accounting_complete?run.observed_tokens.toLocaleString():'未知'} / ${run.elapsed_seconds.toFixed(1)}s`;
  $('evidence-label').textContent=run.provider==='replay'?'固定脚本回放 · 不计模型修复率':'真实模型调用 · 合成开发样例';
  $('run-label').textContent=id.slice(0,12).toUpperCase();
  $('summary').textContent=(run.error_code ? `执行状态：${run.error_code}。运行记录已保留。` : run.result_summary || '任务正在执行，最终结果由测试判定。')+(run.final_public?.test_policy==='layered_v1'?`\n${testDescription(run.final_public)}`:'');
  $('summary-link').href=`/api/runs/${id}/summary`;$('summary-link').hidden=['created','queued','running'].includes(run.status);
  $('pause').disabled=!['queued','running'].includes(run.status);$('resume').disabled=!['paused','error'].includes(run.status);
  renderPatch(run.patch);const timeline=$('timeline');const nearBottom=timeline.scrollHeight-timeline.scrollTop-timeline.clientHeight<70;
  timeline.replaceChildren(...events.map(event=>renderEvent(event,run.provider)));if(nearBottom)timeline.scrollTop=timeline.scrollHeight;
  if(!['queued','running'].includes(run.status)){clearTimeout(timer);timer=null;await history();}
  else timer=setTimeout(()=>refreshRun().catch(error=>notice(error.message)),1200);
  return run;
}
async function selectRun(id) {
  clearTimeout(timer);currentRun=id;
  const [run]=await Promise.all([refreshRun(),history()]);
  if(run && currentRun===id){
    $('case').value=run.case_id;$('strategy').value=run.strategy;
    const option=$('provider').querySelector(`option[value="${run.provider}"]`);
    if(option && !option.disabled)$('provider').value=run.provider;
    chosenCase();updateMode();
  }
}
$('case').addEventListener('change',chosenCase);$('provider').addEventListener('change',updateMode);
$('refresh').addEventListener('click',()=>history().catch(error=>notice(error.message)));
$('start').addEventListener('click',async()=>{
  $('start').disabled=true;notice('');
  try{const run=await api('/api/runs','POST',{case_id:$('case').value,provider:$('provider').value,strategy:$('strategy').value});await selectRun(run.run_id);}
  catch(error){notice(error.message);}finally{$('start').disabled=false;}
});
$('pause').addEventListener('click',async()=>{try{await api(`/api/runs/${currentRun}/pause`,'POST',{});notice('将在当前模型或工具调用结束后保存检查点并暂停。');}catch(error){notice(error.message);}});
$('resume').addEventListener('click',async()=>{try{await api(`/api/runs/${currentRun}/resume`,'POST',{});notice('');await refreshRun();}catch(error){notice(error.message);}});
$('copy-patch').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(currentPatch);notice('已复制当前补丁。');}catch{notice('浏览器不允许访问剪贴板，可在补丁区域选择并复制。');}});
(async()=>{
  try{const [health,items]=await Promise.all([api('/api/health'),api('/api/cases')]);cases=items;
    $('connection').textContent='本地服务已连接';
    const options=cases.map(item=>{const option=document.createElement('option');option.value=item.id;option.textContent=item.title;return option;});$('case').replaceChildren(...options);chosenCase();
    if(!health.deepseek_key_present){const option=$('provider').querySelector('option[value="deepseek"]');option.disabled=true;option.textContent='DeepSeek · 服务器尚未配置凭据';}
    await history();
  }catch(error){$('connection').textContent='连接失败';notice(error.message);}
})();
