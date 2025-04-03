import {mount} from 'svelte'
import App from './App.svelte'

// Mount the Svelte application into the HTML DOM in <div id="app" />
const app = mount(App, {
  target: document.getElementById('app')!,
});

export default app;
