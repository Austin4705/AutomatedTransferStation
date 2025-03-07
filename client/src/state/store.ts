import { consoleMessage } from "./consoleState";

// Define the store interface
interface Store {
  getState: () => {
    appendConsole: (message: consoleMessage) => void;
  };
}

// Create a simple store to access state outside of React components
class StoreImplementation implements Store {
  private appendConsoleCallback: ((message: consoleMessage) => void) | null = null;

  setAppendConsole(callback: (message: consoleMessage) => void) {
    this.appendConsoleCallback = callback;
  }

  getState() {
    return {
      appendConsole: (message: consoleMessage) => {
        if (this.appendConsoleCallback) {
          this.appendConsoleCallback(message);
        } else {
          console.warn("appendConsole not initialized yet");
        }
      }
    };
  }
}

// Export a singleton instance
export const store = new StoreImplementation();

// Hook to initialize the store with the appendConsole function
export const initializeStore = (appendConsole: (message: consoleMessage) => void) => {
  store.setAppendConsole(appendConsole);
}; 