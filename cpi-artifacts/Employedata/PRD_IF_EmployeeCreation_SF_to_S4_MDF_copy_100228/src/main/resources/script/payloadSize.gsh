import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
import groovy.xml.StreamingMarkupBuilder
import groovy.xml.XmlUtil
import groovy.xml.*;

def Message processData(Message message) {
     
    def body = message.getBody(String);

    //size() function wil give the data in Bytes, we need to convert this to KB
    //1024 bytes = 1KB
    
    int i = body.size(); // 'i' will have the size of the payload in bytes now. We need to convert it into KB
    def k =1024;
    
    payloadsize = i.div(k); // converting size from bytes to KB
    
    message.setProperty("size", payloadsize);
    return message;
    }
