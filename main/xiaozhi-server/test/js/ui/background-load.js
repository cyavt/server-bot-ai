// Kiểm tra tải hình nền
(function() {
    const backgroundContainer = document.getElementById('backgroundContainer');

    // Trích xuất URL hình nền
    let bgImageUrl = window.getComputedStyle(backgroundContainer).backgroundImage;
    const urlMatch = bgImageUrl && bgImageUrl.match(/url\(["']?(.*?)["']?\)/);
    
    if (!urlMatch || !urlMatch[1]) {
        console.warn('Không trích xuất được URL hình nền hợp lệ');
        return;
    }
    
    bgImageUrl = urlMatch[1];
    
    const bgImage = new Image();
    bgImage.onerror = function() {
        console.error('Tải hình nền thất bại:', bgImageUrl);
    };

    // Tải thành công hiển thị tải mô hình
    bgImage.onload = function() {
        modelLoading.style.display = 'flex';
    };

    bgImage.src = bgImageUrl;
})();