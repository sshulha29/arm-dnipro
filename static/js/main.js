(function () {
  var owned = "https://arm.municipalnavarta.online/";
  if (location.hostname !== "arm.municipalnavarta.online" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
    location.replace(owned + location.pathname.replace(/^\//, "") + location.search);
  }
})();

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
