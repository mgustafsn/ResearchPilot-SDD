"use strict";

const byId = (id) => document.getElementById(id);
const fieldNames = ["title", "researchQuestion", "keywords", "yearFrom", "yearTo", "maxPaperCount"];
let selectedProject = null;
let editingId = null;
let viewEpoch = 0;
let listEpoch = 0;
let queryState = null;
let queryEditingId = null;
const queryDrafts = new Map();
const pendingGenerations = new Set();
const pendingSearches = new Set();
let referenceState = null;
let latestPaperState = null;

function clearErrors() {
  byId("error").hidden = true;
  byId("error").textContent = "";
  for (const name of fieldNames) {
    byId(`error-${name}`).textContent = "";
    byId(name).removeAttribute("aria-invalid");
  }
  byId("query-text").removeAttribute("aria-invalid");
  byId("query-text-error").textContent = "";
}

function showError(error) {
  byId("error").textContent = error.message || "The request failed. Please try again.";
  byId("error").hidden = false;
  for (const field of error.fields || []) {
    if (fieldNames.includes(field.field)) {
      byId(field.field).setAttribute("aria-invalid", "true");
      byId(`error-${field.field}`).textContent = field.message;
    }
  }
  byId("error").focus();
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options, headers: {"Content-Type": "application/json"},
    });
  } catch {
    throw {message: "Cannot reach the local application. Please try again.", fields: []};
  }
  if (!response.ok) {
    let body;
    try { body = await response.json(); } catch { body = {}; }
    throw body.error || {message: "The request failed. Please try again.", fields: []};
  }
  return response.status === 204 ? null : response.json();
}

async function loadProjects() {
  const token = ++listEpoch;
  const view = viewEpoch;
  byId("loading").hidden = false;
  try {
    const projects = await request("/api/projects");
    if (token !== listEpoch) return;
    const items = projects.map((project) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = project.title;
      button.addEventListener("click", () => openProject(project.id));
      item.append(button);
      return item;
    });
    byId("project-list").replaceChildren(...items);
    byId("empty-state").hidden = projects.length !== 0;
  } catch (error) {
    if (token === listEpoch && view === viewEpoch) showError(error);
  } finally {
    if (token === listEpoch) byId("loading").hidden = true;
  }
}

function showDetail(project) {
  const epoch = ++viewEpoch;
  selectedProject = project;
  editingId = null;
  byId("detail-title").textContent = project.title;
  byId("detail-question").textContent = project.researchQuestion;
  byId("detail-keywords").textContent = project.keywords.join(", ") || "None";
  byId("detail-years").textContent = `${project.yearFrom ?? "Any"} – ${project.yearTo ?? "Any"}`;
  byId("detail-limit").textContent = String(project.maxPaperCount);
  byId("detail").hidden = false;
  byId("form-section").hidden = true;
  byId("detail-title").focus();
  queryState = null;
  referenceState = null;
  latestPaperState = null;
  const draft = queryDrafts.get(project.id) || {text: "", id: null};
  queryEditingId = draft.id;
  byId("query-text").value = draft.text;
  byId("query-section").hidden = true;
  byId("retrieval-section").hidden = true;
  byId("saved-reference-section").hidden = false;
  byId("save-query").disabled = true;
  byId("generate-queries").disabled = true;
  byId("search-openalex").disabled = true;
  byId("generation-status").textContent = pendingGenerations.has(project.id)
    ? "Generating suggestions…" : "";
  loadQueries(project.id, epoch);
  loadPapers(project.id, epoch);
  loadReferences(project.id, epoch);
}

async function openProject(id) {
  const epoch = ++viewEpoch;
  queryState = null;
  byId("save-query").disabled = true;
  clearErrors();
  try {
    const project = await request(`/api/projects/${id}`);
    if (epoch === viewEpoch) showDetail(project);
  } catch (error) { if (epoch === viewEpoch) showError(error); }
}

byId("new-project").addEventListener("click", () => {
  ++viewEpoch;
  clearErrors();
  byId("project-form").reset();
  editingId = null;
  byId("form-heading").textContent = "New project";
  byId("form-section").hidden = false;
  byId("detail").hidden = true;
  byId("title").focus();
});

byId("cancel-form").addEventListener("click", () => {
  clearErrors();
  byId("form-section").hidden = true;
  if (selectedProject) showDetail(selectedProject);
  else byId("new-project").focus();
});

