// Hàm ghi log
export function log(message, type = 'info') {
    // Chia tin nhắn thành nhiều dòng theo ký tự xuống dòng
    const lines = message.split('\n');
    const now = new Date();
    // const timestamp = `[${now.toLocaleTimeString()}] `;
    const timestamp = `[${now.toLocaleTimeString()}.${now.getMilliseconds().toString().padStart(3, '0')}] `;

    // Kiểm tra xem container log có tồn tại không
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) {
        // Nếu container log không tồn tại, chỉ xuất ra console
        console.log(`[${type.toUpperCase()}] ${message}`);
        return;
    }

    // Tạo mục log cho mỗi dòng
    lines.forEach((line, index) => {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        // Nếu là log đầu tiên, hiển thị timestamp
        const prefix = index === 0 ? timestamp : ' '.repeat(timestamp.length);
        logEntry.textContent = `${prefix}${line}`;
        // logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        // logEntry.style giữ lại khoảng trắng ở đầu
        logEntry.style.whiteSpace = 'pre';
        if (type === 'error') {
            logEntry.style.color = 'red';
        } else if (type === 'debug') {
            logEntry.style.color = 'gray';
            return;
        } else if (type === 'warning') {
            logEntry.style.color = 'orange';
        } else if (type === 'success') {
            logEntry.style.color = 'green';
        } else {
            logEntry.style.color = 'black';
        }
        logContainer.appendChild(logEntry);
    });

    logContainer.scrollTop = logContainer.scrollHeight;
}