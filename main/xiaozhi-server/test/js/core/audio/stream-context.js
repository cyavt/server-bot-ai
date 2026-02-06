import BlockingQueue from '../../utils/blocking-queue.js?v=0205';
import { log } from '../../utils/logger.js?v=0205';

// Lớp ngữ cảnh phát luồng âm thanh
export class StreamingContext {
    constructor(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
        this.opusDecoder = opusDecoder;
        this.audioContext = audioContext;

        // Tham số âm thanh
        this.sampleRate = sampleRate;
        this.channels = channels;
        this.minAudioDuration = minAudioDuration;

        // Khởi tạo hàng đợi và trạng thái
        this.queue = [];          // Hàng đợi PCM đã giải mã. Đang phát
        this.activeQueue = new BlockingQueue(); // Hàng đợi PCM đã giải mã. Sẵn sàng phát
        this.pendingAudioBufferQueue = [];  // Hàng đợi bộ đệm chờ xử lý
        this.audioBufferQueue = new BlockingQueue();  // Hàng đợi bộ đệm
        this.playing = false;     // Có đang phát không
        this.endOfStream = false; // Có nhận được tín hiệu kết thúc không
        this.source = null;       // Nguồn âm thanh hiện tại
        this.totalSamples = 0;    // Tổng số mẫu tích lũy
        this.lastPlayTime = 0;    // Timestamp phát lần trước
        this.scheduledEndTime = 0; // Thời gian kết thúc âm thanh đã lên lịch

        // Khởi tạo nút phân tích (dùng cho Live2D)
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
    }

    // Bộ đệm mảng âm thanh
    pushAudioBuffer(item) {
        this.audioBufferQueue.enqueue(...item);
    }

    // Lấy hàng đợi bộ đệm cần xử lý, đơn luồng: trong trạng thái audioBufferQueue luôn cập nhật sẽ không có vấn đề an toàn
    async getPendingAudioBufferQueue() {
        // Chờ dữ liệu đến và lấy
        const data = await this.audioBufferQueue.dequeue();
        // Gán cho hàng đợi chờ xử lý
        this.pendingAudioBufferQueue = data;
    }

    // Lấy hàng đợi PCM đã giải mã đang phát, đơn luồng: trong trạng thái activeQueue luôn cập nhật sẽ không có vấn đề an toàn
    async getQueue(minSamples) {
        const num = minSamples - this.queue.length > 0 ? minSamples - this.queue.length : 1;

        // Chờ dữ liệu và lấy
        const tempArray = await this.activeQueue.dequeue(num);
        this.queue.push(...tempArray);
    }

    // Chuyển đổi dữ liệu âm thanh Int16 thành Float32
    convertInt16ToFloat32(int16Data) {
        const float32Data = new Float32Array(int16Data.length);
        for (let i = 0; i < int16Data.length; i++) {
            // Chuyển đổi phạm vi [-32768,32767] thành [-1,1], sử dụng thống nhất 32768.0 để tránh méo không đối xứng
            float32Data[i] = int16Data[i] / 32768.0;
        }
        return float32Data;
    }

    // Lấy số gói chờ giải mã
    getPendingDecodeCount() {
        return this.audioBufferQueue.length + this.pendingAudioBufferQueue.length;
    }

    // Lấy số mẫu chờ phát (chuyển đổi thành số gói, mỗi gói 960 mẫu)
    getPendingPlayCount() {
        // Tính số mẫu đã có trong hàng đợi
        const queuedSamples = this.activeQueue.length + this.queue.length;

        // Tính số mẫu đã lên lịch nhưng chưa phát (trong bộ đệm Web Audio)
        let scheduledSamples = 0;
        if (this.playing && this.scheduledEndTime) {
            const currentTime = this.audioContext.currentTime;
            const remainingTime = Math.max(0, this.scheduledEndTime - currentTime);
            scheduledSamples = Math.floor(remainingTime * this.sampleRate);
        }

        const totalSamples = queuedSamples + scheduledSamples;
        return Math.ceil(totalSamples / 960);
    }

    // Xóa tất cả bộ đệm âm thanh
    clearAllBuffers() {
        log('Xóa tất cả bộ đệm âm thanh', 'info');

        // Xóa tất cả hàng đợi (sử dụng phương thức clear để giữ nguyên tham chiếu đối tượng)
        this.audioBufferQueue.clear();
        this.pendingAudioBufferQueue = [];
        this.activeQueue.clear();
        this.queue = [];

        // Dừng nguồn âm thanh đang phát
        if (this.source) {
            try {
                this.source.stop();
                this.source.disconnect();
            } catch (e) {
                // Bỏ qua lỗi đã dừng
            }
            this.source = null;
        }

        // Đặt lại trạng thái
        this.playing = false;
        this.scheduledEndTime = this.audioContext.currentTime;
        this.totalSamples = 0;

        log('Bộ đệm âm thanh đã được xóa', 'success');
    }

