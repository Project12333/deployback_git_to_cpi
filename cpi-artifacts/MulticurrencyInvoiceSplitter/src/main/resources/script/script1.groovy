import com.sap.gateway.ip.core.customdev.util.Message;
import groovy.xml.*
Message processData(Message message) {
    def body = message.getBody(String)
    def root = new XmlSlurper().parseText(body)
    def currency = root.Currency.text()
    
    message.setProperty("InvoiceCurrency", currency)
    return message
}
