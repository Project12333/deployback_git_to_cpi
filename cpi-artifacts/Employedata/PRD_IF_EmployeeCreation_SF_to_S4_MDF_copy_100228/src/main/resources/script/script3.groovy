import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message requestLog(Message message) {

	def pmap = message.getProperties();
	
	def body = message.getBody(java.lang.String) as String;
	def properties = message.getProperties() as Map<String, Object>;
	
	def propertiesAsString ="\n";
	properties.each{ it -> propertiesAsString = propertiesAsString + "${it}" + "\n" };
	
	def messageLog = messageLogFactory.getMessageLog(message);    //if EnablePayloadLogging is set to true , log the payload as an attachment with name Log - Request
	if(messageLog != null && properties.get("EnablePayloadLogging") == "true") 
	{      
		messageLog.addAttachmentAsString("Log - SF Payload"  , body, "text/xml");
	}
	
	return message;
}


def Message responseLog(Message message) {

	def pmap = message.getProperties();
	
	def body = message.getBody(java.lang.String) as String;
	def properties = message.getProperties() as Map<String, Object>;
	
	def propertiesAsString ="\n";
	properties.each{ it -> propertiesAsString = propertiesAsString + "${it}" + "\n" };
	
	def messageLog = messageLogFactory.getMessageLog(message);//if EnablePayloadLogging is set to true , log the payload as an attachment with name Log - Response
	if(messageLog != null && properties.get("EnablePayloadLogging") == "true") {
		messageLog.addAttachmentAsString("Log - OA Payload" , body, "text/xml");
	}
	
	return message;
}