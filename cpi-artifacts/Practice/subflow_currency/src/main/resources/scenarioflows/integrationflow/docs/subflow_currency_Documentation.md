Here’s a structured and organized presentation of the consolidated technical report for SAP CPI iFlow: subflow_currency based on your template:

---

### **High-level Architecture**
- **Sender Systems**: Internal systems handling currency transactions (e.g., internal banks, finance modules).
- **Receiver Systems**: External modules or interfaces receiving financial data from the sender systems.
- **Adapters Used**: `iFlow.iConnection` for communication between iFlow and other systems.

---

### **Step-by-step Flow Explanation**
1. **Initiate Transaction**: Use iFlow's API to send a transaction request to an external bank.
2. **Internal Processing**: This is handled by internal sender modules (e.g., banks or departments).
3. **Process Operations**: Perform financial calculations, mappings, and data transformations within the internal systems.
4. **Output Result**: The processed result is sent to the receiver system for storage or further processing.

---

### **Mapping Logic Summary**
- **Sender System Input**: Represents incoming transaction data.
- **Message Mapping**: Transforms input into a standardized format for internal processing.
- **Receiver System Output**: Maps processed data back to an expected format for external use.

---

### **Groovy Script Examples**

```groovy
// Example of sending a currency request using iFlow.iConnection
try {
    iFlow.iConnection("test@domain.com", "USD").write("amount", 1000, "currency").
    capture("input") { print("Input: [$input]") }
    capture("output") { print("Output: [C$1000]") }
} catch (Exception e) {
    log.error("Error sending request: ", e)
}
```

---

### **Error Handling**
- Implement basic error handling using try-catch blocks to ensure data integrity and provide meaningful logs.
- Use appropriate logging for debugging and monitoring purposes.

---

### **Process Flow Diagram**

```mermaid
graph TD;
    sender --|Mapping| receiver
      |iFlow.iConnection|
      |Output|
```

**Comments**: This diagram shows the flow of currency transactions from sender systems to internal processing, then to external receivers via iFlow.iConnection for further use.

---

This report provides a comprehensive overview of the subflow_currency implementation in SAP CPI iFlow, ensuring clarity and thoroughness while adhering to your specified template.