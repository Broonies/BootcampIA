// ia.js - Comportement minimal pour FuelBot
// Définit : sendSuggestion(text), sendMessage(), handleKeyPress(event)

// Helpers DOM
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function scrollToBottom(container) {
  container.scrollTop = container.scrollHeight;
}

function createMessageElement({ role = "ai", text = "" }) {
  const wrapper = document.createElement("div");
  wrapper.className =
    "message " + (role === "user" ? "user-message" : "ai-message");

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "🧑" : "🤖";

  const content = document.createElement("div");
  content.className = "message-content";
  content.innerHTML = text;

  wrapper.appendChild(avatar);
  wrapper.appendChild(content);
  return wrapper;
}

function createTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message ai-message";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "🤖";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator active";
  indicator.innerHTML =
    '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

  wrapper.appendChild(avatar);
  wrapper.appendChild(indicator);
  return wrapper;
}

function createStationCard(station) {
  const card = document.createElement("div");
  card.className = "station-card";

  card.innerHTML = `
        <div class="station-header">
            <div class="station-name">${station.name}</div>
            <div class="station-distance">${station.distance} km</div>
        </div>
        <div class="fuel-prices">
            ${station.prices
              .map(
                (p) => `
                <div class="fuel-price">
                    <div class="fuel-type">${p.type}</div>
                    <div class="price">${p.price} €/L</div>
                </div>
            `
              )
              .join("")}
        </div>
        ${station.best ? '<div class="best-price">Meilleur prix</div>' : ""}
    `;

  return card;
}

// Placeholder pour l'intégration du backend
// Remplacez le contenu de sendToBackend pour effectuer un `fetch()` vers votre API.
// La fonction doit retourner une Promise qui résout une réponse structurée identique
// à celle que la simulation renvoyait auparavant (ex : { type: 'stations', stations: [...] }).
function sendToBackend(query) {
  // TODO: implémentez ici l'appel réel au backend, par ex. :
  // return fetch('/api/search', { method: 'POST', body: JSON.stringify({ query }) })
  //   .then(r => r.json());

  // Par défaut, renvoie une réponse informative pour indiquer que le backend
  // n'est pas encore configuré. Cela permet au frontend de rester fonctionnel.
  return Promise.resolve({
    type: "text",
    text: "Backend non configuré. Intégrez votre backend en remplaçant sendToBackend() par un fetch() vers votre API.",
  });
}

// Fonctions exposées utilisées par l'HTML
function sendSuggestion(text) {
  const input = $("#userInput");
  input.value = text;
  sendMessage();
}

function handleKeyPress(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
}

function sendMessage() {
  const input = $("#userInput");
  const chat = $("#chatMessages");
  const text = (input.value || "").trim();
  if (!text) return;

  // Ajouter message utilisateur
  const userMsg = createMessageElement({
    role: "user",
    text: escapeHtml(text),
  });
  chat.appendChild(userMsg);
  scrollToBottom(chat);

  input.value = "";

  // Ajouter indicateur de frappe
  const typing = createTypingIndicator();
  chat.appendChild(typing);
  scrollToBottom(chat);

  // Appeler le backend (placeholder). sendToBackend renvoie une Promise.
  sendToBackend(text)
    .then((res) => {
      // Retirer indicateur
      typing.remove();

      if (!res) {
        const errMsg = createMessageElement({
          role: "ai",
          text: "Réponse invalide du backend.",
        });
        chat.appendChild(errMsg);
        scrollToBottom(chat);
        return;
      }

      if (res.type === "stations" || res.type === "prices") {
        const container = createMessageElement({
          role: "ai",
          text: "Voici ce que j’ai trouvé :",
        });
        const content = container.querySelector(".message-content");
        content.innerHTML = "";
        res.stations.forEach((st) => {
          const card = createStationCard(st);
          content.appendChild(card);
        });
        chat.appendChild(container);
      } else if (res.type === "single") {
        const aiMsg = createMessageElement({
          role: "ai",
          text: escapeHtml(res.text),
        });
        chat.appendChild(aiMsg);
      } else {
        const aiMsg = createMessageElement({
          role: "ai",
          text: escapeHtml(res.text || String(res)),
        });
        chat.appendChild(aiMsg);
      }

      scrollToBottom(chat);
    })
    .catch((err) => {
      // Retirer indicateur et afficher erreur
      typing.remove();
      const aiMsg = createMessageElement({
        role: "ai",
        text: "Erreur : " + (err && err.message ? err.message : String(err)),
      });
      chat.appendChild(aiMsg);
      scrollToBottom(chat);
    });
}

// Utilitaires
function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Exposer sur window pour que les attributs inline puissent appeler
window.sendSuggestion = sendSuggestion;
window.sendMessage = sendMessage;
window.handleKeyPress = handleKeyPress;

// Auto-focus sur input au chargement
document.addEventListener("DOMContentLoaded", () => {
  const input = $("#userInput");
  if (input) input.focus();
});