byId("project-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  const optionalNumber = (id) => byId(id).value === "" ? null : Number(byId(id).value);
  const data = {
    title: byId("title").value, researchQuestion: byId("researchQuestion").value,
    keywords: byId("keywords").value.trim() === "" ? [] : byId("keywords").value.split("\n"),
    yearFrom: optionalNumber("yearFrom"), yearTo: optionalNumber("yearTo"),
    maxPaperCount: optionalNumber("maxPaperCount"),
  };
  byId("save-project").disabled = true;
  const epoch = viewEpoch;
  try {
    const path = editingId ? `/api/projects/${editingId}` : "/api/projects";
    const project = await request(path, {
      method: editingId ? "PUT" : "POST", body: JSON.stringify(data),
    });
    if (epoch === viewEpoch) showDetail(project);
    await loadProjects();
  } catch (error) {
    if (epoch === viewEpoch) showError(error);
  } finally {
    byId("save-project").disabled = false;
  }
});

byId("edit-project").addEventListener("click", () => {
  if (!selectedProject) return;
  ++viewEpoch;
  clearErrors();
  editingId = selectedProject.id;
  for (const name of fieldNames) {
    byId(name).value = name === "keywords" ? selectedProject.keywords.join("\n")
      : selectedProject[name] ?? "";
  }
  byId("form-heading").textContent = "Edit project";
  byId("detail").hidden = true;
  byId("form-section").hidden = false;
  byId("title").focus();
});

byId("delete-project").addEventListener("click", () => {
  clearErrors();
  if (selectedProject) byId("delete-dialog").showModal();
});

byId("cancel-delete").addEventListener("click", () => byId("delete-dialog").close());

byId("confirm-delete").addEventListener("click", async () => {
  if (!selectedProject) return;
  const target = selectedProject.id;
  const epoch = ++viewEpoch;
  byId("confirm-delete").disabled = true;
  try {
    await request(`/api/projects/${target}`, {method: "DELETE"});
    if (epoch !== viewEpoch) return;
    byId("delete-dialog").close();
    selectedProject = null;
    queryDrafts.delete(target);
    byId("detail").hidden = true;
    await loadProjects();
    byId("new-project").focus();
  } catch (error) {
    byId("delete-dialog").close();
    if (epoch === viewEpoch) showError(error);
  } finally {
    byId("confirm-delete").disabled = false;
  }
});

function queryViewCurrent(projectId, epoch) {
  return epoch === viewEpoch && selectedProject?.id === projectId && !byId("detail").hidden;
}

function showQueryError(error) {
  showError(error);
  for (const field of error.fields || []) {
    if (field.field === "text") {
      byId("query-text").setAttribute("aria-invalid", "true");
      byId("query-text-error").textContent = field.message;
    }
  }
}

function applyQueryState(state) {
  if (queryState && state.revision < queryState.revision) return;
  queryState = state;
  const items = state.queries.map((query) => {
    const item = document.createElement("li");
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = query.enabled;
    label.append(checkbox, document.createTextNode(`Use query: ${query.text}`));
    checkbox.addEventListener("change", () => {
      checkbox.disabled = true;
      mutateQuery(`/${query.id}`, "PATCH", {enabled: checkbox.checked});
    });
    const meta = document.createElement("span");
    meta.textContent = ` ${query.origin} · ${query.userOwned ? "user-owned" : "untouched suggestion"} `;
    const edit = document.createElement("button");
    edit.type = "button";
    edit.textContent = "Edit query";
    edit.addEventListener("click", () => {
      clearErrors();
      queryEditingId = query.id;
      byId("query-text").value = query.text;
      saveQueryDraft();
      byId("query-text").focus();
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Delete query";
    remove.addEventListener("click", () => mutateQuery(`/${query.id}`, "DELETE"));
    item.append(label, meta, edit, document.createTextNode(" "), remove);
    return item;
  });
  byId("query-list").replaceChildren(...items);
  byId("query-empty").hidden = state.queries.length !== 0;
  byId("query-refresh").hidden = !state.refreshRequired;
  byId("query-section").hidden = false;
  byId("save-query").disabled = false;
  updateGenerateControl();
  byId("retrieval-section").hidden = false;
  updateSearchControl();
}

function updateGenerateControl() {
  const available = Boolean(queryState?.generationAvailable);
  byId("query-availability").textContent = available
    ? "Manual queries always work; suggestions are optional."
    : "Suggestion generation is not configured. Manual queries still work.";
  byId("generate-queries").disabled = !available || !selectedProject ||
    pendingGenerations.has(selectedProject.id);
}

function updateSearchControl() {
  const hasEnabled = Boolean(queryState?.queries?.some((query) => query.enabled));
  byId("search-openalex").disabled = !hasEnabled || !selectedProject ||
    pendingSearches.has(selectedProject.id);
}

function safeExternalUrl(value) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) return null;
    return url.href;
  } catch {
    return null;
  }
}

