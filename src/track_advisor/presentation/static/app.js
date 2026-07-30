let studentId = "HV001";
let assessmentId;

const $ = (id) => document.getElementById(id);
function esc(value) { const p = document.createElement("p"); p.textContent = value; return p.innerHTML; }
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
  try {
    const output = await request("/api/chats", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ assessment_id: assessmentId, question }) });
    $("messages").insertAdjacentHTML("beforeend", `<p class="bot">${esc(output.answer)}</p>`);
  } catch (error) { $("messages").insertAdjacentHTML("beforeend", `<p class="bot">${esc(error.message)}</p>`); }
};

async function loadStudents() {
  const data = await request("/api/students");
  $("student-select").innerHTML = data.students.map((student) => `<option value="${esc(student.student_id)}">${esc(student.student_id)} — ${esc(student.name)}</option>`).join("");
  $("student-select").value = studentId;
  await loadProfile();
}

$("student-select").onchange = async (event) => { studentId = event.target.value; await loadProfile(); };
loadStudents().catch((error) => { $("error").textContent = error.message; });
