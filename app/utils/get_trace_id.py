from opentelemetry.trace import get_current_span

def get_trace_id():
    span = get_current_span()
    ctx = span.get_span_context()

    if ctx.trace_id == 0:
        return None
    return format(ctx.trace_id,"032x")