import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'

interface VirtualScrollOptions {
  itemHeight: number
  containerHeight: number
  overscan?: number
  enabled?: boolean
  threshold?: number
}

interface VirtualScrollResult {
  scrollTop: number
  startIndex: number
  endIndex: number
  visibleItems: any[]
  totalHeight: number
  offsetY: number
  containerRef: any
  contentRef: any
  scrollTo: (index: number) => void
  scrollToTop: () => void
  scrollToBottom: () => void
  handleScroll: () => void
}

export function useVirtualScroll<T = any>(
  items: T[],
  options: VirtualScrollOptions
): VirtualScrollResult {
  const {
    itemHeight,
    containerHeight,
    overscan = 5,
    enabled = true,
    threshold = 100
  } = options

  // Refs
  const scrollTop = ref(0)
  const containerRef = ref<HTMLElement>()
  const contentRef = ref<HTMLElement>()

  // Computed
  const totalHeight = computed(() => {
    if (!enabled || items.length < threshold) {
      return items.length * itemHeight
    }
    return items.length * itemHeight
  })

  const startIndex = computed(() => {
    if (!enabled || items.length < threshold) {
      return 0
    }
    const index = Math.floor(scrollTop.value / itemHeight)
    return Math.max(0, index - overscan)
  })

  const endIndex = computed(() => {
    if (!enabled || items.length < threshold) {
      return items.length
    }
    const visibleCount = Math.ceil(containerHeight / itemHeight)
    const index = startIndex.value + visibleCount + overscan * 2
    return Math.min(items.length, index)
  })

  const visibleItems = computed(() => {
    if (!enabled || items.length < threshold) {
      return items
    }
    return items.slice(startIndex.value, endIndex.value)
  })

  const offsetY = computed(() => {
    if (!enabled || items.length < threshold) {
      return 0
    }
    return startIndex.value * itemHeight
  })

  // Methods
  const scrollTo = (index: number) => {
    if (!containerRef.value) return

    const targetScrollTop = index * itemHeight
    containerRef.value.scrollTop = targetScrollTop
    scrollTop.value = targetScrollTop
  }

  const scrollToTop = () => {
    scrollTo(0)
  }

  const scrollToBottom = () => {
    scrollTo(items.length - 1)
  }

  const handleScroll = () => {
    if (!containerRef.value) return
    scrollTop.value = containerRef.value.scrollTop
  }

  const handleWheel = (event: WheelEvent) => {
    if (!containerRef.value) return

    // Enable smooth scrolling with momentum
    const delta = event.deltaY
    const newScrollTop = containerRef.value.scrollTop + delta
    const maxScrollTop = totalHeight.value - containerHeight

    if (newScrollTop >= 0 && newScrollTop <= maxScrollTop) {
      containerRef.value.scrollTop = newScrollTop
      scrollTop.value = newScrollTop
    }
  }

  // Performance optimization: Throttle scroll events
  let scrollTimer: NodeJS.Timeout | null = null
  const throttledHandleScroll = () => {
    if (scrollTimer) return

    scrollTimer = setTimeout(() => {
      handleScroll()
      scrollTimer = null
    }, 16) // ~60fps
  }

  // Lifecycle
  onMounted(() => {
    if (containerRef.value) {
      containerRef.value.addEventListener('scroll', throttledHandleScroll, { passive: true })
      containerRef.value.addEventListener('wheel', handleWheel, { passive: true })
    }
  })

  onUnmounted(() => {
    if (containerRef.value) {
      containerRef.value.removeEventListener('scroll', throttledHandleScroll)
      containerRef.value.removeEventListener('wheel', handleWheel)
    }
    if (scrollTimer) {
      clearTimeout(scrollTimer)
    }
  })

  // Watch for container height changes
  let resizeObserver: ResizeObserver | null = null

  onMounted(() => {
    if (containerRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const { height } = entry.contentRect
          // Trigger recalculation if height changes significantly
          if (Math.abs(height - containerHeight) > 50) {
            nextTick(() => {
              handleScroll()
            })
          }
        }
      })

      resizeObserver.observe(containerRef.value)
    }
  })

  onUnmounted(() => {
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
  })

  return {
    scrollTop,
    startIndex,
    endIndex,
    visibleItems,
    totalHeight,
    offsetY,
    containerRef,
    contentRef,
    scrollTo,
    scrollToTop,
    scrollToBottom,
    handleScroll
  }
}

