// UI controller module
import { loadConfig, saveConfig } from '../config/manager.js?v=0205';
import { getAudioPlayer } from '../core/audio/player.js?v=0205';
import { getAudioRecorder } from '../core/audio/recorder.js?v=0205';
import { getWebSocketHandler } from '../core/network/websocket.js?v=0205';

// UI controller class
class UIController {
    constructor() {
        this.isEditing = false;
        this.visualizerCanvas = null;
        this.visualizerContext = null;
        this.audioStatsTimer = null;
        this.currentBackgroundIndex = localStorage.getItem('backgroundIndex') ? parseInt(localStorage.getItem('backgroundIndex')) : 0;
        this.backgroundImages = ['1.png', '2.png', '3.png'];
        this.dialBtnDisabled = false;

        // Bind methods
        this.init = this.init.bind(this);
        this.initEventListeners = this.initEventListeners.bind(this);
        this.updateDialButton = this.updateDialButton.bind(this);
        this.addChatMessage = this.addChatMessage.bind(this);
        this.switchBackground = this.switchBackground.bind(this);
        this.switchLive2DModel = this.switchLive2DModel.bind(this);
        this.showModal = this.showModal.bind(this);
        this.hideModal = this.hideModal.bind(this);
        this.switchTab = this.switchTab.bind(this);
    }

    // Initialize
    init() {
        console.log('UIController init started');

        this.visualizerCanvas = document.getElementById('audioVisualizer');
        if (this.visualizerCanvas) {
            this.visualizerContext = this.visualizerCanvas.getContext('2d');
            this.initVisualizer();
        }

        // Check if connect button exists during initialization
        const connectBtn = document.getElementById('connectBtn');
        console.log('connectBtn during init:', connectBtn);

        this.initEventListeners();
        this.startAudioStatsMonitor();
        loadConfig();

        // Register recording callback
        const audioRecorder = getAudioRecorder();
        audioRecorder.onRecordingStart = (seconds) => {
            this.updateRecordButtonState(true, seconds);
        };

        // Initialize status display
        this.updateConnectionUI(false);
        // Apply saved background
        const backgroundContainer = document.querySelector('.background-container');
        if (backgroundContainer) {
            backgroundContainer.style.backgroundImage = `url('./images/${this.backgroundImages[this.currentBackgroundIndex]}')`;
        }

        this.updateDialButton(false);

        console.log('UIController init completed');
    }

    // Initialize visualizer
    initVisualizer() {
        if (this.visualizerCanvas) {
            this.visualizerCanvas.width = this.visualizerCanvas.clientWidth;
            this.visualizerCanvas.height = this.visualizerCanvas.clientHeight;
            this.visualizerContext.fillStyle = '#fafafa';
            this.visualizerContext.fillRect(0, 0, this.visualizerCanvas.width, this.visualizerCanvas.height);
        }
    }

