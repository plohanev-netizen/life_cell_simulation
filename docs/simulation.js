'use strict';

const adjacent = [-1, 0, 1].flatMap(dy =>
  [-1, 0, 1].filter(dx => dx || dy).map(dx => [dx, dy])
);

const bombRadius = 15;
const oscillatorPeriods = [2, 3, 4];
const oscillatorCycles = 100;

class Simulation {
  constructor(width = 180, height = 120, random = Math.random) {
    this.width = width;
    this.height = height;
    this.random = random;
    this.mutations = true;
    this.raiders = true;
    this.virus = true;
    this.reset();
  }

  reset(seed = true) {
    this.grid = new Uint8Array(this.width * this.height);
    this.history = [];
    this.oscillatorHistory = [];
    this.oscillatorStreaks = oscillatorPeriods.map(() => new Uint16Array(this.grid.length));
    this.generation = 0;
    this.lastMutation = 0;
    this.virusSince = null;
    this.virusQuiet = 0;
    this.nextVirus = 500 + Math.floor(this.random() * 201);
    this.activity = 0;
    this.events = [];
    if (!seed) return;
    for (let y = 0; y < this.height; y++) {
      for (let x = 0; x < this.width; x++) {
        if (x >= this.width * .47 && x < this.width * .53) continue;
        if (this.random() < .4) this.grid[this.index(x, y)] = x < this.width / 2 ? 1 : 2;
      }
    }
  }

  resize(width, height) {
    if (width === this.width && height === this.height) return;
    const columns = Math.min(width, this.width);
    const rows = Math.min(height, this.height);
    const resizeGrid = grid => {
      const result = new grid.constructor(width * height);
      for (let y = 0; y < rows; y++) {
        const start = y * this.width;
        result.set(grid.subarray(start, start + columns), y * width);
      }
      return result;
    };
    this.grid = resizeGrid(this.grid);
    this.history = this.history.map(resizeGrid);
    this.oscillatorHistory = this.oscillatorHistory.map(resizeGrid);
    this.oscillatorStreaks = this.oscillatorStreaks.map(resizeGrid);
    this.width = width;
    this.height = height;
  }

  index(x, y) {
    return y * this.width + x;
  }

  inside(x, y) {
    return x >= 0 && x < this.width && y >= 0 && y < this.height;
  }

  neighbors(x, y, visit) {
    for (const [dx, dy] of adjacent) {
      if (this.inside(x + dx, y + dy)) visit(this.index(x + dx, y + dy));
    }
  }

  clearOscillatorStreak(index) {
    for (const streak of this.oscillatorStreaks) streak[index] = 0;
  }

  paint(x, y, state) {
    if (!state) {
      for (const [dx, dy] of [[0, 0], ...adjacent]) {
        if (!this.inside(x + dx, y + dy)) continue;
        const index = this.index(x + dx, y + dy);
        if (!this.grid[index]) continue;
        this.grid[index] = 0;
        this.clearOscillatorStreak(index);
      }
    } else {
      const group = [this.index(x, y)];
      for (let i = 0; i < group.length && group.length < 4; i++) {
        const neighbors = [];
        this.neighbors(group[i] % this.width, Math.floor(group[i] / this.width), n => neighbors.push(n));
        while (neighbors.length && group.length < 4) {
          const [n] = neighbors.splice(Math.floor(this.random() * neighbors.length), 1);
          if (!group.includes(n) && !this.grid[n]) group.push(n);
        }
      }
      for (const n of group) {
        if (this.grid[n]) continue;
        this.grid[n] = state;
        this.clearOscillatorStreak(n);
      }
    }
    this.history = [];
  }

  disk(x, y, radius, density, state = 0, grid = this.grid) {
    const cells = [];
    for (let dy = -radius; dy <= radius; dy++) {
      for (let dx = -radius; dx <= radius; dx++) {
        if (dx * dx + dy * dy > radius * radius || !this.inside(x + dx, y + dy)) continue;
        const i = this.index(x + dx, y + dy);
        grid[i] = 0;
        this.clearOscillatorStreak(i);
        cells.push(i);
      }
    }
    const count = Math.floor(cells.length * density);
    for (let j = 0; j < count; j++) {
      const k = j + Math.floor(this.random() * (cells.length - j));
      [cells[j], cells[k]] = [cells[k], cells[j]];
      grid[cells[j]] = state || (j < count / 2 ? 1 : 2);
    }
  }

