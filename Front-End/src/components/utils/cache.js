// 簡單的內存快取實現
class MemoryCache {
  constructor(ttl = 5 * 60 * 1000) { // 預設 5 分鐘過期
    this.cache = new Map();
    this.ttl = ttl;
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  set(key, data) {
    this.cache.set(key, {
      data,
      expiry: Date.now() + this.ttl
    });
  }

  clear() {
    this.cache.clear();
  }

  // 清理過期項目
  cleanup() {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiry) {
        this.cache.delete(key);
      }
    }
  }
}

// 創建全局快取實例
export const newsCache = new MemoryCache();
export const imageCache = new MemoryCache();

// 定期清理過期項目
setInterval(() => {
  newsCache.cleanup();
  imageCache.cleanup();
}, 60000); // 每分鐘清理一次

export default MemoryCache;