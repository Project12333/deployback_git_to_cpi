import com.sap.it.api.mapping.*;

import com.sap.it.api.mapping.MappingContext;

def String getProperty(String OA_ID, MappingContext context) {

    def propValue= context.getProperty(OA_ID);

    return propValue;

}