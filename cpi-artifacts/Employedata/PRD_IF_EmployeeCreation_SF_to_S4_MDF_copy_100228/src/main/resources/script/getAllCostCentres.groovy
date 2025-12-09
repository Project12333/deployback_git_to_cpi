import com.sap.it.api.mapping.*;
import com.sap.it.api.mapping.MappingContext;
import groovy.xml.*;

def String getCostCentreName(String externalCode, MappingContext context) {

    def Payload= context.getProperty("AllCostCentres");
    def FOCostCenter = new XmlSlurper().parseText(Payload);
        
    def CostCentreName = FOCostCenter.FOCostCenter.find{it.externalCode.text().trim()==externalCode}.name_defaultValue.text().trim();
        
    if(!(CostCentreName.isEmpty()))
       return CostCentreName;
    else{
       return CostCentreName;
    }
}

