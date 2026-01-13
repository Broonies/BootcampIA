// ia.js - Comportement minimal pour FuelBot
// Définit : sendSuggestion(text), sendMessage(), handleKeyPress(event)
let userLocation = null;

function getUserLocation() {
  if (!navigator.geolocation) {
    console.warn("Geolocation non supportée");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userLocation = {
        lat: pos.coords.latitude,
        lon: pos.coords.longitude
      };
      console.log("📍 Position:", userLocation);
    },
    () => {
      alert("Autorise la géolocalisation pour utiliser FuelBot");
    }
  );
}

getUserLocation();

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
            <div class="station-distance">${station.distance}</div>
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

// --- MODIFICATION MAJEURE : Fonction connectée au Backend ---
async function sendToBackend(query) {
  try {
    // 1. Appel réel à ton API FastAPI
    // Note : On suppose que ton backend tourne sur le port 8000
    const response = await fetch("http://127.0.0.1:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: query,
      history: [],
      location: userLocation
    }),
  });

    if (!response.ok) {
      throw new Error(`Erreur serveur: ${response.status}`);
    }

    const data = await response.json();

    // 2. Traitement intelligent de la réponse
    // Si le backend renvoie des données de stations (tableau non vide) dans 'data'
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
      
      // On convertit le format du Python vers le format attendu par createStationCard
      const formattedStations = data.data.map((station, index) => ({
        name: `${station.adresse}, ${station.ville}`, // Nom de la station
        distance: station.cp, // On affiche le CP à la place de la distance pour l'instant
        best: index === 0,    // La première est la moins chère (tri backend)
        prices: [
          {
            type: station.fuel_type, // Ou station.fuel_type si disponible dans 'data'
            price: station.price.toFixed(3)
          }
        ]
      }));
      // On renvoie un objet type 'stations' pour que sendMessage affiche les cartes
      return {
        type: "stations", 
        stations: formattedStations,
        // On peut aussi afficher le texte de l'IA si on modifiait sendMessage, 
        // mais ici le format attendu par ton code existant sépare stations ou texte.
        // Pour bien faire, on pourrait afficher le texte PUIS les stations,
        // mais restons simples pour l'instant : on renvoie les stations.
      };
    }

    // 3. Cas par défaut : réponse textuelle simple de l'IA
    return {
      type: "text",
      text: data.response,
    };

  } catch (error) {
    console.error("Erreur API:", error);
    return {
      type: "text",
      text: "❌ Désolé, je n'arrive pas à joindre le serveur. Vérifie que le backend (main.py) est bien lancé sur le port 8000.",
    };
  }
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

  // Appeler le backend
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

      // Si c'est un type 'stations' (notre nouvel objet retourné)
      if (res.type === "stations" || res.type === "prices") {
        const container = createMessageElement({
          role: "ai",
          text: "Voici les stations les moins chères trouvées :",
        });
        const content = container.querySelector(".message-content");
        
        // Création des cartes
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
        // Cas par défaut (texte simple)
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
  if (!unsafe) return "";
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