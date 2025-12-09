import com.sap.it.api.mapping.*;
import com.sap.it.api.mapping.MappingContext;
import groovy.xml.*;

def String getResignationDate(String externalCode, MappingContext context) {

    def Payload= context.getProperty("GetAllResignations");
   
        def Emply_Resignation = new XmlSlurper().parseText(Payload);
        
        def ResignationDate = Emply_Resignation.cust_Emply_Resignation.find{it.externalCode.text().trim()==externalCode}.cust_Field4.text().trim();
        
        if(!(ResignationDate.isEmpty()))
            return ResignationDate;
        else{
            return ResignationDate;
        }
}