  blast(x, y, viral = false) {
    if (viral && !this.virus) this.setVirus(true);
    this.disk(x, y, bombRadius, .45, viral ? 3 : 0);
    if (viral) {
      this.virusSince ??= this.generation;
      this.virusQuiet = 0;
    }
    this.lastMutation = this.generation;
    this.history = [];
    this.events.push({ type: viral ? 'Вирусная бомба' : 'Ручной взрыв', x, y, radius: bombRadius });
  }

  mutate() {
    if (this.random() < .5) {
      const x = Math.floor(this.width / 2);
      const y = Math.floor(this.height / 2);
      const radius = Math.max(1, Math.floor(Math.min(this.width, this.height) / 3));
      this.disk(x, y, radius, .45);
      this.events.push({ type: 'Большой взрыв', x, y, radius });
    } else {
      const count = 6 + Math.floor(this.random() * 7);
      const radius = Math.max(1, Math.floor(Math.min(this.width, this.height) / 12));
      const centers = [];
      for (let attempt = 0; centers.length < count && attempt < 250; attempt++) {
        const x = Math.floor(this.random() * this.width);
        const y = Math.floor(this.random() * this.height);
        if (centers.some(c => Math.hypot(c.x - x, c.y - y) < radius * 1.8)) continue;
        const event = { type: 'Серия взрывов', x, y, radius };
        centers.push(event);
        this.disk(x, y, radius, .45);
        this.events.push(event);
      }
    }
    this.lastMutation = this.generation;
    this.history = [];
  }

  raid(grid) {
    const source = grid.slice();
    const visited = new Uint8Array(grid.length);
    let groups = 0;
    for (let i = 0; i < source.length && groups < 120; i++) {
      const state = source[i];
      if (!state || state === 3 || visited[i]) continue;
      const group = [i];
      let contact = false;
      visited[i] = 1;
      for (let j = 0; j < group.length; j++) {
        this.neighbors(group[j] % this.width, Math.floor(group[j] / this.width), n => {
          if (source[n] === 3 - state) contact = true;
          if (source[n] !== state || visited[n]) return;
          visited[n] = 1;
          group.push(n);
        });
      }
      if (group.length > 8 || !contact || grid[i] !== state) continue;
      groups++;
      const x = i % this.width;
      const y = Math.floor(i / this.width);
      let allies = 0;
      let enemies = 0;
      for (let ny = Math.max(y - 22, 0); ny <= Math.min(y + 22, this.height - 1); ny++) {
        for (let nx = Math.max(x - 22, 0); nx <= Math.min(x + 22, this.width - 1); nx++) {
          const cell = source[this.index(nx, ny)];
          if (cell === 3 - state) enemies++;
          if (cell === state && Math.abs(nx - x) <= 16 && Math.abs(ny - y) <= 16) allies++;
        }
      }
      if (allies > group.length + 2 || enemies <= 20) continue;
      if (this.random() >= Math.min(.95, .25 + .015 * (enemies - 20))) continue;
      this.disk(x, y, 9, .78, state, grid);
      this.events.push({ type: 'Атака рейдеров', x, y, radius: 9 });
    }
  }

  setVirus(enabled) {
    this.virus = enabled;
    if (enabled) return;
    this.grid.forEach((cell, i) => {
      if (cell !== 3) return;
      this.grid[i] = 0;
      this.clearOscillatorStreak(i);
    });
    this.virusSince = null;
    this.virusQuiet = 0;
    this.history = [];
    this.nextVirus = this.generation + 200;
  }

