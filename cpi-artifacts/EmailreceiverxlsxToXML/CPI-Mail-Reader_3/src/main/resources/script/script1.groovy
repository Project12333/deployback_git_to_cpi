import com.sap.gateway.ip.core.customdev.util.Message
import org.apache.poi.xssf.usermodel.XSSFWorkbook
import groovy.xml.MarkupBuilder
import javax.mail.util.ByteArrayDataSource
import javax.activation.DataHandler
 
def Message processData(Message message) {
 
    // ✅ Get XLSX attachment
    def attachmentMap = message.getAttachments()
    def entry = attachmentMap.entrySet().iterator().next()
    def inputStream = entry.getValue().getInputStream()
 
    def workbook = new XSSFWorkbook(inputStream)
    def sheet = workbook.getSheetAt(0)
 
    def headerRow = sheet.getRow(0)
    def headers = headerRow.collect { it.toString().trim().replaceAll("\\s+", "") }
 
    def writer = new StringWriter()
    def xml = new MarkupBuilder(writer)
 
    xml.records {
        (1..sheet.getLastRowNum()).each { i ->
            def row = sheet.getRow(i)
            record {
                headers.eachWithIndex { header, j ->
                    def cell = row.getCell(j)
                    "${header}"(cell?.toString() ?: "")
                }
            }
        }
    }
 
    def xmlString = writer.toString()
 
    // ✅ Create new attachments map
    def newAttachmentMap = [:]
 
    // ✅ Wrap XML string as DataHandler
    def dataSource = new ByteArrayDataSource(xmlString.getBytes("UTF-8"), "application/xml")
    def dataHandler = new DataHandler(dataSource)
 
    // ✅ Add to new attachments map
    newAttachmentMap.put("customerData.xml", dataHandler)
 
    // ✅ Set updated attachments map on the message
    message.setAttachments(newAttachmentMap)
 
    // ✅ Optionally set a simple mail body
    message.setBody("XML created and attached.")
 
    return message
}