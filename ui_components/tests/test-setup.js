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
