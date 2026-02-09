<template>
  <div class="welcome">
    <!-- Đầu trang chung -->
    <HeaderBar :devices="devices" @search="handleSearch" @search-reset="handleSearchReset" />
    <el-main style="padding: 20px;display: flex;flex-direction: column;">
      <div>
        <!-- Nội dung trang chủ -->
        <div class="add-device">
          <div class="add-device-bg">
            <div class="hellow-text" style="margin-top: 30px;">
              {{ $t('home.greeting') }}
            </div>
            <div class="hellow-text">
              {{ $t('home.wish') }}
            </div>
            <div class="hi-hint">
              {{ $t('home.wish') }}
            </div>
            <div class="add-device-btn">
              <div class="left-add" @click="showAddDialog">
                {{ $t('home.addAgent') }}
              </div>
              <div class="button-connector" />
              <div class="right-add" @click="showAddDialog">
                <i class="el-icon-right" />
              </div>
            </div>
          </div>
        </div>
        <div class="device-list-container">
          <template v-if="isLoading">
            <div v-for="i in skeletonCount" :key="'skeleton-' + i" class="skeleton-item">
              <div class="skeleton-image"></div>
              <div class="skeleton-content">
                <div class="skeleton-line"></div>
                <div class="skeleton-line-short"></div>
              </div>
            </div>
          </template>

          <template v-else>
            <DeviceItem v-for="(item, index) in devices" :key="index" :device="item" :feature-status="featureStatus" 
              @configure="goToRoleConfig" @deviceManage="handleDeviceManage" @delete="handleDeleteAgent" 
              @chat-history="handleShowChatHistory" />
          </template>
        </div>
      </div>
      <AddWisdomBodyDialog :visible.sync="addDeviceDialogVisible" @confirm="handleWisdomBodyAdded" />
    </el-main>
    <el-footer>
      <version-footer />
    </el-footer>
    <chat-history-dialog :visible.sync="showChatHistory" :agent-id="currentAgentId" :agent-name="currentAgentName" />
  </div>

</template>

<script>
import Api from '@/apis/api';
import AddWisdomBodyDialog from '@/components/AddWisdomBodyDialog.vue';
import ChatHistoryDialog from '@/components/ChatHistoryDialog.vue';
import DeviceItem from '@/components/DeviceItem.vue';
import HeaderBar from '@/components/HeaderBar.vue';
import VersionFooter from '@/components/VersionFooter.vue';
import featureManager from '@/utils/featureManager';

export default {
  name: 'HomePage',
  components: { DeviceItem, AddWisdomBodyDialog, HeaderBar, VersionFooter, ChatHistoryDialog },
  data() {
    return {
      addDeviceDialogVisible: false,
      devices: [],
      originalDevices: [],
      isSearching: false,
      searchRegex: null,
      isLoading: true,
      skeletonCount: localStorage.getItem('skeletonCount') || 8,
      showChatHistory: false,
      currentAgentId: '',
      currentAgentName: '',
      // Trạng thái chức năng
      featureStatus: {
        voiceprintRecognition: false,
        voiceClone: false,
        knowledgeBase: false
      }
    }
  },

  async mounted() {
    this.fetchAgentList();
    await this.loadFeatureStatus();
  },

  methods: {
    // Tải trạng thái chức năng
    async loadFeatureStatus() {
      await featureManager.waitForInitialization();
      const config = featureManager.getConfig();
      this.featureStatus = {
        voiceprintRecognition: config.voiceprintRecognition,
        voiceClone: config.voiceClone,
        knowledgeBase: config.knowledgeBase
      };
    },
    
    showAddDialog() {
      this.addDeviceDialogVisible = true
    },
    goToRoleConfig() {
      // Sau khi nhấp vào cấu hình vai trò, chuyển đến trang cấu hình vai trò
      this.$router.push('/role-config')
    },
    handleWisdomBodyAdded(res) {
      this.fetchAgentList();
      this.addDeviceDialogVisible = false;
    },
    handleDeviceManage() {
      this.$router.push('/device-management');
    },
    handleSearch(keyword) {
      this.isSearching = true;
      this.isLoading = true;
      // Phát hiện định dạng địa chỉ MAC: chứa 5 dấu hai chấm
      const isMac = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/.test(keyword)
      const searchType = isMac ? 'mac' : 'name';
      Api.agent.searchAgent(keyword, searchType, ({ data }) => {
        if (data?.data) {
          this.devices = data.data.map(item => ({
            ...item,
            agentId: item.id
          }));
        }
        this.isLoading = false;
      }, (error) => {
        console.error('Tìm kiếm tác nhân thất bại:', error);
        this.isLoading = false;
        this.$message.error(this.$t('message.searchFailed'));
      });
    },
    handleSearchReset() {
      this.isSearching = false;
      // Gán trực tiếp danh sách thiết bị gốc cho danh sách thiết bị hiển thị, tránh tải lại dữ liệu
      this.devices = [...this.originalDevices];
    },

    // Cập nhật danh sách tác nhân tìm kiếm
    handleSearchResult(filteredList) {
      this.devices = filteredList; // Cập nhật danh sách thiết bị
    },
    // Lấy danh sách tác nhân
    fetchAgentList() {
      this.isLoading = true;
      Api.agent.getAgentList(({ data }) => {
        if (data?.data) {
          this.originalDevices = data.data.map(item => ({
            ...item,
            agentId: item.id
          }));

          // Đặt động số lượng khung xương (tùy chọn)
          this.skeletonCount = Math.min(
            Math.max(this.originalDevices.length, 3), // Tối thiểu 3
            10 // Tối đa 10
          );

          this.handleSearchReset();
        }
        this.isLoading = false;
      }, (error) => {
        console.error('Failed to fetch agent list:', error);
        this.isLoading = false;
      });
    },
    // Xóa tác nhân
    handleDeleteAgent(agentId) {
      this.$confirm(this.$t('home.confirmDeleteAgent'), 'Thông báo', {
        confirmButtonText: this.$t('button.ok'),
        cancelButtonText: this.$t('button.cancel'),
        type: 'warning'
      }).then(() => {
        Api.agent.deleteAgent(agentId, (res) => {
          if (res.data.code === 0) {
            this.$message.success({
              message: this.$t('home.deleteSuccess'),
              showClose: true
            });
            this.fetchAgentList(); // Làm mới danh sách
          } else {
            this.$message.error({
              message: res.data.msg || this.$t('home.deleteFailed'),
              showClose: true
            });
          }
        });
      }).catch(() => { });
    },
    handleShowChatHistory({ agentId, agentName }) {
      this.currentAgentId = agentId;
      this.currentAgentName = agentName;
      this.showChatHistory = true;
    }
  }
}
</script>

