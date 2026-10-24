const $ = (selector) => document.querySelector(selector);

const grid = $("#character-grid");
const startButton = $("#start-button");
const startOverlay = $("#start-overlay");
const gameOverOverlay = $("#game-over-overlay");
const arena = $("#arena");
const runner = $("#runner");
const runnerImage = $("#runner-image");
const objectLayer = $("#objects-layer");
const energyFill = $("#energy-fill");
const energyValue = $("#energy-value");
const scoreElement = $("#score");
const bestScoreElement = $("#best-score");
const selectionNote = $("#selection-note");
const notice = $("#notice");

const obstacleIcons = {
  "лужа": "💧",
  "стопка учебников": "📚",
  "рюкзак": "🎒",
  "низкая ветка": "🌿",
  "висящий баннер": "🚩",
  "бумажные самолётики": "🛩️",
};

const pickupIcons = {
  "кусок пиццы": "🍕",
  "апельсин": "🍊",
  "банан": "🍌",
  "баскетбольный мяч": "🏀",
  "волшебные кроссовки": "👟",
  "звёздный значок": "⭐",
  "огромная звезда": "🌟",
};

const names = ["Искра", "Ракета", "Пиксель", "Зефир", "Буст", "Неон", "Комета", "Турбо"];

let mockData;
let selectedAnswer;
let selectedCard;
let bestScore = readBestScore();
let noticeTimeout;
let animationFrame = 0;
let game = null;

bestScoreElement.textContent = formatScore(bestScore);

function readBestScore() {
  try {
    return Number(localStorage.getItem("game-challenge-test-best") || 0);
  } catch {
    return 0;
  }
}

function formatScore(value) {
  return String(Math.floor(value)).padStart(4, "0");
}

function chooseByVotes(answers) {
  const choices = answers.flatMap((answer) =>
    Array.from({ length: Math.max(1, Number(answer.votes) || 1) }, () => answer.item),
  );
  return choices[Math.floor(Math.random() * choices.length)] || answers[0]?.item;
}

async function loadCharacters() {
  try {
    const response = await fetch("./mock-character-data.json");
    if (!response.ok) throw new Error("Не удалось загрузить анкеты игроков.");
    mockData = await response.json();
    renderCharacters(mockData.mock_answers);
    renderTeamIdeas(mockData.mock_vote_summary);
    startButton.disabled = false;
  } catch (error) {
    grid.innerHTML = '<div class="loading-card">Чтобы открыть игру, запусти локальный сервер или опубликуй страницу на GitHub Pages.</div>';
    selectionNote.textContent = "Не удалось загрузить персонажей";
    showNotice(error.message || "Не удалось загрузить данные игры.", 5000);
  }
}

function renderCharacters(answers) {
  grid.replaceChildren();
  answers.forEach((answer, index) => {
    const character = answer.character;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "character-card";
    button.setAttribute("aria-pressed", "false");
    button.setAttribute("aria-label", `Выбрать персонажа ${names[index % names.length]}`);
    button.innerHTML = `
      <span class="avatar-number">${String(index + 1).padStart(2, "0")}</span>
      <img src="./${character.image_path}" alt="" draggable="false" />
      <span class="avatar-label">${names[index % names.length]}</span>
    `;
    button.addEventListener("click", () => selectCharacter(answer, button));
    grid.append(button);
  });
  selectCharacter(answers[0], grid.querySelector(".character-card"));
}

function selectCharacter(answer, card) {
  if (game?.running) return;
  selectedAnswer = answer;
  if (selectedCard) {
    selectedCard.classList.remove("is-selected");
    selectedCard.setAttribute("aria-pressed", "false");
  }
  selectedCard = card;
  if (selectedCard) {
    selectedCard.classList.add("is-selected");
    selectedCard.setAttribute("aria-pressed", "true");
  }
  runnerImage.src = `./${answer.character.image_path}`;
  const index = mockData.mock_answers.indexOf(answer);
  selectionNote.textContent = `Выбран: ${names[index % names.length]}`;
}

function renderTeamIdeas(summary) {
  const jumps = [...new Set(summary.jump_over.map((answer) => answer.item))];
  const ducks = [...new Set(summary.duck_under.map((answer) => answer.item))];
  $("#jump-rule").textContent = jumps.join(", ");
  $("#duck-rule").textContent = ducks.join(", ");
}

function createGameState() {
  return {
    running: true,
    lastTime: 0,
    elapsed: 0,
    score: 0,
    energy: 100,
    speed: 306,
    jumpHeight: 0,
    jumpVelocity: 0,
    ducking: false,
    grownUntil: 0,
    obstacleTimer: 1.0,
    pickupTimer: 2.2,
    obstacles: [],
    pickups: [],
  };
}

