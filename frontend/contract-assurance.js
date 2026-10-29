const assuranceConversation = document.querySelector("#assurance-conversation");
const assuranceForm = document.querySelector("#assurance-form");
const assuranceInput = document.querySelector("#assurance-prompt");
const assuranceStatus = document.querySelector("#assurance-status");
const assuranceReset = document.querySelector("#assurance-reset");
const assuranceReceipts = document.querySelector("#assurance-receipts");
let assuranceSession = null;
let assuranceBusy = false;

function renderAssuranceReceipts(receipts) {
  assuranceReceipts.replaceChildren();
  if (!receipts.length) {
    assuranceReceipts.textContent = "No execution receipt; integration unverified.";
    return;
  }
  for (const receipt of receipts) {
    const row = document.createElement("p");
    if (receipt.status === "comparison_completed") {
      const contract = receipt.sessions?.contract;
      const rfp = receipt.sessions?.rfp;
      row.textContent = `Comparison completed | Contract context: ${contract?.session_reused ? "reused" : "new"} (${contract?.session_tag || "unverified"}) | RFP context: ${rfp?.session_reused ? "reused" : "new"} (${rfp?.session_tag || "unverified"})`;
    } else if (receipt.status === "document_validated") {
      row.textContent = `Document validated${receipt.operation_replayed ? " (earlier receipt replayed; no new analyst call)" : ""} | ${receipt.findings?.artifact_id} v${receipt.findings?.version} -> v${receipt.annotated?.version} | Read version: ${receipt.read_artifact?.version} | Parent SHA-256: ${receipt.annotation_parent?.sha256} | SHA-256: ${receipt.annotated?.sha256}`;
    } else {
      row.textContent = receipt.status;
    }
    assuranceReceipts.append(row);
  }
}

function assuranceMessage(role, text, error = false) {
  const article = document.createElement("article");
  article.className = `message ${role}${error ? " error" : ""}`;
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : "Assurance orchestrator";
  const body = document.createElement("p");
  body.textContent = text;
  article.append(label, body);
  assuranceConversation.append(article);
  article.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function assuranceRequest(prompt, reset = false) {
  if (assuranceBusy) return;
  assuranceBusy = true;
  document.querySelectorAll("button").forEach(button => { button.disabled = true; });
  assuranceStatus.textContent = reset ? "Resetting context..." : "Consulting specialists...";
  if (!reset) assuranceMessage("user", prompt);
  try {
    if (!assuranceSession) {
      const sessionResponse = await fetch("/api/assurance/session", { method: "POST" });
      if (!sessionResponse.ok) throw new Error("Unable to create a live review session.");
      assuranceSession = (await sessionResponse.json()).session_id;
    }
    const response = await fetch("/api/assurance/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: assuranceSession, prompt, reset })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    if (result.mode !== "live") throw new Error("Unexpected response mode.");
    if (reset) assuranceConversation.replaceChildren();
    assuranceMessage("agent", result.output_text || "Conversation reset.");
    renderAssuranceReceipts(result.execution_receipts || []);
    assuranceStatus.textContent = result.execution_receipts?.length ? "Execution receipt received" : "Response received; execution unverified";
    assuranceInput.value = "";
  } catch (error) {
    assuranceMessage("agent", error.message, true);
    assuranceStatus.textContent = "Live review unavailable";
  } finally {
    assuranceBusy = false;
    document.querySelectorAll("button").forEach(button => { button.disabled = false; });
  }
}

assuranceForm.addEventListener("submit", event => {
  event.preventDefault();
  const prompt = assuranceInput.value.trim();
  if (prompt) assuranceRequest(prompt);
});
document.querySelectorAll("[data-assurance-prompt]").forEach(button => {
  button.addEventListener("click", () => assuranceRequest(button.dataset.assurancePrompt));
});
assuranceReset.addEventListener("click", () => assuranceRequest("Reset conversation.", true));