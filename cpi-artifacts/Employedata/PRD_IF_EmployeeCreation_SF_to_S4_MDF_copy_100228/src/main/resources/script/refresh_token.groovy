import com.sap.it.api.mapping.*;

import com.sap.it.api.mapping.MappingContext;

def String getProperty(String refresh_token, MappingContext context) {

    def propValue= context.getProperty(refresh_token);

    return propValue;

}