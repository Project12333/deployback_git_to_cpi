import com.sap.gateway.ip.core.customdev.util.Message
import org.apache.poi.xssf.usermodel.XSSFWorkbook
import groovy.xml.MarkupBuilder
import javax.mail.util.ByteArrayDataSource
import javax.activation.DataHandler
import java.io.ByteArrayInputStream

def Message processData(Message message) {

    // Get XLSX bytes from property
    byte[] xlsxBytes = message.getProperty("XLSX_FILE_BYTES") as byte[]
    if (xlsxBytes == null) {
        throw new Exception("XLSX file bytes not found in property.")
    }

    def inputStream = new ByteArrayInputStream(xlsxBytes)
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

    // Create XML attachment
    def newAttachmentMap = [:]
    def dataSource = new ByteArrayDataSource(xmlString.getBytes("UTF-8"), "application/xml")
    def dataHandler = new DataHandler(dataSource)
    newAttachmentMap.put("customerData.xml", dataHandler)

    message.setAttachments(newAttachmentMap)

    // Set email body
    message.setBody("Converted XML from XLSX is attached.")

    return message
}
