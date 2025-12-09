import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message SFRequestFilterLog(Message message)
{
    
         def body = message.getBody(java.lang.String) as String;
         def properties = message.getProperties()
         def messageLog = messageLogFactory.getMessageLog(message);
         if(messageLog != null && properties.get("EnablePayloadLogging").toUpperCase() == "TRUE")
         {
               messageLog.addAttachmentAsString("SF_Payload_Filter_WithPayment.txt", body, "text/xml");
         }
     return message;
}
