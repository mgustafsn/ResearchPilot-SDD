"use strict";

const byId = (id) => document.getElementById(id);
const fieldNames = ["title", "researchQuestion", "keywords", "yearFrom", "yearTo", "maxPaperCount"];
let selectedProject = null;

function clearErrors() {
  byId("error").hidden = true;
  byId("error").textContent = "";
  for (const name of fieldNames) {
    byId(`error-${name}`).textContent = "";
    byId(name).removeAttribute("aria-invalid");
  }
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
  byId("loading").hidden = false;
  try {
    const projects = await request("/api/projects");
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
    showError(error);
  } finally {
    byId("loading").hidden = true;
  }
}

function showDetail(project) {
  selectedProject = project;
  byId("detail-title").textContent = project.title;
  byId("detail-question").textContent = project.researchQuestion;
  byId("detail-keywords").textContent = project.keywords.join(", ") || "None";
  byId("detail-years").textContent = `${project.yearFrom ?? "Any"} – ${project.yearTo ?? "Any"}`;
  byId("detail-limit").textContent = String(project.maxPaperCount);
  byId("detail").hidden = false;
  byId("form-section").hidden = true;
  byId("detail-title").focus();
}

async function openProject(id) {
  clearErrors();
  try { showDetail(await request(`/api/projects/${id}`)); } catch (error) { showError(error); }
}

byId("new-project").addEventListener("click", () => {
  clearErrors();
  byId("project-form").reset();
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
  try {
    const project = await request("/api/projects", {method: "POST", body: JSON.stringify(data)});
    showDetail(project);
    await loadProjects();
  } catch (error) {
    showError(error);
  } finally {
    byId("save-project").disabled = false;
  }
});

loadProjects();
