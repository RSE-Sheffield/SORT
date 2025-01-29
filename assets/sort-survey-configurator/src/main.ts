import { mount } from 'svelte'
import 'bootstrap/dist/js/bootstrap.min'
import 'bootstrap/dist/css/bootstrap.min.css'
import App from './App.svelte'

// function init(){
//     console.log(varInHtml);
//     return mount(App, {
//         target: document.getElementById('app')!,
//     });
// }
//
// const app = init();
//
// // const app = () => {
// //     return mount(App, {
// //         target: document.getElementById('app')!,
// //     });
// // }

const app = mount(App, {
        target: document.getElementById('app')!,
    });

export default app

