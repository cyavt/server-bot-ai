<template>
  <el-header class="header">
    <div class="header-container">
      <!-- Phần tử bên trái -->
      <div class="header-left" @click="goHome">
        <img loading="lazy" alt="" src="@/assets/windify.png" class="logo-img" />
      </div>

      <!-- Menu điều hướng ở giữa -->
      <div class="header-center">
        <div class="equipment-management" :class="{
          'active-tab':
            $route.path === '/home' ||
            $route.path === '/role-config' ||
            $route.path === '/device-management',
        }" @click="goHome">
          <img loading="lazy" alt="" src="@/assets/header/robot.png" :style="{
            filter:
              $route.path === '/home' ||
                $route.path === '/role-config' ||
                $route.path === '/device-management'
                ? 'brightness(0) invert(1)'
                : 'None',
          }" />
          <span class="nav-text">{{ $t("header.smartManagement") }}</span>
        </div>
        <!-- Người dùng thông thường hiển thị nhân bản âm sắc -->
        <div v-if="!isSuperAdmin && featureStatus.voiceClone" class="equipment-management"
          :class="{ 'active-tab': $route.path === '/voice-clone-management' }" @click="goVoiceCloneManagement">
          <img loading="lazy" alt="" src="@/assets/header/voice.png" :style="{
            filter:
              $route.path === '/voice-clone-management'
                ? 'brightness(0) invert(1)'
                : 'None',
          }" />
          <span class="nav-text">{{ $t("header.voiceCloneManagement") }}</span>
        </div>

        <!-- Quản trị viên siêu cấp hiển thị menu thả xuống nhân bản âm sắc -->
        <el-dropdown v-if="isSuperAdmin && featureStatus.voiceClone" trigger="click" class="equipment-management more-dropdown" :class="{
          'active-tab':
            $route.path === '/voice-clone-management' ||
            $route.path === '/voice-resource-management',
        }" @visible-change="handleVoiceCloneDropdownVisibleChange">
          <span class="el-dropdown-link">
            <img loading="lazy" alt="" src="@/assets/header/voice.png" :style="{
              filter:
                $route.path === '/voice-clone-management' ||
                  $route.path === '/voice-resource-management'
                  ? 'brightness(0) invert(1)'
                  : 'None',
            }" />
            <span class="nav-text">{{ $t("header.voiceCloneManagement") }}</span>
            <i class="el-icon-arrow-down el-icon--right" :class="{ 'rotate-down': voiceCloneDropdownVisible }"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item @click.native="goVoiceCloneManagement">
              {{ $t("header.voiceCloneManagement") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goVoiceResourceManagement">
              {{ $t("header.voiceResourceManagement") }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>

        <div v-if="isSuperAdmin" class="equipment-management" :class="{ 'active-tab': $route.path === '/model-config' }"
          @click="goModelConfig">
          <img loading="lazy" alt="" src="@/assets/header/model_config.png" :style="{
            filter:
              $route.path === '/model-config' ? 'brightness(0) invert(1)' : 'None',
          }" />
          <span class="nav-text">{{ $t("header.modelConfig") }}</span>
        </div>
        <div v-if="featureStatus.knowledgeBase" class="equipment-management"
          :class="{ 'active-tab': $route.path === '/knowledge-base-management' || $route.path === '/knowledge-file-upload' }"
          @click="goKnowledgeBaseManagement">
          <img loading="lazy" alt="" src="@/assets/header/knowledge_base.png" :style="{
            filter:
              $route.path === '/knowledge-base-management' || $route.path === '/knowledge-file-upload' ? 'brightness(0) invert(1)' : 'None',
          }" />
          <span class="nav-text">{{ $t("header.knowledgeBase") }}</span>
        </div>
        <el-dropdown v-if="isSuperAdmin" trigger="click" class="equipment-management more-dropdown" :class="{
          'active-tab':
            $route.path === '/dict-management' ||
            $route.path === '/params-management' ||
            $route.path === '/provider-management' ||
            $route.path === '/server-side-management' ||
            $route.path === '/agent-template-management' ||
            $route.path === '/ota-management' ||
            $route.path === '/user-management' ||
            $route.path === '/feature-management',
        }" @visible-change="handleParamDropdownVisibleChange">
          <span class="el-dropdown-link">
            <img loading="lazy" alt="" src="@/assets/header/param_management.png" :style="{
              filter:
                $route.path === '/dict-management' ||
                  $route.path === '/params-management' ||
                  $route.path === '/provider-management' ||
                  $route.path === '/server-side-management' ||
                  $route.path === '/agent-template-management' ||
                  $route.path === '/ota-management' ||
                  $route.path === '/user-management' ||
                  $route.path === '/feature-management'
                  ? 'brightness(0) invert(1)'
                  : 'None',
            }" />
            <span class="nav-text">{{ $t("header.paramDictionary") }}</span>
            <i class="el-icon-arrow-down el-icon--right" :class="{ 'rotate-down': paramDropdownVisible }"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item @click.native="goParamManagement">
              {{ $t("header.paramManagement") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goUserManagement">
              {{ $t("header.userManagement") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goOtaManagement">
              {{ $t("header.otaManagement") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goDictManagement">
              {{ $t("header.dictManagement") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goProviderManagement">
              {{ $t("header.providerManagement") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goAgentTemplateManagement">
              {{ $t("header.agentTemplate") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goServerSideManagement">
              {{ $t("header.serverSideManagement") }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="goFeatureManagement">
                {{ $t("header.featureManagement") }}
              </el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>

      <!-- Phần tử bên phải -->
      <div class="header-right">
        <div class="search-container" v-if="$route.path === '/home' && !(isSuperAdmin && isSmallScreen)">
          <div class="search-wrapper">
            <el-input v-model="search" :placeholder="$t('header.searchPlaceholder')" class="custom-search-input"
              @keyup.enter.native="handleSearch" @focus="showSearchHistory" @blur="hideSearchHistory" clearable
              ref="searchInput">
              <i slot="suffix" class="el-icon-search search-icon" @click="handleSearch"></i>
            </el-input>
            <!-- Hộp thả xuống lịch sử tìm kiếm -->
            <div v-if="showHistory && searchHistory.length > 0" class="search-history-dropdown">
              <div class="search-history-header">
                <span>{{ $t("header.searchHistory") }}</span>
                <el-button type="text" size="small" class="clear-history-btn" @click="clearSearchHistory">
                  {{ $t("header.clearHistory") }}
                </el-button>
              </div>
              <div class="search-history-list">
                <div v-for="(item, index) in searchHistory" :key="index" class="search-history-item"
                  @click.stop="selectSearchHistory(item)">
                  <span class="history-text">{{ item }}</span>
                  <i class="el-icon-close clear-item-icon" @click.stop="removeSearchHistory(index)"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <img loading="lazy" alt="" src="@/assets/home/avatar.png" class="avatar-img" @click="handleAvatarClick" />
        <span class="el-user-dropdown" @click="handleAvatarClick">
          {{ userInfo.username || "Đang tải..." }}
          <i class="el-icon-arrow-down el-icon--right" :class="{ 'rotate-down': userMenuVisible }"></i>
        </span>
        <el-cascader :options="userMenuOptions" trigger="click" :props="cascaderProps"
          style="width: 0px; overflow: hidden" :show-all-levels="false" @change="handleCascaderChange"
          @visible-change="handleUserMenuVisibleChange" ref="userCascader">
          <template slot-scope="{ data }">
            <span>{{ data.label }}</span>
          </template>
        </el-cascader>
      </div>
    </div>

    <!-- Hộp thoại đổi mật khẩu -->
    <ChangePasswordDialog v-model="isChangePasswordDialogVisible" />
  </el-header>
</template>

<script>
import userApi from "@/apis/module/user";
import i18n, { changeLanguage } from "@/i18n";
import { mapActions, mapGetters } from "vuex";
import ChangePasswordDialog from "./ChangePasswordDialog.vue"; // Nhập component hộp thoại đổi mật khẩu
import featureManager from "@/utils/featureManager"; // Nhập lớp công cụ quản lý chức năng

export default {
  name: "HeaderBar",
  components: {
    ChangePasswordDialog,
  },
  props: ["devices"], // Nhận danh sách thiết bị từ component cha
  data() {
    return {
      search: "",
      userInfo: {
        username: "",
        mobile: "",
      },
      isChangePasswordDialogVisible: false, // Điều khiển hiển thị hộp thoại đổi mật khẩu
      paramDropdownVisible: false,
      voiceCloneDropdownVisible: false,
      userMenuVisible: false, // Thêm trạng thái hiển thị menu người dùng
      isSmallScreen: false,
      // Liên quan đến lịch sử tìm kiếm
      searchHistory: [],
      showHistory: false,
      SEARCH_HISTORY_KEY: "xiaozhi_search_history",
      MAX_HISTORY_COUNT: 3,
      // Cấu hình Cascader
      cascaderProps: {
        expandTrigger: "click",
        value: "value",
        label: "label",
        children: "children",
      },
      // Trạng thái chức năng
      featureStatus: {
        voiceClone: false, // Trạng thái chức năng nhân bản âm sắc
        knowledgeBase: false, // Trạng thái chức năng cơ sở tri thức
      },
    };
  },
  computed: {
    ...mapGetters(["getIsSuperAdmin"]),
    isSuperAdmin() {
      return this.getIsSuperAdmin;
    },
    // Lấy ngôn ngữ hiện tại
    currentLanguage() {
      return i18n.locale || "zh_CN";
    },
    // Lấy văn bản hiển thị của ngôn ngữ hiện tại
    currentLanguageText() {
      const currentLang = this.currentLanguage;
      switch (currentLang) {
        case "zh_CN":
          return this.$t("language.zhCN");
        case "zh_TW":
          return this.$t("language.zhTW");
        case "en":
          return this.$t("language.en");
        case "de":
          return this.$t("language.de");
        case "vi":
          return this.$t("language.vi");
        default:
          return this.$t("language.zhCN");
      }
    },
    // Lấy biểu tượng xiaozhi-ai tương ứng với ngôn ngữ hiện tại
    xiaozhiAiIcon() {
      const currentLang = this.currentLanguage;
      switch (currentLang) {
        case "zh_CN":
          return require("@/assets/xiaozhi-ai.png");
        case "zh_TW":
          return require("@/assets/xiaozhi-ai_zh_TW.png");
        case "en":
          return require("@/assets/xiaozhi-ai_en.png");
        case "de":
          return require("@/assets/xiaozhi-ai_de.png");
        case "vi":
          return require("@/assets/xiaozhi-ai_vi.png");
        default:
          return require("@/assets/xiaozhi-ai.png");
      }
    },
    // Tùy chọn menu người dùng
    userMenuOptions() {
      return [
        {
          label: this.currentLanguageText,
          value: "language",
          children: [
            {
              label: this.$t("language.zhCN"),
              value: "zh_CN",
            },
            {
              label: this.$t("language.zhTW"),
              value: "zh_TW",
            },
            {
              label: this.$t("language.en"),
              value: "en",
            },
            {
              label: this.$t("language.de"),
              value: "de",
            },
            {
              label: this.$t("language.vi"),
              value: "vi",
            },
          ],
        },
        {
          label: this.$t("header.changePassword"),
          value: "changePassword",
        },
        {
          label: this.$t("header.logout"),
          value: "logout",
        },
      ];
    },
  },
  async mounted() {
    this.fetchUserInfo();
    this.checkScreenSize();
    window.addEventListener("resize", this.checkScreenSize);
    // Tải lịch sử tìm kiếm từ localStorage
    this.loadSearchHistory();
    // Đợi featureManager khởi tạo hoàn tất sau đó mới tải trạng thái chức năng
    await this.loadFeatureStatus();
  },
  // Xóa trình lắng nghe sự kiện
  beforeDestroy() {
    window.removeEventListener("resize", this.checkScreenSize);
  },
  methods: {
    goHome() {
      // Chuyển đến trang chủ
      this.$router.push("/home");
    },
    goUserManagement() {
      this.$router.push("/user-management");
    },
    goModelConfig() {
      this.$router.push("/model-config");
    },
    goKnowledgeBaseManagement() {
      this.$router.push("/knowledge-base-management");
    },
    goVoiceCloneManagement() {
      this.$router.push("/voice-clone-management");
    },
    goParamManagement() {
      this.$router.push("/params-management");
    },
    goOtaManagement() {
      this.$router.push("/ota-management");
    },
    goDictManagement() {
      this.$router.push("/dict-management");
    },
    goProviderManagement() {
      this.$router.push("/provider-management");
    },
    goServerSideManagement() {
      this.$router.push("/server-side-management");
    },

    // Chuyển đến quản lý tài nguyên âm sắc
    goVoiceResourceManagement() {
      this.$router.push("/voice-resource-management");
    },
    // Thêm phương thức điều hướng quản lý mẫu vai trò mặc định
    goAgentTemplateManagement() {
      this.$router.push("/agent-template-management");
    },
    // Chuyển đến quản lý chức năng
    goFeatureManagement() {
      this.$router.push("/feature-management");
    },
    // Tải trạng thái chức năng
    async loadFeatureStatus() {
      // Đợi featureManager khởi tạo hoàn tất
      await featureManager.waitForInitialization();
      
      const config = featureManager.getConfig();
      
      this.featureStatus.voiceClone = config.voiceClone;
      this.featureStatus.knowledgeBase = config.knowledgeBase;
    },
    // Lấy thông tin người dùng
    fetchUserInfo() {
      userApi.getUserInfo(({ data }) => {
        this.userInfo = data.data;
        if (data.data.superAdmin !== undefined) {
          this.$store.commit("setUserInfo", data.data);
        }
      });
    },
    checkScreenSize() {
      this.isSmallScreen = window.innerWidth <= 1386;
    },
    // Xử lý tìm kiếm
    handleSearch() {
      const searchValue = this.search.trim();

      // Nếu nội dung tìm kiếm trống, kích hoạt sự kiện đặt lại
      if (!searchValue) {
        this.$emit("search-reset");
        return;
      }

      // Lưu lịch sử tìm kiếm
      this.saveSearchHistory(searchValue);

      // Kích hoạt sự kiện tìm kiếm, truyền từ khóa tìm kiếm cho component cha
      this.$emit("search", searchValue);

      // Sau khi tìm kiếm xong, làm cho ô nhập mất tiêu điểm, từ đó kích hoạt sự kiện blur để ẩn lịch sử tìm kiếm
      if (this.$refs.searchInput) {
        this.$refs.searchInput.blur();
      }
    },

    // Hiển thị lịch sử tìm kiếm
    showSearchHistory() {
      this.showHistory = true;
    },

    // Ẩn lịch sử tìm kiếm
    hideSearchHistory() {
      // Trì hoãn ẩn để sự kiện nhấp có thể thực thi
      setTimeout(() => {
        this.showHistory = false;
      }, 200);
    },

    // Tải lịch sử tìm kiếm
    loadSearchHistory() {
      try {
        const history = localStorage.getItem(this.SEARCH_HISTORY_KEY);
        if (history) {
          this.searchHistory = JSON.parse(history);
        }
      } catch (error) {
        console.error("Tải lịch sử tìm kiếm thất bại:", error);
        this.searchHistory = [];
      }
    },

    // Lưu lịch sử tìm kiếm
    saveSearchHistory(keyword) {
      if (!keyword || this.searchHistory.includes(keyword)) {
        return;
      }

      // Thêm vào đầu lịch sử
      this.searchHistory.unshift(keyword);

      // Giới hạn số lượng lịch sử
      if (this.searchHistory.length > this.MAX_HISTORY_COUNT) {
        this.searchHistory = this.searchHistory.slice(0, this.MAX_HISTORY_COUNT);
      }

      // Lưu vào localStorage
      try {
        localStorage.setItem(this.SEARCH_HISTORY_KEY, JSON.stringify(this.searchHistory));
      } catch (error) {
        console.error("Lưu lịch sử tìm kiếm thất bại:", error);
      }
    },

    // Chọn mục lịch sử tìm kiếm
    selectSearchHistory(keyword) {
      this.search = keyword;
      this.handleSearch();
    },

    // Xóa một mục lịch sử tìm kiếm
    removeSearchHistory(index) {
      this.searchHistory.splice(index, 1);
      try {
        localStorage.setItem(this.SEARCH_HISTORY_KEY, JSON.stringify(this.searchHistory));
      } catch (error) {
        console.error("Cập nhật lịch sử tìm kiếm thất bại:", error);
      }
    },

    // Xóa trống tất cả lịch sử tìm kiếm
    clearSearchHistory() {
      this.searchHistory = [];
      try {
        localStorage.removeItem(this.SEARCH_HISTORY_KEY);
      } catch (error) {
        console.error("Xóa trống lịch sử tìm kiếm thất bại:", error);
      }
    },
    // Hiển thị hộp thoại đổi mật khẩu
    showChangePasswordDialog() {
      this.isChangePasswordDialogVisible = true;
      // Thêm: Đặt lại trạng thái hiển thị menu người dùng sau khi hiển thị hộp thoại đổi mật khẩu
      this.userMenuVisible = false;
    },
    // Đăng xuất
    async handleLogout() {
      try {
        // Gọi action logout của Vuex
        await this.logout();
        this.$message.success({
          message: this.$t("message.success"),
          showClose: true,
        });
      } catch (error) {
        console.error("Đăng xuất thất bại:", error);
        this.$message.error({
          message: this.$t("message.error"),
          showClose: true,
        });
      }
    },
    // Lắng nghe thay đổi trạng thái hiển thị của menu thả xuống từ điển tham số
    handleParamDropdownVisibleChange(visible) {
      this.paramDropdownVisible = visible;
    },

    // Lắng nghe thay đổi trạng thái hiển thị của menu thả xuống nhân bản âm sắc
    handleVoiceCloneDropdownVisibleChange(visible) {
      this.voiceCloneDropdownVisible = visible;
    },
    // Thêm một key vào data để buộc render lại component
    // Xử lý thay đổi lựa chọn Cascader
    handleCascaderChange(value) {
      if (!value || value.length === 0) {
        return;
      }

      const action = value[value.length - 1];

      // Xử lý chuyển đổi ngôn ngữ
      if (value.length === 2 && value[0] === "language") {
        this.changeLanguage(action);
      } else {
        // Xử lý các thao tác khác
        switch (action) {
          case "changePassword":
            this.showChangePasswordDialog();
            break;
          case "logout":
            this.handleLogout();
            break;
        }
      }

      // Xóa trống lựa chọn ngay sau khi thao tác hoàn tất
      setTimeout(() => {
        this.completeResetCascader();
      }, 300);
    },

    // Chuyển đổi ngôn ngữ
    changeLanguage(lang) {
      changeLanguage(lang);
      this.$message.success({
        message: this.$t("message.success"),
        showClose: true,
      });
      // Thêm: Đặt lại trạng thái hiển thị menu người dùng sau khi chuyển đổi ngôn ngữ
      this.userMenuVisible = false;
    },

    // Đặt lại hoàn toàn bộ chọn cấp
    completeResetCascader() {
      if (this.$refs.userCascader) {
        try {
          // Thử tất cả các phương pháp có thể để xóa trống lựa chọn
          // 1. Thử sử dụng phương thức clearValue do component cung cấp
          if (this.$refs.userCascader.clearValue) {
            this.$refs.userCascader.clearValue();
          }

          // 2. Xóa trống trực tiếp các thuộc tính nội bộ
          if (this.$refs.userCascader.$data) {
            this.$refs.userCascader.$data.selectedPaths = [];
            this.$refs.userCascader.$data.displayLabels = [];
            this.$refs.userCascader.$data.inputValue = "";
            this.$refs.userCascader.$data.checkedValue = [];
            this.$refs.userCascader.$data.showAllLevels = false;
          }

          // 3. Thao tác DOM để xóa trạng thái đã chọn
          const menuElement = this.$refs.userCascader.$refs.menu;
          if (menuElement && menuElement.$el) {
            const activeItems = menuElement.$el.querySelectorAll(
              ".el-cascader-node.is-active"
            );
            activeItems.forEach((item) => item.classList.remove("is-active"));

            const checkedItems = menuElement.$el.querySelectorAll(
              ".el-cascader-node.is-checked"
            );
            checkedItems.forEach((item) => item.classList.remove("is-checked"));
          }

          console.log("Cascader values cleared");
        } catch (error) {
          console.error("Xóa trống giá trị đã chọn thất bại:", error);
        }
      }
    },

    // Nhấp vào avatar để kích hoạt menu thả xuống cascader
    handleAvatarClick() {
      if (this.$refs.userCascader) {
        // Chuyển đổi trạng thái hiển thị menu
        this.userMenuVisible = !this.userMenuVisible;

        // Xóa trống giá trị đã chọn khi menu thu gọn
        if (!this.userMenuVisible) {
          this.completeResetCascader();
        }

        // Đặt trực tiếp trạng thái hiển thị/ẩn của menu
        try {
          // Thử sử dụng phương thức toggleDropDownVisible
          this.$refs.userCascader.toggleDropDownVisible(this.userMenuVisible);
        } catch (error) {
          // Nếu phương thức toggle thất bại, thử đặt trực tiếp thuộc tính
          if (this.$refs.userCascader.$refs.menu) {
            this.$refs.userCascader.$refs.menu.showMenu(this.userMenuVisible);
          } else {
            console.error("Cannot access menu component");
          }
        }
      }
    },

    // Xử lý thay đổi khả năng hiển thị menu người dùng
    handleUserMenuVisibleChange(visible) {
      this.userMenuVisible = visible;

      // Nếu menu đã đóng, cũng xóa trống giá trị đã chọn
      if (!visible) {
        this.completeResetCascader();
      }
    },

    // Sử dụng mapActions để nhập action logout của Vuex
    ...mapActions(["logout"]),
  },
};
</script>

<style lang="scss" scoped>
.header {
  background: #f6fcfe66;
  border: 1px solid #fff;
  height: 63px !important;
  min-width: 900px;
  /* Đặt chiều rộng tối thiểu để tránh nén quá mức */
  overflow: visible;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 120px;
  cursor: pointer;
}

.logo-img {
  width: 200px;
  object-fit: contain;
}

.brand-img {
  height: 20px;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 25px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 300px;
  justify-content: flex-end;
}

.equipment-management {
  height: 30px;
  border-radius: 15px;
  background: #deeafe;
  display: flex;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  gap: 7px;
  color: #3d4566;
  margin-left: 1px;
  align-items: center;
  transition: all 0.3s ease;
  cursor: pointer;
  flex-shrink: 0;
  /* Ngăn nút điều hướng bị nén */
  padding: 0 15px;
  position: relative;
}

.equipment-management.active-tab {
  background: #5778ff !important;
  color: #fff !important;
}

.equipment-management img {
  width: 15px;
  height: 13px;
}

.search-container {
  margin-right: 5px;
  flex: 0.9;
  min-width: 60px;
  max-width: none;
}

.search-wrapper {
  position: relative;
}

.search-history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e4e6ef;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 2px;
}

.search-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 12px;
  color: #909399;
}

.clear-history-btn {
  color: #909399;
  font-size: 11px;
  padding: 0;
  height: auto;
}

.clear-history-btn:hover {
  color: #606266;
}

.search-history-list {
  max-height: 200px;
  overflow-y: auto;
}

.search-history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 12px;
  color: #606266;
}

.search-history-item:hover {
  background-color: #f5f7fa;
}

.clear-item-icon {
  font-size: 10px;
  color: #909399;
  visibility: hidden;
}
.more-dropdown {
  padding: 0;
}
.more-dropdown .el-dropdown-link {
  display: flex;
  align-items: center;
  gap: 7px;
  height: 100%;
  padding: 0 15px;
}

.search-history-item:hover .clear-item-icon {
  visibility: visible;
}

.clear-item-icon:hover {
  color: #ff4949;
}

.custom-search-input>>>.el-input__inner {
  height: 18px;
  border-radius: 9px;
  background-color: #fff;
  border: 1px solid #e4e6ef;
  padding-left: 8px;
  font-size: 9px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  width: 100%;
}

.search-icon {
  cursor: pointer;
  color: #909399;
  margin-right: 3px;
  font-size: 9px;
  line-height: 18px;
}

.custom-search-input::v-deep .el-input__suffix-inner {
  display: flex;
  align-items: center;
  height: 100%;
}

.avatar-img {
  width: 21px;
  height: 21px;
  flex-shrink: 0;
  cursor: pointer;
}
.el-user-dropdown {
  cursor: pointer;
}

/* Kiểu văn bản điều hướng - Hỗ trợ xuống dòng cho tiếng Trung và tiếng Anh */
.nav-text {
  white-space: normal;
  text-align: center;
  max-width: 80px;
  line-height: 1.2;
}

/* Điều chỉnh responsive */
@media (max-width: 1200px) {
  .header-center {
    gap: 14px;
  }

  .equipment-management {
    width: 79px;
    font-size: 9px;
  }
}

.equipment-management.more-dropdown {
  position: relative;
}

.equipment-management.more-dropdown .el-dropdown-menu {
  position: absolute;
  right: 0;
  min-width: 120px;
  margin-top: 5px;
}

.el-dropdown-menu__item {
  min-width: 60px;
  padding: 8px 20px;
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

/* Thêm kiểu xoay tam giác ngược */
.rotate-down {
  transform: rotate(180deg);
  transition: transform 0.3s ease;
}

.el-icon-arrow-down {
  transition: transform 0.3s ease;
}
</style>
