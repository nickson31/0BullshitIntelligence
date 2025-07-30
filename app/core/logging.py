"""
Logging configuration for 0BullshitIntelligence microservice.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

import structlog


class CustomJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "getMessage", "exc_info", 
                          "exc_text", "stack_info"]:
                log_entry[key] = value
                
        return json.dumps(log_entry)


class StructuredLogger:
    """Structured logger wrapper for better context management"""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
        self._context = {}
    
    def bind_context(self, **kwargs):
        """Bind context to logger"""
        self._context.update(kwargs)
        return self
    
    def clear_context(self):
        """Clear bound context"""
        self._context = {}
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **{**self._context, **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, **{**self._context, **kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, **{**self._context, **kwargs})
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, **{**self._context, **kwargs})


def setup_logging():
    """Setup application logging configuration"""
    from app.core.config import get_settings
    
    settings = get_settings()
    
    # Parse log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    
    # Console formatter for development
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


# ==========================================
# PERFORMANCE LOGGING
# ==========================================

class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self):
        self.logger = get_logger("performance")
    
    def log_api_request(self, endpoint: str, method: str, duration_ms: float, 
                       status_code: int, user_id: Optional[str] = None):
        """Log API request performance"""
        self.logger.info(
            "API request completed",
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            status_code=status_code,
            user_id=user_id
        )
    
    def log_ai_processing(self, system_name: str, duration_ms: float, 
                         tokens_used: Optional[int] = None, success: bool = True):
        """Log AI processing performance"""
        self.logger.info(
            "AI processing completed",
            system_name=system_name,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            success=success
        )
    
    def log_database_query(self, operation: str, table: str, duration_ms: float,
                          rows_affected: Optional[int] = None):
        """Log database query performance"""
        self.logger.info(
            "Database query completed",
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected
        )


# ==========================================
# SECURITY LOGGING
# ==========================================

class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def log_authentication_attempt(self, user_id: Optional[str], success: bool, 
                                  ip_address: Optional[str] = None):
        """Log authentication attempt"""
        self.logger.info(
            "Authentication attempt",
            user_id=user_id,
            success=success,
            ip_address=ip_address
        )
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str):
        """Log rate limit violation"""
        self.logger.warning(
            "Rate limit exceeded",
            ip_address=ip_address,
            endpoint=endpoint
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log suspicious activity"""
        self.logger.warning(
            "Suspicious activity detected",
            activity_type=activity_type,
            **details
        )


# ==========================================
# BUSINESS LOGIC LOGGING
# ==========================================

class BusinessLogger:
    """Logger for business events"""
    
    def __init__(self):
        self.logger = get_logger("business")
    
    def log_conversation_started(self, conversation_id: str, user_id: Optional[str] = None):
        """Log new conversation start"""
        self.logger.info(
            "Conversation started",
            conversation_id=conversation_id,
            user_id=user_id
        )
    
    def log_search_performed(self, search_type: str, filters: Dict[str, Any], 
                           results_count: int, user_id: Optional[str] = None):
        """Log search operation"""
        self.logger.info(
            "Search performed",
            search_type=search_type,
            filters=filters,
            results_count=results_count,
            user_id=user_id
        )
    
    def log_upsell_opportunity(self, opportunity_type: str, user_id: str, 
                              confidence: float):
        """Log upselling opportunity"""
        self.logger.info(
            "Upsell opportunity identified",
            opportunity_type=opportunity_type,
            user_id=user_id,
            confidence=confidence
        )


# ==========================================
# ERROR LOGGING
# ==========================================

class ErrorLogger:
    """Specialized error logger"""
    
    def __init__(self):
        self.logger = get_logger("errors")
    
    def log_ai_error(self, system_name: str, error_message: str, 
                    context: Optional[Dict[str, Any]] = None):
        """Log AI system error"""
        self.logger.error(
            "AI system error",
            system_name=system_name,
            error_message=error_message,
            context=context or {}
        )
    
    def log_database_error(self, operation: str, error_message: str,
                          context: Optional[Dict[str, Any]] = None):
        """Log database error"""
        self.logger.error(
            "Database error",
            operation=operation,
            error_message=error_message,
            context=context or {}
        )
    
    def log_api_error(self, endpoint: str, error_message: str, status_code: int,
                     context: Optional[Dict[str, Any]] = None):
        """Log API error"""
        self.logger.error(
            "API error",
            endpoint=endpoint,
            error_message=error_message,
            status_code=status_code,
            context=context or {}
        )


# ==========================================
# GLOBAL LOGGERS
# ==========================================

# Initialize global loggers
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
business_logger = BusinessLogger()
error_logger = ErrorLogger()


# ==========================================
# LOGGING DECORATORS
# ==========================================

def log_performance(operation_name: str):
    """Decorator to log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                performance_logger.logger.info(
                    f"{operation_name} completed",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=True
                )
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                performance_logger.logger.error(
                    f"{operation_name} failed",
                    operation=operation_name,
                    duration_ms=duration_ms,
                    error=str(e),
                    success=False
                )
                raise
                
        return wrapper
    return decorator