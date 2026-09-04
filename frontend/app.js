const conversation = document.querySelector("#conversation");
const form = document.querySelector("#prompt-form");
const input = document.querySelector("#prompt");
const sendButton = document.querySelector("#send");
const tools = document.querySelector("#tools");
const sources = document.querySelector("#sources");
const approvalPanel = document.querySelector("#approval-panel");
const approvalStatus = document.querySelector("#approval-status");
const entityList = document.querySelector("#entity-list");
let selectedEntity = null;

function promptFor(type) {
  const entityId = selectedEntity?.entity_id || "HWC-1001";
  return type === "followup"
    ? `Prepare a follow-up action for ${entityId} addressing the primary exception. Do not execute it without approval.`
    : `Summarize the current position for ${entityId}. Identify the primary exception and show your sources.`;
}

function formatDate(value, includeTime = false) {
  if (!value) return "Not provided";
  const date = new Date(includeTime ? value : `${value}T00:00:00`);
  return new Intl.DateTimeFormat("en-US", includeTime
    ? { dateStyle: "medium", timeStyle: "short" }
    : { dateStyle: "medium" }).format(date);
}

function selectEntity(entity) {
  selectedEntity = entity;
  document.querySelector("#entity-eyebrow").textContent = `Entity ${entity.entity_id}`;
  document.querySelector("#status-badge").textContent = entity.current_status || entity.status;
  document.querySelector("#detail-owner").textContent = entity.owner || "Not assigned";
  document.querySelector("#detail-severity").textContent = entity.severity || "Not provided";
  document.querySelector("#detail-category").textContent = entity.exception_category || "Not provided";
  document.querySelector("#detail-risk").textContent = entity.primary_risk || entity.risks?.[0] || "Not provided";
  document.querySelector("#detail-due-date").textContent = formatDate(entity.due_date);
  document.querySelector("#detail-last-review").textContent = formatDate(entity.last_review_date);
  document.querySelector("#detail-updated").textContent = formatDate(entity.source_last_updated, true);
  document.querySelectorAll(".entity").forEach(button => {
    button.classList.toggle("active", button.dataset.entityId === entity.entity_id);
  });
}

async function loadEntities() {
  try {
    const response = await fetch("/api/entities");
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Unable to load entities.");
    entityList.replaceChildren();
    for (const entity of result.entities) {
      const button = document.createElement("button");
      button.className = "entity";
      button.type = "button";
      button.dataset.entityId = entity.entity_id;
      button.innerHTML = `<span class="severity" aria-hidden="true"></span><span><strong></strong><small></small></span><span class="severity-label"></span>`;
      button.querySelector("strong").textContent = entity.entity_id;
      button.querySelector("small").textContent = entity.current_status || entity.status;
      button.querySelector(".severity-label").textContent = entity.severity || "-";
      button.addEventListener("click", () => selectEntity(entity));
      entityList.append(button);
    }
    if (result.entities.length) selectEntity(result.entities[0]);
  } catch (error) {
    entityList.innerHTML = `<div class="entity-loading error-text"></div>`;
    entityList.firstElementChild.textContent = error.message;
  }
}

function addMessage(role, text, isError = false) {
  const welcome = conversation.querySelector(".welcome");
  if (welcome) welcome.remove();

  const message = document.createElement("article");
  message.className = `message ${role}${isError ? " error" : ""}`;
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : "HWC governed agent";
  const body = document.createElement("p");
  body.textContent = text;
  message.append(label, body);
  conversation.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderEvidence(container, items) {
  container.replaceChildren();
  for (const item of items || []) {
    const element = document.createElement("div");
    element.className = "evidence-item";
    element.textContent = item;
    container.append(element);
  }
}

async function submitPrompt(prompt) {
  addMessage("user", prompt);
  input.value = "";
  sendButton.disabled = true;

  const loading = document.createElement("article");
  loading.className = "message agent";
  loading.innerHTML = '<span class="message-label">HWC governed agent</span><p>Retrieving governed evidence...</p>';
  conversation.append(loading);

  try {
    const response = await fetch("/api/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    const result = await response.json();
    loading.remove();
    if (!response.ok) throw new Error(result.error || "The agent request failed.");

    addMessage("agent", result.output_text);
    renderEvidence(tools, result.tools_used);
    renderEvidence(sources, result.source_ids);
    approvalPanel.classList.toggle("pending", Boolean(result.approval_required));
    approvalStatus.textContent = result.approval_required ? "Pending approval" : "Not requested";
  } catch (error) {
    loading.remove();
    addMessage("agent", error.message, true);
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  const prompt = input.value.trim();
  if (prompt) submitPrompt(prompt);
});

input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach(button => {
  button.addEventListener("click", () => submitPrompt(promptFor(button.dataset.prompt)));
});

loadEntities();