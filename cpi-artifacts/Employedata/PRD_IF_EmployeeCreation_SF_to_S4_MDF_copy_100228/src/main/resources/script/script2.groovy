import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message SFRequestLog(Message message)
{
    
         def body = message.getBody(java.lang.String) as String;
         def properties = message.getProperties()
         def messageLog = messageLogFactory.getMessageLog(message);
         if(messageLog != null && properties.get("EnablePayloadLogging").toUpperCase() == "TRUE")
         {
               messageLog.addAttachmentAsString("SF_Payload", body, "text/xml");
         }
     return message;
}

def Message OARequestLog(Message message) 
{
        def body = message.getBody(java.lang.String) as String;
        def properties = message.getProperties()
         def refID = properties.get("person_id_external")
        def messageLog = messageLogFactory.getMessageLog(message);
        if(messageLog != null && properties.get("EnablePayloadLogging").toUpperCase() == "TRUE")
        {
                messageLog.addAttachmentAsString("OA_EmpCreation_Request_" + refID , body, "text/xml");
        }
     return message;
}

def Message OAResponseLog(Message message) 
{
        def body = message.getBody(java.lang.String) as String;
        def properties = message.getProperties()
         def refID = properties.get("person_id_external")
        def messageLog = messageLogFactory.getMessageLog(message);
        if(messageLog != null && properties.get("EnablePayloadLogging").toUpperCase() == "TRUE")
        {
                messageLog.addAttachmentAsString("OA_EmpCreation_Response_" + refID , body, "text/xml");
        }
     return message;
}

def Message SharepointRequestLog(Message message) 
{
        def body = message.getBody(java.lang.String) as String;
        def properties = message.getProperties()
         def refID = properties.get("person_id_external")
        def messageLog = messageLogFactory.getMessageLog(message);
        if(messageLog != null && properties.get("EnablePayloadLogging").toUpperCase() == "TRUE")
        {
                messageLog.addAttachmentAsString("SP_EmpCreation_Request_" + refID , body, "text/xml");
        }
     return message;
}

def Message SharepointResponseLog(Message message) 
{
        def body = message.getBody(java.lang.String) as String;
        def properties = message.getProperties()
         def refID = properties.get("person_id_external")
        def messageLog = messageLogFactory.getMessageLog(message);
        if(messageLog != null && properties.get("EnablePayloadLogging").toUpperCase() == "TRUE")
        {
                messageLog.addAttachmentAsString("SP_EmpCreation_Response_" + refID , body, "text/xml");
        }
     return message;
}
