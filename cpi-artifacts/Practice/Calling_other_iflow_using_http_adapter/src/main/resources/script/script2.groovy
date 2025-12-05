import com.sap.gateway.ip.core.customdev.util.Message
import groovy.util.XmlSlurper
import groovy.xml.MarkupBuilder
import java.io.StringWriter

def Message processData(Message message) {
    def body = message.getBody(String)

    // Parse input XML (single <Customer> node after splitter)
    def customer = new XmlSlurper().parseText(body)

    // Get country from message property (e.g. set earlier in Content Modifier or Groovy)
    def country = message.getProperty("country_name")?.trim()

    // Default currency
    def currency = "USD"
    switch (country) {
        case "Germany":
            currency = "EUR"
            break
        case "Mexico":
            currency = "MXN"
            break
        case "India":
            currency = "INR"
            break
    }

    // Create new XML with original data + currency
    def writer = new StringWriter()
    def xml = new MarkupBuilder(writer)
    xml.Customer {
        fname(customer.fname.text())
        lname(customer.lname.text())
        age(customer.age.text())
        id(customer.id.text())
        gender(customer.gender.text())
        date(customer.date.text())
        Country(country)       // use country from property here
        Currency(currency)
    }

    message.setBody(writer.toString())
    return message
}
