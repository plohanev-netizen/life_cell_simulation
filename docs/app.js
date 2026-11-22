'use strict';

const simulation = new Simulation();
const select = id => document.getElementById(id);
const canvas = select('grid');
const context = canvas.getContext('2d');
const field = canvas.parentElement;
const workspace = field.closest('.workspace');
const desktopWidth = canvas.width;
const desktopHeight = canvas.height;
const mobileCellSize = 3;
let image;
const palette = [[10, 20, 23], [225, 241, 250], [255, 119, 106], [182, 239, 114]];
const run = select('run');
const step = select('step');
const speed = select('speed');
const touchLayout = window.matchMedia('(pointer: coarse)');
const desktopControls = select('desktop-controls');
const tapHint = select('tap-hint');
const onboarding = select('onboarding');
let timer = null;
const languageKey = 'cell-wars-language';
let language = navigator.language.toLowerCase().startsWith('ru') ? 'ru' : 'en';
let activityFormatter;
let lastStatus = { type: 'seeded' };

function translate(key, values = {}) {
  return translations[key][language === 'ru' ? 0 : 1].replace(
    /\{(\w+)\}/g, (_, name) => values[name]
  );
}

function updateStatus() {
  const event = translate(lastStatus.type);
  select('event').textContent = lastStatus.generation === undefined
    ? event : translate('eventGeneration', { event, generation: lastStatus.generation });
}

function recordEvent(event) {
  lastStatus = { type: event.type, generation: simulation.generation };
  updateStatus();
}

function updateSpeed() {
  select('speed-value').textContent = translate('speedValue', { speed: speed.value });
}

function render() {
  const pixels = image.data;
  simulation.grid.forEach((cell, i) => {
    const [r, g, b] = palette[cell];
    pixels[i * 4] = r;
    pixels[i * 4 + 1] = g;
    pixels[i * 4 + 2] = b;
    pixels[i * 4 + 3] = 255;
  });
  context.putImageData(image, 0, 0);
  for (const { x, y, radius } of simulation.events) {
    context.beginPath();
    context.arc(x + .5, y + .5, radius, 0, Math.PI * 2);
    context.strokeStyle = '#ffd99c';
    context.lineWidth = 1;
    context.stroke();
  }
  const [, white, red, virus] = simulation.populations();
  select('white').textContent = white;
  select('red').textContent = red;
  select('virus').textContent = virus;
  select('generation').textContent = simulation.generation;
  select('activity').textContent = activityFormatter.format(simulation.activity / 100);
}

function advance() {
  simulation.step();
  const event = simulation.events.at(-1);
  if (event) recordEvent(event);
  render();
}

function start() {
  clearInterval(timer);
  timer = setInterval(advance, 1000 / Number(speed.value));
}

function updateRunControls() {
  step.disabled = timer !== null;
  run.textContent = translate(timer === null ? 'run' : 'pause');
}

function fitField(seed = false) {
  let width = desktopWidth;
  let height = desktopHeight;
  if (touchLayout.matches) {
    const bounds = field.getBoundingClientRect();
    width = Math.max(1, Math.floor(bounds.width / mobileCellSize));
    height = Math.max(1, Math.floor(bounds.height / mobileCellSize));
    canvas.style.width = `${width * mobileCellSize}px`;
    canvas.style.height = `${height * mobileCellSize}px`;
  } else {
    canvas.style.width = '';
    canvas.style.height = '';
    const boardWidth = field.clientHeight * desktopWidth / desktopHeight;
    if (boardWidth > 0) workspace.style.setProperty('--desktop-board-width', `${boardWidth}px`);
  }

  if (image && canvas.width === width && canvas.height === height) return;
  simulation.resize(width, height);
  if (seed) simulation.reset();
  canvas.width = width;
  canvas.height = height;
  image = context.createImageData(width, height);
  render();
}

function applyLayout(seed = false) {
  const mobile = touchLayout.matches;
  document.body.classList.toggle('touch-layout', mobile);
  desktopControls.hidden = mobile;
  tapHint.hidden = !mobile;
  fitField(seed);
  if (mobile && timer === null && !onboarding.open) start();
  updateRunControls();
}

function toggleRun() {
  if (timer === null) {
    start();
  } else {
    clearInterval(timer);
    timer = null;
  }
  updateRunControls();
}

function reset(seed) {
  simulation.reset(seed);
  lastStatus = { type: seed ? 'seeded' : 'cleared' };
  updateStatus();
  render();
}

function edit(event, secondary = false) {
  const rect = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - rect.left) * canvas.width / rect.width);
  const y = Math.floor((event.clientY - rect.top) * canvas.height / rect.height);
  if (!simulation.inside(x, y)) return;
  let tool = 'blast';
  if (!touchLayout.matches) {
    tool = event.shiftKey ? '0' : secondary ? '2' : document.querySelector('[name=brush]:checked').value;
  }
  simulation.events = [];
  if (tool === 'blast' || tool === 'virus-blast') {
    simulation.blast(x, y, tool === 'virus-blast');
    select('biohazard').checked = simulation.virus;
    recordEvent(simulation.events.at(-1));
  } else {
    simulation.paint(x, y, Number(tool));
  }
  render();
}

