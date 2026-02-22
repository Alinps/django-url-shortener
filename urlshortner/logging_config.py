import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self,record):
        log_record = {
            "level":record.levelname,
            "message":record.getMessage(),
            "logger":record.name,
            "timestamp":self.formatTime(record),
        }

        for attr in [
            "request_id",
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