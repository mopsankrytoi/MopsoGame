const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); tg.setHeaderColor("#07172e"); tg.setBackgroundColor("#07172e"); }
const initData = tg?.initData || "";
const headers = {"Content-Type":"application/json","X-Telegram-Init-Data":initData};
let me = null;
let taps = 0;
const $ = id => document.getElementById(id);
function toast(msg){const el=$("toast");el.textContent=msg;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),2200)}
function showPage(name){
 document.querySelectorAll(".page").forEach(p=>p.classList.remove("show"));
 $("page-"+name).classList.add("show");
 document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.page===name));
}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>showPage(b.dataset.page)));
document.querySelectorAll("[data-go]").forEach(b=>b.addEventListener("click",()=>showPage(b.dataset.go)));
function paint(){
 if(!me)return;
 $("hello").textContent=me.first_name||"игрок";
 $("points").textContent=me.points;
 $("level").textContent=me.level;
 $("gamepoints").textContent=me.points;
 $("profile-points").textContent=me.points;
 $("profile-level").textContent=me.level;
 $("profile-name").textContent=me.first_name||"Игрок MopsoGame";
 $("username").textContent=me.username?"@"+me.username:"Игрок MopsoGame";
 $("avatar").textContent=(me.first_name||"M").charAt(0).toUpperCase();
 const within=me.points%100;
 $("progressbar").style.width=within+"%";
 $("progresslabel").textContent=within+" / 100 MP до следующего уровня";
}
function renderTasks(){
 $("tasklist").innerHTML="";
 (me.tasks||[]).forEach(t=>{
  const el=document.createElement("div");el.className="task";
  el.innerHTML=`<div class="task-icon">🎯</div><div class="task-info"><b></b><p></p><div class="reward">+${t.reward} MP</div></div><button class="claim ${t.done?"done":""}" ${t.done?"disabled":""}>${t.done?"ГОТОВО":"ЗАБРАТЬ"}</button>`;
  el.querySelector("b").textContent=t.title;el.querySelector("p").textContent=t.desc;
  if(!t.done)el.querySelector("button").addEventListener("click",()=>claim(t.id));
  $("tasklist").appendChild(el);
 });
}
async function load(){
 if(!initData){$("tasklist").innerHTML='<div class="loading">Открой MopsoGame через кнопку в Telegram, чтобы войти в аккаунт.</div>';toast("Открой приложение через Telegram");return;}
 try{
  const r=await fetch("/api/me",{headers});
  if(!r.ok)throw new Error("Не удалось проверить Telegram");
  me=await r.json();paint();renderTasks();
 }catch(e){toast(e.message)}
}
async function tap(){
 try{
  const r=await fetch("/api/tap",{method:"POST",headers,body:"{}"});
  const d=await r.json();if(!r.ok)throw new Error(d.error||"Ошибка");
  me.points=d.points;me.level=d.level;taps++;paint();
  if(taps===10){const task=me.tasks.find(t=>t.id==="tap10");if(task)toast("10 нажатий! Проверь задания");}
 }catch(e){toast(e.message)}
}
async function claim(id){
 try{
  const r=await fetch("/api/claim",{method:"POST",headers,body:JSON.stringify({task_id:id})});
  const d=await r.json();if(!r.ok)throw new Error(d.error||"Ошибка");
  me.points=d.points;me.level=d.level;const task=me.tasks.find(t=>t.id===id);if(task)task.done=true;
  paint();renderTasks();toast("Награда получена! +MP");
 }catch(e){toast(e.message)}
}
$("tap").addEventListener("click",tap);
load();