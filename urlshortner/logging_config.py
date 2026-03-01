import json
import logging
from opentelemetry.trace import get_current_span

class JSONFormatter(logging.Formatter):
    def format(self,record):
        span = get_current_span()
        ctx = span.get_span_context()
        if ctx.trace_id!=0:
            trace_id=format(ctx.trace_id,"032x")
        else:
            trace_id = None
        log_record = {
            "level":record.levelname,
            "message":record.getMessage(),
            "trace_id":trace_id,
            "logger":record.name,
            "timestamp":self.formatTime(record),
        }

        for attr in [
            "request_id",
            "trace_id",
            "path",
            "method",
            "status_code",
            "duration_ms",
            "error",
            "user_email"
        ]:
            if hasattr(record,attr):
                log_record[attr] = getattr(record, attr)

        return json.dumps(log_record)