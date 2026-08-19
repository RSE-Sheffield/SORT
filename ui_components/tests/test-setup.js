import { vi } from "vitest";

// Stub Chart.js: jsdom provides no canvas rendering context, so the real Chart
// constructor throws. Component tests care about what a component renders around its
// chart, not about the chart's pixels.
vi.mock("chart.js", () => {
  class Chart {
    constructor() {
      this.data = { labels: [], datasets: [] };
      this.options = {};
    }
    update() {}
    destroy() {}
    static register() {}
  }
  return {
    Chart,
    Colors: {},
    ArcElement: {},
    BarController: {},
    BarElement: {},
    CategoryScale: {},
    DoughnutController: {},
    Legend: {},
    LinearScale: {},
    PieController: {},
    PointElement: {},
    Title: {},
    Tooltip: {},
    registerables: [],
  };
});

vi.mock("chartjs-plugin-datalabels", () => ({ default: {} }));

// Mock Web Animations API, which isn't included in jsdom
global.Element.prototype.animate = function () {
  return {
    onfinish: null,
    cancel: () => {},
    finish: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
  };
};

// Mock document.execCommand for rich text editors
global.document.execCommand = function (command, showUI, value) {
  console.log(`Mocked execCommand: ${command}, ${showUI}, ${value}`);
  return true;
};
