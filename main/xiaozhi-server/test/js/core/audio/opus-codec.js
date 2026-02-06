import { log } from '../../utils/logger.js?v=0205';


// Kiểm tra xem thư viện Opus đã được tải chưa
export function checkOpusLoaded() {
    try {
        // Kiểm tra xem Module có tồn tại không (biến toàn cục được xuất từ thư viện cục bộ)
        if (typeof Module === 'undefined') {
            throw new Error('Thư viện Opus chưa được tải, đối tượng Module không tồn tại');
        }

        // Thử sử dụng Module.instance trước (cách xuất ở dòng cuối của libopus.js)
        if (typeof Module.instance !== 'undefined' && typeof Module.instance._opus_decoder_get_size === 'function') {
            // Sử dụng đối tượng Module.instance thay thế đối tượng Module toàn cục
            window.ModuleInstance = Module.instance;
            log('Tải thư viện Opus thành công (sử dụng Module.instance)', 'success');

            // Ẩn trạng thái sau 3 giây
            const statusElement = document.getElementById('scriptStatus');
            if (statusElement) statusElement.style.display = 'none';
            return;
        }

        // Nếu không có Module.instance, kiểm tra hàm Module toàn cục
        if (typeof Module._opus_decoder_get_size === 'function') {
            window.ModuleInstance = Module;
            log('Tải thư viện Opus thành công (sử dụng Module toàn cục)', 'success');

            // Ẩn trạng thái sau 3 giây
            const statusElement = document.getElementById('scriptStatus');
            if (statusElement) statusElement.style.display = 'none';
            return;
        }

        throw new Error('Không tìm thấy hàm giải mã Opus, có thể cấu trúc Module không đúng');
    } catch (err) {
        log(`Tải thư viện Opus thất bại, vui lòng kiểm tra xem tệp libopus.js có tồn tại và đúng không: ${err.message}`, 'error');
    }
}


// Tạo một bộ mã hóa Opus
let opusEncoder = null;
export function initOpusEncoder() {
    try {
        if (opusEncoder) {
            return opusEncoder; // Đã được khởi tạo
        }

        if (!window.ModuleInstance) {
            log('Không thể tạo bộ mã hóa Opus: ModuleInstance không khả dụng', 'error');
            return;
        }

        // Khởi tạo một bộ mã hóa Opus
        const mod = window.ModuleInstance;
        const sampleRate = 16000; // Tần số lấy mẫu 16kHz
        const channels = 1;       // Kênh đơn
        const application = 2048; // OPUS_APPLICATION_VOIP = 2048

        // Tạo bộ mã hóa
        opusEncoder = {
            channels: channels,
            sampleRate: sampleRate,
            frameSize: 960, // 60ms @ 16kHz = 60 * 16 = 960 samples
            maxPacketSize: 4000, // Kích thước gói tối đa
            module: mod,

            // Khởi tạo bộ mã hóa
            init: function () {
                try {
                    // Lấy kích thước bộ mã hóa
                    const encoderSize = mod._opus_encoder_get_size(this.channels);
                    log(`Kích thước bộ mã hóa Opus: ${encoderSize} byte`, 'info');

                    // Cấp phát bộ nhớ
                    this.encoderPtr = mod._malloc(encoderSize);
                    if (!this.encoderPtr) {
                        throw new Error("Không thể cấp phát bộ nhớ cho bộ mã hóa");
                    }

                    // Khởi tạo bộ mã hóa
                    const err = mod._opus_encoder_init(
                        this.encoderPtr,
                        this.sampleRate,
                        this.channels,
                        application
                    );

                    if (err < 0) {
                        throw new Error(`Khởi tạo bộ mã hóa Opus thất bại: ${err}`);
                    }

                    // Thiết lập tốc độ bit (16kbps)
                    mod._opus_encoder_ctl(this.encoderPtr, 4002, 16000); // OPUS_SET_BITRATE

                    // Thiết lập độ phức tạp (0-10, chất lượng càng cao càng tốt nhưng CPU sử dụng càng nhiều)
                    mod._opus_encoder_ctl(this.encoderPtr, 4010, 5);     // OPUS_SET_COMPLEXITY

                    // Thiết lập sử dụng DTX (không truyền khung im lặng)
                    mod._opus_encoder_ctl(this.encoderPtr, 4016, 1);     // OPUS_SET_DTX

                    log("Khởi tạo bộ mã hóa Opus thành công", 'success');
                    return true;
                } catch (error) {
                    if (this.encoderPtr) {
                        mod._free(this.encoderPtr);
                        this.encoderPtr = null;
                    }
                    log(`Khởi tạo bộ mã hóa Opus thất bại: ${error.message}`, 'error');
                    return false;
                }
            },

            // Mã hóa dữ liệu PCM thành Opus
            encode: function (pcmData) {
                if (!this.encoderPtr) {
                    if (!this.init()) {
                        return null;
                    }
                }

                try {
                    const mod = this.module;

                    // Cấp phát bộ nhớ cho dữ liệu PCM
                    const pcmPtr = mod._malloc(pcmData.length * 2); // 2 byte/int16

                    // Sao chép dữ liệu PCM vào HEAP
                    for (let i = 0; i < pcmData.length; i++) {
                        mod.HEAP16[(pcmPtr >> 1) + i] = pcmData[i];
                    }

                    // Cấp phát bộ nhớ cho đầu ra
                    const outPtr = mod._malloc(this.maxPacketSize);

                    // Thực hiện mã hóa
                    const encodedLen = mod._opus_encode(
                        this.encoderPtr,
                        pcmPtr,
                        this.frameSize,
                        outPtr,
                        this.maxPacketSize
                    );

                    if (encodedLen < 0) {
                        throw new Error(`Mã hóa Opus thất bại: ${encodedLen}`);
                    }

                    // Sao chép dữ liệu đã mã hóa
                    const opusData = new Uint8Array(encodedLen);
                    for (let i = 0; i < encodedLen; i++) {
                        opusData[i] = mod.HEAPU8[outPtr + i];
                    }

                    // Giải phóng bộ nhớ
                    mod._free(pcmPtr);
                    mod._free(outPtr);

                    return opusData;
                } catch (error) {
                    log(`Lỗi mã hóa Opus: ${error.message}`, 'error');
                    return null;
                }
            },

            // Hủy bộ mã hóa
            destroy: function () {
                if (this.encoderPtr) {
                    this.module._free(this.encoderPtr);
                    this.encoderPtr = null;
                }
            }
        };

        opusEncoder.init();
        return opusEncoder;
    } catch (error) {
        log(`Tạo bộ mã hóa Opus thất bại: ${error.message}`, 'error');
        return false;
    }
}