run.addEventListener('click', toggleRun);
step.addEventListener('click', advance);
select('reset').addEventListener('click', () => reset(true));
select('clear').addEventListener('click', () => reset(false));
speed.addEventListener('input', () => {
  updateSpeed();
  if (timer !== null) start();
});
for (const id of ['mutations', 'raiders']) {
  select(id).addEventListener('change', event => { simulation[id] = event.target.checked; });
}
select('biohazard').addEventListener('change', event => {
  simulation.setVirus(event.target.checked);
  render();
});
canvas.addEventListener('click', edit);
canvas.addEventListener('contextmenu', event => {
  event.preventDefault();
  if (!touchLayout.matches) edit(event, true);
});
document.addEventListener('keydown', event => {
  if (onboarding.open || touchLayout.matches || event.code !== 'Space' || event.repeat || event.target.closest('button, input, select, summary')) return;
  event.preventDefault();
  toggleRun();
});

const onboardingPages = [...onboarding.querySelectorAll('[data-title]')];
const onboardingTitle = select('onboarding-title');
const onboardingNext = select('onboarding-next');
const onboardingBack = select('onboarding-back');
const onboardingOpen = select('onboarding-open');
const onboardingKey = 'life-wars-onboarding-seen';
let onboardingPage = 0;
let openedFromGame = false;
let resumeAfterOnboarding = false;

function showOnboardingPage(index, focus = true) {
  onboardingPage = index;
  onboardingPages.forEach((page, pageIndex) => { page.hidden = pageIndex !== index; });
  onboardingTitle.textContent = translate(onboardingPages[index].dataset.title);
  select('onboarding-step').textContent = translate('stepProgress', {
    current: index + 1, total: onboardingPages.length
  });
  onboardingBack.hidden = index === 0;
  onboardingNext.textContent = translate(index === onboardingPages.length - 1 ? 'start' : 'next');
  if (focus) onboardingTitle.focus();
}

onboardingOpen.addEventListener('click', () => {
  openedFromGame = true;
  resumeAfterOnboarding = timer !== null;
  if (resumeAfterOnboarding) toggleRun();
  onboarding.showModal();
  showOnboardingPage(0);
});
select('onboarding-skip').addEventListener('click', () => onboarding.close());
onboardingBack.addEventListener('click', () => showOnboardingPage(onboardingPage - 1));
onboardingNext.addEventListener('click', () => {
  if (onboardingPage === onboardingPages.length - 1) {
    onboarding.close();
  } else {
    showOnboardingPage(onboardingPage + 1);
  }
});
onboarding.addEventListener('close', () => {
  try {
    localStorage.setItem(onboardingKey, '1');
  } catch {
    // The simulator still works when storage is unavailable.
  }
  applyLayout();
  if (resumeAfterOnboarding && timer === null) toggleRun();
  if (openedFromGame) onboardingOpen.focus();
  else if (!touchLayout.matches) run.focus();
  resumeAfterOnboarding = false;
  openedFromGame = false;
});

let onboardingSeen = false;
try {
  onboardingSeen = localStorage.getItem(onboardingKey) === '1';
} catch {
  // Show the guide when no saved preference is available.
}
const languageSelectors = [...document.querySelectorAll('.language')];

function applyLanguage() {
  document.documentElement.lang = language;
  activityFormatter = new Intl.NumberFormat(language, { style: 'percent', maximumFractionDigits: 1 });
  for (const node of document.querySelectorAll('[data-text]')) {
    node.textContent = translate(node.dataset.text);
  }
  for (const node of document.querySelectorAll('[data-label]')) {
    node.setAttribute('aria-label', translate(node.dataset.label));
  }
  for (const selector of languageSelectors) selector.value = language;
  showOnboardingPage(onboardingPage, false);
  updateRunControls();
  updateSpeed();
  updateStatus();
  if (image) render();
}

try {
  const savedLanguage = localStorage.getItem(languageKey);
  if (savedLanguage === 'ru' || savedLanguage === 'en') language = savedLanguage;
} catch {
  // Use the browser language when storage is unavailable.
}
for (const selector of languageSelectors) {
  selector.addEventListener('change', () => {
    language = selector.value;
    try {
      localStorage.setItem(languageKey, language);
    } catch {
      // The language still applies to the current visit.
    }
    applyLanguage();
  });
}
applyLanguage();
if (!onboardingSeen) onboarding.showModal();

touchLayout.addEventListener('change', () => applyLayout());
applyLayout(true);
new ResizeObserver(() => fitField()).observe(field);
