let studentId = "HV001";
let assessmentId;

const $ = (id) => document.getElementById(id);
function esc(value) {
  const p = document.createElement("p");
  p.textContent = value == null ? "" : String(value);
  return p.innerHTML;
}
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

function showLesson(lesson) {
  if (!lesson) return;
  $("viewer-content").innerHTML = `
    <h3>${esc(lesson.title)}</h3>
    <div class="lesson-meta"><span>ID: ${esc(lesson.lesson_id)}</span><span>Điểm: ${lesson.score ?? 0}/100</span></div>
    <div class="pill-list">${(lesson.skills || []).map(s => `<span class="pill">${esc(s)}</span>`).join('')}</div>
    <div style="margin-top:12px;border-radius:10px;padding:16px;background:#fff;border:1px solid #eef2f7">
      <p class="muted">Mô phỏng slide / nội dung tóm tắt cho bài này.</p>
      <p>Đây là nội dung demo cho <b>${esc(lesson.title)}</b>. Bạn có thể hỏi trợ lý AI về cách cải thiện điểm hoặc lộ trình tiếp theo.</p>
    </div>
  `;
}

function renderProfile(profile) {
  const lessons = Array.isArray(profile.course_lessons) ? profile.course_lessons : [];
  const cv = profile.cv_descriptions || {};
  const labScore = profile.lab_completion_score ?? "—";
  const quizScore = profile.quiz_score_accumulation ?? "—";

  $("profile-content").innerHTML = `
    <div class="kpi-grid">
      <article class="kpi-card">
        <p class="eyebrow">HỌC VIÊN</p>
        <h3>${esc(profile.name || profile.student_id)}</h3>
        <strong>${esc(profile.student_id)}</strong>
      </article>
      <article class="kpi-card">
        <p class="eyebrow">LAB COMPLETION</p>
        <h3>Điểm Lab</h3>
        <strong>${labScore}/100</strong>
      </article>
      <article class="kpi-card">
        <p class="eyebrow">QUIZ TÍCH LŨY</p>
        <h3>Điểm Quiz</h3>
        <strong>${quizScore}/100</strong>
      </article>
      <article class="kpi-card">
        <p class="eyebrow">LỘ TRÌNH</p>
        <h3>Bài học</h3>
        <strong>${lessons.length} bài</strong>
      </article>
    </div>
    <div class="cv-grid">
      <article class="cv-card">
        <h3>Điểm mạnh CV</h3>
        <div class="pill-list">${(cv.strengths || []).map((item) => `<span class="pill">${esc(item)}</span>`).join("")}</div>
      </article>
      <article class="cv-card">
        <h3>Kỹ năng nổi bật</h3>
        <div class="pill-list">${(cv.technical_skills || []).map((item) => `<span class="pill">${esc(item)}</span>`).join("")}</div>
      </article>
    </div>
    <div class="lesson-grid">
      ${lessons.map((lesson) => `
        <article class="lesson-card" data-lesson="${esc(lesson.lesson_id)}">
          <div class="lesson-meta">
            <span>${esc(lesson.lesson_id)}</span>
            <span>${lesson.score ?? 0}/100</span>
          </div>
          <h3>${esc(lesson.title)}</h3>
          <div class="progress"><span style="width:${Math.max(8, lesson.score || 0)}%"></span></div>
          <div class="pill-list">${(lesson.skills || []).map((skill) => `<span class="pill">${esc(skill)}</span>`).join("")}</div>
        </article>
      `).join("")}
    </div>
  `;

  // populate left nav list
  const left = $("left-nav-list");
  left.innerHTML = lessons.map((lesson, idx) => `
    <div class="nav-item" data-lesson="${esc(lesson.lesson_id)}" tabindex="0">
      <strong>${idx + 1}. ${esc(lesson.title)}</strong>
      <div class="muted">${lesson.score ?? 0}/100</div>
    </div>
  `).join("");

  // attach click handlers to nav items and lesson cards
  Array.from(document.querySelectorAll('.nav-item')).forEach((el) => {
    el.onclick = () => {
      const id = el.dataset.lesson;
      const lesson = lessons.find(l => l.lesson_id === id);
      showLesson(lesson);
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      el.classList.add('active');
    };
  });

  Array.from(document.querySelectorAll('.lesson-card')).forEach((card) => {
    card.onclick = () => {
      const id = card.dataset.lesson;
      const lesson = lessons.find(l => l.lesson_id === id);
      showLesson(lesson);
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      const nav = document.querySelector(`.nav-item[data-lesson="${id}"]`);
      if (nav) nav.classList.add('active');
    };
  });

  // clear viewer until a lesson is selected
  $("viewer-content").innerHTML = 'Chọn một bài ở trái để xem chi tiết.';

  $("dashboard").hidden = true;
  assessmentId = undefined;
}