    // Lấy nút phân tích (dùng cho Live2D)
    getAnalyser() {
        return this.analyser;
    }

    // Giải mã dữ liệu Opus thành PCM
    async decodeOpusFrames() {
        if (!this.opusDecoder) {
            log('Bộ giải mã Opus chưa được khởi tạo, không thể giải mã', 'error');
            return;
        } else {
            log('Bộ giải mã Opus khởi động', 'info');
        }

        while (true) {
            let decodedSamples = [];
            for (const frame of this.pendingAudioBufferQueue) {
                try {
                    // Sử dụng bộ giải mã Opus để giải mã
                    const frameData = this.opusDecoder.decode(frame);
                    if (frameData && frameData.length > 0) {
                        // Chuyển đổi thành Float32
                        const floatData = this.convertInt16ToFloat32(frameData);
                        // Sử dụng vòng lặp thay thế toán tử mở rộng
                        for (let i = 0; i < floatData.length; i++) {
                            decodedSamples.push(floatData[i]);
                        }
                    }
                } catch (error) {
                    log("Giải mã Opus thất bại: " + error.message, 'error');
                }
            }

            if (decodedSamples.length > 0) {
                // Sử dụng vòng lặp thay thế toán tử mở rộng
                for (let i = 0; i < decodedSamples.length; i++) {
                    this.activeQueue.enqueue(decodedSamples[i]);
                }
                this.totalSamples += decodedSamples.length;
            } else {
                log('Không có mẫu giải mã thành công', 'warning');
            }
            await this.getPendingAudioBufferQueue();
        }
    }

    // Bắt đầu phát âm thanh
    async startPlaying() {
        this.scheduledEndTime = this.audioContext.currentTime; // Theo dõi thời gian kết thúc âm thanh đã lên lịch

        while (true) {
            // Bộ đệm ban đầu: Chờ đủ mẫu rồi mới bắt đầu phát
            const minSamples = this.sampleRate * this.minAudioDuration * 2;
            if (!this.playing && this.queue.length < minSamples) {
                await this.getQueue(minSamples);
            }
            this.playing = true;

            // Tiếp tục phát âm thanh trong hàng đợi, mỗi lần phát một khối nhỏ
            while (this.playing && this.queue.length > 0) {
                // Mỗi lần phát 120ms âm thanh (2 gói Opus)
                const playDuration = 0.12;
                const targetSamples = Math.floor(this.sampleRate * playDuration);
                const actualSamples = Math.min(this.queue.length, targetSamples);

                if (actualSamples === 0) break;

                const currentSamples = this.queue.splice(0, actualSamples);
                const audioBuffer = this.audioContext.createBuffer(this.channels, currentSamples.length, this.sampleRate);
                audioBuffer.copyToChannel(new Float32Array(currentSamples), 0);

                // Tạo nguồn âm thanh
                this.source = this.audioContext.createBufferSource();
                this.source.buffer = audioBuffer;

                // Lên lịch chính xác thời gian phát
                const currentTime = this.audioContext.currentTime;
                const startTime = Math.max(this.scheduledEndTime, currentTime);

                // Kết nối đến bộ phân tích và đầu ra
                this.source.connect(this.analyser);
                this.source.connect(this.audioContext.destination);

                log(`Lên lịch phát ${currentSamples.length} mẫu, khoảng ${(currentSamples.length / this.sampleRate).toFixed(2)} giây`, 'debug');
                this.source.start(startTime);

                // Cập nhật thời gian lên lịch cho khối âm thanh tiếp theo
                const duration = audioBuffer.duration;
                this.scheduledEndTime = startTime + duration;
                this.lastPlayTime = startTime;

                // Nếu dữ liệu trong hàng đợi không đủ, chờ dữ liệu mới
                if (this.queue.length < targetSamples) {
                    break;
                }
            }

            // Chờ dữ liệu mới
            await this.getQueue(minSamples);
        }
    }
}

// Hàm factory tạo instance streamingContext
export function createStreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration) {
    return new StreamingContext(opusDecoder, audioContext, sampleRate, channels, minAudioDuration);
}