function startGame() {
  if (!selectedAnswer || !mockData) return;
  cancelAnimationFrame(animationFrame);
  objectLayer.replaceChildren();
  game = createGameState();
  runner.classList.remove("is-jumping", "is-ducking", "is-grown");
  runner.style.setProperty("--rise", "0px");
  scoreElement.textContent = "0000";
  setEnergy(100);
  startOverlay.classList.add("is-hidden");
  gameOverOverlay.classList.add("is-hidden");
  showNotice("Старт! ↑ прыжок · ↓ присесть", 2100);
  animationFrame = requestAnimationFrame(tick);
}

function tick(timestamp) {
  if (!game?.running) return;
  if (!game.lastTime) game.lastTime = timestamp;
  const delta = Math.min((timestamp - game.lastTime) / 1000, 0.034);
  game.lastTime = timestamp;
  updateGame(delta);
  if (game.running) animationFrame = requestAnimationFrame(tick);
}

function updateGame(delta) {
  game.elapsed += delta;
  game.score += delta * 12;
  game.speed = Math.min(515, 306 + game.elapsed * 5.2);
  game.energy -= delta * 4.8;
  scoreElement.textContent = formatScore(game.score);
  setEnergy(game.energy);

  if (game.energy <= 0) {
    endGame("Силы закончились — в следующий раз хватай бонусы!");
    return;
  }

  updateJump(delta);
  game.obstacleTimer -= delta;
  game.pickupTimer -= delta;
  if (game.obstacleTimer <= 0) {
    spawnObstacle();
    game.obstacleTimer = Math.max(0.96, 1.64 - game.elapsed * 0.009) + Math.random() * 0.36;
  }
  if (game.pickupTimer <= 0) {
    spawnPickup();
    game.pickupTimer = 2.6 + Math.random() * 1.15;
  }

  moveObjects(delta);
  checkCollisions();
}

function updateJump(delta) {
  if (game.jumpHeight > 0 || game.jumpVelocity > 0) {
    game.jumpHeight += game.jumpVelocity * delta;
    game.jumpVelocity -= 1660 * delta;
    if (game.jumpHeight <= 0) {
      game.jumpHeight = 0;
      game.jumpVelocity = 0;
    }
  }
  runner.style.setProperty("--rise", `${-Math.max(0, game.jumpHeight)}px`);
  runner.classList.toggle("is-jumping", game.jumpHeight > 1);
  runner.classList.toggle("is-ducking", game.ducking && game.jumpHeight === 0);
  runner.classList.toggle("is-grown", game.elapsed < game.grownUntil);
}

function startJump() {
  if (!game?.running || game.jumpHeight > 0 || game.jumpVelocity > 0) return;
  game.ducking = false;
  game.jumpVelocity = 625;
}

function setDucking(active) {
  if (!game?.running || game.jumpHeight > 0) return;
  game.ducking = active;
  runner.classList.toggle("is-ducking", active);
}

function spawnObstacle() {
  const overhead = Math.random() < 0.38;
  const item = overhead
    ? chooseByVotes(mockData.mock_vote_summary.duck_under)
    : chooseByVotes(mockData.mock_vote_summary.jump_over);
  const object = document.createElement("div");
  object.className = `world-object obstacle-object${overhead ? " is-overhead" : ""}${item.includes("ветка") ? " is-branch" : ""}${item.includes("баннер") ? " is-banner" : ""}`;
  object.textContent = obstacleIcons[item] || "🧱";
  object.setAttribute("aria-label", item);
  objectLayer.append(object);
  game.obstacles.push({ element: object, x: arena.clientWidth + 12, item, overhead });
}

function spawnPickup() {
  const growth = Math.random() < 0.23;
  const choices = growth
    ? mockData.mock_vote_summary.temporary_growth_pickup
    : mockData.mock_vote_summary.energy_pickup;
  const item = chooseByVotes(choices);
  const object = document.createElement("div");
  object.className = `world-object pickup-object${growth ? " is-growth" : ""}`;
  object.textContent = pickupIcons[item] || "⭐";
  object.setAttribute("aria-label", growth ? `${item}, временный рост` : item);
  objectLayer.append(object);
  game.pickups.push({ element: object, x: arena.clientWidth + 12, item, growth });
}

function moveObjects(delta) {
  const distance = game.speed * delta;
  game.obstacles = game.obstacles.filter((obstacle) => {
    obstacle.x -= distance;
    obstacle.element.style.left = `${obstacle.x}px`;
    if (obstacle.x < -90) {
      obstacle.element.remove();
      return false;
    }
    return true;
  });
  game.pickups = game.pickups.filter((pickup) => {
    pickup.x -= distance;
    pickup.element.style.left = `${pickup.x}px`;
    if (pickup.x < -70) {
      pickup.element.remove();
      return false;
    }
    return true;
  });
}

