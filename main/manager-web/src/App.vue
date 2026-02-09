<template>
  <div id="app">
    <router-view />
    <cache-viewer v-if="isCDNEnabled" :visible.sync="showCacheViewer" />
  </div>
</template>

<style lang="scss">
#app {
  font-family: var(--font-family-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: var(--text-primary);
  background: linear-gradient(135deg, 
    var(--primary-blue-lightest) 0%, 
    #ffffff 30%, 
    #ffffff 70%, 
    var(--primary-orange-lightest) 100%);
  background-attachment: fixed;
  min-height: 100vh;
  line-height: var(--line-height-normal);
}

nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: var(--text-primary);

    &.router-link-exact-active {
      color: var(--primary-blue);
    }
  }
}

.copyright {
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 400;
  margin-top: auto;
  padding: 30px 0 20px;
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
}

.el-message {
  top: 70px !important;
  box-shadow: var(--shadow-lg) !important;
  border: none !important;
  min-width: 380px !important;
  
  .el-message__content {
    color: #FFFFFF !important;
    font-weight: var(--font-weight-medium) !important;
    font-size: var(--font-size-base) !important;
    line-height: var(--line-height-normal) !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
  }
  
  .el-message__icon {
    color: #FFFFFF !important;
    font-size: 18px !important;
  }
  
  .el-message__closeBtn {
    color: rgba(255, 255, 255, 0.9) !important;
    
    &:hover {
      color: #FFFFFF !important;
    }
  }
}

// Update message colors to match theme with better contrast
.el-message--success {
  background: linear-gradient(135deg, var(--success-color) 0%, #059669 100%) !important;
  border-left: 4px solid #FFFFFF !important;
  
  .el-message__icon {
    color: #FFFFFF !important;
  }
}

.el-message--warning {
  background: linear-gradient(135deg, var(--warning-color) 0%, #D97706 100%) !important;
  border-left: 4px solid #FFFFFF !important;
  
  .el-message__icon {
    color: #FFFFFF !important;
  }
}

.el-message--error {
  background: linear-gradient(135deg, var(--error-color) 0%, #DC2626 100%) !important;
  border-left: 4px solid #FFFFFF !important;
  
  .el-message__icon {
    color: #FFFFFF !important;
  }
}

.el-message--info {
  background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-dark) 100%) !important;
  border-left: 4px solid #FFFFFF !important;
  
  .el-message__icon {
    color: #FFFFFF !important;
  }
}
</style>
<script>
import CacheViewer from '@/components/CacheViewer.vue';
import { logCacheStatus } from '@/utils/cacheViewer';

export default {
  name: 'App',
  components: {
    CacheViewer
  },
  data() {
    return {
      showCacheViewer: false,
      isCDNEnabled: process.env.VUE_APP_USE_CDN === 'true'
    };
  },
  mounted() {
    // Kiểm tra xem có phải thiết bị di động và VUE_APP_H5_URL không rỗng không, nếu cả hai điều kiện đều thỏa mãn thì chuyển đến trang H5
    if (this.isMobileDevice() && process.env.VUE_APP_H5_URL) {
      window.location.href = process.env.VUE_APP_H5_URL;
      return;
    }
    
    // Chỉ thêm các sự kiện và chức năng liên quan khi CDN được bật
    if (this.isCDNEnabled) {
      // Thêm phím tắt toàn cục Alt+C để hiển thị trình xem cache
      document.addEventListener('keydown', this.handleKeyDown);

      // Thêm phương thức kiểm tra cache vào đối tượng toàn cục, thuận tiện cho việc gỡ lỗi
      window.checkCDNCacheStatus = () => {
        this.showCacheViewer = true;
      };

      // Xuất thông tin gợi ý ra bảng điều khiển
      console.info(
        '%c[' + this.$t('system.name') + '] ' + this.$t('cache.cdnEnabled'),
        'color: #409EFF; font-weight: bold;'
      );
      console.info(
        'Nhấn tổ hợp phím Alt+C hoặc chạy checkCDNCacheStatus() trong bảng điều khiển để xem trạng thái cache CDN'
      );

      // Kiểm tra trạng thái Service Worker
      this.checkServiceWorkerStatus();
    } else {
      console.info(
        '%c[' + this.$t('system.name') + '] ' + this.$t('cache.cdnDisabled'),
        'color: #67C23A; font-weight: bold;'
      );
    }
  },
  beforeDestroy() {
    // Chỉ cần xóa trình lắng nghe sự kiện khi CDN được bật
    if (this.isCDNEnabled) {
      document.removeEventListener('keydown', this.handleKeyDown);
    }
  },
  methods: {
    handleKeyDown(e) {
      // Phím tắt Alt+C
      if (e.altKey && e.key === 'c') {
        this.showCacheViewer = true;
      }
    },
    isMobileDevice() {
      // Hàm kiểm tra xem có phải thiết bị di động không
      return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    async checkServiceWorkerStatus() {
      // Kiểm tra xem Service Worker đã được đăng ký chưa
      if ('serviceWorker' in navigator) {
        try {
          const registrations = await navigator.serviceWorker.getRegistrations();
          if (registrations.length > 0) {
            console.info(
              '%c[' + this.$t('system.name') + '] ' + this.$t('cache.serviceWorkerRegistered'),
              'color: #67C23A; font-weight: bold;'
            );

            // Xuất trạng thái cache ra bảng điều khiển
            setTimeout(async () => {
              const hasCaches = await logCacheStatus();
              if (!hasCaches) {
                console.info(
                '%c[' + this.$t('system.name') + '] ' + this.$t('cache.noCacheDetected'),
                'color: #E6A23C; font-weight: bold;'
              );

              // Cung cấp gợi ý bổ sung trong môi trường phát triển
              if (process.env.NODE_ENV === 'development') {
                console.info(
                  '%c[' + this.$t('system.name') + '] ' + this.$t('cache.swDevEnvWarning'),
                  'color: #E6A23C; font-weight: bold;'
                );
                console.info(this.$t('cache.swCheckMethods'));
                console.info('1. ' + this.$t('cache.swCheckMethod1'));
                console.info('2. ' + this.$t('cache.swCheckMethod2'));
                console.info('3. ' + this.$t('cache.swCheckMethod3'));
              }
              }
            }, 2000);
          } else {
            console.info(
                  '%c[' + this.$t('system.name') + '] ' + this.$t('cache.serviceWorkerNotRegistered'),
                  'color: #F56C6C; font-weight: bold;'
                );

                if (process.env.NODE_ENV === 'development') {
                  console.info(
                    '%c[' + this.$t('system.name') + '] ' + this.$t('cache.swDevEnvNormal'),
                    'color: #E6A23C; font-weight: bold;'
                  );
                  console.info(this.$t('cache.swProdOnly'));
                  console.info(this.$t('cache.swTestingTitle'));
                  console.info('1. ' + this.$t('cache.swTestingStep1'));
                  console.info('2. ' + this.$t('cache.swTestingStep2'));
                }
          }
        } catch (error) {
          console.error('Kiểm tra trạng thái Service Worker thất bại:', error);
        }
      } else {
          console.warn(this.$t('cache.swNotSupported'));
        }
    }
  }
};
</script>