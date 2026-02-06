// Điểm vào ứng dụng chính
import { checkOpusLoaded, initOpusEncoder } from './core/audio/opus-codec.js?v=0205';
import { getAudioPlayer } from './core/audio/player.js?v=0205';
import { checkMicrophoneAvailability, isHttpNonLocalhost } from './core/audio/recorder.js?v=0205';
import { initMcpTools } from './core/mcp/tools.js?v=0205';
import { uiController } from './ui/controller.js?v=0205';
import { log } from './utils/logger.js?v=0205';

// Hàm hỗ trợ: Chuyển đổi dữ liệu Base64 thành Blob
function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}

// Lớp ứng dụng
class App {
    constructor() {
        this.uiController = null;
        this.audioPlayer = null;
        this.live2dManager = null;
        this.cameraStream = null;
    }

    // Khởi tạo ứng dụng
    async init() {
        log('Đang khởi tạo ứng dụng...', 'info');
        // Khởi tạo bộ điều khiển UI
        this.uiController = uiController;
        this.uiController.init();
        // Kiểm tra thư viện Opus
        checkOpusLoaded();
        // Khởi tạo bộ mã hóa Opus
        initOpusEncoder();
        // Khởi tạo trình phát âm thanh
        this.audioPlayer = getAudioPlayer();
        await this.audioPlayer.start();
        // Khởi tạo công cụ MCP
        initMcpTools();
        // Kiểm tra tính khả dụng của microphone
        await this.checkMicrophoneAvailability();
        // Kiểm tra tính khả dụng của camera
        this.checkCameraAvailability();
        // Khởi tạo Live2D
        await this.initLive2D();
        // Khởi tạo camera
        this.initCamera();
        // Tắt trạng thái tải loading
        this.setModelLoadingStatus(false);
        log('Khởi tạo ứng dụng hoàn tất', 'success');
    }

    // Khởi tạo Live2D
    async initLive2D() {
        try {
            // Kiểm tra xem Live2DManager đã được tải chưa
            if (typeof window.Live2DManager === 'undefined') {
                throw new Error('Live2DManager chưa được tải, vui lòng kiểm tra thứ tự nhập script');
            }
            this.live2dManager = new window.Live2DManager();
            await this.live2dManager.initializeLive2D();
            // Cập nhật trạng thái UI
            const live2dStatus = document.getElementById('live2dStatus');
            if (live2dStatus) {
                live2dStatus.textContent = '● Đã tải';
                live2dStatus.className = 'status loaded';
            }
            log('Khởi tạo Live2D hoàn tất', 'success');
        } catch (error) {
            log(`Khởi tạo Live2D thất bại: ${error.message}`, 'error');
            // Cập nhật trạng thái UI
            const live2dStatus = document.getElementById('live2dStatus');
            if (live2dStatus) {
                live2dStatus.textContent = '● Tải thất bại';
                live2dStatus.className = 'status error';
            }
        }
    }

    // Thiết lập trạng thái tải model
    setModelLoadingStatus(isLoading) {
        const modelLoading = document.getElementById('modelLoading');
        if (modelLoading) {
            modelLoading.style.display = isLoading ? 'flex' : 'none';
        }
    }

    /**
     * Kiểm tra tính khả dụng của microphone
     * Được gọi khi khởi tạo ứng dụng, kiểm tra microphone có khả dụng không và cập nhật trạng thái UI
     */
    async checkMicrophoneAvailability() {
        try {
            const isAvailable = await checkMicrophoneAvailability();
            const isHttp = isHttpNonLocalhost();
            // Lưu trạng thái khả dụng vào biến toàn cục
            window.microphoneAvailable = isAvailable;
            window.isHttpNonLocalhost = isHttp;
            // Cập nhật UI
            if (this.uiController) {
                this.uiController.updateMicrophoneAvailability(isAvailable, isHttp);
            }
            log(`Kiểm tra tính khả dụng của microphone hoàn tất: ${isAvailable ? 'Khả dụng' : 'Không khả dụng'}`, isAvailable ? 'success' : 'warning');
        } catch (error) {
            log(`Kiểm tra tính khả dụng của microphone thất bại: ${error.message}`, 'error');
            // Mặc định đặt là không khả dụng
            window.microphoneAvailable = false;
            window.isHttpNonLocalhost = isHttpNonLocalhost();
            if (this.uiController) {
                this.uiController.updateMicrophoneAvailability(false, window.isHttpNonLocalhost);
            }
        }
    }

    // Kiểm tra tính khả dụng của camera
    checkCameraAvailability() {
        window.cameraAvailable = true;
        log('Kiểm tra tính khả dụng của camera hoàn tất: Mặc định đã liên kết mã xác thực', 'success');
    }

    // Khởi tạo camera
    async initCamera() {
        const cameraContainer = document.getElementById('cameraContainer');
        const cameraVideo = document.getElementById('cameraVideo');

        if (!cameraContainer || !cameraVideo) {
            log('Không tìm thấy phần tử camera, bỏ qua khởi tạo', 'warning');
            return Promise.resolve(false);
        }

        let isDragging = false;
        let currentX, currentY, initialX, initialY;
        let xOffset = 0, yOffset = 0;

        cameraContainer.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);
        cameraContainer.addEventListener('touchstart', dragStart, { passive: false });
        document.addEventListener('touchmove', drag, { passive: false });
        document.addEventListener('touchend', dragEnd);