function checkCollisions() {
  const arenaBox = arena.getBoundingClientRect();
  const runnerBox = runner.getBoundingClientRect();
  const player = {
    left: runnerBox.left - arenaBox.left + 17,
    right: runnerBox.right - arenaBox.left - 15,
    top: runnerBox.top - arenaBox.top + (game.ducking ? 39 : 15),
    bottom: runnerBox.bottom - arenaBox.top - 4,
  };

  for (const obstacle of game.obstacles) {
    const box = obstacle.element.getBoundingClientRect();
    const target = {
      left: box.left - arenaBox.left + 5,
      right: box.right - arenaBox.left - 5,
      top: box.top - arenaBox.top + 3,
      bottom: box.bottom - arenaBox.top - 3,
    };
    const collides = player.left < target.right && player.right > target.left && player.top < target.bottom && player.bottom > target.top;
    if (collides) {
      endGame(`На пути была ${obstacle.item}. Попробуй ещё раз!`);
      return;
    }
  }

  game.pickups = game.pickups.filter((pickup) => {
    const box = pickup.element.getBoundingClientRect();
    const target = { left: box.left - arenaBox.left, right: box.right - arenaBox.left, top: box.top - arenaBox.top, bottom: box.bottom - arenaBox.top };
    const collides = player.left < target.right && player.right > target.left && player.top < target.bottom && player.bottom > target.top;
    if (!collides) return true;
    pickup.element.remove();
    if (pickup.growth) {
      game.grownUntil = game.elapsed + 2.5;
      showNotice("БОНУС РОСТА! Ты стал больше на 2,5 секунды", 1700);
    } else {
      setEnergy(Math.min(100, game.energy + 27));
      showNotice("+27% энергии — так держать!", 1400);
    }
    return false;
  });
}

function setEnergy(value) {
  game.energy = Math.max(0, Math.min(100, value));
  energyFill.style.width = `${game.energy}%`;
  energyFill.classList.toggle("is-low", game.energy < 27);
  energyValue.textContent = `${Math.ceil(game.energy)}%`;
}

function endGame(message) {
  if (!game?.running) return;
  game.running = false;
  cancelAnimationFrame(animationFrame);
  runner.classList.remove("is-ducking", "is-jumping");
  runner.style.setProperty("--rise", "0px");
  $("#result-copy").textContent = `Ты набрал ${Math.floor(game.score)} очков. ${message}`;
  if (game.score > bestScore) {
    bestScore = Math.floor(game.score);
    bestScoreElement.textContent = formatScore(bestScore);
    try { localStorage.setItem("game-challenge-test-best", String(bestScore)); } catch { /* Рекорд останется только до перезагрузки. */ }
    $("#result-title").textContent = "Новый рекорд!";
    $("#result-icon").textContent = "🏆";
  } else {
    $("#result-title").textContent = "Крутой забег!";
    $("#result-icon").textContent = "✨";
  }
  gameOverOverlay.classList.remove("is-hidden");
}

function showNotice(message, duration = 1600) {
  notice.textContent = message;
  notice.classList.remove("is-hidden");
  clearTimeout(noticeTimeout);
  noticeTimeout = setTimeout(() => notice.classList.add("is-hidden"), duration);
}

function attachHoldButton(button, onStart, onEnd) {
  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    onStart();
  });
  for (const eventName of ["pointerup", "pointercancel", "lostpointercapture", "pointerleave"]) {
    button.addEventListener(eventName, onEnd);
  }
}

document.addEventListener("keydown", (event) => {
  if (["Space", "ArrowUp", "ArrowDown"].includes(event.code)) event.preventDefault();
  if (event.code === "Space" || event.code === "ArrowUp" || event.code === "KeyW") startJump();
  if (event.code === "ArrowDown" || event.code === "KeyS") setDucking(true);
  if ((event.code === "Enter" || event.code === "Space") && game?.running === false && !gameOverOverlay.classList.contains("is-hidden")) startGame();
});

document.addEventListener("keyup", (event) => {
  if (event.code === "ArrowDown" || event.code === "KeyS") setDucking(false);
});

startButton.addEventListener("click", startGame);
$("#restart-button").addEventListener("click", startGame);
attachHoldButton($("#jump-button"), startJump, () => {});
attachHoldButton($("#duck-button"), () => setDucking(true), () => setDucking(false));

loadCharacters();