    // Initialize event listeners
    initEventListeners() {
        // Settings button
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                this.showModal('settingsModal');
            });
        }

        // Background switch button
        const backgroundBtn = document.getElementById('backgroundBtn');
        if (backgroundBtn) {
            backgroundBtn.addEventListener('click', this.switchBackground);
        }

        // Model select change event
        const modelSelect = document.getElementById('live2dModelSelect');
        if (modelSelect) {
            modelSelect.addEventListener('change', () => {
                this.switchLive2DModel();
            });
        }

        // Dial button
        const dialBtn = document.getElementById('dialBtn');
        if (dialBtn) {
            dialBtn.addEventListener('click', () => {
                dialBtn.disabled = true;
                this.dialBtnDisabled = true;
                setTimeout(() => {
                    dialBtn.disabled = false;
                    this.dialBtnDisabled = false;
                }, 3000);

                const wsHandler = getWebSocketHandler();
                const isConnected = wsHandler.isConnected();

                if (isConnected) {
                    wsHandler.disconnect();
                    this.updateDialButton(false);
                    this.addChatMessage('Disconnected, see you next time~😊', false);
                } else {
                    // Check if OTA URL is filled
                    const otaUrlInput = document.getElementById('otaUrl');
                    if (!otaUrlInput || !otaUrlInput.value.trim()) {
                        // If OTA URL is not filled, show settings modal and switch to device tab
                        this.showModal('settingsModal');
                        this.switchTab('device');
                        this.addChatMessage('Please fill in OTA server URL', false);
                        return;
                    }

                    // Start connection process
                    this.handleConnect();
                }
            });
        }

        // Camera button
        const cameraBtn = document.getElementById('cameraBtn');
        let cameraTimer = null;
        if (cameraBtn) {
            cameraBtn.addEventListener('click', () => {
                if (cameraTimer) {
                    clearTimeout(cameraTimer);
                    cameraTimer = null;
                }
                cameraTimer = setTimeout(() => {
                    const cameraContainer = document.getElementById('cameraContainer');
                    if (!cameraContainer) {
                        log('Container camera không tồn tại', 'warning');
                        return;
                    }

                    const isActive = cameraContainer.classList.contains('active');
                    if (isActive) {
                        // Đóng camera
                        if (typeof window.stopCamera === 'function') {
                            window.stopCamera();
                        }
                        cameraContainer.classList.remove('active');
                        cameraBtn.classList.remove('camera-active');
                        cameraBtn.querySelector('.btn-text').textContent = 'Camera';
                        log('Camera đã đóng', 'info');
                    } else {
                        // Mở camera
                        if (typeof window.startCamera === 'function') {
                            window.startCamera().then(success => {
                                if (success) {
                                    cameraBtn.classList.add('camera-active');
                                    cameraBtn.querySelector('.btn-text').textContent = 'Đóng';
                                } else {
                                    this.addChatMessage('⚠️ Khởi động camera thất bại, vui lòng kiểm tra quyền trình duyệt', false);
                                }
                            }).catch(error => {
                                log(`Khởi động camera bất thường: ${error.message}`, 'error');
                            });
                        } else {
                            log('Hàm startCamera chưa được định nghĩa', 'warning');
                        }
                    }
                }, 300);
            });
        }

        // Record button
        const recordBtn = document.getElementById('recordBtn');
        if (recordBtn) {
            let recordTimer = null;
            recordBtn.addEventListener('click', () => {
                if (recordTimer) {
                    clearTimeout(recordTimer);
                    recordTimer = null;
                }
                recordTimer = setTimeout(() => {
                    const audioRecorder = getAudioRecorder();
                    if (audioRecorder.isRecording) {
                        audioRecorder.stop();
                        // Khôi phục nút ghi âm về trạng thái bình thường
                        recordBtn.classList.remove('recording');
                        recordBtn.querySelector('.btn-text').textContent = 'Ghi âm';
                    } else {
                        // Cập nhật trạng thái nút sang đang ghi âm
                        recordBtn.classList.add('recording');
                        recordBtn.querySelector('.btn-text').textContent = 'Đang ghi âm';

                        // Start recording, update button state after delay
                        setTimeout(() => {
                            audioRecorder.start();
                        }, 100);
                    }
                }, 300);
            });
        }

        // Chat input event listener
        const chatIpt = document.getElementById('chatIpt');
        if (chatIpt) {
            const wsHandler = getWebSocketHandler();
            chatIpt.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    if (e.target.value) {
                        wsHandler.sendTextMessage(e.target.value);
                        e.target.value = '';
                        return;
                    }
                }
            });
        }

        // Close button
        const closeButtons = document.querySelectorAll('.close-btn');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const modal = e.target.closest('.modal');
                if (modal) {
                    if (modal.id === 'settingsModal') {
                        saveConfig();
                    }
                    this.hideModal(modal.id);
                }
            });
        });

        // Settings tab switch
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Nhấp vào nền modal để đóng (chỉ vô hiệu hóa chức năng này cho các modal cụ thể)
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    // settingsModal、mcpToolModal、mcpPropertyModal chỉ có thể đóng bằng cách nhấp vào X
                    const nonClosableModals = ['settingsModal', 'mcpToolModal', 'mcpPropertyModal'];
                    if (nonClosableModals.includes(modal.id)) {
                        return; // Cấm nhấp vào nền để đóng
                    }
                    this.hideModal(modal.id);
                }
            });
        });

        // Add MCP tool button
        const addMCPToolBtn = document.getElementById('addMCPToolBtn');
        if (addMCPToolBtn) {
            addMCPToolBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.addMCPTool();
            });
        }

        // Connect button and send button are not removed, can be added to dial button later
    }

    // Update connection status UI
    updateConnectionUI(isConnected) {
        const connectionStatus = document.getElementById('connectionStatus');
        const statusDot = document.querySelector('.status-dot');

        if (connectionStatus) {
            if (isConnected) {
                connectionStatus.textContent = 'Đã kết nối';
                if (statusDot) {
                    statusDot.className = 'status-dot status-connected';
                }
            } else {
                connectionStatus.textContent = 'Ngoại tuyến';
                if (statusDot) {
                    statusDot.className = 'status-dot status-disconnected';
                }
            }
        }
    }

    // Update dial button state
    updateDialButton(isConnected) {
        const dialBtn = document.getElementById('dialBtn');
        const recordBtn = document.getElementById('recordBtn');
        const cameraBtn = document.getElementById('cameraBtn');

        if (dialBtn) {
            if (isConnected) {
                dialBtn.classList.add('dial-active');
                dialBtn.querySelector('.btn-text').textContent = 'Ngắt kết nối';
                // Cập nhật icon nút quay số thành icon ngắt kết nối
                dialBtn.querySelector('svg').innerHTML = `
                    <path d="M12,9C10.4,9 9,10.4 9,12C9,13.6 10.4,15 12,15C13.6,15 15,13.6 15,12C15,10.4 13.6,9 12,9M12,17C9.2,17 7,14.8 7,12C7,9.2 9.2,7 12,7C14.8,7 17,9.2 17,12C17,14.8 14.8,17 12,17M12,4.5C7,4.5 2.7,7.6 1,12C2.7,16.4 7,19.5 12,19.5C17,19.5 21.3,16.4 23,12C21.3,7.6 17,4.5 12,4.5Z"/>
                `;
            } else {
                dialBtn.classList.remove('dial-active');
                dialBtn.querySelector('.btn-text').textContent = 'Quay số';
                // Khôi phục icon nút quay số
                dialBtn.querySelector('svg').innerHTML = `
                    <path d="M6.62,10.79C8.06,13.62 10.38,15.94 13.21,17.38L15.41,15.18C15.69,14.9 16.08,14.82 16.43,14.93C17.55,15.3 18.75,15.5 20,15.5A1,1 0 0,1 21,16.5V20A1,1 0 0,1 20,21A17,17 0 0,1 3,4A1,1 0 0,1 4,3H7.5A1,1 0 0,1 8.5,4C8.5,5.25 8.7,6.45 9.07,7.57C9.18,7.92 9.1,8.31 8.82,8.59L6.62,10.79Z"/>
                `;
            }
        }

        // Cập nhật trạng thái nút camera - đặt lại về mặc định khi ngắt kết nối
        if (cameraBtn && !isConnected) {
            const cameraContainer = document.getElementById('cameraContainer');
            if (cameraContainer && cameraContainer.classList.contains('active')) {
                cameraContainer.classList.remove('active');
            }
            cameraBtn.classList.remove('camera-active');
            cameraBtn.querySelector('.btn-text').textContent = 'Camera';
            cameraBtn.disabled = true;
            cameraBtn.title = 'Vui lòng kết nối máy chủ trước';
            // Đóng camera
            if (typeof window.stopCamera === 'function') {
                window.stopCamera();
            }
        }

        // Cập nhật trạng thái nút camera - bật khi đã kết nối và camera khả dụng
        if (cameraBtn && isConnected) {
            if (window.cameraAvailable) {
                cameraBtn.disabled = false;
                cameraBtn.title = 'Mở/Đóng camera';
            } else {
                cameraBtn.disabled = true;
                cameraBtn.title = 'Vui lòng liên kết mã xác thực trước';
            }
        }

        // Cập nhật trạng thái nút ghi âm
        if (recordBtn) {
            const microphoneAvailable = window.microphoneAvailable !== false;
            if (isConnected && microphoneAvailable) {
                recordBtn.disabled = false;
                recordBtn.title = 'Bắt đầu ghi âm';
                // Khôi phục nút ghi âm về trạng thái bình thường
                recordBtn.querySelector('.btn-text').textContent = 'Ghi âm';
                recordBtn.classList.remove('recording');
            } else {
                recordBtn.disabled = true;
                if (!microphoneAvailable) {
                    recordBtn.title = window.isHttpNonLocalhost ? 'Hiện tại do truy cập http, không thể ghi âm, chỉ có thể tương tác bằng văn bản' : 'Microphone không khả dụng';
                } else {
                    recordBtn.title = 'Vui lòng kết nối máy chủ trước';
                }
                // Khôi phục nút ghi âm về trạng thái bình thường
                recordBtn.querySelector('.btn-text').textContent = 'Ghi âm';
                recordBtn.classList.remove('recording');
            }
        }
    }

    // Cập nhật trạng thái nút ghi âm
    updateRecordButtonState(isRecording, seconds = 0) {
        const recordBtn = document.getElementById('recordBtn');
        if (recordBtn) {
            if (isRecording) {
                recordBtn.querySelector('.btn-text').textContent = `Đang ghi âm`;
                recordBtn.classList.add('recording');
            } else {
                recordBtn.querySelector('.btn-text').textContent = 'Ghi âm';
                recordBtn.classList.remove('recording');
            }
            // Chỉ bật nút khi microphone khả dụng
            recordBtn.disabled = window.microphoneAvailable === false;
        }
    }

    /**
     * Update microphone availability state
     * @param {boolean} isAvailable - Whether microphone is available
     * @param {boolean} isHttpNonLocalhost - Whether it is HTTP non-localhost access
     */
    updateMicrophoneAvailability(isAvailable, isHttpNonLocalhost) {
        const recordBtn = document.getElementById('recordBtn');
        if (!recordBtn) return;
        if (!isAvailable) {
            // Vô hiệu hóa nút ghi âm
            recordBtn.disabled = true;
            // Cập nhật văn bản và tiêu đề nút
            recordBtn.querySelector('.btn-text').textContent = 'Ghi âm';
            recordBtn.title = isHttpNonLocalhost ? 'Hiện tại do truy cập http, không thể ghi âm, chỉ có thể tương tác bằng văn bản' : 'Microphone không khả dụng';

        } else {
            // Nếu đã kết nối, bật nút ghi âm
            const wsHandler = getWebSocketHandler();
            if (wsHandler && wsHandler.isConnected()) {
                recordBtn.disabled = false;
                recordBtn.title = 'Bắt đầu ghi âm';
            }
        }
    }

    // Add chat message
    addChatMessage(content, isUser = false) {
        const chatStream = document.getElementById('chatStream');
        if (!chatStream) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user' : 'ai'}`;
        messageDiv.innerHTML = `<div class="message-bubble">${content}</div>`;
        chatStream.appendChild(messageDiv);

        // Scroll to bottom
        chatStream.scrollTop = chatStream.scrollHeight;
    }

    // Switch background
    switchBackground() {
        this.currentBackgroundIndex = (this.currentBackgroundIndex + 1) % this.backgroundImages.length;
        const backgroundContainer = document.querySelector('.background-container');
        if (backgroundContainer) {
            backgroundContainer.style.backgroundImage = `url('./images/${this.backgroundImages[this.currentBackgroundIndex]}')`;
        }
        localStorage.setItem('backgroundIndex', this.currentBackgroundIndex);
    }

    // Chuyển đổi mô hình Live2D
    switchLive2DModel() {
        const modelSelect = document.getElementById('live2dModelSelect');
        if (!modelSelect) {
            console.error('Hộp chọn mô hình không tồn tại');
            return;
        }

        const selectedModel = modelSelect.value;
        const app = window.chatApp;

        if (app && app.live2dManager) {
            app.live2dManager.switchModel(selectedModel)
                .then(success => {
                    if (success) {
                        this.addChatMessage(`Đã chuyển sang mô hình: ${selectedModel}`, false);
                    } else {
                        this.addChatMessage('Chuyển đổi mô hình thất bại', false);
                    }
                })
                .catch(error => {
                    console.error('Lỗi chuyển đổi mô hình:', error);
                    this.addChatMessage('Lỗi chuyển đổi mô hình', false);
                });
        } else {
            this.addChatMessage('Trình quản lý Live2D chưa được khởi tạo', false);
        }
    }

    // Show modal
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    // Hide modal
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Switch tab
    switchTab(tabName) {
        // Remove active class from all tabs
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));

        // Activate selected tab
        const activeTabBtn = document.querySelector(`[data-tab="${tabName}"]`);
        const activeTabContent = document.getElementById(`${tabName}Tab`);

        if (activeTabBtn && activeTabContent) {
            activeTabBtn.classList.add('active');
            activeTabContent.classList.add('active');
        }
    }

    // Bắt đầu phiên chat AI sau khi kết nối
    startAIChatSession() {
        this.addChatMessage('Kết nối thành công, bắt đầu trò chuyện nhé~😊', false);
        // Kiểm tra tính khả dụng của microphone và hiển thị thông báo lỗi nếu cần
        if (!window.microphoneAvailable) {
            if (window.isHttpNonLocalhost) {
                this.addChatMessage('⚠️ Hiện tại do truy cập http, không thể ghi âm, chỉ có thể tương tác bằng văn bản', false);
            } else {
                this.addChatMessage('⚠️ Microphone không khả dụng, vui lòng kiểm tra cài đặt quyền, chỉ có thể tương tác bằng văn bản', false);
            }
        }
        // Chỉ bắt đầu ghi âm nếu microphone khả dụng
        if (window.microphoneAvailable) {
            const recordBtn = document.getElementById('recordBtn');
            if (recordBtn) {
                recordBtn.click();
            }
        }
        // Chỉ khởi động camera nếu camera khả dụng (đã liên kết với mã xác thực)
        if (window.cameraAvailable && typeof window.startCamera === 'function') {
            window.startCamera().then(success => {
                if (success) {
                    const cameraBtn = document.getElementById('cameraBtn');
                    if (cameraBtn) {
                        cameraBtn.classList.add('camera-active');
                        cameraBtn.querySelector('.btn-text').textContent = 'Đóng';
                    }
                } else {
                    this.addChatMessage('⚠️ Khởi động camera thất bại, có thể bị trình duyệt từ chối', false);
                }
            }).catch(error => {
                log(`Khởi động camera bất thường: ${error.message}`, 'error');
            });
        }
    }

    // Handle connect button click
    async handleConnect() {
        console.log('handleConnect called');

        // Switch to device settings tab
        this.switchTab('device');

        // Wait for DOM update
        await new Promise(resolve => setTimeout(resolve, 50));

        const otaUrlInput = document.getElementById('otaUrl');

        console.log('otaUrl element:', otaUrlInput);

        if (!otaUrlInput || !otaUrlInput.value) {
            this.addChatMessage('Vui lòng nhập địa chỉ máy chủ OTA', false);
            return;
        }

        const otaUrl = otaUrlInput.value;
        console.log('otaUrl value:', otaUrl);

        // Cập nhật trạng thái nút quay số sang đang kết nối
        const dialBtn = document.getElementById('dialBtn');
        if (dialBtn) {
            dialBtn.classList.add('dial-active');
            dialBtn.querySelector('.btn-text').textContent = 'Đang kết nối...';
            dialBtn.disabled = true;
        }

        // Hiển thị thông báo đang kết nối
        this.addChatMessage('Đang kết nối máy chủ...', false);

        const chatIpt = document.getElementById('chatIpt');
        if (chatIpt) {
            chatIpt.style.display = 'flex';
        }

        try {

            // Get WebSocket handler instance
            const wsHandler = getWebSocketHandler();

            // Register connection state callback BEFORE connecting
            wsHandler.onConnectionStateChange = (isConnected) => {
                this.updateConnectionUI(isConnected);
                this.updateDialButton(isConnected);
            };

            // Register chat message callback BEFORE connecting
            wsHandler.onChatMessage = (text, isUser) => {
                this.addChatMessage(text, isUser);
            };

            // Đăng ký callback trạng thái nút ghi âm TRƯỚC KHI kết nối
            wsHandler.onRecordButtonStateChange = (isRecording) => {
                const recordBtn = document.getElementById('recordBtn');
                if (recordBtn) {
                    if (isRecording) {
                        recordBtn.classList.add('recording');
                        recordBtn.querySelector('.btn-text').textContent = 'Đang ghi âm';
                    } else {
                        recordBtn.classList.remove('recording');
                        recordBtn.querySelector('.btn-text').textContent = 'Ghi âm';
                    }
                }
            };

            const isConnected = await wsHandler.connect();

            if (isConnected) {
                // Kiểm tra tính khả dụng của microphone (kiểm tra lại sau khi kết nối)
                const { checkMicrophoneAvailability } = await import('../core/audio/recorder.js?v=0205');
                const micAvailable = await checkMicrophoneAvailability();

                if (!micAvailable) {
                    const isHttp = window.isHttpNonLocalhost;
                    if (isHttp) {
                        this.addChatMessage('⚠️ Hiện tại do truy cập http, không thể ghi âm, chỉ có thể tương tác bằng văn bản', false);
                    }
                    // Cập nhật trạng thái toàn cục
                    window.microphoneAvailable = false;
                }

                // Cập nhật trạng thái nút quay số
                const dialBtn = document.getElementById('dialBtn');
                if (dialBtn) {
                    if (!this.dialBtnDisabled) {
                        dialBtn.disabled = false;
                    }
                    dialBtn.querySelector('.btn-text').textContent = 'Ngắt kết nối';
                    dialBtn.classList.add('dial-active');
                }

                this.hideModal('settingsModal');
            } else {
                throw new Error('Kết nối OTA thất bại');
            }
        } catch (error) {
            console.error('Connection error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });

            // Hiển thị thông báo lỗi
            const errorMessage = error.message.includes('Cannot set properties of null')
                ? 'Kết nối thất bại: Vui lòng kiểm tra kết nối thiết bị'
                : `Kết nối thất bại: ${error.message}`;

            this.addChatMessage(errorMessage, false);

            // Khôi phục trạng thái nút quay số
            const dialBtn = document.getElementById('dialBtn');
            if (dialBtn) {
                if (!this.dialBtnDisabled) {
                    dialBtn.disabled = false;
                }
                dialBtn.querySelector('.btn-text').textContent = 'Quay số';
                dialBtn.classList.remove('dial-active');
                console.log('Dial button state restored successfully');
            }
        }
    }

    // Add MCP tool
    addMCPTool() {
        const mcpToolsList = document.getElementById('mcpToolsList');
        if (!mcpToolsList) return;

        const toolId = `mcp-tool-${Date.now()}`;
        const toolDiv = document.createElement('div');
        toolDiv.className = 'properties-container';
        toolDiv.innerHTML = `
            <div class="property-item">
                <input type="text" placeholder="Tên công cụ" value="Công cụ mới">
                <input type="text" placeholder="Mô tả công cụ" value="Mô tả công cụ">
                <button class="remove-property" onclick="uiController.removeMCPTool('${toolId}')">Xóa</button>
            </div>
        `;

        mcpToolsList.appendChild(toolDiv);
    }

    // Remove MCP tool
    removeMCPTool(toolId) {
        const toolElement = document.getElementById(toolId);
        if (toolElement) {
            toolElement.remove();
        }
    }

    // Update audio statistics display
    updateAudioStats() {
        const audioPlayer = getAudioPlayer();
        if (!audioPlayer) return;

        const stats = audioPlayer.getAudioStats();
        // Here can add audio statistics UI update logic
    }

    // Start audio statistics monitor
    startAudioStatsMonitor() {
        // Update audio statistics every 100ms
        this.audioStatsTimer = setInterval(() => {
            this.updateAudioStats();
        }, 100);
    }

    // Stop audio statistics monitor
    stopAudioStatsMonitor() {
        if (this.audioStatsTimer) {
            clearInterval(this.audioStatsTimer);
            this.audioStatsTimer = null;
        }
    }

    // Draw audio visualizer waveform
    drawVisualizer(dataArray) {
        if (!this.visualizerContext || !this.visualizerCanvas) return;

        this.visualizerContext.fillStyle = '#fafafa';
        this.visualizerContext.fillRect(0, 0, this.visualizerCanvas.width, this.visualizerCanvas.height);

        const barWidth = (this.visualizerCanvas.width / dataArray.length) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
            barHeight = dataArray[i] / 2;

            // Create gradient color: from purple to blue to green
            const gradient = this.visualizerContext.createLinearGradient(0, 0, 0, this.visualizerCanvas.height);
            gradient.addColorStop(0, '#8e44ad');
            gradient.addColorStop(0.5, '#3498db');
            gradient.addColorStop(1, '#1abc9c');

            this.visualizerContext.fillStyle = gradient;
            this.visualizerContext.fillRect(x, this.visualizerCanvas.height - barHeight, barWidth, barHeight);
            x += barWidth + 1;
        }
    }

    // Update session status UI
    updateSessionStatus(isSpeaking) {
        // Here can add session status UI update logic
        // For example: update Live2D model's mouth movement status
    }

    // Update session emotion
    updateSessionEmotion(emoji) {
        // Here can add emotion update logic
        // For example: display emoji in status indicator
    }
}

// Create singleton instance
export const uiController = new UIController();

// Export class for module usage
export { UIController };
