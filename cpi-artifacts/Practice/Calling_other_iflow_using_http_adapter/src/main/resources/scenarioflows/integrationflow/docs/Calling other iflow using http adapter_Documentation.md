```markdown
# IntegrationFlow: Calling other iflow using http adapter

## Flow Name
Calling other iflow using http adapter  

## Business Purpose (short but meaningful)
Call another IfLow component via HTTP adapter  
---

### High-Level Technical Flow  
1. Call the target IfLow component using HTTP adapter  
2. Route response to the appropriate participant or endpoint  
3. Ensure all events are properly logged and exposed for downstream integration  

## Steps Explanation  
1. Begin the IntegrationFlow by initiating a request to the specified URL.  
2. Use the HTTP adapter to make the necessary authenticated request to the target IfLow component.  
3. Route any response back to the appropriate participant or endpoint.  
4. Ensure all events are logged and exposed for downstream integration.  

## Scripts & Mappings Summary  
- No specific scripts or mappings were defined in this scenario flow.  

## Exception Handling  
- Exception handling is not required as no custom exceptions were defined in this scenario.  

## Properties Used  
- HTTP adapter  
- Participant configuration  
- Extension elements (Participant_1, sender)  
- Log configurations (all events)  

## Deployment Notes  
- Deploy the IfLow component using the specified HTTP adapter.  
- Configure endpoints and participants appropriately for integration.  
```