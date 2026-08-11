const api = "/api/v1/stories";
let story = null;
let concept = null;
let chapters = [];
let currentStep = "idea";
const feedback = document.querySelector("#feedback");

async function loadModels() {
  try {
    const models = await request("/api/v1/models");
    const select = document.querySelector("#model-select");
    select.replaceChildren(...models.map((model) => new Option(model.display_name, model.provider)));
  } catch {
    document.querySelector("#model-hint").textContent = "模型列表加载失败，仅使用默认模型。";
  }
}

function selectedProvider() {
  return document.querySelector("#model-select").value || "fake";
}

function setFeedback(message, error = false) {
  feedback.textContent = message;
  feedback.className = error ? "feedback error" : "feedback";
}

function pretty(value) {
  return value ? JSON.stringify(value, null, 2) : "尚未确认";
}

function parseJson(input, label) {
  try {
    return JSON.parse(input.value);
  } catch {
    throw new Error(`${label} 必须是有效 JSON。`);
  }
}

function lockedPaths() {
  return document.querySelector("#concept-locks").value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function activate(step) {
  currentStep = step;
  document.querySelectorAll(".step[data-step]").forEach((item) => {
    item.classList.toggle("active", item.dataset.step === step);
  });
  document.querySelectorAll("[data-step]").forEach((item) => {
    const unlocked = availableSteps().includes(item.dataset.step);
    item.disabled = !unlocked;
    item.classList.toggle("disabled", !unlocked);
  });
  document.querySelectorAll("#idea-panel, #concept-panel, #blueprint-panel, #chapters-panel, #workspace-panel").forEach((panel) => panel.classList.add("hidden"));
  const panel = document.querySelector(`#${step === "chapters" ? "chapters" : step}-panel`);
  if (panel) panel.classList.remove("hidden");
  document.querySelector("#state-panel").classList.toggle("hidden", step !== "blueprint");
}

function markDone(step) {
  document.querySelector(`[data-step="${step}"]`).classList.add("done");
}

function availableSteps() {
  if (!story) return ["idea"];
  const steps = ["idea", "concept"];
  if (["concept_confirmed", "blueprint_review", "blueprint_confirmed", "chapter_planning"].includes(story.status)) steps.push("blueprint");
  if (["blueprint_confirmed", "chapter_planning"].includes(story.status)) steps.push("chapters");
  if (chapters.some((chapter) => chapter.access_status === "active")) steps.push("workspace");
  return steps;
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail?.code || "请求失败，请检查输入后重试。");
  }
  return response.json();
}

async function optionalArtifact(kind) {
  return request(`${api}/${story.id}/artifacts/${kind}`).catch((error) => {
    if (error.message === "not_found") return null;
    throw error;
  });
}

function renderStates(containerId, entries) {
  const container = document.querySelector(containerId);
  container.replaceChildren();
  if (!entries.length) {
    container.textContent = "暂无已确认状态条目。";
    container.className = "state-list empty";
    return;
  }
  container.className = "state-list";
  entries.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "state-card";
    const title = document.createElement("b");
    title.textContent = entry.path;
    card.append(title);
    [["值", entry.value], ["来源", entry.source_ref], ["时间", entry.temporal_scope]].forEach(([label, value]) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = `${label}：${pretty(value)}`;
      card.append(paragraph);
    });
    const policy = document.createElement("p");
    policy.textContent = `${entry.certainty} · ${entry.context_policy}`;
    card.append(policy);
    container.append(card);
  });
}

