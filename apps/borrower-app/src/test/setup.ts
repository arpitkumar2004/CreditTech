import "@testing-library/jest-dom/vitest";

// jsdom polyfills for recharts
class ResizeObserverPolyfill {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = (globalThis as any).ResizeObserver || ResizeObserverPolyfill;
