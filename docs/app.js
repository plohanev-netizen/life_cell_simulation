'use strict';

const simulation = new Simulation();
const select = id => document.getElementById(id);
const canvas = select('grid');
const context = canvas.getContext('2d');
const image = context.createImageData(canvas.width, canvas.height);
const palette = [[10, 20, 23], [225, 241, 250], [255, 119, 106], [182, 239, 114]];
const run = select('run');
const step = select('step');
const speed = select('speed');
let timer = null;

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
  select('activity').textContent = new Intl.NumberFormat('ru', { maximumFractionDigits: 1 }).format(simulation.activity) + '%';
}

function advance() {
  simulation.step();
  const event = simulation.events.at(-1);
  if (event) select('event').textContent = `${event.type} · поколение ${simulation.generation}`;
  render();
}

function start() {
  clearInterval(timer);
  timer = setInterval(advance, 1000 / Number(speed.value));
}

function toggleRun() {
  if (timer === null) {
    start();
  } else {
    clearInterval(timer);
    timer = null;
  }
  step.disabled = timer !== null;
  run.textContent = timer === null ? 'Пуск' : 'Пауза';
}

function reset(seed) {
  simulation.reset(seed);
  select('event').textContent = seed ? 'Поле заселено' : 'Поле очищено';
  render();
}

function edit(event, secondary = false) {
  const rect = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - rect.left) * canvas.width / rect.width);
  const y = Math.floor((event.clientY - rect.top) * canvas.height / rect.height);
  if (!simulation.inside(x, y)) return;
  const tool = event.shiftKey ? '0' : secondary ? '2' : document.querySelector('[name=brush]:checked').value;
  simulation.events = [];
  if (tool === 'blast') {
    simulation.blast(x, y);
    select('event').textContent = `Ручной взрыв · поколение ${simulation.generation}`;
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
  select('speed-value').textContent = `${speed.value} поколений/с`;
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
  edit(event, true);
});
document.addEventListener('keydown', event => {
  if (event.code !== 'Space' || event.repeat || event.target.closest('button, input')) return;
  event.preventDefault();
  toggleRun();
});

render();
