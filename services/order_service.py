# services/order_service.py

import logging
import json
import socket
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Initialize OpenTelemetry Tracer
resource = Resource.create(attributes={"service.name": "order_service"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)
exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(exporter)
provider.add_span_processor(span_processor)
tracer = trace.get_tracer(__name__)

# Instrument logging
LoggingInstrumentor().instrument(set_logging_format=True)

class LogstashHandler(logging.Handler):
    def __init__(self, host, port):
        logging.Handler.__init__(self)
        self.host = host
        self.port = port

    def emit(self, record):
        log_entry = self.format(record)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        sock.sendall(log_entry.encode("utf-8"))
        sock.close()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_service")
logstash_handler = LogstashHandler(host="localhost", port=5044)
logger.addHandler(logstash_handler)

def create_order(order_id, product_name):
    with tracer.start_as_current_span("create_order_span") as span:
        logger.info(json.dumps({
            "message": f"Creating order with ID: {order_id}, Product: {product_name}",
            "service_name": "order_service",
            "order_id": order_id
        }))
        span.set_attribute("order.id", order_id)
        span.set_attribute("product.name", product_name)
    return {"status": "Order created", "order_id": order_id, "product_name": product_name}

if __name__ == "__main__":
    create_order(1011, "Laptop")
