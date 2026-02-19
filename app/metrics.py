from prometheus_client import Counter, Histogram

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