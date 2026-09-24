const status = document.querySelector("#lane4-status");
const speedEl = document.querySelector("#lane4-speed");
const distanceEl = document.querySelector("#lane4-distance");

const core = window.OldSchoolRacing;
if (!core) {
  status.dataset.upstream = "error";
  throw new Error("Vendored old-school-racing bundle did not load");
}

const { Car, Track, Race, RaceRender, BasicCPUControl } = core;
const track = new Track("EvoWild Lane 4 upstream proof");

track.addSegments(4, { color: 0xeeeeee, sideColor: 0x40613e, lines: 4 });
const sections = [
  [55, 0.00, 0.00],
  [38, -0.20, -0.04],
  [45, -0.42, 0.02],
  [32, 0.00, 0.06],
  [48, 0.34, -0.03],
  [36, 0.18, 0.05],
  [50, -0.36, -0.02],
  [42, 0.00, -0.05],
  [55, 0.28, 0.03],
  [70, 0.00, 0.00]
];

for (let lap = 0; lap < 3; lap++) {
  for (const [length, curve, hill] of sections) {
    track.addSegments(length, {
      curve,
      hill,
      width: 1180,
      color: 0x555b60,
      sideColor: lap % 2 ? 0x355a3b : 0x3d6340,
      lines: 5,
      lineSize: 9,
      lineColor: 0xdde8e8
    });
  }
}

const sAsset = `${import.meta.env.BASE_URL}concept/S.webp`;
const cars = [];
for (let i = 0; i < 10; i++) {
  const car = new Car(sAsset, {
    engine: 0.48 + (i % 5) * 0.018,
    brake: 0.58,
    grip: 0.62 + (i % 3) * 0.035
  });
  car.renderScale = i === 0 ? 0.30 : 0.24;
  car.position.z = i === 0 ? 0 : 180 + i * 115;
  car.position.x = ((i % 5) - 2) * 150;
  cars.push(car);
  new BasicCPUControl(car);
}

const race = new Race(track, cars, cars[0]);
const render = new RaceRender(race);
window.__lane4 = { track, cars, race, render };

status.dataset.upstream = "running";

function updateProbe() {
  const base = cars[0];
  const pixelPerFrame = base.dynamics.speed;
  const kmh = Math.round(((pixelPerFrame / 16) * 1000 / 10) * 3.6);
  speedEl.textContent = `${kmh} km/h`;
  distanceEl.textContent = `z ${Math.round(base.position.z)} / track ${Math.round(track.length)}`;
  status.dataset.baseZ = String(Math.round(base.position.z));
  requestAnimationFrame(updateProbe);
}
requestAnimationFrame(updateProbe);