// Enhanced virtual scroll with dynamic item heights
export function useDynamicVirtualScroll<T = any>(
  items: T[],
  getItemHeight: (item: T, index: number) => number,
  containerHeight: number,
  options: {
    overscan?: number
    enabled?: boolean
    threshold?: number
    estimatedItemHeight?: number
  } = {}
) {
  const {
    overscan = 5,
    enabled = true,
    threshold = 100,
    estimatedItemHeight = 40
  } = options

  // Refs
  const scrollTop = ref(0)
  const containerRef = ref<HTMLElement>()
  const contentRef = ref<HTMLElement>()
  const itemHeights = ref<number[]>([])
  const itemPositions = ref<number[]>([])

  // Computed
  const totalHeight = computed(() => {
    if (!enabled || items.length < threshold) {
      return itemHeights.value.reduce((sum, height) => sum + height, 0)
    }
    return itemPositions.value[itemPositions.value.length - 1] +
           (itemHeights.value[itemHeights.value.length - 1] || estimatedItemHeight)
  })

  const startIndex = computed(() => {
    if (!enabled || items.length < threshold) {
      return 0
    }

    // Binary search for start index
    let left = 0
    let right = itemPositions.value.length - 1

    while (left <= right) {
      const mid = Math.floor((left + right) / 2)
      if (itemPositions.value[mid] < scrollTop.value) {
        left = mid + 1
      } else {
        right = mid - 1
      }
    }

    return Math.max(0, left - overscan)
  })

  const endIndex = computed(() => {
    if (!enabled || items.length < threshold) {
      return items.length
    }

    const visibleHeight = containerHeight
    const scrollBottom = scrollTop.value + visibleHeight

    // Binary search for end index
    let left = startIndex.value
    let right = itemPositions.value.length - 1

    while (left <= right) {
      const mid = Math.floor((left + right) / 2)
      const itemBottom = itemPositions.value[mid] + (itemHeights.value[mid] || estimatedItemHeight)

      if (itemBottom <= scrollBottom) {
        left = mid + 1
      } else {
        right = mid - 1
      }
    }

    return Math.min(items.length, left + overscan)
  })

  const visibleItems = computed(() => {
    if (!enabled || items.length < threshold) {
      return items
    }
    return items.slice(startIndex.value, endIndex.value)
  })

  const offsetY = computed(() => {
    if (!enabled || items.length < threshold) {
      return 0
    }
    return itemPositions.value[startIndex.value] || 0
  })

  // Methods
  const updateItemHeights = () => {
    if (!enabled || items.length < threshold) {
      itemHeights.value = items.map(() => estimatedItemHeight)
      itemPositions.value = items.map((_, index) => index * estimatedItemHeight)
      return
    }

    const newHeights: number[] = []
    const newPositions: number[] = []
    let currentPosition = 0

    for (let i = 0; i < items.length; i++) {
      const height = getItemHeight(items[i], i)
      newHeights.push(height)
      newPositions.push(currentPosition)
      currentPosition += height
    }

    itemHeights.value = newHeights
    itemPositions.value = newPositions
  }

  const scrollTo = (index: number) => {
    if (!containerRef.value || index < 0 || index >= items.length) return

    const targetScrollTop = itemPositions.value[index] || 0
    containerRef.value.scrollTop = targetScrollTop
    scrollTop.value = targetScrollTop
  }

  const scrollToTop = () => {
    scrollTo(0)
  }

  const scrollToBottom = () => {
    scrollTo(items.length - 1)
  }

  const handleScroll = () => {
    if (!containerRef.value) return
    scrollTop.value = containerRef.value.scrollTop
  }

  // Watch for items changes
  watch(items, () => {
    updateItemHeights()
  }, { immediate: true })

  // Lifecycle
  onMounted(() => {
    if (containerRef.value) {
      containerRef.value.addEventListener('scroll', handleScroll, { passive: true })
    }
    updateItemHeights()
  })

  onUnmounted(() => {
    if (containerRef.value) {
      containerRef.value.removeEventListener('scroll', handleScroll)
    }
  })

  return {
    scrollTop,
    startIndex,
    endIndex,
    visibleItems,
    totalHeight,
    offsetY,
    containerRef,
    contentRef,
    scrollTo,
    scrollToTop,
    scrollToBottom,
    handleScroll,
    updateItemHeights
  }
}

// Intersection Observer for lazy loading
export function useIntersectionObserver(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options: IntersectionObserverInit = {}
) {
  const targetRef = ref<HTMLElement>()
  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (typeof IntersectionObserver !== 'undefined' && targetRef.value) {
      observer = new IntersectionObserver(callback, {
        threshold: 0.1,
        rootMargin: '50px',
        ...options
      })
      observer.observe(targetRef.value)
    }
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
    }
  })

  return {
    targetRef
  }
}