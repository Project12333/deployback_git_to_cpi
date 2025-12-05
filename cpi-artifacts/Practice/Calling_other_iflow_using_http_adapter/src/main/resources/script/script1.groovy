import com.sap.gateway.ip.core.customdev.util.Message

def Message processData(Message message) {
    def body = message.getBody(String)
    def country = new XmlSlurper().parseText(body).Country.text()
    def currency = country == "Germany" ? "EUR" :
                   country == "Mexico"  ? "MXN" :
                   "USD"
    message.setBody("<Response><Currency>${currency}</Currency></Response>")
    return message
}
