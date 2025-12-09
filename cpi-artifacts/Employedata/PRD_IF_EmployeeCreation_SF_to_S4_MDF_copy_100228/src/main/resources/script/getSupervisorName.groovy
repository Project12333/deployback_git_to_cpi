import com.sap.it.api.mapping.*;
import com.sap.it.api.mapping.MappingContext;
import groovy.xml.*;

def String getSupervisorName(String externalCode, MappingContext context) {

    def Payload= context.getProperty("GetAllPerPersonal");
   
        def PerPersonal = new XmlSlurper().parseText(Payload);
        
        def Supervisorfname = PerPersonal.PerPersonal.find{it.personIdExternal.text().trim()==externalCode}.firstName.text().trim();
        def Supervisorlname = PerPersonal.PerPersonal.find{it.personIdExternal.text().trim()==externalCode}.lastName.text().trim();
        def Supervisorfullname = Supervisorfullname = Supervisorfname + ' ' + Supervisorlname;

        if(!(Supervisorfullname.isEmpty()))
            return Supervisorfullname;
        else{
            return Supervisorfullname;
        }
}