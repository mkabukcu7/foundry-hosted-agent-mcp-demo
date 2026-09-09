const conversation = document.querySelector("#conversation");
const form = document.querySelector("#prompt-form");
const input = document.querySelector("#prompt");
const sendButton = document.querySelector("#send");
const tools = document.querySelector("#tools");
const sources = document.querySelector("#sources");
const approvalPanel = document.querySelector("#approval-panel");
const approvalStatus = document.querySelector("#approval-status");
const approverInput = document.querySelector("#approver");
const approveButton = document.querySelector("#approve-approval");
const rejectButton = document.querySelector("#reject-approval");
const entitySelect = document.querySelector("#entity-select");
const refreshButton = document.querySelector("#refresh-entities");
const statusDot = document.querySelector("#status-dot");
const systemStatusMessage = document.querySelector("#system-status-message");
let entities = [];
let selectedEntity = null;
let requestInFlight = false;
let approvalInFlight = false;

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
  entitySelect.value = entity.entity_id;
}

function setSystemStatus(connected, message) {
  systemStatusMessage.textContent = message;
  statusDot.classList.toggle("error", !connected);
}

function resetBriefing() {
  conversation.replaceChildren();
  tools.className = "empty-evidence";
  tools.textContent = "Retrieving MCP activity...";
  sources.className = "empty-evidence";
  sources.textContent = "Retrieving governed sources...";
  approvalPanel.classList.remove("pending");
  approvalStatus.textContent = "Not requested";
}

function setApprovalControls(disabled) {
  approveButton.disabled = disabled;
  rejectButton.disabled = disabled;
  approverInput.disabled = disabled;
}

async function submitApproval(decision) {
  if (approvalInFlight || !selectedEntity) return;
  const approver = approverInput.value.trim();
  if (!approver) {
    approvalStatus.textContent = "Approver required";
    approverInput.focus();
    return;
  }

  approvalInFlight = true;
  setApprovalControls(true);
  approvalPanel.classList.add("pending");
  approvalStatus.textContent = "Recording decision...";
  try {
    const response = await fetch("/api/approvals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entity_id: selectedEntity.entity_id,
        decision,
        approver
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "The approval decision could not be recorded.");
    approvalPanel.classList.toggle("approved", decision === "APPROVED");
    approvalPanel.classList.toggle("rejected", decision === "REJECTED");
    approvalPanel.classList.remove("pending");
    approvalStatus.textContent = decision === "APPROVED" ? "Approved" : "Rejected";
    addMessage(
      "agent",
      `${selectedEntity.entity_id} was ${decision.toLowerCase()} by ${approver}. Approval ID: ${result.approval_id || "recorded in Fabric"}.`
    );
  } catch (error) {
    approvalPanel.classList.remove("pending");
    approvalStatus.textContent = "Decision failed";
    addMessage("agent", error.message, true);
  } finally {
    approvalInFlight = false;
    setApprovalControls(false);
  }
}

async function loadEntities({ refresh = false, summarize = false } = {}) {
  const selectedEntityId = selectedEntity?.entity_id;
  refreshButton.disabled = true;
  refreshButton.classList.toggle("refreshing", refresh);
  try {
    const healthResponse = await fetch("/api/health");
    const health = await healthResponse.json();
    if (!healthResponse.ok) throw new Error(health.error || "MCP is unavailable.");
    setSystemStatus(true, "MCP connected");
    const response = await fetch(`/api/entities${refresh ? "?refresh=1" : ""}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Unable to load entities.");
    entities = result.entities;
    entitySelect.replaceChildren();
    for (const entity of entities) {
      const option = document.createElement("option");
      const severity = entity.severity ? ` · ${entity.severity}` : "";
      option.value = entity.entity_id;
      option.textContent = `${entity.entity_id}${severity}`;
      entitySelect.append(option);
    }
    entitySelect.disabled = !entities.length;
    const nextEntity = entities.find(entity => entity.entity_id === selectedEntityId) || entities[0];
    if (nextEntity) {
      selectEntity(nextEntity);
      if (summarize) {
        resetBriefing();
        await submitPrompt(promptFor("summary"));
      }
    }
  } catch (error) {
    setSystemStatus(false, "MCP unavailable");
    entitySelect.replaceChildren(new Option(error.message));
    entitySelect.disabled = true;
  } finally {
    refreshButton.disabled = false;
    refreshButton.classList.remove("refreshing");
  }
}

entitySelect.addEventListener("change", () => {
  const entity = entities.find(item => item.entity_id === entitySelect.value);
  if (entity) {
    selectEntity(entity);
    resetBriefing();
    submitPrompt(promptFor("summary"));
  }
});

refreshButton.addEventListener("click", () => {
  loadEntities({ refresh: true, summarize: true });
});

approveButton.addEventListener("click", () => submitApproval("APPROVED"));
rejectButton.addEventListener("click", () => submitApproval("REJECTED"));

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
  if (requestInFlight) return;
  requestInFlight = true;
  addMessage("user", prompt);
  input.value = "";
  sendButton.disabled = true;
  entitySelect.disabled = true;

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
    requestInFlight = false;
    sendButton.disabled = false;
    entitySelect.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  const prompt = input.value.trim();
  if (prompt) {
    const entityId = selectedEntity?.entity_id;
    const explicitEntity = /\bHWC-\d+\b/i.test(prompt);
    submitPrompt(!explicitEntity && entityId ? `${prompt} for ${entityId}` : prompt);
  }
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