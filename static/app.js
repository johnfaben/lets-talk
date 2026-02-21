(function () {
  const STORAGE_KEY = "conversation_session_id";

  function getSessionId() {
    let id = localStorage.getItem(STORAGE_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(STORAGE_KEY, id);
    }
    return id;
  }

  const sessionId = getSessionId();
  let currentQuestion = null;
  let ratedCount = 0;

  const cardEl = document.getElementById("question-card");
  const textEl = document.getElementById("question-text");
  const badgeEl = document.getElementById("source-badge");
  const btnUp = document.getElementById("btn-up");
  const btnDown = document.getElementById("btn-down");
  const btnSkip = document.getElementById("btn-skip");
  const statsEl = document.getElementById("stats");

  async function fetchQuestion() {
    try {
      const res = await fetch(`/api/question?session_id=${encodeURIComponent(sessionId)}`);
      if (!res.ok) {
        textEl.textContent = "No more questions right now — check back soon!";
        badgeEl.textContent = "";
        currentQuestion = null;
        return;
      }
      const data = await res.json();
      currentQuestion = data;
      showQuestion(data);
    } catch {
      textEl.textContent = "Couldn't load question. Check your connection.";
    }
  }

  function showQuestion(q) {
    cardEl.classList.remove("swipe-left", "swipe-right", "swipe-up");
    // Force reflow so the entering animation replays
    void cardEl.offsetWidth;
    cardEl.classList.add("entering");
    textEl.textContent = q.text;
    badgeEl.textContent = q.source === "generated" ? "AI generated" : "";
    badgeEl.className = "badge" + (q.source === "generated" ? " generated" : "");
    setButtonsEnabled(true);
  }

  function setButtonsEnabled(enabled) {
    btnUp.disabled = !enabled;
    btnDown.disabled = !enabled;
    btnSkip.disabled = !enabled;
  }

  async function rate(rating) {
    if (!currentQuestion) return;
    setButtonsEnabled(false);

    // Pick animation direction
    const direction =
      rating === "up" ? "swipe-right" : rating === "down" ? "swipe-left" : "swipe-up";
    cardEl.classList.add(direction);

    // Send rating
    try {
      await fetch("/api/rate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          session_id: sessionId,
          rating: rating,
        }),
      });
      ratedCount++;
      updateStats();
    } catch {
      // Silently continue
    }

    // Wait for animation then load next
    setTimeout(() => fetchQuestion(), 400);
  }

  function updateStats() {
    statsEl.textContent = `Questions rated this session: ${ratedCount}`;
  }

  // Event listeners
  btnUp.addEventListener("click", () => rate("up"));
  btnDown.addEventListener("click", () => rate("down"));
  btnSkip.addEventListener("click", () => rate("skip"));

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") rate("up");
    else if (e.key === "ArrowLeft") rate("down");
    else if (e.key === "ArrowUp" || e.key === " ") rate("skip");
  });

  // Start
  fetchQuestion();
  updateStats();
})();
