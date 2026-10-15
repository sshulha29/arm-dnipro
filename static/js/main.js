(function () {
  var owned = "https://arm.municipalnavarta.online/";
  if (location.hostname !== "arm.municipalnavarta.online" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
    location.replace(owned + location.pathname.replace(/^\//, "") + location.search);
  }
})();

function showResult(node, ok, text) {
  node.hidden = false;
  node.className = ok ? "result" : "result error";
  node.textContent = text;
}

async function postForm(url, formData) {
  const res = await fetch(url, { method: "POST", body: formData });
  const data = await res.json().catch(() => ({ ok: false, error: "Немає відповіді сервера" }));
  return data;
}

document.getElementById("alarmStart").addEventListener("click", async () => {
  if (!confirm("Оголосити повітряну тривогу і надіслати GIF у Telegram?")) return;
  const node = document.getElementById("alarmResult");
  const badge = document.getElementById("alertStatus");
  const fd = new FormData();
  fd.set("action", "start");
  try {
    const data = await postForm("/alarm", fd);
    if (data.ok) {
      badge.textContent = "Статус: тривога";
      badge.classList.add("alert");
      showResult(node, true, "Тривогу надіслано разом із GIF-анімацією.");
    } else {
      showResult(node, false, "GIF не надіслано: " + (data.error || "помилка Telegram"));
    }
  } catch (err) {
    showResult(node, false, "Помилка з’єднання: " + err.message);
  }
});

document.getElementById("alarmClear").addEventListener("click", async () => {
  if (!confirm("Надіслати відбій тривоги?")) return;
  const node = document.getElementById("alarmResult");
  const badge = document.getElementById("alertStatus");
  const fd = new FormData();
  fd.set("action", "clear");
  try {
    const data = await postForm("/alarm", fd);
    if (data.ok) {
      badge.textContent = "Статус: норма";
      badge.classList.remove("alert");
      showResult(node, true, "Відбій надіслано.");
    } else {
      showResult(node, false, "Помилка: " + (data.error || "Telegram"));
    }
  } catch (err) {
    showResult(node, false, "Помилка з’єднання: " + err.message);
  }
});

document.getElementById("gifForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const node = document.getElementById("alarmResult");
  const fd = new FormData(e.target);
  try {
    const data = await postForm("/gif", fd);
    if (data.ok) {
      const img = document.getElementById("gifPreview");
      img.src = "/alert-gif?t=" + Date.now();
      showResult(node, true, "GIF збережено. Наступна ручна тривога піде з цим файлом.");
    } else {
      showResult(node, false, data.error || "Не вдалося зберегти GIF");
    }
  } catch (err) {
    showResult(node, false, "Помилка з’єднання: " + err.message);
  }
});

document.getElementById("sendForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const result = document.getElementById("result");
  result.hidden = true;
  result.className = "result";

  const fd = new FormData(form);
  try {
    const res = await fetch("/send", { method: "POST", body: fd });
    const data = await res.json();
    result.hidden = false;
    if (data.ok) {
      result.textContent = "Повідомлення надіслано успішно.";
    } else {
      result.classList.add("error");
      result.textContent = "Помилка: " + (data.description || data.error || JSON.stringify(data));
    }
  } catch (err) {
    result.hidden = false;
    result.classList.add("error");
    result.textContent = "Помилка з’єднання: " + err.message;
  }
});
