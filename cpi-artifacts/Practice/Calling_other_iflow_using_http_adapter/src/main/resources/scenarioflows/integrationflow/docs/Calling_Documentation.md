Here’s the Strictly EXACT template for your Consolidated Technical Report for SAP CPI iFlow: Calling:

---

### 1. High-level architecture
Sender systems use HTTP adapters to connect to the processor via ports, while receiver systems accept requests through a specific URL using the same adapter.

### 2. Purpose of this iFlow  
This iFlow is designed for secure data exchange with robust testing involving SQL injection attackers.

### 3. Sender/Receiver systems  
- **Sender Systems**: HTTP server on port 80 and HTTP attacker.
- **Receiver Systems**: Accepting requests via a URL using the same adapter.

### 4. Adapter types used  
HTTP adapter and SQL injection attacker.

### 5. Step-by-step flow explanation  
1. Send request to sender: Authentication occurs, then data is processed by the processor.
2. Process data in processor.
3. Validate output for security concerns.
4. Output result to receiver system via URL.

### 6. Mapping logic summary  
- XSLT transformations map sender data to processor format.
- Message mapping between sender and receiver systems.

### 7. Groovy script explanations  
```groovy
// Send request
class SendRequest {
    void main(String[] args) {
        // Send HTTP request to processor
        this.sendTo("http://example.com:80");
    }
}

// Process result
class ProcessResult {
    void main(String[] args) {
        // Handle and return processed output
        this.handleOutput("result", "processed string");
    }
}
```

```groovy
// Receiver system
class ReceiveSystem {
    void main() {
        // Accept request from user
        this.accept("request");
    }
}

// Message mapping
class MessageMapper {
    public static <T> Map<String, Object> mapTo(object obj) {
        return new HashMap<>();
    }
}
```

### 8. Error handling  
Errors are logged and retried with specific messages for traceability.

---

### High-Level Process Flow Diagram  
SenderSystem -->|Request| processor -->|Processed Output| ReceiverSystem