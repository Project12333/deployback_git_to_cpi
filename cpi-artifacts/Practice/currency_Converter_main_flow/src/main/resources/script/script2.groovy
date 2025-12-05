import com.sap.gateway.ip.core.customdev.util.Message
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

Message processData(Message message) {
    def body = message.getBody(String)
    def json = new JsonSlurper().parseText(body)

    def toCurrency = message.getProperty("to")
    def converted = json.rates[toCurrency]

    def result = [convertedAmount: converted]
    message.setBody(JsonOutput.toJson(result))

    return message
}
