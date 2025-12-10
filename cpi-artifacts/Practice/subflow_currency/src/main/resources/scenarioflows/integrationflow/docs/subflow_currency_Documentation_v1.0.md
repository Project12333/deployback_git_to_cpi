To integrate the 'Integration Process' and 'SequenceFlow_3' lines in your flow diagram, follow these steps:

1. **Add Integration Process Edge**:
   - Connect the receiver after integration start to mark the transition between receiving and processing.

2. **Add SequenceFlow 3 Edge**:
   - From the integration process, draw an edge leading to 'SequenceFlow_3' with an output event definition.

3. **Include Default Collaboration Diagram**:
   - After Integration Process is completed, draw a separate line to show the collaboration diagram that was used before integration starts.

Here's how your flow diagram would look:

```mermaid
graph TD
    Sender System -->|Request| CPI
    CPI -->|Processed Output| Receiver System
    receiver System -->[Integration Process]|
        Integration Process|
        Integration Process: Integration via messageflow
    Integration Process -->|Output Event Definition| SequenceFlow_3
    SequenceFlow_6 -->|Output Event Definition| Integration Process
    SequenceFlow_3 -->|Output Event Definition| Default Collaboration Diagram
```

**Explanation of Labels**:
- "Integration Process" is labeled as such for clarity.
- "SequenceFlow 6" and "Default Collaboration Diagram" are used to indicate the specific sequence or collaboration context before integration.

This structure ensures that each part of the flow is clear and provides a logical path through the system.