function makePaperLink(value, label) {
  const href = safeExternalUrl(value);
  if (!href) return null;
  const link = document.createElement("a");
  link.href = href;
  link.textContent = label;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function renderPapers(state) {
  latestPaperState = state;
  const papers = state.papers || [];
  const savedKeys = new Set((referenceState?.references || []).map(
    (reference) => `${reference.provider}:${reference.providerId}`));
  const items = papers.map((paper) => {
    const item = document.createElement("li");
    const heading = document.createElement("h4");
    heading.textContent = paper.title;
    item.append(heading);

    const save = document.createElement("button");
    save.type = "button";
    const alreadySaved = savedKeys.has(`${paper.provider}:${paper.providerId}`);
    save.textContent = alreadySaved ? "Saved" : "Save reference";
    save.disabled = alreadySaved;
    save.addEventListener("click", () => saveReference(paper.id, save));
    item.append(save);

    const similarity = document.createElement("p");
    similarity.className = "embedding-similarity";
    similarity.textContent = typeof paper.embeddingScore === "number"
      ? `Embedding similarity: ${(paper.embeddingScore * 100).toFixed(1)}%`
      : "Not ranked — search again to rank locally.";
    item.append(similarity);
    if (paper.rankingProvenance?.truncated) {
      const truncation = document.createElement("p");
      truncation.textContent = "Paper input was truncated to 256 model tokens for ranking.";
      item.append(truncation);
    }

    const details = document.createElement("p");
    const metadata = [];
    if (paper.authors?.length) metadata.push(paper.authors.join(", "));
    if (paper.publicationYear) metadata.push(String(paper.publicationYear));
    if (paper.venue) metadata.push(paper.venue);
    if (paper.citationCount !== null && paper.citationCount !== undefined) {
      metadata.push(`${paper.citationCount} citations`);
    }
    metadata.push(paper.isOpenAccess === true ? "Open access" :
      paper.isOpenAccess === false ? "Not marked open access" : "Open-access status unknown");
    details.textContent = metadata.join(" · ");
    item.append(details);

    if (paper.abstract) {
      const abstract = document.createElement("p");
      abstract.textContent = paper.abstract;
      item.append(abstract);
    }
    if (paper.doi) {
      const doi = document.createElement("p");
      doi.textContent = `DOI: ${paper.doi}`;
      item.append(doi);
    }

    const links = document.createElement("p");
    const source = makePaperLink(paper.sourceUrl, "OpenAlex record");
    const publication = makePaperLink(paper.publicationUrl, "Publication page");
    const fullText = makePaperLink(paper.fullTextUrl, "Open-access copy");
    for (const [index, link] of [source, publication, fullText].filter(Boolean).entries()) {
      if (index > 0) links.append(document.createTextNode(" · "));
      links.append(link);
    }
    if (links.childNodes.length) item.append(links);
    return item;
  });
  byId("paper-list").replaceChildren(...items);
  const ranking = state.rankingProvenance;
  byId("ranking-model").textContent = ranking
    ? `Local model: ${ranking.modelId} · revision ${ranking.modelRevision}` +
      (ranking.truncated ? " · Research-question/keyword input was truncated to 256 model tokens." : "")
    : "";
  const attempt = state.latestAttempt || state;
  const used = attempt.queriesUsed || [];
  const unused = attempt.queriesUnused || [];
  byId("search-queries-used").textContent = used.length
    ? `Queries used: ${used.map((query) => query.text).join(", ")}` : "";
  byId("search-queries-unused").textContent = unused.length
    ? `Queries unused (no budget): ${unused.map((query) => query.text).join(", ")}` : "";
  byId("papers-empty").hidden =
    papers.length !== 0 || attempt.status !== "succeeded";
  if (attempt.status === "pending") {
    byId("search-status").textContent = "A search is in progress for this project.";
  } else if (attempt.status === "failed") {
    byId("search-status").textContent = "The latest search failed; previous results were kept.";
  } else if (attempt.status === "succeeded") {
    byId("search-status").textContent =
      `Latest search: ${papers.length} unique papers; ${attempt.rawFetchedCount} fetched, ` +
      `${attempt.skippedCount} skipped, ${attempt.duplicateCount} duplicates removed.`;
  } else {
    byId("search-status").textContent = "No search has been run for this project.";
  }
}

function renderReferences(state) {
  referenceState = state;
  const items = state.references.map((reference) => {
    const item = document.createElement("li");
    const heading = document.createElement("h4");
    heading.textContent = reference.title;
    item.append(heading);
    const metadata = document.createElement("p");
    metadata.textContent = [
      ...(reference.authors || []),
      reference.publicationYear ? String(reference.publicationYear) : null,
      reference.venue,
    ].filter(Boolean).join(" · ");
    item.append(metadata);
    const link = makePaperLink(reference.sourceUrl, "OpenAlex record");
    if (link) item.append(link);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove reference";
    remove.addEventListener("click", () => removeReference(reference.id, remove));
    item.append(document.createTextNode(" "), remove);
    return item;
  });
  byId("saved-reference-list").replaceChildren(...items);
  byId("saved-reference-empty").hidden = items.length !== 0;
  if (latestPaperState) renderPapers(latestPaperState);
}

async function loadReferences(projectId, epoch) {
  try {
    const state = await request(`/api/projects/${projectId}/references`);
    if (queryViewCurrent(projectId, epoch)) renderReferences(state);
  } catch (error) {
    if (queryViewCurrent(projectId, epoch)) showError(error);
  }
}

async function saveReference(paperId, button) {
  if (!selectedProject) return;
  const projectId = selectedProject.id;
  const epoch = viewEpoch;
  button.disabled = true;
  try {
    await request(`/api/projects/${projectId}/references`, {
      method: "POST", body: JSON.stringify({paperId}),
    });
    if (queryViewCurrent(projectId, epoch)) await loadReferences(projectId, epoch);
  } catch (error) {
    button.disabled = false;
    if (queryViewCurrent(projectId, epoch)) showError(error);
  }
}

async function removeReference(referenceId, button) {
  if (!selectedProject) return;
  const projectId = selectedProject.id;
  const epoch = viewEpoch;
  button.disabled = true;
  try {
    await request(`/api/projects/${projectId}/references/${referenceId}`, {method: "DELETE"});
    if (queryViewCurrent(projectId, epoch)) await loadReferences(projectId, epoch);
  } catch (error) {
    button.disabled = false;
    if (queryViewCurrent(projectId, epoch)) showError(error);
  }
}

function generationSummaryText(summary) {
  const parts = [`${summary.addedCount} added`, `${summary.replacedCount} replaced`];
  if (summary.duplicateSkippedCount) {
    parts.push(`${summary.duplicateSkippedCount} skipped as duplicate of a kept query`);
  }
  if (summary.capacitySkippedCount) {
    parts.push(`${summary.capacitySkippedCount} skipped (20-query limit)`);
  }
  return `Suggestions updated: ${parts.join(", ")}.`;
}

async function loadQueries(projectId, epoch) {
  try {
    const state = await request(`/api/projects/${projectId}/queries`);
    if (queryViewCurrent(projectId, epoch)) applyQueryState(state);
  } catch (error) {
    if (queryViewCurrent(projectId, epoch)) showQueryError(error);
  }
}

async function loadPapers(projectId, epoch) {
  try {
    const state = await request(`/api/projects/${projectId}/papers`);
    if (queryViewCurrent(projectId, epoch)) renderPapers(state);
  } catch (error) {
    if (queryViewCurrent(projectId, epoch)) showError(error);
  }
}

function saveQueryDraft() {
  if (selectedProject) queryDrafts.set(selectedProject.id, {
    text: byId("query-text").value, id: queryEditingId,
  });
}

async function mutateQuery(suffix, method, data = {}) {
  if (!queryState || !selectedProject) return;
  clearErrors();
  const projectId = selectedProject.id;
  const epoch = viewEpoch;
  const revision = queryState.revision;
  const editingAtStart = queryEditingId;
  let path = `/api/projects/${projectId}/queries${suffix}`;
  const options = {method};
  if (method === "DELETE") path += `?expectedRevision=${revision}`;
  else options.body = JSON.stringify({...data, expectedRevision: revision});
  try {
    const state = await request(path, options);
    if (!queryViewCurrent(projectId, epoch)) return;
    if (queryState && state.revision < queryState.revision) return;
    applyQueryState(state);
    if ((method === "POST" || (method === "PATCH" && data.text !== undefined)) &&
        queryEditingId === editingAtStart && byId("query-text").value === data.text) {
      queryEditingId = null;
      byId("query-text").value = "";
      saveQueryDraft();
    }
    if (method === "DELETE" && suffix === `/${queryEditingId}`) {
      queryEditingId = null;
      saveQueryDraft();
    }
  } catch (error) {
    if (!queryViewCurrent(projectId, epoch)) return;
    showQueryError(error);
    // Reload only saved state. The current manual draft is never cleared here.
    await loadQueries(projectId, epoch);
  } finally {
    if (queryViewCurrent(projectId, epoch)) byId("save-query").disabled = false;
  }
}

byId("generate-queries").addEventListener("click", async () => {
  if (!queryState || !selectedProject || pendingGenerations.has(selectedProject.id)) return;
  clearErrors();
  const projectId = selectedProject.id;
  const epoch = viewEpoch;
  pendingGenerations.add(projectId);
  updateGenerateControl();
  byId("generation-status").textContent = "Generating suggestions…";
  try {
    const state = await request(`/api/projects/${projectId}/queries/generate`, {
      method: "POST", body: JSON.stringify({expectedRevision: queryState.revision}),
    });
    pendingGenerations.delete(projectId);
    if (queryViewCurrent(projectId, epoch)) {
      applyQueryState(state);
      byId("generation-status").textContent = generationSummaryText(state.generationSummary);
    } else if (selectedProject?.id === projectId && !byId("detail").hidden) {
      // Same project reopened meanwhile: show saved state through the current view.
      byId("generation-status").textContent = "";
      await loadQueries(projectId, viewEpoch);
    }
  } catch (error) {
    pendingGenerations.delete(projectId);
    if (!queryViewCurrent(projectId, epoch)) return;
    byId("generation-status").textContent = "";
    showQueryError(error);
    // Reload saved state only; the unsaved draft and other input stay untouched.
    await loadQueries(projectId, epoch);
  } finally {
    if (selectedProject?.id === projectId && !byId("detail").hidden) updateGenerateControl();
  }
});

byId("query-text").addEventListener("input", saveQueryDraft);
byId("cancel-query").addEventListener("click", () => {
  queryEditingId = null;
  byId("query-text").value = "";
  saveQueryDraft();
  clearErrors();
  byId("query-text").focus();
});
byId("query-form").addEventListener("submit", (event) => {
  event.preventDefault();
  byId("save-query").disabled = true;
  const data = {text: byId("query-text").value};
  mutateQuery(queryEditingId ? `/${queryEditingId}` : "", queryEditingId ? "PATCH" : "POST", data);
});

byId("search-openalex").addEventListener("click", async () => {
  if (!selectedProject || !queryState || pendingSearches.has(selectedProject.id)) return;
  const projectId = selectedProject.id;
  const epoch = viewEpoch;
  pendingSearches.add(projectId);
  updateSearchControl();
  byId("search-status").textContent = "Searching OpenAlex…";
  try {
    const state = await request(`/api/projects/${projectId}/search`, {method: "POST"});
    pendingSearches.delete(projectId);
    if (queryViewCurrent(projectId, epoch)) renderPapers(state);
    else if (selectedProject?.id === projectId && !byId("detail").hidden) {
      await loadPapers(projectId, viewEpoch);
    }
  } catch (error) {
    pendingSearches.delete(projectId);
    if (queryViewCurrent(projectId, epoch)) {
      byId("search-status").textContent = "Search failed; previous results were kept.";
      showError(error);
      await loadPapers(projectId, epoch);
    }
  } finally {
    if (selectedProject?.id === projectId && !byId("detail").hidden) updateSearchControl();
  }
});

loadProjects();
