/* eslint-disable no-console */

export const register = () => {
  if (process.env.NODE_ENV === 'production' && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      const swUrl = `${process.env.BASE_URL}service-worker.js`;
      
      console.info(`[Dịch vụ Xiaozhi] Đang thử đăng ký Service Worker, URL: ${swUrl}`);
      
      // Kiểm tra xem Service Worker đã được đăng ký chưa
      navigator.serviceWorker.getRegistrations().then(registrations => {
        if (registrations.length > 0) {
          console.info('[Dịch vụ Xiaozhi] Phát hiện Service Worker đã được đăng ký, đang kiểm tra cập nhật');
        }
        
        // Tiếp tục đăng ký Service Worker
        navigator.serviceWorker
          .register(swUrl)
          .then(registration => {
            console.info('[Dịch vụ Xiaozhi] Đăng ký Service Worker thành công');
            
            // Xử lý cập nhật
            registration.onupdatefound = () => {
              const installingWorker = registration.installing;
              if (installingWorker == null) {
                return;
              }
              installingWorker.onstatechange = () => {
                if (installingWorker.state === 'installed') {
                  if (navigator.serviceWorker.controller) {
                    // Nội dung đã được cập nhật trong cache, thông báo người dùng làm mới
                    console.log('[Dịch vụ Xiaozhi] Nội dung mới có sẵn, vui lòng làm mới trang');
                    // Có thể hiển thị thông báo cập nhật ở đây
                    const updateNotification = document.createElement('div');
                    updateNotification.style.cssText = `
                      position: fixed;
                      bottom: 20px;
                      right: 20px;
                      background: #409EFF;
                      color: white;
                      padding: 12px 20px;
                      border-radius: 4px;
                      box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
                      z-index: 9999;
                    `;
                    updateNotification.innerHTML = `
                      <div style="display: flex; align-items: center;">
                        <span style="margin-right: 10px;">Phát hiện phiên bản mới, nhấp để làm mới ứng dụng</span>
                        <button style="background: white; color: #409EFF; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Làm mới</button>
                      </div>
                    `;
                    document.body.appendChild(updateNotification);
                    updateNotification.querySelector('button').addEventListener('click', () => {
                      window.location.reload();
                    });
                  } else {
                    // Mọi thứ bình thường, Service Worker đã được cài đặt thành công
                    console.log('[Dịch vụ Xiaozhi] Nội dung đã được lưu vào cache để sử dụng ngoại tuyến');
                    
                    // Có thể khởi tạo cache ở đây
                    setTimeout(() => {
                      // Làm nóng cache CDN
                      const cdnUrls = [
                        'https://unpkg.com/element-ui@2.15.14/lib/theme-chalk/index.css',
                        'https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css',
                        'https://unpkg.com/vue@2.6.14/dist/vue.min.js',
                        'https://unpkg.com/vue-router@3.6.5/dist/vue-router.min.js',
                        'https://unpkg.com/vuex@3.6.2/dist/vuex.min.js',
                        'https://unpkg.com/element-ui@2.15.14/lib/index.js',
                        'https://unpkg.com/axios@0.27.2/dist/axios.min.js',
                        'https://unpkg.com/opus-decoder@0.7.7/dist/opus-decoder.min.js'
                      ];
                      
                      // Làm nóng cache
                      cdnUrls.forEach(url => {
                        fetch(url, { mode: 'no-cors' }).catch(err => {
                          console.log(`Làm nóng cache ${url} thất bại`, err);
                        });
                      });
                    }, 2000);
                  }
                }
              };
            };
          })
          .catch(error => {
            console.error('Đăng ký Service Worker thất bại:', error);
            
            if (error.name === 'TypeError' && error.message.includes('Failed to register a ServiceWorker')) {
              console.warn('[Dịch vụ Xiaozhi] Lỗi mạng khi đăng ký Service Worker, tài nguyên CDN có thể không thể lưu vào cache');
              if (process.env.NODE_ENV === 'production') {
                console.info(
                  'Nguyên nhân có thể: 1. Máy chủ chưa cấu hình đúng loại MIME 2. Vấn đề chứng chỉ SSL của máy chủ 3. Máy chủ không trả về tệp service-worker.js'
                );
              }
            }
          });
      });
    });
  }
};

export const unregister = () => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then(registration => {
        registration.unregister();
      })
      .catch(error => {
        console.error(error.message);
      });
  }
}; 