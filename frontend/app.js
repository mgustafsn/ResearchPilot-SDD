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
  const draft = queryDrafts.get(project.id) || {text: "", id: null};
  queryEditingId = draft.id;
  byId("query-text").value = draft.text;
  byId("query-section").hidden = true;
  byId("save-query").disabled = true;
  loadQueries(project.id, epoch);
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
}

async function loadQueries(projectId, epoch) {
  try {
    const state = await request(`/api/projects/${projectId}/queries`);
    if (queryViewCurrent(projectId, epoch)) applyQueryState(state);
  } catch (error) {
    if (queryViewCurrent(projectId, epoch)) showQueryError(error);
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

loadProjects();