  updateVirus(old, next) {
    if (!this.virus) return;
    if (this.virusSince !== null) {
      const changed = next.some((cell, i) => (cell === 3) !== (old[i] === 3));
      this.virusQuiet = changed ? 0 : this.virusQuiet + 1;
      if (!next.includes(3) || this.generation - this.virusSince >= 800 || this.virusQuiet >= 100) {
        next.forEach((cell, i) => { if (cell === 3) next[i] = 0; });
        this.virusSince = null;
        this.nextVirus = this.generation + 800;
      }
      return;
    }
    if (this.generation < this.nextVirus) return;
    for (let group = 0; group < 5; group++) {
      let x = Math.floor(this.random() * this.width);
      let y = Math.floor(this.random() * this.height);
      this.events.push({ type: 'Вирусная волна', x, y, radius: 5 });
      for (let i = 0; i < 80; i++) {
        next[this.index(x, y)] = 3;
        x = Math.max(0, Math.min(this.width - 1, x + Math.floor(this.random() * 3) - 1));
        y = Math.max(0, Math.min(this.height - 1, y + Math.floor(this.random() * 3) - 1));
      }
    }
    this.virusSince = this.generation;
    this.virusQuiet = 0;
  }

  explodeOscillators(old, next) {
    const triggered = [];
    for (const [index, period] of oscillatorPeriods.entries()) {
      const streak = this.oscillatorStreaks[index];
      const previous = this.oscillatorHistory[period - 2];
      if (!previous) {
        streak.fill(0);
        continue;
      }
      const intermediate = this.oscillatorHistory.slice(0, period - 2);
      const threshold = (oscillatorCycles - 1) * period + 1;
      for (let i = 0; i < next.length; i++) {
        const cell = next[i];
        const varies = old[i] !== cell || intermediate.some(grid => grid[i] !== cell);
        streak[i] = previous[i] === cell && varies ? streak[i] + 1 : 0;
        if (streak[i] === threshold) triggered.push([i, streak]);
      }
    }
    for (const [i, streak] of triggered) {
      if (!streak[i]) continue;
      const x = i % this.width;
      const y = Math.floor(i / this.width);
      const radius = Math.round(bombRadius * 1.5);
      this.disk(x, y, radius, .45);
      this.events.push({ type: 'Взрыв осциллятора', x, y, radius });
      this.lastMutation = this.generation;
    }
  }

  step() {
    this.events = [];
    const old = this.grid;
    const infected = old.slice();
    if (this.virus && old.includes(3)) {
      old.forEach((cell, i) => {
        if (cell !== 3) return;
        this.neighbors(i % this.width, Math.floor(i / this.width), n => {
          if (old[n]) infected[n] = 3;
        });
      });
    }
    const next = new Uint8Array(old.length);
    for (let y = 0; y < this.height; y++) {
      for (let x = 0; x < this.width; x++) {
        const i = this.index(x, y);
        let white = 0;
        let red = 0;
        let virus = 0;
        this.neighbors(x, y, n => {
          const state = infected[n];
          white += Number(state === 1);
          red += Number(state === 2);
          virus += Number(state === 3);
        });
        const count = white + red + virus;
        if (infected[i]) {
          if (count === 2 || count === 3) next[i] = infected[i];
        } else if (count === 3) {
          next[i] = white >= 2 ? 1 : red >= 2 ? 2 : virus >= 2 ? 3 : 1 + Math.floor(this.random() * 3);
        }
      }
    }
    if (this.raiders && this.generation % 2 === 0) this.raid(next);
    this.generation++;
    this.updateVirus(old, next);
    let active = 0;
    let occupied = 0;
    next.forEach((cell, i) => {
      if (cell || old[i]) occupied++;
      if (cell !== old[i] && !this.history.some(previous => previous[i] === cell)) active++;
    });
    this.activity = occupied ? 100 * active / occupied : 0;
    this.grid = next;
    this.explodeOscillators(old, next);
    this.oscillatorHistory.unshift(old);
    if (this.oscillatorHistory.length > 3) this.oscillatorHistory.pop();
    this.history.unshift(old);
    if (this.history.length > 3) this.history.pop();
    if (this.mutations && this.activity < 1 && this.generation - this.lastMutation >= 30) this.mutate();
  }

  populations() {
    const counts = [0, 0, 0, 0];
    this.grid.forEach(cell => counts[cell]++);
    return counts;
  }
}