<style scoped>
.welcome {
  min-width: 900px;
  min-height: 506px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, 
    var(--primary-blue-lightest) 0%, 
    #ffffff 25%, 
    #ffffff 75%, 
    var(--primary-orange-lightest) 100%);
  background-attachment: fixed;
  background-size: cover;
  background-position: center;
  -webkit-background-size: cover;
  -o-background-size: cover;
}

.add-device {
  padding-bottom: 10px;
  border-radius: var(--radius-md);
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg,
      var(--primary-blue-lightest) 0%,
      var(--primary-blue-lighter) 50%,
      var(--primary-orange-lighter) 100%);
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-base);
  
  &:hover {
    box-shadow: var(--shadow-xl);
    transform: translateY(-2px);
  }
}

.add-device-bg {
  width: 100%;
  height: 100%;
  text-align: left;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  -webkit-background-size: cover;
  -o-background-size: cover;
  box-sizing: border-box;

  .hellow-text {
    margin-left: 75px;
    color: #3d4566;
    font-size: 33px;
    font-weight: 700;
    letter-spacing: 0;
  }

  .hi-hint {
    font-weight: 400;
    font-size: 12px;
    text-align: left;
    color: #818cae;
    margin-left: 75px;
    margin-top: 5px;
  }
}

.add-device-btn {
  display: flex;
  align-items: center;
  margin-left: 75px;
  margin-top: 15px;
  cursor: pointer;
  position: relative;
  height: 34px;

  /* Tạo background chung cho toàn bộ button để đảm bảo gradient liên tục */
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 162px; /* 105 + 23 + 34 */
    height: 34px;
    background: linear-gradient(135deg, #4A90E2 0%, #FF6B35 100%);
    border-radius: 6px;
    z-index: 0;
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
    transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  &:hover::before {
    box-shadow: 0 8px 24px rgba(74, 144, 226, 0.3);
  }

  .left-add {
    width: 105px;
    height: 34px;
    border-radius: 6px 0 0 6px;
    background: transparent;
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    line-height: 34px;
    transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    position: relative;
    z-index: 1;
    border: none;
    
    &:hover {
      transform: translateX(2px);
    }
  }

  .button-connector {
    width: 23px;
    height: 34px;
    background: transparent;
    margin-left: -10px;
    z-index: 1;
    position: relative;
    flex-shrink: 0;
  }

  .right-add {
    width: 34px;
    height: 34px;
    border-radius: 0 6px 6px 0;
    background: transparent;
    margin-left: -6px;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    z-index: 2;
    position: relative;
    flex-shrink: 0;
    
    i {
      font-size: 20px;
      color: #fff;
      transition: transform 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    &:hover {
      i {
        transform: translateX(2px) rotate(5deg);
      }
    }
  }
}

.device-list-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--spacing-6);
  padding: var(--spacing-6) 0;
}

/* Trong style của DeviceItem.vue */
.device-item {
  margin: 0 !important;
  /* Tránh xung đột */
  width: auto !important;
}

.footer {
  font-size: 12px;
  font-weight: 400;
  margin-top: auto;
  padding-top: 30px;
  color: #979db1;
  text-align: center;
  /* Hiển thị ở giữa */
}

/* Hoạt ảnh khung xương */
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

.skeleton-item {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  height: 120px;
  position: relative;
  overflow: hidden;
  margin-bottom: 20px;
}

.skeleton-image {
  width: 80px;
  height: 80px;
  background: #f0f2f5;
  border-radius: 4px;
  float: left;
  position: relative;
  overflow: hidden;
}

.skeleton-content {
  margin-left: 100px;
}

.skeleton-line {
  height: 16px;
  background: #f0f2f5;
  border-radius: 4px;
  margin-bottom: 12px;
  width: 70%;
  position: relative;
  overflow: hidden;
}

.skeleton-line-short {
  height: 12px;
  background: #f0f2f5;
  border-radius: 4px;
  width: 50%;
}

.skeleton-item::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg,
      rgba(255, 255, 255, 0),
      rgba(255, 255, 255, 0.3),
      rgba(255, 255, 255, 0));
  animation: shimmer 1.5s infinite;
}
</style>