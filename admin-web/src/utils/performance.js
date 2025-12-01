/**
 * 性能优化工具
 * 提供防抖、节流、懒加载等性能优化功能
 */

/**
 * 防抖函数
 * 在指定时间内多次调用只执行最后一次
 * 
 * @param {Function} func - 要防抖的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, delay = 300) {
  let timeoutId = null;
  
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      func.apply(this, args);
    }, delay);
  };
}

/**
 * 节流函数
 * 在指定时间内最多执行一次
 * 
 * @param {Function} func - 要节流的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, delay = 300) {
  let lastCall = 0;
  
  return function(...args) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func.apply(this, args);
    }
  };
}

/**
 * 图片懒加载指令
 * 
 * 使用示例:
 * <img v-lazy="imageUrl" />
 */
export const lazyLoadDirective = {
  mounted(el, binding) {
    const imageUrl = binding.value;
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          el.src = imageUrl;
          observer.unobserve(el);
        }
      });
    });
    
    observer.observe(el);
    
    // 保存observer以便清理
    el._lazyLoadObserver = observer;
  },
  
  unmounted(el) {
    if (el._lazyLoadObserver) {
      el._lazyLoadObserver.disconnect();
    }
  }
};

/**
 * 虚拟滚动列表
 * 只渲染可见区域的列表项
 */
export class VirtualScroller {
  constructor(options) {
    this.container = options.container;
    this.items = options.items || [];
    this.itemHeight = options.itemHeight || 50;
    this.renderItem = options.renderItem;
    this.buffer = options.buffer || 5;
    
    this.scrollTop = 0;
    this.visibleStart = 0;
    this.visibleEnd = 0;
    
    this.init();
  }
  
  init() {
    this.container.addEventListener('scroll', this.onScroll.bind(this));
    this.update();
  }
  
  onScroll() {
    this.scrollTop = this.container.scrollTop;
    this.update();
  }
  
  update() {
    const containerHeight = this.container.clientHeight;
    
    // 计算可见范围
    this.visibleStart = Math.floor(this.scrollTop / this.itemHeight);
    this.visibleEnd = Math.ceil((this.scrollTop + containerHeight) / this.itemHeight);
    
    // 添加缓冲区
    const start = Math.max(0, this.visibleStart - this.buffer);
    const end = Math.min(this.items.length, this.visibleEnd + this.buffer);
    
    // 渲染可见项
    this.render(start, end);
  }
  
  render(start, end) {
    const fragment = document.createDocumentFragment();
    
    // 添加顶部占位
    const topSpacer = document.createElement('div');
    topSpacer.style.height = `${start * this.itemHeight}px`;
    fragment.appendChild(topSpacer);
    
    // 渲染可见项
    for (let i = start; i < end; i++) {
      const item = this.renderItem(this.items[i], i);
      fragment.appendChild(item);
    }
    
    // 添加底部占位
    const bottomSpacer = document.createElement('div');
    bottomSpacer.style.height = `${(this.items.length - end) * this.itemHeight}px`;
    fragment.appendChild(bottomSpacer);
    
    // 更新容器
    this.container.innerHTML = '';
    this.container.appendChild(fragment);
  }
  
  setItems(items) {
    this.items = items;
    this.update();
  }
  
  destroy() {
    this.container.removeEventListener('scroll', this.onScroll);
  }
}

/**
 * 性能监控器
 */
export class PerformanceMonitor {
  constructor() {
    this.metrics = {
      pageLoadTime: 0,
      apiCalls: [],
      renderTimes: []
    };
    
    this.init();
  }
  
  init() {
    // 监控页面加载时间
    window.addEventListener('load', () => {
      const perfData = performance.timing;
      this.metrics.pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
      console.log(`页面加载时间: ${this.metrics.pageLoadTime}ms`);
    });
  }
  
  /**
   * 记录API调用时间
   */
  recordApiCall(url, duration) {
    this.metrics.apiCalls.push({
      url,
      duration,
      timestamp: Date.now()
    });
    
    // 只保留最近100条记录
    if (this.metrics.apiCalls.length > 100) {
      this.metrics.apiCalls.shift();
    }
    
    // 慢API警告
    if (duration > 1000) {
      console.warn(`慢API检测: ${url} 耗时 ${duration}ms`);
    }
  }
  
  /**
   * 记录渲染时间
   */
  recordRenderTime(componentName, duration) {
    this.metrics.renderTimes.push({
      component: componentName,
      duration,
      timestamp: Date.now()
    });
    
    // 只保留最近100条记录
    if (this.metrics.renderTimes.length > 100) {
      this.metrics.renderTimes.shift();
    }
    
    // 慢渲染警告
    if (duration > 16) {
      console.warn(`慢渲染检测: ${componentName} 耗时 ${duration}ms`);
    }
  }
  
  /**
   * 获取性能统计
   */
  getStats() {
    const avgApiTime = this.metrics.apiCalls.length > 0
      ? this.metrics.apiCalls.reduce((sum, call) => sum + call.duration, 0) / this.metrics.apiCalls.length
      : 0;
    
    const avgRenderTime = this.metrics.renderTimes.length > 0
      ? this.metrics.renderTimes.reduce((sum, render) => sum + render.duration, 0) / this.metrics.renderTimes.length
      : 0;
    
    return {
      pageLoadTime: this.metrics.pageLoadTime,
      avgApiTime,
      avgRenderTime,
      totalApiCalls: this.metrics.apiCalls.length,
      slowApiCalls: this.metrics.apiCalls.filter(call => call.duration > 1000).length,
      slowRenders: this.metrics.renderTimes.filter(render => render.duration > 16).length
    };
  }
  
  /**
   * 清除统计数据
   */
  clear() {
    this.metrics.apiCalls = [];
    this.metrics.renderTimes = [];
  }
}

// 全局性能监控器实例
export const performanceMonitor = new PerformanceMonitor();

/**
 * 请求缓存
 */
export class RequestCache {
  constructor(maxSize = 100, ttl = 5 * 60 * 1000) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.ttl = ttl; // 默认5分钟过期
  }
  
  /**
   * 生成缓存键
   */
  generateKey(url, params) {
    return `${url}:${JSON.stringify(params)}`;
  }
  
  /**
   * 获取缓存
   */
  get(url, params) {
    const key = this.generateKey(url, params);
    const cached = this.cache.get(key);
    
    if (!cached) {
      return null;
    }
    
    // 检查是否过期
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  /**
   * 设置缓存
   */
  set(url, params, data) {
    const key = this.generateKey(url, params);
    
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  /**
   * 清除缓存
   */
  clear() {
    this.cache.clear();
  }
  
  /**
   * 清除匹配的缓存
   */
  clearPattern(pattern) {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}

// 全局请求缓存实例
export const requestCache = new RequestCache();

/**
 * 组件性能监控混入
 */
export const performanceMixin = {
  mounted() {
    this._mountTime = performance.now();
  },
  
  updated() {
    const updateTime = performance.now() - this._mountTime;
    performanceMonitor.recordRenderTime(this.$options.name || 'Unknown', updateTime);
  }
};
