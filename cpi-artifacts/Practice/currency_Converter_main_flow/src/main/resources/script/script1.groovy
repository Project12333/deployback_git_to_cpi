import com.sap.gateway.ip.core.customdev.util.Message
import groovy.json.JsonSlurper

Message processData(Message message) {
    def body = message.getBody(String)
    def json = new JsonSlurper().parseText(body)
    
    message.setProperty("from", json.from)
    message.setProperty("to", json.to)
    message.setProperty("amount", json.amount)
    
    return message
}
