const state = { page: 1, limit: 6, total: 0, query: "", location: "", type: "", jobs: [] };
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const titleCase = (s) => String(s || "").toLowerCase().replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

async function api(url, options = {}) {
  const response = await fetch(url, { headers: {"Content-Type":"application/json"}, ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Something went wrong. Please try again.");
  return data;
}
function showMessage(text) { $("message").textContent = text; $("message").classList.remove("hidden"); }
function hideMessage() { $("message").classList.add("hidden"); }
function setView(view) {
  $("jobs-view").classList.toggle("hidden", view !== "jobs");
  $("history-view").classList.toggle("hidden", view !== "history");
  document.querySelectorAll("[data-view]").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  if (view === "history") $("history-email").focus();
}
document.querySelectorAll("[data-view]").forEach(b => b.addEventListener("click", () => setView(b.dataset.view)));

async function loadJobs(append = false) {
  hideMessage();
  if (!append) { state.page = 1; $("job-list").innerHTML = '<div class="empty">Finding opportunities…</div>'; }
  const params = new URLSearchParams({q:state.query, location:state.location, job_type:state.type, page:state.page, limit:state.limit});
  try {
    const data = await api(`/api/jobs?${params}`);
    state.total = data.total;
    state.jobs = append ? [...state.jobs, ...data.items] : data.items;
    $("stat-jobs").textContent = data.total;
    $("results-count").textContent = `${data.total} opportunity${data.total === 1 ? "" : "ies"} found`;
    $("job-list").innerHTML = state.jobs.length ? state.jobs.map(jobCard).join("") : '<div class="empty">No jobs match those filters. Try another keyword or location.</div>';
    $("load-more").classList.toggle("hidden", state.jobs.length >= state.total || !state.total);
    document.querySelectorAll("[data-job]").forEach(el => el.addEventListener("click", (e) => {
      if (e.target.closest(".bookmark")) { e.stopPropagation(); const b=e.target.closest(".bookmark"); b.textContent=b.textContent==="♡"?"♥":"♡"; b.classList.toggle("saved"); return; }
      openJob(Number(el.dataset.job));
    }));
  } catch (e) { $("job-list").innerHTML = ""; showMessage(e.message); }
}
function jobCard(job) {
  const initials = job.company.split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase();
  return `<article class="job-card" data-job="${job.id}" tabindex="0" role="button" aria-label="View ${esc(job.title)}">
    <div class="job-card-top"><div style="display:flex;gap:12px;align-items:center"><div class="company-logo">${esc(initials)}</div><div><h3>${esc(job.title)}</h3><div class="company">${esc(job.company)}</div></div></div><button class="bookmark" aria-label="Save job" type="button">♡</button></div>
    <div class="job-meta"><span class="pill">⌖ ${esc(job.location)}</span><span class="pill">${esc(job.job_type)}</span></div>
    <div class="salary">${esc(job.salary)}</div><p class="job-description">${esc(job.description)}</p>
    <div class="job-card-bottom"><span class="posted">Posted ${job.posted_days===1?"yesterday":job.posted_days+" days ago"}</span><button class="text-btn" type="button">View details ↗</button></div>
  </article>`;
}
$("search-form").addEventListener("submit", e => {
  e.preventDefault();
  state.query = $("search-q").value.trim();
  state.location = $("search-location").value.trim();
  state.type = $("search-type").value;
  loadJobs(false);
});
$("load-more").addEventListener("click", () => { state.page++; loadJobs(true); });

function openModal(html) {
  $("modal-content").innerHTML = html;
  $("modal").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}
function closeModal() { $("modal").classList.add("hidden"); document.body.style.overflow = ""; }
$("modal-close").addEventListener("click", closeModal);
$("modal").addEventListener("click", e => { if (e.target.dataset.close) closeModal(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

async function openJob(id) {
  try {
    const job = await api(`/api/jobs/${id}`);
    openModal(`<p class="eyebrow">JOB DETAILS</p><h2 id="modal-title">${esc(job.title)}</h2><div class="detail-company">${esc(job.company)} · ${esc(job.location)}</div>
      <div class="job-meta"><span class="pill">${esc(job.job_type)}</span><span class="pill">${esc(job.salary)}</span></div>
      <h3>About the role</h3><p class="detail-description">${esc(job.description)}</p><h3>Skills</h3><div class="detail-skills">${job.skills.map(s=>`<span class="pill">${esc(s)}</span>`).join("")}</div>
      <button class="primary-btn" id="apply-open">Apply for this job</button> <p class="modal-note">Demo application form. Your email is used to find your application history.</p>`);
    $("apply-open").addEventListener("click", () => showApplyForm(job));
  } catch(e) { showMessage(e.message); }
}
function showApplyForm(job) {
  $("modal-content").innerHTML = `<p class="eyebrow">APPLICATION</p><h2 id="modal-title">Apply for ${esc(job.title)}</h2><p class="detail-company">${esc(job.company)}</p>
    <form class="apply-form" id="apply-form">
      <label>Full name<input name="user_name" required minlength="2" maxlength="100" placeholder="Your full name"></label>
      <label>Email address<input name="user_email" type="email" required placeholder="you@example.com"></label>
      <label>Resume file name<input name="resume_name" required maxlength="200" placeholder="e.g. resume.pdf"><span class="modal-note">Demo version records the resume filename only; it does not upload the file.</span></label>
      <label>Cover letter (optional)<textarea name="cover_letter" maxlength="2000" placeholder="Why are you a good fit?"></textarea></label>
      <button class="primary-btn" type="submit">Submit application</button><p class="modal-note">Submitting means you agree that your details are stored in this local demo database.</p>
    </form>`;
  $("apply-form").addEventListener("submit", async e => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const button = e.currentTarget.querySelector("button[type=submit]");
    button.disabled = true; button.textContent = "Submitting…";
    try {
      const result = await api(`/api/jobs/${job.id}/applications`, {method:"POST", body:JSON.stringify(payload)});
      const a = result.application;
      openModal(`<div class="success-panel"><div style="font-size:28px">✓</div><strong>Application submitted!</strong><p>${esc(job.title)} at ${esc(job.company)}</p><p>Your application ID is <b>#${a.id}</b>.</p><p>Status: <b>${esc(a.status)}</b></p><p>Use the same email to view your application history.</p></div><div style="display:flex;gap:10px;margin-top:18px"><button class="primary-btn" id="view-history">View applications</button><button class="secondary-btn" id="close-success">Continue browsing</button></div>`);
      $("view-history").addEventListener("click", () => { $("history-email").value = payload.user_email; closeModal(); setView("history"); loadHistory(payload.user_email); });
      $("close-success").addEventListener("click", () => { closeModal(); loadJobs(false); });
    } catch(err) {
      const note = document.createElement("p"); note.className="message"; note.textContent=err.message; e.currentTarget.prepend(note);
      button.disabled=false; button.textContent="Submit application";
    }
  });
}

$("history-form").addEventListener("submit", e => { e.preventDefault(); loadHistory($("history-email").value.trim()); });
async function loadHistory(email) {
  $("history-list").innerHTML = '<div class="empty">Loading your applications…</div>';
  try {
    const data = await api(`/api/users/applications?email=${encodeURIComponent(email)}`);
    if (!data.items.length) { $("history-list").innerHTML = '<div class="empty">No applications found for this email yet. Apply for a job first.</div>'; return; }
    $("history-list").innerHTML = `<p class="muted">${data.total} application${data.total===1?"":"s"} found</p>` + data.items.map(a=>`<article class="history-card"><div><h3>${esc(a.job_title)}</h3><div class="company">${esc(a.company)} · ${esc(a.location)}</div><p class="posted">Application #${a.application_id} · ${esc(a.created_at)} · ${esc(a.job_type)}</p></div><span class="status ${esc(a.status)}">${esc(titleCase(a.status))}</span></article>`).join("");
  } catch(e) { $("history-list").innerHTML = `<div class="message">${esc(e.message)}</div>`; }
}

loadJobs();
