// ===== IMAGE OPTIMIZATION =====
class ImageOptimizer {
    constructor() {
        this.supportedFormats = {
            webp: this.checkWebPSupport(),
            jpeg: true,
            png: true
        };
    }

    checkWebPSupport() {
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('image/webp') === 5;
    }

    convertToWebP(imagePath) {
        if (!this.supportedFormats.webp) return imagePath;
        return imagePath.replace(/\.(jpg|jpeg|png)$/i, '.webp');
    }

    getOptimizedUrl(imagePath, width = 400) {
        const format = this.supportedFormats.webp ? 'webp' : 'jpeg';
        const optimized = this.convertToWebP(imagePath);
        return `${optimized}?w=${width}&q=80&f=${format}`;
    }

    enableLazyLoading(imageElement) {
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            }, { rootMargin: '50px' });

            if (imageElement.classList.contains('lazy')) {
                observer.observe(imageElement);
            }
        } else {
            // Fallback for older browsers
            imageElement.src = imageElement.dataset.src;
        }
    }
}

// ===== PERFORMANCE CACHING =====
class PerformanceCache {
    constructor(cacheName = 'yummy-cache-v1') {
        this.cacheName = cacheName;
        this.memoryCache = new Map();
        this.cacheExpiry = 30 * 60 * 1000; // 30 minutes
    }

    async set(key, value, ttl = this.cacheExpiry) {
        this.memoryCache.set(key, {
            value,
            timestamp: Date.now(),
            ttl
        });

        // Also store in localStorage for persistence
        try {
            localStorage.setItem(`cache_${key}`, JSON.stringify({
                value,
                timestamp: Date.now(),
                ttl
            }));
        } catch (e) {
            console.warn('LocalStorage write failed:', e);
        }
    }

    async get(key) {
        // Check memory cache first
        const memEntry = this.memoryCache.get(key);
        if (memEntry && Date.now() - memEntry.timestamp < memEntry.ttl) {
            return memEntry.value;
        }

        // Check localStorage
        try {
            const stored = localStorage.getItem(`cache_${key}`);
            if (stored) {
                const { value, timestamp, ttl } = JSON.parse(stored);
                if (Date.now() - timestamp < ttl) {
                    this.memoryCache.set(key, { value, timestamp, ttl });
                    return value;
                }
                localStorage.removeItem(`cache_${key}`);
            }
        } catch (e) {
            console.warn('LocalStorage read failed:', e);
        }

        return null;
    }

    async clear(key) {
        this.memoryCache.delete(key);
        try {
            localStorage.removeItem(`cache_${key}`);
        } catch (e) {
            console.warn('LocalStorage clear failed:', e);
        }
    }

    async clearAll() {
        this.memoryCache.clear();
        try {
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('cache_')) {
                    localStorage.removeItem(key);
                }
            });
        } catch (e) {
            console.warn('LocalStorage clearAll failed:', e);
        }
    }
}

// ===== ERROR LOGGING =====
class ErrorLogger {
    constructor(serviceName = 'Yummy') {
        this.serviceName = serviceName;
        this.logs = [];
        this.maxLogs = 100;
        this.setupGlobalErrorHandler();
    }

    setupGlobalErrorHandler() {
        window.addEventListener('error', (event) => {
            this.logError('uncaught', {
                message: event.message,
                source: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.logError('unhandled-rejection', {
                reason: event.reason
            });
        });
    }

    logError(type, details) {
        const errorEntry = {
            type,
            timestamp: new Date().toISOString(),
            details,
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        this.logs.push(errorEntry);
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }

        console.error(`[${this.serviceName}] Error:`, errorEntry);
        this.sendToServer(errorEntry);
    }

    async sendToServer(errorEntry) {
        try {
            // Send to your backend error tracking service
            // Example: Sentry, LogRocket, etc.
            // await fetch('/api/logs/error', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify(errorEntry)
            // });
        } catch (e) {
            console.warn('Failed to send error log:', e);
        }
    }

    getLogs() {
        return this.logs;
    }

    clearLogs() {
        this.logs = [];
    }
}

// ===== PERFORMANCE MONITORING =====
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.marks = {};
    }

    markStart(label) {
        this.marks[label] = performance.now();
    }

    markEnd(label) {
        if (!this.marks[label]) return;
        const duration = performance.now() - this.marks[label];
        this.metrics[label] = duration;
        console.log(`⏱️ ${label}: ${duration.toFixed(2)}ms`);
        delete this.marks[label];
        return duration;
    }

    getMetrics() {
        return {
            ...this.metrics,
            memory: performance.memory ? {
                usedJSHeapSize: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
                totalJSHeapSize: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB'
            } : null,
            navigation: {
                domContentLoaded: performance.getEntriesByName('navigation')[0]?.domContentLoadedEventEnd - performance.getEntriesByName('navigation')[0]?.domContentLoadedEventStart,
                loadComplete: performance.getEntriesByName('navigation')[0]?.loadEventEnd - performance.getEntriesByName('navigation')[0]?.loadEventStart
            }
        };
    }

    reportMetrics() {
        console.table(this.getMetrics());
    }
}

// ===== BUNDLE SIZE ANALYZER =====
class BundleSizeAnalyzer {
    static analyzePage() {
        const resources = performance.getEntriesByType('resource');
        const bundleInfo = {
            totalSize: 0,
            scripts: [],
            styles: [],
            images: [],
            fonts: [],
            others: []
        };

        resources.forEach(resource => {
            const size = resource.transferSize;
            bundleInfo.totalSize += size;

            if (resource.name.includes('.js')) {
                bundleInfo.scripts.push({ name: resource.name, size });
            } else if (resource.name.includes('.css')) {
                bundleInfo.styles.push({ name: resource.name, size });
            } else if (resource.name.match(/\.(jpg|jpeg|png|webp|gif)$/i)) {
                bundleInfo.images.push({ name: resource.name, size });
            } else if (resource.name.match(/\.(woff|woff2|ttf|eot)$/i)) {
                bundleInfo.fonts.push({ name: resource.name, size });
            } else {
                bundleInfo.others.push({ name: resource.name, size });
            }
        });

        return bundleInfo;
    }

    static formatSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    static reportBundleSize() {
        const analysis = this.analyzePage();
        console.group('📦 Bundle Size Analysis');
        console.log('Total:', this.formatSize(analysis.totalSize));
        console.log('Scripts:', this.formatSize(analysis.scripts.reduce((sum, s) => sum + s.size, 0)));
        console.log('Styles:', this.formatSize(analysis.styles.reduce((sum, s) => sum + s.size, 0)));
        console.log('Images:', this.formatSize(analysis.images.reduce((sum, s) => sum + s.size, 0)));
        console.log('Fonts:', this.formatSize(analysis.fonts.reduce((sum, s) => sum + s.size, 0)));
        console.groupEnd();
        return analysis;
    }
}

// Export instances
window.imageOptimizer = new ImageOptimizer();
window.performanceCache = new PerformanceCache();
window.errorLogger = new ErrorLogger('Yummy');
window.performanceMonitor = new PerformanceMonitor();
window.BundleSizeAnalyzer = BundleSizeAnalyzer;
