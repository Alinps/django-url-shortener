from prometheus_client import Counter, Histogram, Gauge

#----------------------
# Redirect Layer
#----------------------

redirect_request_total = Counter(
    "redirect_request_total",
    "Total redirect requests received"
)

cache_hit_total = Counter(
    "cache_hit_total",
    "Total Redis cache hits"
)

cache_miss_total = Counter(
    "cache_miss_total",
    "Total Redis cache misses"
)

#------------------
# Rate Limiting
#-----------------

rate_limit_trigger_total = Counter(
    "rate_limit_trigger_total",
    "Total times rate limit blocked a request"
)

#------------------
# Click Analytics
#-------------------

click_enqueued_total =Counter(
    "click_enqueued_total",
    "Total click events enqueued to Redis"
)

# -------------------------
# Flush Metrics
# -------------------------

flush_duration_seconds = Histogram(
    "flush_duration_seconds",
    "Time taken to flush analytics from Redis to DB"
)

flush_lock_failed_total = Counter(
    "flush_lock_failed_total",
    "Total times flush lock was not acquired"
)

flush_click_count_total = Counter(
    "flush_click_count_total",
    "Total click_count values flushed to DB"
)

flush_event_count_total = Counter(
    "flush_event_count_total",
    "Total click events flushed to DB"
)

redis_click_count_backlog = Gauge(
    "redis_click_count_backlog",
    "Number of click_count keys waiting in Redis",
    multiprocess_mode="livesum"  # It ignores dead process files, Sum gauge values across active processes, Remove pid label from output
)

redis_click_event_backlog = Gauge(
    "redis_click_event_backlog",
    "Number of click_event keys waiting in Redis",
    multiprocess_mode="livesum"
)

redirect_latency_seconds = Histogram(
    "redirect_latency_seconds",
    "Time taken to serve redirect request",
    buckets=(
        0.005,   # 5ms
        0.01,    # 10ms
        0.025,   # 50ms
        0.05,    # 50ms
        0.075,   # 75ms
        0.1,     # 100ms
        0.25,    # 250ms
        0.5,     # 500ms
        0.75,    # 750ms
        1.0,     # 1 s
        2.5      # 2 s#1000ms
    )
)
