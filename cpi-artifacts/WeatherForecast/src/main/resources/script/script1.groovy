import com.sap.gateway.ip.core.customdev.util.Message;

Message processData(Message message) {
    def body = message.getBody(String)
    
    def messageLog = messageLogFactory.getMessageLog(message)
    if (messageLog != null) {
        messageLog.addAttachment("RawResponse.txt", body.getBytes("UTF-8"))
    }

    return message
}