        function dragStart(e) {
            if (e.type === 'touchstart') {
                initialX = e.touches[0].clientX - xOffset;
                initialY = e.touches[0].clientY - yOffset;
            } else {
                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;
            }
            isDragging = true;
            cameraContainer.classList.add('dragging');
        }

        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                if (e.type === 'touchmove') {
                    currentX = e.touches[0].clientX - initialX;
                    currentY = e.touches[0].clientY - initialY;
                } else {
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;
                }
                xOffset = currentX;
                yOffset = currentY;
                cameraContainer.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
            }
        }

        function dragEnd() {
            initialX = currentX;
            initialY = currentY;
            isDragging = false;
            cameraContainer.classList.remove('dragging');
        }

        return new Promise((resolve) => {
            window.startCamera = async () => {
                try {
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        log('Trình duyệt không hỗ trợ API camera', 'warning');
                        return false;
                    }
                    log('Đang yêu cầu quyền camera...', 'info');
                    this.cameraStream = await navigator.mediaDevices.getUserMedia({
                        video: { width: 320, height: 240, facingMode: 'user' },
                        audio: false
                    });
                    cameraVideo.srcObject = this.cameraStream;
                    cameraContainer.classList.add('active');
                    log('Camera đã khởi động', 'success');
                    return true;
                } catch (error) {
                    log(`Khởi động camera thất bại: ${error.name} - ${error.message}`, 'error');
                    if (error.name === 'NotAllowedError') {
                        log('Quyền camera bị từ chối, vui lòng kiểm tra cài đặt trình duyệt', 'warning');
                    } else if (error.name === 'NotFoundError') {
                        log('Không tìm thấy thiết bị camera', 'warning');
                    } else if (error.name === 'NotReadableError') {
                        log('Camera đang được chương trình khác sử dụng', 'warning');
                    }
                    return false;
                }
            };

            window.stopCamera = () => {
                if (this.cameraStream) {
                    this.cameraStream.getTracks().forEach(track => track.stop());
                    this.cameraStream = null;
                    cameraVideo.srcObject = null;
                    log('Camera đã đóng', 'info');
                }
            };

            window.takePhoto = (question = 'Mô tả vật phẩm bạn nhìn thấy') => {
                return new Promise(async (resolve) => {
                    const canvas = document.createElement('canvas');
                    const video = cameraVideo;

                    if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) {
                        log('Không thể chụp ảnh: Camera chưa sẵn sàng', 'warning');
                        resolve({
                            success: false,
                            error: 'Camera chưa sẵn sàng, vui lòng đảm bảo đã kết nối và camera đã khởi động'
                        });
                        return;
                    }

                    canvas.width = video.videoWidth || 320;
                    canvas.height = video.videoHeight || 240;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                    const photoData = canvas.toDataURL('image/jpeg', 0.8);
                    log(`Chụp ảnh thành công, độ dài dữ liệu hình ảnh: ${photoData.length}`, 'success');

                    try {
                        const xz_tester_vision = localStorage.getItem('xz_tester_vision');
                        if (xz_tester_vision) {
                            let visionInfo = null;

                            try {
                                visionInfo = JSON.parse(xz_tester_vision);
                            } catch (err) {
                                throw new Error(`Phân tích cấu hình thị giác thất bại`);
                            }

                            const { url, token } = visionInfo || {};
                            if (!url || !token) {
                                throw new Error('Phân tích thị giác thất bại: Cấu hình thiếu địa chỉ giao diện (url) hoặc token');
                            }

                            log(`Đang gửi hình ảnh đến giao diện phân tích thị giác: ${url}`, 'info');

                            const deviceId = document.getElementById('deviceMac')?.value || '';
                            const clientId = document.getElementById('clientId')?.value || 'web_test_client';

                            const formData = new FormData();
                            formData.append('question', question);
                            formData.append('image', dataURItoBlob(photoData), 'photo.jpg');

                            const response = await fetch(url, {
                                method: 'POST',
                                body: formData,
                                headers: {
                                    'Device-Id': deviceId,
                                    'Client-Id': clientId,
                                    'Authorization': `Bearer ${token}`
                                }
                            });

                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }

                            const analysisResult = await response.json();
                            log(`Phân tích thị giác hoàn tất: ${JSON.stringify(analysisResult).substring(0, 200)}...`, 'success');

                            resolve({
                                success: true,
                                message: question,
                                photo_data: photoData,
                                photo_width: canvas.width,
                                photo_height: canvas.height,
                                vision_analysis: analysisResult
                            });
                        } else {
                            log('Chưa cấu hình dịch vụ phân tích thị giác', 'warning');
                        }
                    } catch (error) {
                        log(`Phân tích thị giác thất bại: ${error.message}`, 'error');
                        resolve({
                            success: true,
                            message: question,
                            photo_data: photoData,
                            photo_width: canvas.width,
                            photo_height: canvas.height,
                            vision_analysis: {
                                success: false,
                                error: error.message,
                                fallback: 'Không thể kết nối đến dịch vụ phân tích thị giác'
                            }
                        });
                    }
                });
            };

            log('Khởi tạo camera hoàn tất', 'success');
            resolve(true);
        });
    }
}

// Tạo và khởi động ứng dụng
const app = new App();
// Phơi bày instance ứng dụng ra toàn cục để các module khác truy cập
window.chatApp = app;
document.addEventListener('DOMContentLoaded', () => {
    // Khởi tạo ứng dụng
    app.init();
});
export default app;
