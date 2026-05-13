import { mount } from 'svelte'
import App from './App.svelte'
import 'vanilla-framework/scss/build.scss'
import './app.css'

const target = document.getElementById('app')
const app = target ? mount(App, { target }) : null

export default app
