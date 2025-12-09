import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
def Message ErrorResponseLog(Message message)
{
    
         def body = message.getBody(java.lang.String) as String;
         def properties = message.getProperties()
         def messageLog = messageLogFactory.getMessageLog(message);
         String employeeid = properties.get("PersonExternalID");
         if(messageLog != null)
         {
               messageLog.addAttachmentAsString("ErrorResponse_"+employeeid, body, "text/xml");
         }
     return message;
}