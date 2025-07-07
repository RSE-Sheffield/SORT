// Mock Web Animations API, which isn't included in jsdom
global.Element.prototype.animate = function () {
    return {
        onfinish: null,
        cancel: () => {
        },
        finish: () => {
        },
        addEventListener: () => {
        },
        removeEventListener: () => {
        }
    }
};
