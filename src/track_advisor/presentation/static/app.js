let studentId = "HV001";
let assessmentId;

const $ = (id) => document.getElementById(id);
function esc(value) { const p = document.createElement("p"); p.textContent = value; return p.innerHTML; }
const inline = (value) => value.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
function markdown(value) {
  // Escape first, then build HTML: câu trả lời của model không bao giờ chèn được thẻ thật.
  const lines = esc(value).replace(/\s*(#{1,6}\s)/g, "\n$1").replace(/\s+(- )/g, "\n$1").split("\n").map((line) => line.trim());
  let html = "", inList = false;
  for (const line of lines) {
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    if (line.startsWith("- ") || line.startsWith("* ")) {
      html += (inList ? "" : "<ul>") + `<li>${inline(line.slice(2))}</li>`;
      inList = true;
      continue;
    }
    if (inList) { html += "</ul>"; inList = false; }
    if (line) html += heading ? `<h4>${inline(heading[1])}</h4>` : `<p>${inline(line)}</p>`;
  }
  return html + (inList ? "</ul>" : "");
}
const attr = (value) => esc(value).replace(/"/g, "&quot;");
function httpUrl(value) {
  // Nguồn đến từ model/web nên chỉ nhận http(s), chặn javascript: và data:.
  try { const url = new URL(String(value), location.href); return /^https?:$/.test(url.protocol) ? url.href : ""; }
  catch { return ""; }
}
function sourceList(sources, grounded) {
  const items = (sources || []).map((source) => ({ ...source, href: httpUrl(source.url) })).filter((source) => source.href);
  if (!items.length) return "";
  const label = grounded ? "Nguồn tham khảo tìm được" : "Link tra cứu gợi ý";
  return `<div class="sources"><p class="sources-title">${label}</p><ul>${items.map((source) =>
    `<li><span class="kind">${source.kind === "video" ? "▶" : "📄"}</span><a href="${attr(source.href)}" target="_blank" rel="noopener noreferrer">${esc(source.title || source.href)}</a>${source.source ? `<span class="host">${esc(source.source)}</span>` : ""}</li>`
  ).join("")}</ul></div>`;
}
async function request(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Có lỗi xảy ra");
  return payload;
}

async function loadProfile() {
  const profile = await request(`/api/students/${studentId}/profile`);
  $("profile-content").innerHTML = `<dl><dt>Học viên</dt><dd>${esc(profile.name)} (${esc(profile.student_id)})</dd><dt>Điểm quá trình</dt><dd>${Object.entries(profile.learning_scores).map(([lesson, score]) => `${esc(lesson)}: ${score}/100`).join(" · ")}</dd></dl>`;
  $("dashboard").hidden = true;
  assessmentId = undefined;
}

function render(snapshot) {
  assessmentId = snapshot.assessment_id;
  const recommendations = snapshot.track_results.filter((result) => snapshot.recommendation_ids.includes(result.track_id));
  $("recommendation").innerHTML = `<h2>Gợi ý chính: ${recommendations.map((result) => esc(result.track_name)).join(" và ")}</h2><p>${recommendations.flatMap((result) => result.reasons).map(esc).join(" ")}</p>`;
  $("tracks").innerHTML = snapshot.track_results.map((result) => `<article><h3>${esc(result.track_name)}</h3><strong>Độ phù hợp: ${result.suitability_score}/10</strong><p>${result.reasons.map(esc).join(" ")}</p><p><b>Đề xuất:</b> ${result.suggestions.map(esc).join(", ") || "Không có"}</p></article>`).join("");
  $("dashboard").hidden = false;
  $("dashboard").scrollIntoView({ behavior: "smooth" });
}

$("assess").onclick = async () => {
  try {
    $("error").textContent = "";
    render(await request("/api/assessments", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ student_id: studentId }) }));
  } catch (error) { $("error").textContent = error.message; }
};

$("chat").onsubmit = async (event) => {
  event.preventDefault();
  const question = $("question").value.trim();
  if (!question || !assessmentId) return;
  $("messages").insertAdjacentHTML("beforeend", `<p class="user">${esc(question)}</p>`);
  $("question").value = "";
  $("messages").insertAdjacentHTML("beforeend", `<p class="bot pending">Đang tìm câu trả lời…</p>`);
  const pending = $("messages").lastElementChild;
  try {
    const output = await request("/api/chats", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ assessment_id: assessmentId, question }) });
    pending.remove();
    $("messages").insertAdjacentHTML("beforeend", `<div class="bot">${markdown(output.answer)}${sourceList(output.sources, output.grounded)}</div>`);
  } catch (error) {
    pending.remove();
    $("messages").insertAdjacentHTML("beforeend", `<p class="bot">${esc(error.message)}</p>`);
  }
};

async function loadStudents() {
  const data = await request("/api/students");
  $("student-select").innerHTML = data.students.map((student) => `<option value="${esc(student.student_id)}">${esc(student.student_id)} — ${esc(student.name)}</option>`).join("");
  $("student-select").value = studentId;
  await loadProfile();
}

$("student-select").onchange = async (event) => { studentId = event.target.value; await loadProfile(); };
loadStudents().catch((error) => { $("error").textContent = error.message; });