async function loadProfile() {
  const profile = await request(`/api/students/${studentId}/profile`);
  renderProfile(profile);
}

function render(snapshot) {
  assessmentId = snapshot.assessment_id;
  const recommendations = snapshot.track_results.filter((result) => snapshot.recommendation_ids.includes(result.track_id));
  const context = snapshot.self_assessment_context || {};
  $("recommendation").innerHTML = `
    <div class="recommend-card">
      <p class="eyebrow">GỢI Ý CHÍNH</p>
      <h2>${recommendations.map((result) => esc(result.track_name)).join(" và ")}</h2>
      <p>${recommendations.flatMap((result) => result.reasons).map(esc).join(" ")}</p>
    </div>
  `;
  $("self-assessment").innerHTML = `
    <div class="kpi-grid">
      <article class="kpi-card">
        <p class="eyebrow">LAB</p>
        <h3>Lab completion</h3>
        <strong>${context.lab_completion_score ?? "—"}/100</strong>
      </article>
      <article class="kpi-card">
        <p class="eyebrow">QUIZ</p>
        <h3>Quiz tích lũy</h3>
        <strong>${context.quiz_score_accumulation ?? "—"}/100</strong>
      </article>
      <article class="kpi-card">
        <p class="eyebrow">ĐIỂM MẠNH</p>
        <h3>Lesson nổi bật</h3>
        <strong>${context.top_strength_lessons?.map((item) => `${esc(item.lesson)} (${item.score})`).join(", ") || "—"}</strong>
      </article>
      <article class="kpi-card">
        <p class="eyebrow">CV</p>
        <h3>Thế mạnh</h3>
        <strong>${context.cv_strengths?.join(", ") || "—"}</strong>
      </article>
    </div>
  `;
  $("tracks").innerHTML = snapshot.track_results.map((result) => `
    <article class="track-card">
      <h3>${esc(result.track_name)}</h3>
      <strong>Độ phù hợp: ${result.suitability_score}/10</strong>
      <p>${result.reasons.map(esc).join(" ")}</p>
      <p><b>Đề xuất:</b> ${result.suggestions.map(esc).join(", ") || "Không có"}</p>
    </article>
  `).join("");
  $("dashboard").hidden = false;
  $("dashboard").scrollIntoView({ behavior: "smooth" });
}

$("assess").onclick = async () => {
  try {
    $("error").textContent = "";
    render(await request("/api/assessments", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ student_id: studentId }) }));
  } catch (error) {
    $("error").textContent = error.message;
  }
};

$("chat").onsubmit = async (event) => {
  event.preventDefault();
  const question = $("question").value.trim();
  if (!question) return;
  $("messages").insertAdjacentHTML("beforeend", `<p class="user">${esc(question)}</p>`);
  $("question").value = "";
  if (!assessmentId) {
    $("messages").insertAdjacentHTML("beforeend", `<p class="bot">Bấm <b>Xem đánh giá Giai đoạn 1</b> trước để trợ lý AI có thể dùng kết quả của bạn.</p>`);
    return;
  }
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

Array.from(document.querySelectorAll(".chip")).forEach((button) => {
  button.onclick = () => {
    $("question").value = button.dataset.question || "";
    $("question").focus();
  };
});

async function loadStudents() {
  const data = await request("/api/students");
  $("student-select").innerHTML = data.students.map((student) => `<option value="${esc(student.student_id)}">${esc(student.student_id)} — ${esc(student.name)}</option>`).join("");
  $("student-select").value = studentId;
  await loadProfile();
}

$("student-select").onchange = async (event) => {
  studentId = event.target.value;
  await loadProfile();
};

loadStudents().catch((error) => {
  $("error").textContent = error.message;
});
