import com.sap.gateway.ip.core.customdev.util.Message;
import groovy.json.JsonSlurper

Message processData(Message message) {
    def body = message.getBody(String)
    def json = new JsonSlurper().parseText(body)
    
    def tempList = json.hourly.temperature_2m
    def firstTemp = tempList ? tempList[0] : "N/A"

    def response = "🌡️ First hourly temperature in London: ${firstTemp}°C"
    message.setBody(response)

    return message
}
