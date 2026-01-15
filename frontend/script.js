// ia.js - Comportement minimal pour FuelBot
// Définit : sendSuggestion(text), sendMessage(), handleKeyPress(event)
let userLocation = null;

function getUserLocation() {
  if (!navigator.geolocation) {
    console.warn("❌ Geolocation non supportée - utilisant position par défaut");
    // Fallback: position par défaut (Rennes centre)
    userLocation = {
      lat: 48.1104,
      lon: -1.6769
    };
    return;
  }

  // Timeout après 5 secondes
  const timeoutId = setTimeout(() => {
    console.warn("⚠️ Geolocation timeout (>5s) - utilisant fallback");
    if (!userLocation) {
      userLocation = {
        lat: 48.1104,
        lon: -1.6769
      };
    }
  }, 5000);

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      clearTimeout(timeoutId);
      userLocation = {
        lat: pos.coords.latitude,
        lon: pos.coords.longitude
      };
      console.log("✓ Position GPS acquise:", userLocation);
    },
    (err) => {
      clearTimeout(timeoutId);
      console.warn("⚠️ Geolocation refusée ou erreur:", err.message);
      // Fallback
      if (!userLocation) {
        userLocation = {
          lat: 48.1104,
          lon: -1.6769
        };
        console.log("📍 Position fallback utilisée:", userLocation);
      }
    },
    { 
      timeout: 5000,
      enableHighAccuracy: false
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

function createParkingCard(parking) {
  const card = document.createElement("div");
  card.className = "station-card"; // Réutiliser le style station-card

  let pricingHTML = "";
  if (parking.prices && parking.prices.length > 0) {
    pricingHTML = `
      <div class="fuel-prices">
        ${parking.prices
          .map(
            (p) => `
            <div class="fuel-price">
                <div class="fuel-type">${p.type}</div>
                <div class="price">${p.price}</div>
            </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  card.innerHTML = `
        <div class="station-header">
            <div class="station-name">${parking.name}</div>
            <div class="station-distance">${parking.distance}</div>
        </div>
        <div class="station-info">
            <div>${parking.status}</div>
            <div>${parking.available}/${parking.total} places</div>
        </div>
        ${pricingHTML}
    `;

  return card;
}

// --- MODIFICATION MAJEURE : Fonction connectée au Backend ---
async function sendToBackend(query) {
  try {
    // 1. Appel réel à ton API FastAPI
    // Note : On suppose que ton backend tourne sur le port 8000
    console.log("📍 userLocation avant envoi:", userLocation);
    const response = await fetch("http://127.0.0.1:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: query,
        history: [],
        latitude: userLocation ? userLocation.lat : null,
        longitude: userLocation ? userLocation.lon : null
      }),
    });

    console.log("✓ Fetch réussi, status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("❌ Erreur serveur:", response.status, errorText);
      throw new Error(`Erreur serveur ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log("✓ JSON parsé, data reçue:", data);

    // 2. Traitement intelligent de la réponse
    // Si le backend renvoie des données (tableau non vide) dans 'data'
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
      console.log("📊 Données détectées, type d'élément:", typeof data.data[0]);
      
      // Vérifier si c'est des parkings ou des stations
      const isParking = data.data[0].available !== undefined; // Les parkings ont "available"
      
      if (isParking) {
        console.log("🅿️ Détecté: Parkings");
        // Formater les parkings
        const formattedParkings = data.data.map((parking) => ({
          name: parking.name,
          distance: `${parking.distance_km} km`,
          available: parking.available,
          total: parking.total,
          status: parking.status,
          prices: parking.pricing ? Object.entries(parking.pricing).map(([duration, price]) => ({
            type: duration,
            price: price
          })) : []
        }));
        return {
          type: "parkings",
          parkings: formattedParkings,
        };
      } else {
        console.log("⛽ Détecté: Stations essence");
        // On convertit le format du Python vers le format attendu par createStationCard
        const formattedStations = data.data.map((station, index) => ({
          name: `${station.adresse}, ${station.ville}`,
          distance: `${station.distance_km} km`,
          best: index === 0,
          prices: [
            {
              type: station.fuel_type || "Gazole",
              price: station.price.toFixed(3)
            }
          ]
        }));
        return {
          type: "stations",
          stations: formattedStations,
        };
      }
    }

    console.log("📝 Pas de données, retournant texte simple");
    // 3. Cas par défaut : réponse textuelle simple de l'IA
    return {
      type: "text",
      text: data.response,
    };

  } catch (error) {
    console.error("❌ Erreur dans sendToBackend:", error);
    console.error("Stack:", error.stack);
    return {
      type: "text",
      text: "❌ Erreur: " + error.message,
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

      } else if (res.type === "parkings") {
        const container = createMessageElement({
          role: "ai",
          text: "Voici les parkings les plus proches :",
        });
        const content = container.querySelector(".message-content");
        
        // Création des cartes de parkings
        res.parkings.forEach((parking) => {
          const card = createParkingCard(parking);
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