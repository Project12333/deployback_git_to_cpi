import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

def Message processData(Message message) {
     
       def map = message.getProperties();
       def ManualStartDate = map.get("ManualStartDate")
       def LogStartDate = map.get("LogStartDate")
       def LogEndDate = map.get("LogEndDate")
       def whereQuery
       if (message.getProperty("Initial_Run").toUpperCase().equals("TRUE")) {
            if(message.getProperty("ManualStartDate").equals("")){
                throw new Exception("ManualStartDate Parameter not maintained for Initial_Run Trigger");
            } else{
                 message.setProperty("LogStartDate", ManualStartDate);
                 message.setProperty("LastModifiedOn", ManualStartDate);
            } 
	   }
		else{
                 message.setProperty("LogStartDate", LogStartDate);
       message.setProperty("EndDate", LogEndDate);
       return message;
       }
   
}