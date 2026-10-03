"use strict";
const $ = id => document.getElementById(id);
const sides = ["left", "right"];
const loaded = {left: null, right: null};
let busy = false, events = [], runs = [];
const labels = {
  search_patch_generated: ["01 原始模型输出", "raw_output"],
  search_patch_parsed: ["02 Parsed SearchPatch", "patch"],
  search_patch_validated: ["03 校验结果", null],
  search_state_merged: ["04 合并状态与字段变更", null],
  search_query_compiled: ["05 编译后的搜索查询", null],
  search_error: ["执行错误", null]
};
function status(side, state, text) {
  const box = $(side + "-status"); box.dataset.state = state; box.textContent = text;
}
function updateControls() {
  $("run").disabled = busy || sides.some(s => loaded[s] !== $(s + "-model").value || !loaded[s]);
  for (const side of sides) {
    $(side + "-load").disabled = busy || !$(side + "-model").value;
    $(side + "-unload").disabled = busy;
    $(side + "-model").disabled = busy;
    $(side + "-state").disabled = busy;
  }
  for (const id of ["user-input", "comparison-mode", "reset-states", "sync-state"]) $(id).disabled = busy;
  for (const id of ["export-json", "export-ndjson"]) $(id).disabled = busy;
}
async function request(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(body)
  });
  if (!response.ok) {
    let message = await response.text();
    try { const parsed = JSON.parse(message); message = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail); } catch {}
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response;
}
function reportError(error, context) {
  request("/api/client-logs", {level: "error", message: String(error.message).slice(0, 2048), context}).catch(() => {});
}
function readState(side) {
  const text = $(side + "-state").value.trim();
  const value = text ? JSON.parse(text) : null;
  if (value !== null && (typeof value !== "object" || Array.isArray(value))) throw new Error(`${side === "left" ? "左" : "右"}侧状态应为 JSON 对象或 null`);
  return value;
}
function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(k => [k, sorted(value[k])]));
  return value;
}
function updateStateBadge() {
  try {
    $("state-comparison").textContent = JSON.stringify(sorted(readState("left"))) === JSON.stringify(sorted(readState("right"))) ? "两侧状态相同" : "两侧状态不同";
  } catch { $("state-comparison").textContent = "状态 JSON 待校正"; }
}
async function loadModel(side) {
  busy = true; updateControls(); status(side, "loading", "正在加载模型…");
  loaded[side] = null;
  try {
    const modelId = $(side + "-model").value;
    await request(`/api/model-slots/${side}/load`, {model_id: modelId});
    loaded[side] = modelId; status(side, "ready", "模型就绪");
  } catch (error) { status(side, "error", `加载失败：${error.message}`); reportError(error, {action: "load", side}); }
  finally { busy = false; updateControls(); }
}
function appendStep(side, event) {
  const [label, key] = labels[event.type];
  const details = document.createElement("details"); details.className = "trace-step";
  if (event.type === "search_error" || (event.type === "search_patch_validated" && !event.payload.valid)) details.classList.add("error");
  if (event.type === "search_patch_validated" && event.payload.valid) details.classList.add("validation-pass");
  details.open = ["search_patch_parsed", "search_patch_validated", "search_query_compiled", "search_error"].includes(event.type);
  const summary = document.createElement("summary"); summary.textContent = label;
  if (event.type === "search_patch_validated") {
    const badge = document.createElement("small"); badge.textContent = event.payload.valid ? "PASS" : "ERROR"; summary.append(badge);
  }
  const pre = document.createElement("pre");
  const value = key ? event.payload[key] : event.payload;
  pre.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  details.append(summary, pre); $(side + "-trace").append(details);
}
function ms(value) { return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value)} ms` : "n/a"; }
function acceptEvent(event, completed) {
  if (!sides.includes(event.side)) throw new Error("收到未知模型侧的事件");
  events.push(event);
  if (event.type === "side_status") status(event.side, "inferencing", "正在推理…");
  else if (labels[event.type]) appendStep(event.side, event);
  else if (event.type === "side_result") {
    if (completed.has(event.side)) throw new Error("收到重复侧结果");
    completed.add(event.side);
    const result = event.payload, metrics = result.metrics || {};
    $(event.side + "-metrics").textContent = `推理 ${ms(metrics.inference_duration_ms)} · 首 token ${ms(metrics.first_token_ms)} · 输入 ${metrics.input_tokens ?? "n/a"} / 输出 ${metrics.output_tokens ?? "n/a"} tokens · ${typeof metrics.tokens_per_s === "number" ? metrics.tokens_per_s.toFixed(1) : "n/a"} tokens/s`;
    if (result.status === "complete") {
      $(event.side + "-state").value = JSON.stringify(result.next_state, null, 2);
      status(event.side, "complete", `完成 · ${ms(metrics.inference_duration_ms)}`);
    } else {
      status(event.side, "error", `失败 · ${result.error?.stage || "unknown"} · 状态未更新`);
      if (!$(event.side + "-trace").querySelector(".error")) appendStep(event.side, {type: "search_error", payload: result.error || {message: "未返回有效结果"}});
    }
    updateStateBadge();
  }
}
async function readEvents(response, completed) {
  if (!response.body) throw new Error("浏览器无法读取响应流");
  const reader = response.body.getReader(), decoder = new TextDecoder(); let pending = "";
  try {
    while (true) {
      const {done, value} = await reader.read();
      pending += decoder.decode(value || new Uint8Array(), {stream: !done});
      const lines = pending.split("\n"); pending = lines.pop();
      for (const line of lines) if (line.trim()) acceptEvent(JSON.parse(line), completed);
      if (done) break;
    }
    if (pending.trim()) acceptEvent(JSON.parse(pending), completed);
  } finally { reader.releaseLock(); }
  if (completed.size !== 2) throw new Error("响应流提前结束，部分模型未返回结果");
}
$("run").onclick = async () => {
  const userInput = $("user-input").value;
  if (!userInput.trim()) { $("run-status").textContent = "请输入搜索需求。"; return; }
  let body;
  try { body = {
    left_model_id: $("left-model").value, right_model_id: $("right-model").value,
    mode: $("comparison-mode").value, user_input: userInput,
    left_current_search_state: readState("left"), right_current_search_state: readState("right")
  }; } catch (error) { $("run-status").textContent = `状态格式错误：${error.message}`; return; }
  const run = {request: body, events: []}, startIndex = events.length, completed = new Set(); runs.push(run);
  busy = true; updateControls(); $("run-status").className = "";
  $("run-status").textContent = body.mode === "parallel" ? "并行运行中，延迟不可直接比较。" : "按顺序运行左右模型…";
  for (const side of sides) {
    $(side + "-trace").replaceChildren(); const input = document.createElement("p");
    input.className = "turn-label"; input.textContent = `本轮：${userInput}`; $(side + "-trace").append(input);
    status(side, "waiting", "等待推理…");
  }
  try {
    await readEvents(await request("/api/compare", body), completed);
    $("run-status").textContent = sides.some(s => $(s + "-status").dataset.state === "error") ? "对比结束，失败侧的状态已保留。" : "对比完成，可继续输入下一轮需求。";
  } catch (error) {
    $("run-status").className = "error"; $("run-status").textContent = `对比失败：${error.message}`;
    for (const side of sides) if (!completed.has(side)) status(side, "error", "请求失败 · 状态未更新");
    reportError(error, {action: "compare"});
  } finally { run.events = events.slice(startIndex); busy = false; updateControls(); }
};
for (const side of sides) {
  $(side + "-load").onclick = () => loadModel(side);
  $(side + "-unload").onclick = async () => {
    busy = true; updateControls();
    try { await request(`/api/model-slots/${side}/unload`, {}); loaded[side] = null; status(side, "idle", "模型已卸载"); }
    catch (error) { status(side, "error", error.message); }
    finally { busy = false; updateControls(); }
  };
  $(side + "-model").onchange = () => {
    loaded[side] = null; $(side + "-state").value = ""; $(side + "-trace").replaceChildren();
    status(side, "idle", "模型已切换，请加载 · 状态已清空"); updateControls(); updateStateBadge();
  };
  $(side + "-state").oninput = updateStateBadge;
}
$("reset-states").onclick = () => {
  for (const side of sides) {
    $(side + "-state").value = ""; $(side + "-trace").replaceChildren(); $(side + "-metrics").textContent = "状态已清空";
    status(side, loaded[side] ? "ready" : "idle", loaded[side] ? "模型就绪 · 状态已清空" : "等待加载");
  }
  updateStateBadge(); $("run-status").textContent = "下一轮将从空状态开始；导出记录仍保留。";
};
$("sync-state").onclick = () => { $("right-state").value = $("left-state").value; updateStateBadge(); };
$("comparison-mode").onchange = () => { $("mode-note").textContent = $("comparison-mode").value === "parallel" ? "两侧并发运行，延迟受资源竞争影响，不可直接比较。" : "顺序运行便于比较本次推理延迟。"; };
document.querySelectorAll("[data-example]").forEach(button => { button.onclick = () => { if (!busy) { $("user-input").value = button.dataset.example; $("user-input").focus(); } }; });
$("user-input").onkeydown = event => { if (event.ctrlKey && event.key === "Enter" && !$("run").disabled) $("run").click(); };
function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], {type})); const a = document.createElement("a");
  a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$("export-json").onclick = () => download("search-comparison.json", JSON.stringify({runs}, null, 2), "application/json");
$("export-ndjson").onclick = () => download("search-comparison.ndjson", events.map(e => JSON.stringify(e)).join("\n") + (events.length ? "\n" : ""), "application/x-ndjson");
async function init() {
  const models = await (await request("/api/models")).json();
  const config = await (await request("/api/registry")).json();
  if (config.inference_mode === "injected") $("environment").textContent = "离线后端验证";
  $("registry-version").textContent = `v${config.registry.registry_version}`;
  $("currency-note").textContent = `价格编译币种：${config.currency}。明确的其他币种会报错。`;
  for (const field of Object.keys(config.registry.fields)) { const chip = document.createElement("span"); chip.textContent = field; $("registry-fields").append(chip); }
  for (const side of sides) {
    const select = $(side + "-model"); const placeholder = document.createElement("option");
    placeholder.value = ""; placeholder.textContent = "选择模型"; select.append(placeholder);
    for (const model of models) {
      const option = document.createElement("option"); option.value = model.model_id; option.disabled = !model.available;
      option.textContent = model.model_id + (model.available ? "" : "（产物不可用）"); option.title = model.unavailable_reason || ""; select.append(option);
    }
    const available = models.filter(m => m.available);
    const desired = side === "left" ? 0.6 : 1.7;
    const model = available.find(m => m.size_b === desired && m.artifact_kind === "q4_k_m") || available[0];
    if (model) select.value = model.model_id;
    else status(side, "idle", "暂无可用模型，请先构建搜索 GGUF 与 Manifest。");
  }
  updateControls();
}
init().catch(error => { $("run-status").className = "error"; $("run-status").textContent = `初始化失败：${error.message}`; reportError(error, {action: "init"}); });
