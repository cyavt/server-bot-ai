export default class BlockingQueue {
    #items   = [];
    #waiters = [];          // {resolve, reject, min, timer, onTimeout}

    /* Cổng một lần cho hàng đợi trống */
    #emptyPromise = null;
    #emptyResolve = null;

    /* Nhà sản xuất: Đưa dữ liệu vào */
    enqueue(item, ...restItems) {
        if (restItems.length === 0) {
            this.#items.push(item);
        }
        // Nếu có tham số bổ sung, xử lý hàng loạt tất cả các mục
        else {
            const items = [item, ...restItems].filter(i => i);
            if (items.length === 0) return;
            this.#items.push(...items);
        }
        // Nếu có cổng hàng đợi trống, cho phép tất cả người chờ đi qua một lần
        if (this.#emptyResolve) {
            this.#emptyResolve();
            this.#emptyResolve = null;
            this.#emptyPromise = null;
        }

        // Đánh thức tất cả waiter đang chờ
        this.#wakeWaiters();
    }

    /* Người tiêu dùng: min mục hoặc timeout ms, cái nào đến trước */
    async dequeue(min = 1, timeout = Infinity, onTimeout = null) {
        // 1. Nếu trống, đợi dữ liệu đầu tiên đến (tất cả các lời gọi chia sẻ cùng một promise)
        if (this.#items.length === 0) {
            await this.#waitForFirstItem();
        }

        // Thỏa mãn ngay lập tức
        if (this.#items.length >= min) {
            return this.#flush();
        }

        // Cần chờ đợi
        return new Promise((resolve, reject) => {
            let timer = null;
            const waiter = { resolve, reject, min, onTimeout, timer };

            // Logic hết thời gian chờ
            if (Number.isFinite(timeout)) {
                waiter.timer = setTimeout(() => {
                    this.#removeWaiter(waiter);
                    if (onTimeout) onTimeout(this.#items.length);
                    resolve(this.#flush());
                }, timeout);
            }

            this.#waiters.push(waiter);
        });
    }

    /* Bộ tạo cổng hàng đợi trống */
    #waitForFirstItem() {
        if (!this.#emptyPromise) {
            this.#emptyPromise = new Promise(r => (this.#emptyResolve = r));
        }
        return this.#emptyPromise;
    }

    /* Nội bộ: Sau mỗi lần dữ liệu thay đổi, kiểm tra waiter nào đã được thỏa mãn */
    #wakeWaiters() {
        for (let i = this.#waiters.length - 1; i >= 0; i--) {
            const w = this.#waiters[i];
            if (this.#items.length >= w.min) {
                this.#removeWaiter(w);
                w.resolve(this.#flush());
            }
        }
    }

    #removeWaiter(waiter) {
        const idx = this.#waiters.indexOf(waiter);
        if (idx !== -1) {
            this.#waiters.splice(idx, 1);
            if (waiter.timer) clearTimeout(waiter.timer);
        }
    }

    #flush() {
        const snapshot = [...this.#items];
        this.#items.length = 0;
        return snapshot;
    }

    /* Độ dài cache hiện tại (không bao gồm người chờ) */
    get length() {
        return this.#items.length;
    }

    /* Xóa hàng đợi (giữ nguyên tham chiếu đối tượng, không ảnh hưởng đến người chờ) */
    clear() {
        this.#items.length = 0;
    }
}