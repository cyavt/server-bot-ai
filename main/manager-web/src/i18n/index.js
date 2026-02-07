import Vue from 'vue';
import VueI18n from 'vue-i18n';
import locale from 'element-ui/lib/locale';
import langZhCN from 'element-ui/lib/locale/lang/zh-CN';
import langZhTW from 'element-ui/lib/locale/lang/zh-TW';
import langEn from 'element-ui/lib/locale/lang/en';
import langDe from 'element-ui/lib/locale/lang/de';
import zhCN from './zh_CN';
import zhTW from './zh_TW';
import en from './en';
import de from './de';
import vi from './vi';

Vue.use(VueI18n);

// Hàm lấy locale cho Element UI
const getElementLocale = (lang) => {
  switch (lang) {
    case 'zh_CN':
      return langZhCN;
    case 'zh_TW':
      return langZhTW;
    case 'en':
      return langEn;
    case 'de':
      return langDe;
    case 'vi':
      // Tạo locale tùy chỉnh cho tiếng Việt dựa trên tiếng Anh
      const viLocale = Object.assign({}, langEn);
      viLocale.table = Object.assign({}, langEn.table || {}, {
        emptyText: 'Không có dữ liệu'
      });
      return viLocale;
    default:
      return langZhCN;
  }
};

// 从本地存储获取语言设置，如果没有则使用浏览器语言或默认语言
const getDefaultLanguage = () => {
  const savedLang = localStorage.getItem('userLanguage');
  if (savedLang) {
    return savedLang;
  }
  const browserLang = navigator.language || navigator.userLanguage;
  if (browserLang.indexOf('zh') === 0) {
    if (browserLang === 'zh-TW' || browserLang === 'zh-HK' || browserLang === 'zh-MO') {
      return 'zh_TW';
    }
    return 'zh_CN';
  }
  if (browserLang.indexOf('de') === 0) {
    return 'de';
  }
  if (browserLang.indexOf('vi') === 0) {
    return 'vi';
  }
  return 'en';
};

const i18n = new VueI18n({
  locale: getDefaultLanguage(),
  fallbackLocale: 'zh_CN',
  messages: {
    'zh_CN': zhCN,
    'zh_TW': zhTW,
    'en': en,
    'de': de,
    'vi': vi
  }
});

export default i18n;
export { getElementLocale };

// 提供一个方法来切换语言
export const changeLanguage = (lang) => {
  i18n.locale = lang;
  localStorage.setItem('userLanguage', lang);
  // Cập nhật locale cho Element UI
  locale.use(getElementLocale(lang));
  // 通知组件语言已更改
  Vue.prototype.$eventBus.$emit('languageChanged', lang);
};