async function refreshWorkspace() {
  story = await request(`${api}/${story.id}`);
  const [latestConcept, bible, arc, living, states] = await Promise.all([
    optionalArtifact("concept"),
    optionalArtifact("bible"),
    optionalArtifact("arc"),
    optionalArtifact("living_state"),
    request(`${api}/${story.id}/state-entries`),
  ]);
  concept = latestConcept;
  document.querySelector("#story-title").textContent = story.title;
  document.querySelector("#story-status").textContent = story.status;
  document.querySelector("#current-story-id").textContent = story.id;
  document.querySelector("#bible").textContent = pretty(bible?.payload);
  document.querySelector("#arc").textContent = pretty(arc?.payload);
  document.querySelector("#living-state").textContent = pretty(living?.payload);
  renderStates("#character-states", states.character);
  renderStates("#world-states", states.world);
  renderStates("#timeline-states", states.timeline);
  if (concept) {
    document.querySelector("#concept-json").value = pretty(concept.payload);
    document.querySelector("#concept-locks").value = concept.locked_paths.join(",");
    document.querySelector("#concept-version").textContent = `v${concept.version} · ${concept.status}`;
  }
  if (["concept_confirmed", "blueprint_review", "blueprint_confirmed"].includes(story.status)) {
    markDone("concept");
  }
  if (["blueprint_review", "blueprint_confirmed"].includes(story.status)) {
    document.querySelector("#blueprint-status").textContent = story.status;
  }
  if (["blueprint_confirmed", "chapter_planning"].includes(story.status)) {
    markDone("blueprint");
    chapters = await request(`${api}/${story.id}/chapters`);
    renderChapters();
  }
  activate(currentStep);
}

function renderChapters() {
  const cards = document.querySelector("#chapter-cards");
  cards.replaceChildren();
  document.querySelector("#chapter-count").textContent = chapters.length ? `${chapters.length} 章` : "等待生成";
  if (!chapters.length) {
    cards.innerHTML = '<p class="empty">确认 Blueprint 后，生成全书章节卡片。第一章将被激活，其余章节保持雏形和锁定状态。</p>';
    return;
  }
  chapters.forEach((chapter) => {
    const card = document.createElement("article");
    card.className = `chapter-card ${chapter.access_status}`;
    const badge = chapter.access_status === "active" ? "当前可进入" : "🔒 等待前一章完成";
    card.innerHTML = `<span class="chapter-number">Chapter ${String(chapter.ordinal).padStart(2, "0")}</span><span class="chapter-status">${badge}</span><h3></h3><p class="chapter-goal"></p><p class="chapter-summary"></p><p class="chapter-meta"></p>`;
    card.querySelector("h3").textContent = chapter.title;
    card.querySelector(".chapter-goal").textContent = `目标：${chapter.goal}`;
    card.querySelector(".chapter-summary").textContent = chapter.summary;
    card.querySelector(".chapter-meta").textContent = `${chapter.plan_status} · ${chapter.arc_relation}`;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = chapter.access_status === "active" ? "进入 Chapter Workspace →" : "完成前一章后解锁";
    button.disabled = chapter.access_status !== "active";
    button.addEventListener("click", () => run(() => openWorkspace(chapter)));
    card.append(button);
    cards.append(card);
  });
}

async function openWorkspace(chapter) {
  const workspace = await request(`/api/v1/chapters/${chapter.id}/workspace`);
  document.querySelector("#workspace-title").textContent = `Chapter ${String(workspace.chapter.ordinal).padStart(2, "0")} · ${workspace.chapter.title}`;
  document.querySelector("#workspace-message").textContent = workspace.message;
  activate("workspace");
}

async function createStory() {
  const idea = document.querySelector("#idea").value.trim();
  if (!idea) throw new Error("请先填写创作意图。");
  story = await request(api, {
    method: "POST",
    body: JSON.stringify({ title: document.querySelector("#title").value.trim() || null, idea }),
  });
  document.querySelector("#story-id").value = story.id;
  await refreshWorkspace();
  activate("concept");
  setFeedback("Story 已创建。现在可以生成并确认 Concept。");
}

async function generateConcept() {
  setFeedback(`正在调用 ${selectedProvider()} 生成 Concept，请稍候…`);
  const task = await request(`${api}/${story.id}/generations`, {
    method: "POST",
    body: JSON.stringify({ action: "generate_concept", parameters: { provider: selectedProvider() } }),
  });
  document.querySelector("#concept-json").value = pretty(task.output);
  document.querySelector("#concept-version").textContent = "AI 候选 · 尚未确认";
  setFeedback("Concept 候选已生成。请编辑、选择需要锁定的字段，再确认。");
}

async function confirmConcept() {
  const payload = parseJson(document.querySelector("#concept-json"), "Concept");
  concept = await request(`${api}/${story.id}/artifacts/concept`, {
    method: "PUT",
    body: JSON.stringify({
      payload,
      locked_paths: lockedPaths(),
      expected_version: (concept?.version || 0) + 1,
      status: "confirmed",
    }),
  });
  await refreshWorkspace();
  activate("blueprint");
  setFeedback("Concept 已由作者确认，现可生成 Blueprint 候选。");
}

