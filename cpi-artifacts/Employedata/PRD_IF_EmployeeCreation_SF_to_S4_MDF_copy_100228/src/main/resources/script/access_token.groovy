import com.sap.it.api.mapping.*;

import com.sap.it.api.mapping.MappingContext;

def String getProperty(String access_token, MappingContext context) {

    def propValue= context.getProperty(access_token);

    return propValue;

}