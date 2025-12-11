# iFlow Documentation for Currency Converter Main Flow

## 1. Flow Name
- **Currency Converter Main Flow**  
- Facilitates cross-border currency exchanges to manage financial transactions smoothly.

## 2. Business Purpose (short but meaningful)
- The flow handles currency conversions between different currencies using Integration Framework Language (IFL) endpoints to facilitate seamless financial transactions across borders.

## 3. High-Level Technical Flow
- An endpoint sender participant processes transactions, converting source currency into target currency.
- Errors are handled by setting exceptions for immediate access or sending them back.
- Targets receive converted amounts and notify the endpoint.

## 4. Mermaid Diagram

```
bpmn2:flowName="Currency Converter Main Flow"
<ifl:participant>
    <bpmn2:Participant id="Participant_1" ifl:type="EndpointSender">
        <ifl:extensionElements>
            <ifl:property key="enableBasicAuthentication" value="true">
                sendTransaction
            </ifl:property>
            <ifl:property key="ifl:type" value="EndpointSender">
                enableBasicAuthentication
            </ifl:property>
        </ifl:extensionElements>
    </bpmn2:participant>
<ifl:participant>
    <bpmn2:Participant id="Part_2" ifl:type="Receiver">
        <ifl:extensionElements>
            <ifl:property key="returnExceptionToSender" value="true">
                returnExceptions
            </ifl:property>
            <ifl:property key="handleError" value="None">
                handleError
            </ifl:property>
        </ifl:extensionElements>
    </bpmn2:participant>
</ifl:participant>

<ifl:graph>mermaid
A to B
A -> C
C -> D
D
</ifl:graph>
```

## 5. Steps Explanation

1. **Define Source Currency**: The flow starts by defining the source currency using `sendTransaction`.
2. **Send Transaction**: A transaction is sent from the participant (Sender) to the target endpoint.
3. **Handle Errors**: If an error occurs during processing, it is set back for immediate access or sent via a 'returnExceptions' variable.
4. **Convert to Target Currency**: The transaction is converted into euros and notified to the receiver.

## 6. Scripts & Mappings Summary
- `ifl:transferTransaction`: Processes currency exchange between source and target currencies.
- `ifl:handleError`: Handles any exceptions during processing by setting them back for immediate access or sending them directly.

## 7. Exception Handling
- All errors are handled by setting exceptions to 'true', ensuring they can be accessed from another endpoint or sent after conversion.

## 8. Properties Used
- httpSessionHandling
- accessControlMaxAge
- returnExceptionToSender
- transportEndpoint

## 9. Test Cases
1. Convert EUR to USD without errors.
2. Transaction fails due to network issues, exception set back.
3. Multiple currencies convert into euros.
4. Error occurs after conversion.

## 10. Deployment Notes
- Configure IFL extensions for the target endpoint.
- Use appropriate network interfaces and port numbers.
- Ensure the flow is properly integrated with IFL components.