async function generateBlueprint() {
  setFeedback(`正在调用 ${selectedProvider()} 生成 Blueprint，请稍候…`);
  const task = await request(`${api}/${story.id}/generations`, {
    method: "POST",
    body: JSON.stringify({ action: "generate_blueprint", parameters: { provider: selectedProvider() } }),
  });
  document.querySelector("#bible-json").value = pretty(task.output.bible);
  document.querySelector("#arc-json").value = pretty(task.output.arc);
  document.querySelector("#living-json").value = pretty(task.output.living_state);
  document.querySelector("#blueprint-status").textContent = "AI 候选 · 尚未确认";
  setFeedback("Blueprint 候选已生成。请编辑后确认三个独立工件。");
}

async function confirmBlueprint() {
  const [bible, arc, living] = [
    parseJson(document.querySelector("#bible-json"), "Initial Story Bible"),
    parseJson(document.querySelector("#arc-json"), "Story Arc"),
    parseJson(document.querySelector("#living-json"), "Living State"),
  ];
  const current = await Promise.all([optionalArtifact("bible"), optionalArtifact("arc"), optionalArtifact("living_state")]);
  await Promise.all([
    request(`${api}/${story.id}/artifacts/bible`, { method: "PUT", body: JSON.stringify({ payload: bible, expected_version: (current[0]?.version || 0) + 1, status: "confirmed" }) }),
    request(`${api}/${story.id}/artifacts/arc`, { method: "PUT", body: JSON.stringify({ payload: arc, expected_version: (current[1]?.version || 0) + 1, status: "confirmed" }) }),
    request(`${api}/${story.id}/artifacts/living_state`, { method: "PUT", body: JSON.stringify({ payload: living, layer: "living", expected_version: (current[2]?.version || 0) + 1, status: "confirmed" }) }),
  ]);
  await request(`${api}/${story.id}/blueprint/confirm`, { method: "POST" });
  chapters = [];
  await refreshWorkspace();
  activate("chapters");
  setFeedback("Blueprint 已确认。现在生成 Chapter Plan，第一章将成为唯一可进入的章节。");
}

async function generateChapters() {
  setFeedback(`正在调用 ${selectedProvider()} 生成 Chapter Plan，请稍候…`);
  chapters = await request(`${api}/${story.id}/chapter-plan`, {
    method: "POST",
    body: JSON.stringify({ provider: selectedProvider(), chapter_count: Number(document.querySelector("#chapter-count-input").value) }),
  });
  story = await request(`${api}/${story.id}`);
  renderChapters();
  activate("chapters");
  setFeedback("Chapter Plan 已生成：第 1 章已激活，后续章节以锁定雏形保留。进入第 1 章继续规划。 ");
}

async function run(action) {
  try {
    document.querySelectorAll("button").forEach((button) => { button.disabled = true; });
    await action();
  } catch (error) {
    setFeedback(error.message, true);
  } finally {
    document.querySelectorAll("button").forEach((button) => { button.disabled = false; });
  }
}

loadModels();
activate("idea");
document.querySelectorAll(".step[data-step]").forEach((button) => button.addEventListener("click", () => activate(button.dataset.step)));
document.querySelector("#show-loader").addEventListener("click", () => document.querySelector("#loader").classList.toggle("hidden"));
document.querySelector("#create-story").addEventListener("click", () => run(createStory));
document.querySelector("#load-story").addEventListener("click", () => run(async () => {
  story = { id: document.querySelector("#story-id").value.trim() };
  if (!story.id) throw new Error("请输入 Story ID。");
  await refreshWorkspace();
  setFeedback("Story 已加载。");
}));
document.querySelector("#generate-concept").addEventListener("click", () => run(generateConcept));
document.querySelector("#confirm-concept").addEventListener("click", () => run(confirmConcept));
document.querySelector("#generate-blueprint").addEventListener("click", () => run(generateBlueprint));
document.querySelector("#confirm-blueprint").addEventListener("click", () => run(confirmBlueprint));
document.querySelector("#generate-chapters").addEventListener("click", () => run(generateChapters));
document.querySelector("#back-to-chapters").addEventListener("click", () => activate("chapters"));
