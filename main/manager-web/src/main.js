import 'element-ui/lib/theme-chalk/index.css';
import 'normalize.css/normalize.css'; // A modern alternative to CSS resets
import Vue from 'vue';
import ElementUI from 'element-ui';
import locale from 'element-ui/lib/locale';
import App from './App.vue';
import router from './router';
import store from './store';
import i18n, { getElementLocale } from './i18n';
import './styles/global.scss';
import { register as registerServiceWorker } from './registerServiceWorker';
import featureManager from './utils/featureManager';

Vue.prototype.$eventBus = new Vue();

// Khởi tạo locale cho Element UI
locale.use(getElementLocale(i18n.locale));

Vue.use(ElementUI, { locale: getElementLocale(i18n.locale) });

Vue.config.productionTip = false

registerServiceWorker();

new Vue({
  router,
  store,
  i18n,
  render: function (h) { return h(App) }
}).$mount('#app')
