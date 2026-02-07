/* global self, workbox */

// Logic xử lý tùy chỉnh cho việc cài đặt và kích hoạt Service Worker
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Danh sách tài nguyên CDN
const CDN_CSS = [
  'https://unpkg.com/element-ui@2.15.14/lib/theme-chalk/index.css',
  'https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css'
];

const CDN_JS = [
  'https://unpkg.com/vue@2.6.14/dist/vue.min.js',
  'https://unpkg.com/vue-router@3.6.5/dist/vue-router.min.js',
  'https://unpkg.com/vuex@3.6.2/dist/vuex.min.js',
  'https://unpkg.com/element-ui@2.15.14/lib/index.js',
  'https://unpkg.com/axios@0.27.2/dist/axios.min.js',
  'https://unpkg.com/opus-decoder@0.7.7/dist/opus-decoder.min.js'
];

// Tự động thực thi sau khi Service Worker được tiêm manifest
const manifest = self.__WB_MANIFEST || [];

// Kiểm tra xem có bật chế độ CDN không
const isCDNEnabled = manifest.some(entry => 
  entry.url === 'cdn-mode' && entry.revision === 'enabled'
);

console.log(`Service Worker đã được khởi tạo, Chế độ CDN: ${isCDNEnabled ? 'Bật' : 'Tắt'}`);

// Tiêm mã liên quan đến workbox
importScripts('https://storage.googleapis.com/workbox-cdn/releases/7.0.0/workbox-sw.js');
workbox.setConfig({ debug: false });

// Bật workbox
workbox.core.skipWaiting();
workbox.core.clientsClaim();

// Làm nóng cache trang ngoại tuyến
const OFFLINE_URL = '/offline.html';
workbox.precaching.precacheAndRoute([
  { url: OFFLINE_URL, revision: null }
]);

// Thêm trình xử lý sự kiện cài đặt hoàn tất, hiển thị thông báo cài đặt trong bảng điều khiển
self.addEventListener('install', event => {
  if (isCDNEnabled) {
    console.log('Service Worker đã được cài đặt, bắt đầu lưu vào cache tài nguyên CDN');
  } else {
    console.log('Service Worker đã được cài đặt, chế độ CDN bị tắt, chỉ lưu vào cache tài nguyên cục bộ');
  }
  
  // Đảm bảo trang ngoại tuyến được lưu vào cache
  event.waitUntil(
    caches.open('offline-cache').then((cache) => {
      return cache.add(OFFLINE_URL);
    })
  );
});

// Thêm trình xử lý sự kiện kích hoạt
self.addEventListener('activate', event => {
  console.log('Service Worker đã được kích hoạt, hiện đang kiểm soát trang');
  
  // Dọn dẹp cache phiên bản cũ
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          // Dọn dẹp cache ngoại trừ phiên bản hiện tại
          return cacheName.startsWith('workbox-') && !workbox.core.cacheNames.runtime.includes(cacheName);
        }).map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
});

// Thêm bộ chặn sự kiện fetch để xem tài nguyên CDN có trúng cache không
self.addEventListener('fetch', event => {
  // Chỉ giám sát cache tài nguyên CDN khi chế độ CDN được bật
  if (isCDNEnabled) {
    const url = new URL(event.request.url);
    
    // Đối với tài nguyên CDN, xuất thông tin có trúng cache không
    if ([...CDN_CSS, ...CDN_JS].includes(url.href)) {
      // Không can thiệp vào quy trình fetch bình thường, chỉ thêm nhật ký
      console.log(`Yêu cầu tài nguyên CDN: ${url.href}`);
    }
  }
});

// Chỉ lưu vào cache tài nguyên CDN khi ở chế độ CDN
if (isCDNEnabled) {
  // Lưu vào cache tài nguyên CSS của CDN
  workbox.routing.registerRoute(
    ({ url }) => CDN_CSS.includes(url.href),
    new workbox.strategies.CacheFirst({
      cacheName: 'cdn-stylesheets',
      plugins: [
        new workbox.expiration.ExpirationPlugin({
          maxAgeSeconds: 365 * 24 * 60 * 60, // Tăng lên 1 năm cache
          maxEntries: 10, // Tối đa 10 tệp CSS được lưu vào cache
        }),
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200], // Lưu vào cache phản hồi thành công
        }),
      ],
    })
  );

  // Lưu vào cache tài nguyên JS của CDN
  workbox.routing.registerRoute(
    ({ url }) => CDN_JS.includes(url.href),
    new workbox.strategies.CacheFirst({
      cacheName: 'cdn-scripts',
      plugins: [
        new workbox.expiration.ExpirationPlugin({
          maxAgeSeconds: 365 * 24 * 60 * 60, // Tăng lên 1 năm cache
          maxEntries: 20, // Tối đa 20 tệp JS được lưu vào cache
        }),
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200], // Lưu vào cache phản hồi thành công
        }),
      ],
    })
  );
}

// Bất kể có bật chế độ CDN hay không, đều lưu vào cache tài nguyên tĩnh cục bộ
workbox.routing.registerRoute(
  /\.(?:js|css|png|jpg|jpeg|svg|gif|ico|woff|woff2|eot|ttf|otf)$/,
  new workbox.strategies.StaleWhileRevalidate({
    cacheName: 'static-resources',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxAgeSeconds: 7 * 24 * 60 * 60, // Cache 7 ngày
        maxEntries: 50, // Tối đa 50 tệp được lưu vào cache
      }),
    ],
  })
);

// Lưu vào cache trang HTML
workbox.routing.registerRoute(
  /\.html$/,
  new workbox.strategies.NetworkFirst({
    cacheName: 'html-cache',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxAgeSeconds: 1 * 24 * 60 * 60, // Cache 1 ngày
        maxEntries: 10, // Tối đa 10 tệp HTML được lưu vào cache
      }),
    ],
  })
);

// Trang ngoại tuyến - sử dụng cách xử lý đáng tin cậy hơn
workbox.routing.setCatchHandler(async ({ event }) => {
  // Trả về trang mặc định phù hợp theo loại yêu cầu
  switch (event.request.destination) {
    case 'document':
      // Nếu là yêu cầu trang web, trả về trang ngoại tuyến
      return caches.match(OFFLINE_URL);
    default:
      // Tất cả các yêu cầu khác trả về lỗi
      return Response.error();
  }
}); 