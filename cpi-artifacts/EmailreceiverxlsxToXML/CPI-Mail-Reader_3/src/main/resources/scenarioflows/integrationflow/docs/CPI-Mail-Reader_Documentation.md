Here is the **SAP CPI Documentation** based on the EXACT TEMPLATE provided:

---

### High-level architecture  
The sender system sends messages using an adapter (e.g., PAM-RECEIVER) and processes them for output. The receiver system reads these messages, maps them via another adapter (e.g., XLS-TEXT-Converter), and handles any errors during the process.

---

### Purpose of this iFlow  
This iFlow processes emails from a sender to deliver them as an XML file to the receiver.

---

### Sender/Receiver systems  
- **Sender Systems:** PAM-RECEIVER  
- **Receiver Systems:** XLS-TEXT-Converter  

---

### Adapter types used  
- PAM-RECEIVER  
- XLS-TEXT-Converter  

---

### Step-by-step flow explanation  
1. Create a message from data source.  
2. Trigger the sender to send the message.  
3. Message is processed in the receiver system.  
4. Output results or close the flow.  

---

### Mapping logic summary  
Explain mapping XSLT for mapping messages to output files.

---

### Groovy script explanations  
1. **Message Reader Script:** Reads data from a file and outputs it using the adapter.  
2. **Email Parser Script:** Processes incoming emails by converting them into XML.  
3. **Error Handler Script:** Handles and reports any errors during message processing.  

---

### Error handling  
The error-handling approach includes checking for XML parsing errors before writing files, preventing data loss.

---

### High-Level Process Flow Diagram  
SenderSystem -> Request -> CPI 
|
CPI -> ProcessedOutput -> ReceiverSystem  
|  
SendErrorHandler

--- 

This documentation provides a clear overview of the sender and receiver systems, adapters used, error handling, and mapping logic.